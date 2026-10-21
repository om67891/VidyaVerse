"""
Master Mathematics Part II Textbook Indexing Pipeline.

Indexes the 7 chapters of Mathematics Part II (Standard X) into a dedicated ChromaDB
collection (`mathematics_master`), preserving exact PDF page numbers, printed book page
numbers, chapter IDs, and mathematical topic metadata.

Usage:
    python -m backend.services.math_indexing            # index if missing
    python -m backend.services.math_indexing --force    # re-index from scratch
    python -m backend.services.math_indexing --dry-run  # simulate extraction
"""
from __future__ import annotations

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF

from backend.config import settings

MATH_MANIFEST_PATH = settings.subjects_base_path / "Maths" / "metadata" / "chapter_manifest.json"
MATH_CHAPTERS_DIR = settings.subjects_base_path / "Maths" / "chapters"


def clean_text(text: str) -> str:
    """Normalize whitespace and clean up raw PDF text."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+\n", "\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    """
    Split text into overlapping character-based chunks, breaking at sentence / definition boundaries.
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
            for sep in [". ", ".\n", "? ", "! ", "\n\n", ";\n"]:
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


def load_math_chapters_manifest() -> list[dict]:
    """Load the verified chapter metadata from Maths/metadata/chapter_manifest.json."""
    if not MATH_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Math manifest missing at {MATH_MANIFEST_PATH}")
    with open(MATH_MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chapters", [])


def extract_math_chunks() -> list[dict]:
    """
    Extract text page-by-page from all 7 Mathematics chapter PDFs and chunk them.
    Returns list of dicts with:
      id, text, metadata { subject_id, chapter_id, chapter_number, chapter_title,
                           source, chapter_pdf, page_number, pdf_page, book_page, chunk_id }
    """
    chapters = load_math_chapters_manifest()
    all_chunks: list[dict] = []

    print(f"[*] Extracting text from {len(chapters)} Mathematics chapters...")

    for ch in chapters:
        ch_id = ch["chapter_id"]
        ch_num = ch["chapter_number"]
        ch_title = ch["title"]
        rel_pdf = ch.get("pdf_path", "")
        pdf_path = settings.subjects_base_path / "Maths" / rel_pdf
        if not pdf_path.exists():
            # Try chapters dir
            pdf_path = MATH_CHAPTERS_DIR / Path(rel_pdf).name

        if not pdf_path.exists():
            print(f"  [!] Missing PDF for Chapter {ch_num}: {pdf_path}")
            continue

        source_start_pdf = ch.get("source_pdf_page_start_1based", 1)
        printed_start = ch.get("printed_book_page_start", 1)

        doc = pymupdf.open(str(pdf_path))
        print(f"  -> Ch.{ch_num:02d}: {ch_title} ({len(doc)} pages in {pdf_path.name})")

        for page_idx, page in enumerate(doc):
            ch_page_num = page_idx + 1
            master_pdf_page = source_start_pdf + page_idx
            printed_book_page = printed_start + page_idx

            raw = page.get_text()
            cleaned = clean_text(raw)
            if len(cleaned) < 25:
                continue

            page_chunks = chunk_text(cleaned, chunk_size=700, overlap=120)
            for c_idx, chunk in enumerate(page_chunks, start=1):
                chunk_id = f"MATH_CH{ch_num:02d}_P{ch_page_num:02d}_C{c_idx:02d}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        "subject_id": "MATHEMATICS",
                        "chapter_id": ch_id,
                        "chapter_number": ch_num,
                        "chapter_title": ch_title,
                        "chapter_name": ch_title,
                        "source": "Mathematics.pdf",
                        "chapter_pdf": pdf_path.name,
                        "page_number": printed_book_page,
                        "pdf_page": master_pdf_page,
                        "book_page": printed_book_page,
                        "chunk_id": chunk_id,
                    },
                })
        doc.close()

    print(f"[*] Total extracted Mathematics chunks: {len(all_chunks)}")
    return all_chunks


def index_mathematics(force: bool = False, dry_run: bool = False) -> int:
    """
    Embed and store Mathematics chunks in ChromaDB `mathematics_master` collection.
    """
    import chromadb
    from backend.services.indexing import get_embedding_model

    client = chromadb.PersistentClient(path=str(settings.vectorstore_path))
    collection_name = settings.math_collection_name

    existing_collections = [c.name for c in client.list_collections()]
    if collection_name in existing_collections:
        col = client.get_collection(collection_name)
        existing_count = col.count()
        if existing_count > 0 and not force:
            print(f"[i] Collection '{collection_name}' already indexed with {existing_count} chunks. Use --force to reindex.")
            return existing_count
        if force:
            print(f"[*] Deleting existing collection '{collection_name}' ({existing_count} chunks)...")
            client.delete_collection(collection_name)

    chunks = extract_math_chunks()
    if dry_run:
        print(f"[dry-run] Would index {len(chunks)} chunks into '{collection_name}'. Exiting.")
        return len(chunks)

    if not chunks:
        print("[!] No chunks extracted for Mathematics.")
        return 0

    print(f"[*] Creating ChromaDB collection '{collection_name}'...")
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "l2", "description": "Standard X Mathematics Part II Chapter Chunks"}
    )

    print("[*] Loading embedding model...")
    model = get_embedding_model()

    batch_size = 64
    total = len(chunks)
    print(f"[*] Embedding and inserting {total} chunks in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        texts = [b["text"] for b in batch]
        ids = [b["id"] for b in batch]
        metadatas = [b["metadata"] for b in batch]

        # Use passage: prefix for E5 embedding
        prefixed = [f"passage: {t}" for t in texts]
        vectors = model.encode(prefixed, normalize_embeddings=True).tolist()

        collection.add(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"  Indexed chunks {i + 1}..{min(i + batch_size, total)} of {total}")

    final_count = collection.count()
    print(f"[✓] Mathematics indexing complete! Total chunks stored: {final_count}")
    return final_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Mathematics textbook into ChromaDB")
    parser.add_argument("--force", action="store_true", help="Force re-indexing from scratch")
    parser.add_argument("--dry-run", action="store_true", help="Simulate extraction without writing")
    args = parser.parse_args()

    index_mathematics(force=args.force, dry_run=args.dry_run)
