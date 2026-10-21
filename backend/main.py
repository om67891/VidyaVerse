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
    CreateConversationRequest,
    SendMessageRequest,
    QuizValidateRequest,
    MathValidateRequest,
)
from backend.repositories.conversation_repository import get_conversation_repository
from backend.services.tutoring_service import get_tutoring_service, TutoringMessageRequest
from backend.services.learning_map_service import get_learning_map_service
from backend.services.glossary_service import get_glossary_service
from backend.services.quiz_service import get_quiz_service
from backend.services.math_validator import get_math_validator
from backend.services.persona_manager import get_persona_manager
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


@app.get("/api/personas/{persona_id}")
async def get_persona_details(persona_id: str):
    """Return full persona profile, boundaries, and teaching behavior."""
    from backend.services.persona_manager import get_persona_manager
    p = get_persona_manager().get_persona(persona_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' not found.")
    return p


# ── Chat ───────────────────────────────────────────────────────────────────────


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return an AI-generated response."""
    from backend.services.rag import process_chat

    # Check if chapter is standard chapter ID or subject-level chat
    clean_chap = request.chapter_id.strip()
    is_subject_chat = clean_chap.lower().endswith("_all") or clean_chap.lower() in ("subject", "all", "history", "mathematics", "evs")

    if not is_subject_chat:
        chapter = get_chapter(clean_chap)
        if chapter is None:
            # Try upper case
            chapter = get_chapter(clean_chap.upper())
        if chapter is None:
            raise HTTPException(status_code=404, detail=f"Chapter not found: {request.chapter_id}")
        request = request.model_copy(update={"chapter_id": chapter.chapter_id})

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


# ── Part 04: Persistent Conversations Endpoints ──────────────────────────────


@app.post("/api/conversations")
async def create_conversation(req: CreateConversationRequest):
    """
    Create a new persistent conversation with strictly locked persona, subject, and scope.
    Survives server restarts via SQLite.
    """
    repo = get_conversation_repository()
    pm = get_persona_manager()

    # Validate persona
    persona = pm.get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{req.persona_id}' is not registered.")

    # Validate subject
    norm_sub = req.subject_id.strip().lower()
    if norm_sub in ("math", "maths"):
        norm_sub = "mathematics"
    if norm_sub not in ("history", "mathematics", "evs"):
        raise HTTPException(status_code=400, detail=f"Invalid subject '{req.subject_id}'.")

    # Scope validation
    scope = req.chat_scope.strip().lower()
    if scope not in ("subject", "chapter"):
        raise HTTPException(status_code=400, detail=f"Invalid chat scope '{req.chat_scope}'. Must be 'subject' or 'chapter'.")

    actual_chap_id = None
    if scope == "chapter":
        if not req.chapter_id:
            raise HTTPException(status_code=400, detail="chapter_id is required when chat_scope is 'chapter'.")
        actual_chap_id = req.chapter_id.strip()
    else:
        # Subject scope strictly forces chapter_id to null
        actual_chap_id = None

    conv = repo.create_conversation(
        subject_id=norm_sub,
        chat_scope=scope,
        chapter_id=actual_chap_id,
        persona_id=persona["persona_id"],
        title=req.title,
    )
    return conv


@app.get("/api/conversations")
async def list_conversations(
    subject_id: Optional[str] = None,
    chat_scope: Optional[str] = None,
    chapter_id: Optional[str] = None,
    limit: int = 50,
):
    """
    List conversations filtered by subject, chat scope, and chapter.
    Enforces independent history views for subject-wide vs chapter-wise chats.
    """
    repo = get_conversation_repository()
    norm_sub = subject_id.strip().lower() if subject_id else None
    if norm_sub in ("math", "maths"):
        norm_sub = "mathematics"

    return repo.list_conversations(
        subject_id=norm_sub,
        chat_scope=chat_scope.strip().lower() if chat_scope else None,
        chapter_id=chapter_id.strip() if chapter_id else None,
        limit=limit,
    )


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve full conversation details, stored messages, and learning progress."""
    repo = get_conversation_repository()
    conv = repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found.")
    messages = repo.get_messages(conversation_id)
    conv["messages"] = messages
    return conv


@app.post("/api/conversations/{conversation_id}/messages")
async def send_message_to_conversation(conversation_id: str, req: SendMessageRequest):
    """
    Send a message or execute an interactive choice within an existing conversation.
    Authoritative scope and persona are enforced from the database.
    """
    ts = get_tutoring_service()
    try:
        resp = ts.process_message(
            TutoringMessageRequest(
                conversation_id=conversation_id,
                message=req.message,
                action_payload=req.action_payload,
                response_mode=req.response_mode,
                question_format=req.question_format,
            )
        )
        return resp
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal tutoring error: {e}")


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a specific conversation and all associated messages."""
    repo = get_conversation_repository()
    deleted = repo.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found.")
    return {"status": "deleted", "conversation_id": conversation_id}


# ── Learning Maps & Moments ───────────────────────────────────────────────────


@app.get("/api/learning-map/{subject_id}/{chapter_id}")
async def get_chapter_learning_map(subject_id: str, chapter_id: str):
    """Return the structured learning map, objectives, key facts, and moments for a chapter."""
    lms = get_learning_map_service()
    ch_map = lms.get_chapter_map(subject_id, chapter_id)
    if not ch_map:
        raise HTTPException(status_code=404, detail=f"Learning map not found for {subject_id} / {chapter_id}")
    return ch_map


# ── Glossary & Definitions ─────────────────────────────────────────────────────


@app.get("/api/glossary/{subject_id}")
async def list_glossary_terms(subject_id: str, chapter_id: Optional[str] = None):
    """Return chapter-specific glossary terms with child-friendly and detailed definitions."""
    gs = get_glossary_service()
    return gs.get_terms_for_chapter(subject_id, chapter_id)


# ── Interactive Quizzes ────────────────────────────────────────────────────────


@app.get("/api/quiz/{subject_id}/{chapter_id}")
async def get_chapter_quiz(subject_id: str, chapter_id: str):
    """Return student-safe quiz questions without exposing the private correct answer keys."""
    qs = get_quiz_service()
    questions = qs.get_questions_for_chapter(subject_id, chapter_id)
    return questions


@app.post("/api/quiz/validate")
async def validate_quiz_answer(req: QuizValidateRequest):
    """Deterministically validates a student's quiz answer and returns constructive feedback."""
    qs = get_quiz_service()
    res = qs.validate_answer(req.question_id, req.selected_index)
    if not res:
        raise HTTPException(status_code=404, detail=f"Question '{req.question_id}' not found.")
    return res


# ── Deterministic Mathematical Validation ──────────────────────────────────────


@app.post("/api/math/validate")
async def validate_math_calculation(req: MathValidateRequest):
    """
    Deterministic mathematical calculation and validation engine for Std X Mathematics.
    Supports Pythagoras, 30-60-90, coordinate geometry, trigonometry, and mensuration.
    """
    mv = get_math_validator()
    op = req.operation.lower().strip()
    p = req.params

    if op == "pythagoras":
        return mv.solve_pythagoras(a=p.get("a"), b=p.get("b"), c=p.get("c"))
    elif op == "30_60_90":
        hyp = p.get("hypotenuse")
        if hyp is None:
            raise HTTPException(status_code=400, detail="hypotenuse is required for 30_60_90 calculation.")
        return mv.solve_30_60_90(hyp)
    elif op == "geometric_mean":
        return mv.solve_geometric_mean(p.get("seg1", 0), p.get("seg2", 0))
    elif op == "apollonius":
        return mv.solve_apollonius(p.get("ab", 0), p.get("ac", 0), p.get("bm", 0))
    elif op == "distance":
        return mv.coordinate_distance(p.get("x1", 0), p.get("y1", 0), p.get("x2", 0), p.get("y2", 0))
    elif op == "midpoint":
        return mv.coordinate_midpoint(p.get("x1", 0), p.get("y1", 0), p.get("x2", 0), p.get("y2", 0))
    elif op == "slope":
        return mv.coordinate_slope(p.get("x1", 0), p.get("y1", 0), p.get("x2", 0), p.get("y2", 0))
    elif op == "trig":
        return mv.trig_standard_value(p.get("func", "sin"), p.get("angle", 30))
    elif op == "cylinder":
        return mv.mensuration_cylinder(p.get("r", 0), p.get("h", 0))
    elif op == "cone":
        return mv.mensuration_cone(p.get("r", 0), p.get("h", 0))
    elif op == "sphere":
        return mv.mensuration_sphere(p.get("r", 0))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported math operation: {op}")



