"""
Master History Textbook Indexing Pipeline.

Indexes the entire master textbook `History/History.pdf` into a dedicated ChromaDB
collection (`history_master`), preserving exact PDF page numbers, book page numbers,
and lesson metadata for each chunk.

Usage:
    python -m backend.services.history_indexing            # index if missing
    python -m backend.services.history_indexing --force    # re-index from scratch
    python -m backend.services.history_indexing --dry-run  # simulate extraction
"""
from __future__ import annotations

import os
# Prevent OpenBLAS thread pool exhaustion on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF

from backend.config import settings

# ── 18 Lessons Page Boundaries in History.pdf ─────────────────────────────────
# book_page = pdf_page - 10 for pages 11..90
LESSON_RANGES = [
    (1, "Maharashtra before Shivaji", 11, 12, 1, 2),
    (2, "Work of the Saints", 13, 17, 3, 7),
    (3, "Maratha Sardars - The Famous House of the Bhonsales", 18, 21, 8, 11),
    (4, "Shivaji's Childhood", 22, 26, 12, 16),
    (5, "Shivaji's Education", 27, 30, 17, 20),
    (6, "The Oath of Swaraj", 31, 34, 21, 24),
    (7, "Swaraj : First Conquest", 35, 38, 25, 28),
    (8, "Defeat of Internal Enemies", 39, 41, 29, 31),
    (9, "Pratapgad makes History", 42, 46, 32, 36),
    (10, "Baji Prabhu and the Memorable Battle of Ghodkhind", 47, 51, 37, 41),
    (11, "The Discomfiture of Shaistakhan", 52, 54, 42, 44),
    (12, "The Siege of Purandar and the Treaty with the Moghul Emperor", 55, 59, 45, 49),
    (13, "Shivaji gives the slip to the Emperor", 60, 62, 50, 52),
    (14, "The Fort is captured but the Lion is dead", 63, 66, 53, 56),
    (15, "A Memorable Ceremony", 67, 69, 57, 59),
    (16, "Campaign in the South", 70, 74, 60, 64),
    (17, "Management of Forts and the Navy", 75, 79, 65, 69),
    (18, "Management of the Welfare State of Swaraj", 80, 90, 70, 80),
]


def get_lesson_for_pdf_page(pdf_page: int) -> tuple[int, str]:
    """Return (lesson_number, lesson_title) for a given 1-based PDF page."""
    for num, title, p_start, p_end, _, _ in LESSON_RANGES:
        if p_start <= pdf_page <= p_end:
            return num, title
    if pdf_page <= 10:
        return 0, "Front Matter & Table of Contents"
    return 18, "Management of the Welfare State of Swaraj"


# ── Text Cleaning & Chunking ──────────────────────────────────────────────────


def clean_text(text: str) -> str:
    """Normalize whitespace and remove junk characters."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+\n", "\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    """
    Split text into overlapping character-based chunks, breaking at sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            search_start = start + int(chunk_size * 0.75)
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
        start = max(end - overlap, start + 1)

    return chunks


# ── PDF Extraction ────────────────────────────────────────────────────────────


