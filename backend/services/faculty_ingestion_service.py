"""
Faculty PDF Ingestion Service for VidyaVerse Learning Hub.

Handles:
- Safe filesystem storage of uploaded PDFs with path traversal protection
- PDF structure and content validation (magic bytes, page extraction, scan detection)
- Semantic text chunking (preserving page boundaries)
- Passage embedding via local intfloat/multilingual-e5-small model
- Persistent storage in ChromaDB ('faculty_uploads' collection)
- Transactional state updates and error logging in SQLite
- Idempotent reindexing and clean vector deletion
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Any, Optional

import pymupdf  # PyMuPDF

from backend.config import settings
from backend.repositories.uploaded_resource_repository import (
    UploadedResourceRepository,
    get_uploaded_resource_repository,
)
from backend.services.indexing import (
    clean_text,
    chunk_text,
    embed_passages,
    get_embedding_model,
)


def _safe_slug(text: str) -> str:
    """Generate a filesystem-safe slug from text."""
    slug = re.sub(r"[^\w\s-]", "", text.strip().lower())
    slug = re.sub(r"[-\s]+", "_", slug)
    return slug[:40] or "material"


def _sanitize_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal or special character issues."""
    name = Path(filename).name
    clean = re.sub(r"[^\w.-]", "_", name)
    return clean[:100] or "document.pdf"


