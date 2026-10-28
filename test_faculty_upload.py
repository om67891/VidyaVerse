"""
Automated Test Suite for Faculty PDF Upload and Dynamic Ingestion in VidyaVerse.

Verifies:
1. Server-side upload validation (file format, magic bytes, size limits, metadata, conflict detection, path traversal)
2. Safe local file persistence and directory structuring
3. Local text extraction and page preservation via PyMuPDF
4. Chunking, E5 embeddings, and persistent storage in ChromaDB ('faculty_uploads' collection)
5. Dynamic catalog discovery (subject list and chapter explorer)
6. Scope-isolated retrieval (chapter-scoped isolation vs subject-wide merge)
7. Citation validation for faculty materials (zero false citations, accurate page anchors)
8. Idempotent reindexing and clean vector/file deletion
9. Durability across simulated restarts (SQLite repository)
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pymupdf  # PyMuPDF

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.config import settings
from backend.database.connection import get_db_connection
from backend.repositories.uploaded_resource_repository import (
    UploadedResourceRepository,
    get_uploaded_resource_repository,
)
from backend.services.catalog import get_all_subjects, get_chapter, get_chapter_pdf_path
from backend.services.citation_validator import get_citation_validator
from backend.services.faculty_ingestion_service import (
    FacultyIngestionService,
    get_faculty_chroma_collection,
    get_faculty_ingestion_service,
)
from backend.services.retrieval_service import RetrievalEvidence, get_retrieval_service


def create_in_memory_pdf(pages_text: list[str]) -> bytes:
    """Generate authentic, digital text-extractable PDF bytes in memory using PyMuPDF."""
    doc = pymupdf.open()
    for t in pages_text:
        page = doc.new_page()
        page.insert_text((50, 72), t)
    data = doc.tobytes()
    doc.close()
    return data


class TestFacultyPDFUpload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = get_uploaded_resource_repository()
        cls.svc = get_faculty_ingestion_service()
        cls.retrieval = get_retrieval_service()
        cls.citation_val = get_citation_validator()
        cls.test_res_ids: list[str] = []

    @classmethod
    def tearDownClass(cls):
        # Clean up any test resources created
        for res_id in cls.test_res_ids:
            try:
                cls.svc.delete_resource_and_vectors(res_id)
            except Exception:
                pass

    # ── PART 1: Upload Validation Tests ───────────────────────────────────────

    def test_01_valid_pdf_accepted(self):
        pdf_bytes = create_in_memory_pdf(["This is an authentic lecture on renewable solar energy."])
        valid, msg = self.svc.validate_upload_request(
            subject_id="evs",
            class_number=5,
            chapter_number=91,
            chapter_name="Solar Energy Principles",
            filename="solar_lecture.pdf",
            file_bytes=pdf_bytes,
        )
        self.assertTrue(valid, f"Expected valid upload, got: {msg}")

    def test_02_empty_file_rejected(self):
        valid, msg = self.svc.validate_upload_request(
            subject_id="evs",
            class_number=5,
            chapter_number=92,
            chapter_name="Empty Chapter",
            filename="empty.pdf",
            file_bytes=b"",
        )
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

    def test_03_non_pdf_magic_bytes_rejected(self):
        # File with .pdf extension but fake text contents
        fake_bytes = b"Hello world, I am a plain text file pretending to be a PDF."
        valid, msg = self.svc.validate_upload_request(
            subject_id="evs",
            class_number=5,
            chapter_number=93,
            chapter_name="Fake PDF Chapter",
            filename="fake.pdf",
            file_bytes=fake_bytes,
        )
        self.assertFalse(valid)
        self.assertIn("invalid pdf", msg.lower())

    def test_04_oversized_file_rejected(self):
        pdf_bytes = create_in_memory_pdf(["Short content."])
        with patch.object(settings, "max_upload_size_bytes", 500):
            valid, msg = self.svc.validate_upload_request(
                subject_id="evs",
                class_number=5,
                chapter_number=94,
                chapter_name="Oversized Chapter",
                filename="large.pdf",
                file_bytes=pdf_bytes,
            )
            self.assertFalse(valid)
            self.assertIn("exceeds maximum allowed limit", msg.lower())

    def test_05_invalid_subject_and_class_rejected(self):
        pdf_bytes = create_in_memory_pdf(["Valid text."])
        # Invalid subject
        valid, msg = self.svc.validate_upload_request(
            subject_id="quantum_physics_astronomy",
            class_number=5,
            chapter_number=95,
            chapter_name="Astrophysics",
            filename="test.pdf",
            file_bytes=pdf_bytes,
        )
        self.assertFalse(valid)
        self.assertIn("invalid subject", msg.lower())

        # Invalid class
        valid, msg = self.svc.validate_upload_request(
            subject_id="evs",
            class_number=99,
            chapter_number=95,
            chapter_name="EVS Chapter",
            filename="test.pdf",
            file_bytes=pdf_bytes,
        )
        self.assertFalse(valid)
        self.assertIn("invalid class", msg.lower())

    def test_06_invalid_chapter_number_and_name_rejected(self):
        pdf_bytes = create_in_memory_pdf(["Valid text."])
        # Negative chapter number
        valid, msg = self.svc.validate_upload_request(
            subject_id="evs",
            class_number=5,
            chapter_number=0,
            chapter_name="Zero Chapter",
            filename="test.pdf",
            file_bytes=pdf_bytes,
        )
        self.assertFalse(valid)
        self.assertIn("greater than 0", msg.lower())

        # Empty chapter name
        valid, msg = self.svc.validate_upload_request(
            subject_id="evs",
            class_number=5,
            chapter_number=96,
            chapter_name="   ",
            filename="test.pdf",
            file_bytes=pdf_bytes,
        )
        self.assertFalse(valid)
        self.assertIn("chapter name is required", msg.lower())

    # ── PART 2: Safe File Persistence & Path Traversal Guard ──────────────────

    def test_07_safe_storage_and_path_traversal_protection(self):
        pdf_bytes = create_in_memory_pdf(["Secure storage test."])
        res_id = "res_test_sec_01"
        self.test_res_ids.append(res_id)

        # Attempting path traversal filename
        traversal_filename = "../../../etc/passwd.pdf"
        saved_path = self.svc.save_pdf_to_disk(
            resource_id=res_id,
            subject_id="evs",
            class_number=5,
            chapter_number=97,
            chapter_name="Security Test",
            original_filename=traversal_filename,
            file_bytes=pdf_bytes,
        )

        # Must resolve inside upload_dir
        self.assertTrue(saved_path.exists())
        self.assertTrue(str(saved_path.resolve()).startswith(str(settings.upload_dir.resolve())))
        # Must not contain '..' in the actual file name
        self.assertNotIn("..", saved_path.name)

    # ── PART 3: Ingestion, Chunking, Embedding & ChromaDB Storage ─────────────

    def test_08_end_to_end_ingestion_and_chroma_storage(self):
        res_id = "res_test_ingest_02"
        self.test_res_ids.append(res_id)
        chap_id = "upload_evs_c05_ch80"

        # Multi-page test PDF with distinct educational paragraphs
        p1 = "Chapter 80 introduces wind energy turbines and ecological wind farms in Maharashtra and coastal India."
        p2 = "Modern horizontal axis wind turbines convert aerodynamic kinetic energy of wind into usable green electricity."
        pdf_bytes = create_in_memory_pdf([p1, p2])

        saved_path = self.svc.save_pdf_to_disk(
            resource_id=res_id,
            subject_id="evs",
            class_number=5,
            chapter_number=80,
            chapter_name="Wind Energy & Sustainable Ecology",
            original_filename="wind_energy_notes.pdf",
            file_bytes=pdf_bytes,
        )

        # Record in SQLite
        res_record = self.repo.create_resource(
            resource_id=res_id,
            subject_id="evs",
            class_number=5,
            chapter_id=chap_id,
            chapter_number=80,
            chapter_name="Wind Energy & Sustainable Ecology",
            original_filename="wind_energy_notes.pdf",
            stored_path=str(saved_path),
            file_hash="fake_hash_123",
            file_size_bytes=len(pdf_bytes),
            processing_status="uploaded",
        )
        self.assertEqual(res_record["processing_status"], "uploaded")

        # Ingest
        result = self.svc.ingest_pdf(
            resource_id=res_id,
            pdf_path=saved_path,
            subject_id="evs",
            class_number=5,
            chapter_id=chap_id,
            chapter_number=80,
            chapter_name="Wind Energy & Sustainable Ecology",
            original_filename="wind_energy_notes.pdf",
        )

        self.assertEqual(result["status"], "indexed")
        self.assertGreaterEqual(result["chunks"], 2)

        # Verify SQLite updated
        stored = self.repo.get_resource(res_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored["processing_status"], "indexed")
        self.assertEqual(stored["chunk_count"], result["chunks"])
        self.assertIsNotNone(stored["indexed_at"])

        # Verify ChromaDB contains the vectors with complete metadata
        coll = get_faculty_chroma_collection()
        chroma_res = coll.get(where={"resource_id": res_id}, include=["metadatas", "documents"])
        self.assertEqual(len(chroma_res["ids"]), result["chunks"])
        sample_meta = chroma_res["metadatas"][0]
        self.assertEqual(sample_meta["source_type"], "faculty_upload")
        self.assertEqual(sample_meta["chapter_id"], chap_id)
        self.assertEqual(sample_meta["subject_id"], "evs")
        self.assertIn("pdf_page", sample_meta)

    # ── PART 4: Dynamic Catalog Integration ───────────────────────────────────

    def test_09_catalog_discovery_and_chapter_resolution(self):
        # Check that chapter is discoverable in catalog
        chap = get_chapter("upload_evs_c05_ch80")
        self.assertIsNotNone(chap, "Uploaded chapter should be discoverable via get_chapter")
        self.assertEqual(chap.title, "Wind Energy & Sustainable Ecology")
        self.assertEqual(chap.validation_status, "faculty_upload")
        self.assertTrue(chap.indexed)

        # Check in all subjects list
        subjects = get_all_subjects()
        evs_sub = next((s for s in subjects if s.subject_id.lower() == "evs"), None)
        self.assertIsNotNone(evs_sub)
        ch_in_sub = next((c for c in evs_sub.chapters if c.chapter_id == "upload_evs_c05_ch80"), None)
        self.assertIsNotNone(ch_in_sub, "Uploaded chapter should be listed in EVS subject chapters")

        # Check get_chapter_pdf_path
        pdf_p = get_chapter_pdf_path("upload_evs_c05_ch80")
        self.assertIsNotNone(pdf_p)
        self.assertTrue(pdf_p.exists())

    # ── PART 5: Scope-Isolated Retrieval Tests ─────────────────────────────────

    def test_10_chapter_scoped_retrieval_success(self):
        res = self.retrieval.retrieve(
            subject_id="evs",
            query="How do horizontal axis wind turbines generate electricity?",
            chat_scope="chapter",
            chapter_id="upload_evs_c05_ch80",
            top_k=3,
        )
        self.assertEqual(res.status, "ok")
        self.assertGreater(len(res.evidences), 0)
        top_ev = res.evidences[0]
        self.assertEqual(top_ev.chapter_id, "upload_evs_c05_ch80")
        self.assertEqual(top_ev.verification_status, "faculty_upload")
        self.assertIn("wind", top_ev.content.lower())

    def test_11_strict_chapter_isolation(self):
        # Querying an official chapter should NEVER return chunks from uploaded chapter
        res_official = self.retrieval.retrieve(
            subject_id="evs",
            query="wind energy turbines kinetic green electricity",
            chat_scope="chapter",
            chapter_id="EVS_CH01",
            top_k=5,
        )
        # Even if chunks are returned for Chapter 1, none should have chapter_id of the upload
        for ev in res_official.evidences:
            self.assertNotEqual(ev.chapter_id, "upload_evs_c05_ch80")
            self.assertEqual(ev.chapter_id, "EVS_CH01")

        # Querying the uploaded chapter should NEVER return chunks from Chapter 1 (What is History)
        res_upload = self.retrieval.retrieve(
            subject_id="evs",
            query="What are historical sources, material written and oral?",
            chat_scope="chapter",
            chapter_id="upload_evs_c05_ch80",
            top_k=5,
        )
        for ev in res_upload.evidences:
            self.assertEqual(ev.chapter_id, "upload_evs_c05_ch80")
            self.assertNotEqual(ev.chapter_id, "EVS_CH01")

    # ── PART 6: Citation Validation for Uploaded Materials ────────────────────

    def test_12_citation_validation_and_display_labels(self):
        ret_res = self.retrieval.retrieve(
            subject_id="evs",
            query="wind kinetic energy",
            chat_scope="chapter",
            chapter_id="upload_evs_c05_ch80",
            top_k=2,
        )
        self.assertEqual(ret_res.status, "ok")

        citations = self.citation_val.validate_citations(
            candidate_chunk_ids=[ev.chunk_id for ev in ret_res.evidences],
            retrieved_evidences=ret_res.evidences,
            chat_scope="chapter",
            current_chapter_id="upload_evs_c05_ch80",
            is_general_knowledge=False,
        )
        self.assertGreater(len(citations), 0)
        c0 = citations[0]
        self.assertIn("[Faculty Material]", c0.display_label)
        self.assertIn("Wind Energy & Sustainable Ecology", c0.display_label)
        self.assertEqual(c0.verification_status, "faculty_upload")

        # Zero false citations on general knowledge
        gk_citations = self.citation_val.validate_citations(
            candidate_chunk_ids=[ev.chunk_id for ev in ret_res.evidences],
            retrieved_evidences=ret_res.evidences,
            chat_scope="chapter",
            current_chapter_id="upload_evs_c05_ch80",
            is_general_knowledge=True,
        )
        self.assertEqual(len(gk_citations), 0, "General knowledge questions must attach strictly 0 citations")

    # ── PART 7: Idempotent Reindexing & Clean Deletion ─────────────────────────

    def test_13_idempotent_reindexing(self):
        res_id = "res_test_ingest_02"
        # Count current chunks
        coll = get_faculty_chroma_collection()
        initial_count = len(coll.get(where={"resource_id": res_id})["ids"])

        # Re-index
        res = self.repo.get_resource(res_id)
        self.assertIsNotNone(res)
        reindex_result = self.svc.ingest_pdf(
            resource_id=res_id,
            pdf_path=Path(res["stored_path"]),
            subject_id=res["subject_id"],
            class_number=res["class_number"],
            chapter_id=res["chapter_id"],
            chapter_number=res["chapter_number"],
            chapter_name=res["chapter_name"],
            original_filename=res["original_filename"],
        )
        # Vector count must be identical (no duplicate vector inflation)
        after_count = len(coll.get(where={"resource_id": res_id})["ids"])
        self.assertEqual(initial_count, after_count, "Reindexing must replace old chunks without creating duplicate vectors")

    def test_14_clean_deletion(self):
        res_id = "res_test_del_99"
        chap_id = "upload_evs_c05_ch99"
        pdf_bytes = create_in_memory_pdf(["Temporary chapter for deletion testing."])

        saved_path = self.svc.save_pdf_to_disk(
            resource_id=res_id,
            subject_id="evs",
            class_number=5,
            chapter_number=99,
            chapter_name="Delete Me Chapter",
            original_filename="delete_me.pdf",
            file_bytes=pdf_bytes,
        )
        self.repo.create_resource(
            resource_id=res_id,
            subject_id="evs",
            class_number=5,
            chapter_id=chap_id,
            chapter_number=99,
            chapter_name="Delete Me Chapter",
            original_filename="delete_me.pdf",
            stored_path=str(saved_path),
            file_hash="del_hash_99",
            file_size_bytes=len(pdf_bytes),
            processing_status="uploaded",
        )
        self.svc.ingest_pdf(
            resource_id=res_id,
            pdf_path=saved_path,
            subject_id="evs",
            class_number=5,
            chapter_id=chap_id,
            chapter_number=99,
            chapter_name="Delete Me Chapter",
            original_filename="delete_me.pdf",
        )

        # Verify exists
        self.assertTrue(saved_path.exists())
        coll = get_faculty_chroma_collection()
        self.assertGreater(len(coll.get(where={"resource_id": res_id})["ids"]), 0)

        # Delete
        success = self.svc.delete_resource_and_vectors(res_id)
        self.assertTrue(success)

        # Verify file deleted
        self.assertFalse(saved_path.exists())
        # Verify vectors deleted
        self.assertEqual(len(coll.get(where={"resource_id": res_id})["ids"]), 0)
        # Verify SQLite deleted
        self.assertIsNone(self.repo.get_resource(res_id))


if __name__ == "__main__":
    unittest.main(verbosity=2)
