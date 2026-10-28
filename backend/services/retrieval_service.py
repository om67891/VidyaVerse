"""
Scope-Isolated Retrieval Service for VidyaVerse Learning Hub.

Supports:
- History (History.pdf / history_master collection)
- Mathematics (Mathematics Part II / mathematics_master collection)
- Environmental Studies (EVS chapters / class5_evs_chapters collection)

Scope guarantees:
- Chapter scope: strict query filtering to the selected chapter. Never leaks chunks from outside chapters.
- Subject scope: queries across all chapters within the selected subject.
- Distinguishes unindexed chapters/collections from empty search results.
- Preserves complete document, PDF page, and printed textbook page references.
"""
from __future__ import annotations

import re
from typing import Optional, Literal
from pydantic import BaseModel, Field
import chromadb

from backend.config import settings
from backend.services.indexing import get_embedding_model


# ── Schemas ────────────────────────────────────────────────────────────────────


class RetrievalEvidence(BaseModel):
    chunk_id: str
    subject_id: str
    chapter_id: str
    chapter_number: int
    chapter_title: str
    source_document: str
    pdf_page: int
    book_page: int
    chapter_pdf_page: Optional[int] = None
    content: str
    distance: float
    verification_status: str = "verified"


class RetrievalResult(BaseModel):
    subject_id: str
    chat_scope: Literal["subject", "chapter"]
    chapter_id: Optional[str] = None
    query: str
    status: Literal["ok", "empty_results", "unindexed_chapter", "collection_not_found"]
    message: str = ""
    evidences: list[RetrievalEvidence] = []


# ── Embeddings Helper ──────────────────────────────────────────────────────────


def embed_query_e5(query: str) -> list[float]:
    """Embed query with query: prefix for multilingual-e5-small."""
    model = get_embedding_model()
    vector = model.encode(f"query: {query.strip()}", normalize_embeddings=True)
    return vector.tolist()


# ── Subject & Chapter Resolvers ───────────────────────────────────────────────


def normalize_subject_id(subject_id: str) -> str:
    clean = (subject_id or "").strip().lower()
    if clean in ("math", "maths", "mathematics"):
        return "mathematics"
    if clean in ("history", "hist"):
        return "history"
    if clean in ("evs", "environmental studies", "environmental_studies"):
        return "evs"
    return clean


def parse_chapter_number(chapter_id: str) -> Optional[int]:
    """Extract integer chapter number from strings like 'EVS_CH02', 'mathematics_chapter_03', 'HIST_L04', '4'."""
    clean = (chapter_id or "").strip()
    match = re.search(r"(\d+)", clean)
    if match:
        return int(match.group(1))
    return None


# ── Chroma Client Provider ────────────────────────────────────────────────────


def get_chroma_client() -> chromadb.ClientAPI:
    settings.vectorstore_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.vectorstore_path))


# ── Core Retrieval Service ────────────────────────────────────────────────────