def get_faculty_chroma_collection():
    """Return the ChromaDB collection dedicated to faculty-uploaded resources."""
    import chromadb

    settings.vectorstore_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.vectorstore_path))
    return client.get_or_create_collection(
        name=settings.faculty_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


class FacultyIngestionService:
    def __init__(self, repo: Optional[UploadedResourceRepository] = None):
        self.repo = repo or get_uploaded_resource_repository()

    def generate_canonical_chapter_id(
        self, subject_id: str, class_number: int, chapter_number: int
    ) -> str:
        """
        Generate a unique, stable canonical chapter identifier for an uploaded chapter.
        Example: 'upload_evs_c05_ch11'
        """
        clean_sub = subject_id.strip().lower()
        return f"upload_{clean_sub}_c{class_number:02d}_ch{chapter_number:02d}"

    def validate_upload_request(
        self,
        subject_id: str,
        class_number: int,
        chapter_number: int,
        chapter_name: str,
        filename: str,
        file_bytes: bytes,
    ) -> tuple[bool, str]:
        """
        Server-side validation of upload metadata and binary content.
        Returns (is_valid, error_message).
        """
        # 1. Subject validation
        clean_sub = subject_id.strip().lower()
        if clean_sub in ("math", "maths"):
            clean_sub = "mathematics"
        valid_subjects = ("history", "mathematics", "evs")
        if clean_sub not in valid_subjects:
            return False, f"Invalid subject '{subject_id}'. Supported subjects are: History, Mathematics, Environmental Studies."

        # 2. Class validation (standard 1-12)
        if not (1 <= class_number <= 12):
            return False, f"Invalid class/standard '{class_number}'. Must be between 1 and 12."

        # 3. Chapter number validation
        if chapter_number < 1:
            return False, "Chapter number must be an integer greater than 0."

        # 4. Chapter name validation
        if not chapter_name or len(chapter_name.strip()) < 2:
            return False, "Chapter name is required and must be at least 2 characters."
        if len(chapter_name.strip()) > 150:
            return False, "Chapter name cannot exceed 150 characters."

        # 5. File presence & size
        if not file_bytes:
            return False, "Uploaded file is empty (0 bytes)."
        if len(file_bytes) > settings.max_upload_size_bytes:
            max_mb = settings.max_upload_size_bytes // (1024 * 1024)
            return False, f"File size ({len(file_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed limit of {max_mb} MB."

        # 6. Filename validation
        if not filename.lower().endswith(".pdf"):
            return False, "Only PDF files (.pdf) are accepted."

        # 7. PDF Magic Bytes validation (%PDF-)
        if not file_bytes.startswith(b"%PDF-"):
            return False, "Invalid PDF file header. The uploaded file is not a valid PDF document."

        # 8. Check for existing active upload conflict
        conflict = self.repo.check_conflict(
            subject_id=clean_sub,
            class_number=class_number,
            chapter_number=chapter_number,
        )
        if conflict:
            return (
                False,
                f"Chapter {chapter_number} already exists for {subject_id.capitalize()} (Class {class_number}): '{conflict['chapter_name']}'. "
                "Please choose a different chapter number or re-index the existing resource.",
            )

        return True, ""

    def save_pdf_to_disk(
        self,
        resource_id: str,
        subject_id: str,
        class_number: int,
        chapter_number: int,
        chapter_name: str,
        original_filename: str,
        file_bytes: bytes,
    ) -> Path:
        """
        Safely store the uploaded PDF into local storage directory.
        Enforces path traversal protection and directory structure.
        """
        clean_sub = subject_id.strip().lower()
        slug = _safe_slug(chapter_name)
        safe_fname = _sanitize_filename(original_filename)

        # Directory: data/uploads/{subject}/class_{class_num}/chapter_{ch_num}_{slug}
        target_dir = (
            settings.upload_dir
            / clean_sub
            / f"class_{class_number:02d}"
            / f"chapter_{chapter_number:02d}_{slug}"
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"{resource_id}_{safe_fname}"

        # Path traversal guard
        resolved_file = target_file.resolve()
        resolved_base = settings.upload_dir.resolve()
        if not str(resolved_file).startswith(str(resolved_base)):
            raise ValueError("Path traversal attempt detected. Upload rejected.")

        with open(target_file, "wb") as f:
            f.write(file_bytes)

        return target_file

    def ingest_pdf(
        self,
        resource_id: str,
        pdf_path: Path,
        subject_id: str,
        class_number: int,
        chapter_id: str,
        chapter_number: int,
        chapter_name: str,
        original_filename: str,
    ) -> dict[str, Any]:
        """
        Executes text extraction, semantic chunking, embedding generation,
        and persistent storage in ChromaDB.
        """
        clean_sub = subject_id.strip().lower()

        try:
            # 1. Update status to 'processing'
            self.repo.update_status(resource_id=resource_id, status="processing")

            # 2. Open PDF and validate readability
            try:
                doc = pymupdf.open(str(pdf_path))
            except Exception as e:
                raise ValueError(f"Corrupted PDF file could not be parsed: {e}")

            if doc.is_encrypted:
                doc.close()
                raise ValueError("Password-protected or encrypted PDFs are not supported.")

            total_pages = len(doc)
            if total_pages == 0:
                doc.close()
                raise ValueError("The uploaded PDF contains 0 pages.")

            # 3. Extract text page-by-page
            pages_data: list[dict[str, Any]] = []
            for page_idx, page in enumerate(doc, start=1):
                raw = page.get_text()
                cleaned = clean_text(raw)
                if len(cleaned) >= 20:  # extractable threshold
                    pages_data.append({"page": page_idx, "text": cleaned})

            doc.close()

            if not pages_data:
                raise ValueError(
                    "The uploaded PDF does not contain extractable digital text. "
                    "It may be a scanned document or image-only PDF. "
                    "VidyaVerse requires PDFs with extractable digital text."
                )

            # 4. Chunk text while preserving page number
            all_chunks: list[dict[str, Any]] = []
            for p in pages_data:
                chunks = chunk_text(
                    p["text"],
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap,
                )
                for chunk in chunks:
                    all_chunks.append({"text": chunk, "page": p["page"]})

            if not all_chunks:
                raise ValueError("Could not generate text chunks from the extracted pages.")

            # 5. Generate embeddings with 'passage: ' prefix in batches of 32
            batch_size = 32
            all_texts = [c["text"] for c in all_chunks]
            all_vectors: list[list[float]] = []

            for i in range(0, len(all_texts), batch_size):
                batch = all_texts[i : i + batch_size]
                all_vectors.extend(embed_passages(batch))

            # 6. Prepare IDs and standardized metadata
            chunk_ids = [f"{resource_id}_chunk_{i:04d}" for i in range(len(all_chunks))]
            metadatas = [
                {
                    "resource_id": resource_id,
                    "subject_id": clean_sub,
                    "class_number": int(class_number),
                    "chapter_id": chapter_id,
                    "chapter_number": int(chapter_number),
                    "chapter_name": chapter_name,
                    "source_type": "faculty_upload",
                    "pdf_page": int(c["page"]),
                    "source": original_filename,
                }
                for c in all_chunks
            ]

            # 7. Upsert into ChromaDB
            collection = get_faculty_chroma_collection()

            # Clean any existing chunks for this resource_id to ensure idempotency
            try:
                collection.delete(where={"resource_id": resource_id})
            except Exception:
                pass

            collection.upsert(
                ids=chunk_ids,
                embeddings=all_vectors,
                documents=all_texts,
                metadatas=metadatas,
            )

            # 8. Mark resource as 'indexed' in SQLite
            updated = self.repo.update_status(
                resource_id=resource_id,
                status="indexed",
                chunk_count=len(all_chunks),
                error_message=None,
            )

            return {
                "resource_id": resource_id,
                "status": "indexed",
                "chunks": len(all_chunks),
                "pages": total_pages,
            }

        except Exception as e:
            err_msg = str(e)
            print(f"[FacultyIngestion] Error ingesting {resource_id}: {err_msg}")
            self.repo.update_status(
                resource_id=resource_id,
                status="failed",
                error_message=err_msg,
            )
            raise

    def delete_resource_and_vectors(self, resource_id: str) -> bool:
        """
        Completely deletes an uploaded resource:
        1. Removes embeddings from ChromaDB
        2. Deletes the physical PDF file
        3. Deletes record from SQLite
        """
        res = self.repo.get_resource(resource_id)
        if not res:
            return False

        # 1. Delete vectors
        try:
            collection = get_faculty_chroma_collection()
            collection.delete(where={"resource_id": resource_id})
        except Exception as e:
            print(f"[FacultyIngestion] Vector cleanup notice: {e}")

        # 2. Delete file
        stored_path = res.get("stored_path")
        if stored_path:
            p = Path(stored_path)
            try:
                if p.exists():
                    p.unlink()
                # Remove parent directory if empty
                if p.parent.exists() and not any(p.parent.iterdir()):
                    p.parent.rmdir()
            except Exception as e:
                print(f"[FacultyIngestion] File deletion notice: {e}")

        # 3. Delete database record
        return self.repo.delete_resource(resource_id)


# Global singleton ingestion service
_faculty_ingestion: Optional[FacultyIngestionService] = None


def get_faculty_ingestion_service() -> FacultyIngestionService:
    global _faculty_ingestion
    if _faculty_ingestion is None:
        _faculty_ingestion = FacultyIngestionService()
    return _faculty_ingestion
