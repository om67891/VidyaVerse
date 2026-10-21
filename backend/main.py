"""
FastAPI backend for the Class 5 Educational Chatbot.

Start with:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional

from backend.config import settings
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    IndexRequest,
    IndexStatusResponse,
    SubjectSchema,
    ChapterSchema,
    PersonaSchema,
    HistoryActionRequest,
    HistoryAskRequest,
)
from backend.services.catalog import (
    get_all_subjects,
    get_subject,
    get_chapter,
    get_personas,
)
from backend.services.indexing import get_chroma_collection, run_indexing
from backend.services.history_service import (
    get_or_create_session,
    build_session_response,
    process_lesson_action,
    handle_custom_question,
    HistorySessionState,
)
from backend.services.history_map import get_all_lessons
from backend.services.history_indexing import (
    get_history_collection,
    run_history_indexing,
)

app = FastAPI(
    title="Class 5 Chatbot API",
    description="Educational chatbot for Class 5 with chapter-isolated RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    """Quick health check including Ollama availability."""
    import requests as req

    ollama_ok = False
    ollama_model_ok = False
    try:
        r = req.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        if r.status_code == 200:
            ollama_ok = True
            tags = r.json().get("models", [])
            ollama_model_ok = any(
                t.get("name", "").startswith(settings.ollama_model)
                for t in tags
            )
    except Exception:
        pass

    return {
        "status": "ok",
        "ollama_running": ollama_ok,
        "model_available": ollama_model_ok,
        "model": settings.ollama_model,
        "collection": settings.chroma_collection_name,
    }


# ── Subjects & Chapters ────────────────────────────────────────────────────────


@app.get("/api/subjects", response_model=list[SubjectSchema])
async def list_subjects():
    """Return all subjects with chapter availability."""
    return get_all_subjects()


@app.get("/api/subjects/{subject_id}", response_model=SubjectSchema)
async def get_subject_detail(subject_id: str):
    subject = get_subject(subject_id.upper())
    if subject is None:
        raise HTTPException(status_code=404, detail=f"Subject not found: {subject_id}")
    return subject


@app.get("/api/subjects/{subject_id}/chapters", response_model=list[ChapterSchema])
async def list_chapters(subject_id: str):
    subject = get_subject(subject_id.upper())
    if subject is None:
        raise HTTPException(status_code=404, detail=f"Subject not found: {subject_id}")
    return subject.chapters + subject.demo_chapters


@app.get("/api/chapters/{chapter_id}", response_model=ChapterSchema)
async def get_chapter_detail(chapter_id: str):
    chapter = get_chapter(chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail=f"Chapter not found: {chapter_id}")
    return chapter


# ── Personas ───────────────────────────────────────────────────────────────────


@app.get("/api/personas", response_model=list[PersonaSchema])
async def list_personas(subject_id: Optional[str] = None, chapter_id: Optional[str] = None):
    """Return registered personas from catalog, optionally filtered/prioritized by subject and chapter."""
    return get_personas(subject_id=subject_id, chapter_id=chapter_id)


# ── Chat ───────────────────────────────────────────────────────────────────────


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return an AI-generated response."""
    from backend.services.rag import process_chat

    # Validate chapter exists
    chapter = get_chapter(request.chapter_id.upper())
    if chapter is None:
        raise HTTPException(status_code=404, detail=f"Chapter not found: {request.chapter_id}")

    # Normalise chapter_id to uppercase
    request = request.model_copy(update={"chapter_id": request.chapter_id.upper()})

    try:
        return process_chat(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


# ── Indexing ───────────────────────────────────────────────────────────────────


@app.post("/api/index")
async def trigger_index(request: IndexRequest):
    """Trigger indexing for a subject (runs synchronously — suitable for POC)."""
    if request.subject_id.upper() != "EVS":
        raise HTTPException(status_code=400, detail="Only EVS indexing is supported currently.")
    results = run_indexing(force=request.force)
    return {"results": results}


@app.get("/api/index/status", response_model=IndexStatusResponse)
async def index_status():
    """Return current indexing status from ChromaDB."""
    collection = get_chroma_collection()
    total = collection.count()

    indexed_ids: set[str] = set()
    if total > 0:
        results = collection.get(include=["metadatas"])
        indexed_ids = {m.get("chapter_id") for m in results["metadatas"] if m.get("chapter_id")}

    return IndexStatusResponse(
        collection_name=settings.chroma_collection_name,
        total_chunks=total,
        indexed_chapters=sorted(indexed_ids),
        status="ready" if total > 0 else "empty",
    )


# ── History Prototype Endpoints ───────────────────────────────────────────────


@app.get("/api/history/session/start", response_model=HistorySessionState)
async def start_history_session(session_id: Optional[str] = None):
    """Start or resume a guided interactive History session."""
    session = get_or_create_session(session_id)
    return build_session_response(session)


@app.post("/api/history/action", response_model=HistorySessionState)
async def history_action(request: HistoryActionRequest):
    """Handle student choice clicks, quiz answers, and lesson transitions."""
    return process_lesson_action(
        session_id=request.session_id,
        action={
            "action_type": request.action_type,
            "choice_id": request.choice_id,
            "selected_index": request.selected_index,
            "lesson_id": request.lesson_id,
        }
    )


@app.post("/api/history/ask", response_model=HistorySessionState)
async def history_ask(request: HistoryAskRequest):
    """
    Handle custom questions at any point without erasing ongoing lesson progression.
    Routes intelligently between guided topic, full textbook search, and general knowledge.
    """
    return handle_custom_question(
        session_id=request.session_id,
        question=request.question,
    )


@app.get("/api/history/map")
async def history_learning_map():
    """Return the structured 18-lesson curriculum map derived from History.pdf."""
    return get_all_lessons()


@app.get("/api/history/status")
async def history_indexing_status():
    """Return status of the dedicated history_master ChromaDB collection."""
    collection = get_history_collection()
    count = collection.count()
    return {
        "collection_name": settings.history_collection_name,
        "total_chunks": count,
        "pdf_path": str(settings.history_pdf_path),
        "pdf_exists": settings.history_pdf_path.exists(),
        "status": "ready" if count > 0 else "empty",
    }


@app.post("/api/history/index")
async def history_index_trigger(force: bool = False):
    """Trigger indexing of the master History textbook."""
    result = run_history_indexing(force=force)
    return result


# ── Development Diagnostics ───────────────────────────────────────────────────


@app.get("/api/dev/diagnostics")
async def dev_diagnostics(chapter_id: str = "EVS_CH01", query: str = "What is history?"):
    """
    Development-only endpoint to inspect RAG pipeline internals:
    selected chapter, indexed chunks, retrieval distances, citations, filter verification.
    """
    from backend.services.rag import get_diagnostics
    return get_diagnostics(chapter_id.upper(), query)


