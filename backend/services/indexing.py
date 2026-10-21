"""
Indexing pipeline for EVS chapter PDFs.

Usage:
    python -m backend.indexing               # index only new/missing chapters
    python -m backend.indexing --force       # re-index all chapters
    python -m backend.indexing --dry-run     # show what would be done, do nothing
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF

from backend.config import settings
from backend.services.catalog import EVS_CHAPTER_MAP, get_evs_chapter_pdf_path


# ── Text utilities ─────────────────────────────────────────────────────────────


def clean_text(text: str) -> str:
    """Remove excessive whitespace and garbage characters from extracted text."""
    text = re.sub(r"[ \t]+", " ", text)          # collapse horizontal whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse 3+ blank lines to 2
    text = re.sub(r"[^\S\n]+\n", "\n", text)      # strip trailing spaces on lines
    text = text.strip()
    return text


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping character-based chunks.
    Tries to break at sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # Try to break at sentence boundary within last 20% of the chunk
            search_start = start + int(chunk_size * 0.8)
            break_pos = -1
            for sep in [". ", ".\n", "? ", "! ", "\n\n"]:
                pos = text.rfind(sep, search_start, end)
                if pos != -1:
                    break_pos = pos + len(sep)
                    break
            if break_pos != -1:
                end = break_pos
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap

    return chunks


# ── PDF extraction ─────────────────────────────────────────────────────────────


def extract_pages(pdf_path: Path) -> list[dict]:
    """
    Extract text page-by-page from a PDF.
    Returns list of {"page": int, "text": str} dicts.
    Only returns pages with extractable text.
    """
    pages = []
    try:
        doc = pymupdf.open(str(pdf_path))
        for page_num, page in enumerate(doc, start=1):
            raw = page.get_text()
            cleaned = clean_text(raw)
            if len(cleaned) >= 20:   # skip near-empty/scanned pages
                pages.append({"page": page_num, "text": cleaned})
            else:
                print(f"  ⚠  Page {page_num}: little text extracted (possibly scanned)")
        doc.close()
    except Exception as e:
        print(f"  ✗  Failed to open {pdf_path.name}: {e}")
    return pages


# ── Embedding ──────────────────────────────────────────────────────────────────


_embedding_model = None


def get_embedding_model():
    """Load and cache the sentence-transformers model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model: {settings.embedding_model_name} …")
        try:
            _embedding_model = SentenceTransformer(settings.embedding_model_name, local_files_only=True)
        except Exception:
            _embedding_model = SentenceTransformer(settings.embedding_model_name)
        print("  ✓  Embedding model loaded.")
    return _embedding_model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed texts with the passage: prefix required by E5 models."""
    model = get_embedding_model()
    prefixed = [f"passage: {t}" for t in texts]
    vectors = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


# ── ChromaDB ───────────────────────────────────────────────────────────────────


def get_chroma_collection():
    """Return (create if needed) the single unified ChromaDB collection."""
    import chromadb
    settings.vectorstore_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.vectorstore_path))
    collection = client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def get_indexed_chapter_ids(collection) -> set[str]:
    """Return set of chapter_ids that already have chunks in the collection."""
    if collection.count() == 0:
        return set()
    results = collection.get(include=["metadatas"])
    return {m.get("chapter_id") for m in results["metadatas"] if m.get("chapter_id")}


def delete_chapter_chunks(collection, chapter_id: str) -> int:
    """Delete all chunks for a given chapter_id from the collection."""
    results = collection.get(where={"chapter_id": chapter_id}, include=["metadatas"])
    ids = results["ids"]
    if ids:
        collection.delete(ids=ids)
    return len(ids)


# ── Main indexing logic ────────────────────────────────────────────────────────


def index_chapter(
    collection,
    stem: str,
    chapter_num: int,
    chapter_id: str,
    chapter_title: str,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Index one EVS chapter. Returns a result dict.
    """
    pdf_path = get_evs_chapter_pdf_path(chapter_id)
    if pdf_path is None:
        return {"chapter_id": chapter_id, "status": "no_pdf", "chunks": 0}

    # Determine whether to skip
    indexed_ids = get_indexed_chapter_ids(collection)
    already_indexed = chapter_id in indexed_ids

    if already_indexed and not force:
        print(f"  ⏭  {chapter_id} already indexed — skipping (use --force to re-index)")
        return {"chapter_id": chapter_id, "status": "skipped", "chunks": 0}

    if dry_run:
        print(f"  [DRY-RUN] Would index {chapter_id} from {pdf_path.name}")
        return {"chapter_id": chapter_id, "status": "dry_run", "chunks": 0}

    print(f"\n📄 Indexing {chapter_id}: {chapter_title}")
    print(f"   File: {pdf_path.name}")

    # Delete stale chunks if force-reindexing
    if already_indexed and force:
        deleted = delete_chapter_chunks(collection, chapter_id)
        print(f"   Deleted {deleted} stale chunks.")

    # Extract
    pages = extract_pages(pdf_path)
    if not pages:
        print(f"  ✗  No extractable text in {pdf_path.name}")
        return {"chapter_id": chapter_id, "status": "no_text", "chunks": 0}

    total_chars = sum(len(p["text"]) for p in pages)
    print(f"   Extracted {len(pages)} pages, {total_chars} chars")

    # Chunk
    all_chunks: list[dict] = []
    for page_data in pages:
        page_num = page_data["page"]
        chunks = chunk_text(page_data["text"], settings.chunk_size, settings.chunk_overlap)
        for chunk in chunks:
            all_chunks.append({"text": chunk, "page": page_num})

    print(f"   Created {len(all_chunks)} chunks")

    if not all_chunks:
        return {"chapter_id": chapter_id, "status": "no_chunks", "chunks": 0}

    # Embed in batches of 32
    batch_size = 32
    all_texts = [c["text"] for c in all_chunks]
    all_vectors: list[list[float]] = []
    for i in range(0, len(all_texts), batch_size):
        batch = all_texts[i : i + batch_size]
        all_vectors.extend(embed_passages(batch))
    print(f"   Generated {len(all_vectors)} embeddings")

    # Build IDs and metadata
    ids = [f"{chapter_id}_chunk_{i:04d}" for i in range(len(all_chunks))]
    metadatas = [
        {
            "subject_id": "EVS",
            "chapter_id": chapter_id,
            "chapter_name": chapter_title,
            "source": pdf_path.name,
            "page_number": c["page"],
        }
        for c in all_chunks
    ]

    # Upsert into ChromaDB
    collection.upsert(
        ids=ids,
        embeddings=all_vectors,
        documents=all_texts,
        metadatas=metadatas,
    )
    print(f"  ✓  Indexed {len(all_chunks)} chunks → {chapter_id}")
    return {"chapter_id": chapter_id, "status": "indexed", "chunks": len(all_chunks)}