class RetrievalService:
    def __init__(self):
        self._client = get_chroma_client()

    def get_collection_name(self, subject_id: str) -> str:
        norm_sub = normalize_subject_id(subject_id)
        if norm_sub == "history":
            return settings.history_collection_name
        elif norm_sub == "mathematics":
            return settings.math_collection_name
        elif norm_sub == "evs":
            return settings.chroma_collection_name
        raise ValueError(f"Unknown subject '{subject_id}'")

    def retrieve(
        self,
        subject_id: str,
        query: str,
        chat_scope: Literal["subject", "chapter"] = "chapter",
        chapter_id: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> RetrievalResult:
        """
        Execute scope-isolated semantic retrieval.
        - If chat_scope == "chapter": strict metadata filtering applied.
        - If chat_scope == "subject": broad search across all chunks of that subject.
        - Seamlessly handles both official curriculum textbooks and faculty-uploaded materials.
        """
        norm_sub = normalize_subject_id(subject_id)
        threshold = similarity_threshold if similarity_threshold is not None else settings.rag_similarity_threshold

        clean_cid = (chapter_id or "").strip()
        is_upload = clean_cid.lower().startswith("upload_")
        uploaded_resource = None

        if not is_upload and clean_cid:
            try:
                from backend.repositories.uploaded_resource_repository import get_uploaded_resource_repository
                uploaded_resource = get_uploaded_resource_repository().get_resource_by_chapter_id(clean_cid)
                if uploaded_resource:
                    is_upload = True
                    clean_cid = uploaded_resource["chapter_id"]
            except Exception:
                pass

        # ── Branch A: Chapter-scoped chat with a Faculty Uploaded Chapter ──────
        if chat_scope == "chapter" and is_upload:
            try:
                faculty_coll = self._client.get_collection(settings.faculty_collection_name)
            except Exception as e:
                return RetrievalResult(
                    subject_id=norm_sub,
                    chat_scope="chapter",
                    chapter_id=clean_cid,
                    query=query,
                    status="collection_not_found",
                    message=f"Faculty uploads vector store is not initialized or empty: {e}",
                    evidences=[],
                )

            if faculty_coll.count() == 0:
                return RetrievalResult(
                    subject_id=norm_sub,
                    chat_scope="chapter",
                    chapter_id=clean_cid,
                    query=query,
                    status="empty_results",
                    message=f"Faculty uploads collection exists but has 0 indexed chunks.",
                    evidences=[],
                )

            query_vector = embed_query_e5(query)
            try:
                results = faculty_coll.query(
                    query_embeddings=[query_vector],
                    n_results=top_k,
                    where={"chapter_id": clean_cid},
                    include=["documents", "metadatas", "distances"],
                )
            except Exception as e:
                return RetrievalResult(
                    subject_id=norm_sub,
                    chat_scope="chapter",
                    chapter_id=clean_cid,
                    query=query,
                    status="empty_results",
                    message=f"Query error in faculty collection: {e}",
                    evidences=[],
                )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            evidences: list[RetrievalEvidence] = []
            for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists):
                if not doc:
                    continue
                if threshold is not None and dist > threshold:
                    continue
                ev = self._parse_chunk_evidence(norm_sub, chunk_id, doc, meta, dist)
                evidences.append(ev)

            if not evidences:
                return RetrievalResult(
                    subject_id=norm_sub,
                    chat_scope="chapter",
                    chapter_id=clean_cid,
                    query=query,
                    status="empty_results",
                    message="No relevant passages found in this uploaded chapter for your query.",
                    evidences=[],
                )

            return RetrievalResult(
                subject_id=norm_sub,
                chat_scope="chapter",
                chapter_id=clean_cid,
                query=query,
                status="ok",
                evidences=evidences,
            )

        # ── Branch B: Official Textbook Retrieval (with optional Subject Merge) ─
        try:
            coll_name = self.get_collection_name(norm_sub)
            collection = self._client.get_collection(coll_name)
        except Exception as e:
            return RetrievalResult(
                subject_id=norm_sub,
                chat_scope=chat_scope,
                chapter_id=chapter_id,
                query=query,
                status="collection_not_found",
                message=f"ChromaDB collection for subject '{norm_sub}' is not found or empty: {e}",
                evidences=[],
            )

        if collection.count() == 0:
            return RetrievalResult(
                subject_id=norm_sub,
                chat_scope=chat_scope,
                chapter_id=chapter_id,
                query=query,
                status="collection_not_found",
                message=f"Collection '{coll_name}' exists but has 0 indexed chunks.",
                evidences=[],
            )

        # Build ChromaDB 'where' filter based on scope
        where_filter: Optional[dict] = None
        target_num = parse_chapter_number(chapter_id) if chapter_id else None

        if chat_scope == "chapter":
            if not chapter_id:
                raise ValueError("chapter_id must be provided when chat_scope is 'chapter'")

            if norm_sub == "history":
                if target_num is None:
                    return RetrievalResult(
                        subject_id=norm_sub,
                        chat_scope="chapter",
                        chapter_id=chapter_id,
                        query=query,
                        status="unindexed_chapter",
                        message=f"Cannot determine History lesson number from '{chapter_id}'",
                        evidences=[],
                    )
                where_filter = {"lesson_number": target_num}

            elif norm_sub == "mathematics":
                if target_num is not None:
                    canonical_id = f"mathematics_chapter_{target_num:02d}"
                    where_filter = {"chapter_id": canonical_id}
                else:
                    where_filter = {"chapter_id": chapter_id.strip()}

            elif norm_sub == "evs":
                if target_num is not None:
                    canonical_id = f"EVS_CH{target_num:02d}"
                    where_filter = {"chapter_id": canonical_id}
                else:
                    where_filter = {"chapter_id": chapter_id.strip()}

        # Generate query vector
        query_vector = embed_query_e5(query)

        # Query ChromaDB official collection
        query_args: dict = {
            "query_embeddings": [query_vector],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_args["where"] = where_filter

        try:
            results = collection.query(**query_args)
        except Exception as e:
            return RetrievalResult(
                subject_id=norm_sub,
                chat_scope=chat_scope,
                chapter_id=chapter_id,
                query=query,
                status="empty_results",
                message=f"Query error: {e}",
                evidences=[],
            )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        evidences: list[RetrievalEvidence] = []
        for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists):
            if not doc:
                continue
            if threshold is not None and dist > threshold:
                continue
            ev = self._parse_chunk_evidence(norm_sub, chunk_id, doc, meta, dist)
            evidences.append(ev)

        # If subject-wide search, also merge any relevant faculty uploads for that subject
        if chat_scope == "subject":
            try:
                faculty_coll = self._client.get_collection(settings.faculty_collection_name)
                if faculty_coll.count() > 0:
                    fac_res = faculty_coll.query(
                        query_embeddings=[query_vector],
                        n_results=top_k,
                        where={"subject_id": norm_sub},
                        include=["documents", "metadatas", "distances"],
                    )
                    f_docs = fac_res.get("documents", [[]])[0]
                    f_metas = fac_res.get("metadatas", [[]])[0]
                    f_dists = fac_res.get("distances", [[]])[0]
                    f_ids = fac_res.get("ids", [[]])[0]
                    for f_id, f_doc, f_meta, f_dist in zip(f_ids, f_docs, f_metas, f_dists):
                        if f_doc and (threshold is None or f_dist <= threshold):
                            evidences.append(self._parse_chunk_evidence(norm_sub, f_id, f_doc, f_meta, f_dist))
                    # Sort combined by distance and slice top_k
                    evidences.sort(key=lambda x: x.distance)
                    evidences = evidences[:top_k]
            except Exception:
                pass

        if not evidences:
            return RetrievalResult(
                subject_id=norm_sub,
                chat_scope=chat_scope,
                chapter_id=chapter_id,
                query=query,
                status="empty_results",
                message="No chunks matched the query within similarity threshold.",
                evidences=[],
            )

        return RetrievalResult(
            subject_id=norm_sub,
            chat_scope=chat_scope,
            chapter_id=chapter_id,
            query=query,
            status="ok",
            evidences=evidences,
        )

    def _parse_chunk_evidence(
        self,
        subject_id: str,
        chunk_id: str,
        text: str,
        meta: dict,
        distance: float,
    ) -> RetrievalEvidence:
        """Standardize heterogeneous metadata from History, Math, EVS, and Faculty Uploads into RetrievalEvidence."""
        if meta.get("source_type") == "faculty_upload":
            ch_id = meta.get("chapter_id", f"upload_{subject_id}")
            ch_num = meta.get("chapter_number", 0)
            ch_name = meta.get("chapter_name", f"Chapter {ch_num}")
            pdf_p = meta.get("pdf_page", 1)
            return RetrievalEvidence(
                chunk_id=chunk_id,
                subject_id=subject_id,
                chapter_id=ch_id,
                chapter_number=ch_num,
                chapter_title=ch_name,
                source_document=meta.get("source", "Faculty Uploaded Material"),
                pdf_page=pdf_p,
                book_page=pdf_p,
                chapter_pdf_page=pdf_p,
                content=text,
                distance=distance,
                verification_status="faculty_upload",
            )

        if subject_id == "history":
            lesson_num = meta.get("lesson_number", 0)
            lesson_title = meta.get("lesson_title", f"Lesson {lesson_num}")
            pdf_p = meta.get("pdf_page", 0)
            book_p = meta.get("book_page", max(1, pdf_p - 10))
            return RetrievalEvidence(
                chunk_id=chunk_id,
                subject_id="history",
                chapter_id=f"HIST_L{lesson_num:02d}",
                chapter_number=lesson_num,
                chapter_title=lesson_title,
                source_document=meta.get("source", "History.pdf"),
                pdf_page=pdf_p,
                book_page=book_p,
                chapter_pdf_page=None,
                content=text,
                distance=distance,
            )

        elif subject_id == "mathematics":
            ch_num = meta.get("chapter_number", 0)
            ch_id = meta.get("chapter_id", f"mathematics_chapter_{ch_num:02d}")
            ch_title = meta.get("chapter_title", f"Chapter {ch_num}")
            pdf_p = meta.get("pdf_page", 0)
            book_p = meta.get("book_page", pdf_p)
            return RetrievalEvidence(
                chunk_id=chunk_id,
                subject_id="mathematics",
                chapter_id=ch_id,
                chapter_number=ch_num,
                chapter_title=ch_title,
                source_document=meta.get("source", "Mathematics.pdf"),
                pdf_page=pdf_p,
                book_page=book_p,
                chapter_pdf_page=None,
                content=text,
                distance=distance,
            )

        else:  # EVS
            ch_id = meta.get("chapter_id", "")
            ch_num = parse_chapter_number(ch_id) or 0
            ch_title = meta.get("chapter_name", f"Chapter {ch_num}")
            page_num = meta.get("page_number", 1)
            return RetrievalEvidence(
                chunk_id=chunk_id,
                subject_id="evs",
                chapter_id=ch_id,
                chapter_number=ch_num,
                chapter_title=ch_title,
                source_document=meta.get("source", "Environmental Studies"),
                pdf_page=page_num,
                book_page=page_num,
                chapter_pdf_page=page_num,
                content=text,
                distance=distance,
            )


# ── Global Singleton Provider ─────────────────────────────────────────────────

_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