def extract_history_pages(pdf_path: Path) -> list[dict]:
    """
    Extract text page-by-page from History.pdf.
    Returns list of dicts:
        {
            "pdf_page": int,
            "book_page": int,
            "lesson_number": int,
            "lesson_title": str,
            "text": str
        }
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"History PDF not found at: {pdf_path}")

    doc = pymupdf.open(str(pdf_path))
    extracted = []

    for page_idx in range(len(doc)):
        pdf_page = page_idx + 1  # 1-indexed PDF page
        raw_text = doc[page_idx].get_text()
        cleaned = clean_text(raw_text)

        # Skip completely blank pages (e.g. covers without text, blank end pages)
        if len(cleaned) < 15:
            continue

        book_page = pdf_page - 10 if 11 <= pdf_page <= 90 else 0
        lesson_num, lesson_title = get_lesson_for_pdf_page(pdf_page)

        extracted.append({
            "pdf_page": pdf_page,
            "book_page": book_page,
            "lesson_number": lesson_num,
            "lesson_title": lesson_title,
            "text": cleaned,
        })

    doc.close()
    return extracted


# ── Embedding & ChromaDB ──────────────────────────────────────────────────────


_embedding_model = None


def get_embedding_model():
    """Load and cache the sentence-transformers model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model: {settings.embedding_model_name} ...")
        _embedding_model = SentenceTransformer(settings.embedding_model_name)
        print("  ✓ Embedding model loaded.")
    return _embedding_model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed texts with 'passage: ' prefix required by E5 models."""
    model = get_embedding_model()
    prefixed = [f"passage: {t}" for t in texts]
    vectors = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(query: str) -> list[float]:
    """Embed a search query with 'query: ' prefix required by E5 models."""
    model = get_embedding_model()
    prefixed = f"query: {query.strip()}"
    vector = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return vector.tolist()


def get_history_collection():
    """Return (or create) the dedicated ChromaDB collection for the master History textbook."""
    import chromadb
    settings.vectorstore_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.vectorstore_path))
    collection = client.get_or_create_collection(
        name=settings.history_collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ── Indexing Logic ────────────────────────────────────────────────────────────


def run_history_indexing(force: bool = False, dry_run: bool = False) -> dict:
    """
    Index the complete History textbook into the dedicated history_master collection.
    Skips if already indexed unless force=True.
    """
    pdf_path = settings.history_pdf_path
    if not pdf_path.exists():
        raise FileNotFoundError(f"Master History textbook missing: {pdf_path}")

    collection = get_history_collection()
    current_count = collection.count()

    if current_count > 0 and not force:
        print(f"  ⏭ History collection '{settings.history_collection_name}' already contains {current_count} chunks.")
        print("     Skipping indexing. (Use --force to force re-indexing)")
        return {
            "status": "skipped",
            "collection_name": settings.history_collection_name,
            "total_chunks": current_count,
            "message": "Already indexed. Pass force=True to re-index.",
        }

    print(f"\n📚 Extracting pages from master History textbook: {pdf_path} ...")
    pages = extract_history_pages(pdf_path)
    print(f"  ✓ Extracted {len(pages)} content pages from {pdf_path.name}")

    # Build all chunks
    all_chunks: list[dict] = []
    for p_info in pages:
        chunks = chunk_text(p_info["text"], chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
        for c_idx, chunk in enumerate(chunks, start=1):
            chunk_id = f"HIST_P{p_info['pdf_page']:02d}_C{c_idx:02d}"
            all_chunks.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    "subject_id": "HISTORY",
                    "source": "History.pdf",
                    "pdf_page": p_info["pdf_page"],
                    "page_number": p_info["pdf_page"],  # Primary citation standard
                    "book_page": p_info["book_page"],
                    "lesson_number": p_info["lesson_number"],
                    "lesson_title": p_info["lesson_title"],
                    "chunk_id": chunk_id,
                }
            })

    print(f"  ✓ Prepared {len(all_chunks)} chunks across {len(pages)} pages.")

    if dry_run:
        print(f"  [DRY RUN] Would index {len(all_chunks)} chunks into '{settings.history_collection_name}'.")
        return {
            "status": "dry_run",
            "collection_name": settings.history_collection_name,
            "extracted_pages": len(pages),
            "chunks_prepared": len(all_chunks),
        }

    # If force, delete existing chunks from the collection
    if current_count > 0 and force:
        print(f"  🗑 Force re-indexing: purging existing {current_count} chunks from '{settings.history_collection_name}' ...")
        import chromadb
        client = chromadb.PersistentClient(path=str(settings.vectorstore_path))
        client.delete_collection(name=settings.history_collection_name)
        collection = client.create_collection(
            name=settings.history_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # Batch embedding and upsert
    batch_size = 64
    print(f"  ⚡ Generating embeddings and storing in ChromaDB in batches of {batch_size} ...")

    total_added = 0
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        embeddings = embed_passages(texts)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total_added += len(batch)
        print(f"    Indexed {total_added}/{len(all_chunks)} chunks ...")

    final_count = collection.count()
    print(f"  ✓ Master History indexing complete! Total chunks stored: {final_count}")

    return {
        "status": "indexed",
        "collection_name": settings.history_collection_name,
        "extracted_pages": len(pages),
        "total_chunks": final_count,
    }


def verify_retrieval() -> bool:
    """
    Run test queries against history_master to verify retrieval across different parts of the book.
    """
    collection = get_history_collection()
    if collection.count() == 0:
        print("  ✗ Cannot verify: History collection is empty.")
        return False

    test_queries = [
        ("Where was Shivaji Maharaj born?", [22, 23]),                 # Lesson 4: Shivneri
        ("Who took the oath of Swaraj at Raireshwar?", [31, 32, 33]),   # Lesson 6: Raireshwar
        ("What happened to Afzalkhan at Pratapgad?", [42, 43, 44, 45]), # Lesson 9: Pratapgad
        ("Who defended Ghodkhind with great courage?", [47, 48, 49]),   # Lesson 10: Baji Prabhu
        ("How did Shivaji Maharaj escape from Agra?", [60, 61, 62]),     # Lesson 13: Agra escape
    ]

    print("\n🔍 Verifying History RAG retrieval against history_master:")
    all_ok = True

    for query, expected_pages in test_queries:
        q_emb = embed_query(query)
        res = collection.query(query_embeddings=[q_emb], n_results=3, include=["documents", "metadatas", "distances"])
        matched_pages = [m["pdf_page"] for m in res["metadatas"][0]]
        distances = res["distances"][0]

        hit = any(p in expected_pages for p in matched_pages)
        status_symbol = "✓" if hit else "⚠"
        print(f"  {status_symbol} Query: '{query}' -> Top Pages: {matched_pages} (Distances: {[round(d, 3) for d in distances]})")
        if not hit:
            all_ok = False

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master History Textbook Indexer")
    parser.add_argument("--force", action="store_true", help="Force re-indexing all chunks")
    parser.add_argument("--dry-run", action="store_true", help="Simulate extraction and chunking")
    parser.add_argument("--verify", action="store_true", help="Verify retrieval on indexed collection")
    args = parser.parse_args()

    if args.verify:
        verify_retrieval()
    else:
        result = run_history_indexing(force=args.force, dry_run=args.dry_run)
        print("\nResult:", result)
        if not args.dry_run:
            verify_retrieval()