def run_indexing(force: bool = False, dry_run: bool = False) -> list[dict]:
    """
    Index all available EVS chapter PDFs.
    Returns list of per-chapter result dicts.
    """
    print("=" * 60)
    print("Class 5 Chatbot — Indexing Pipeline")
    print(f"Collection: {settings.chroma_collection_name}")
    print(f"Vectorstore: {settings.vectorstore_path}")
    print(f"Force: {force} | Dry-run: {dry_run}")
    print("=" * 60)

    if not dry_run:
        collection = get_chroma_collection()
    else:
        collection = None  # won't be used

    results = []
    for stem, (num, chapter_id, title) in sorted(EVS_CHAPTER_MAP.items(), key=lambda x: x[1][0]):
        result = index_chapter(
            collection=collection,
            stem=stem,
            chapter_num=num,
            chapter_id=chapter_id,
            chapter_title=title,
            force=force,
            dry_run=dry_run,
        )
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("Indexing summary:")
    for r in results:
        status_icon = {"indexed": "✓", "skipped": "⏭", "no_pdf": "✗", "no_text": "✗", "no_chunks": "✗", "dry_run": "○"}.get(r["status"], "?")
        print(f"  {status_icon}  {r['chapter_id']:12s}  {r['status']:12s}  chunks: {r['chunks']}")

    if not dry_run and collection is not None:
        print(f"\nTotal chunks in collection: {collection.count()}")
    print("=" * 60)
    return results


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index EVS chapter PDFs into ChromaDB.")
    parser.add_argument("--force", action="store_true", help="Re-index all chapters (delete existing chunks first).")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be indexed without doing anything.")
    args = parser.parse_args()

    results = run_indexing(force=args.force, dry_run=args.dry_run)
    failed = [r for r in results if r["status"] in ("no_pdf", "no_text", "no_chunks")]
    sys.exit(1 if failed else 0)
