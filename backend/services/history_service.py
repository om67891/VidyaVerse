"""
Interactive History Lesson Orchestrator & Conversational RAG Engine.

Key Features:
- Chhatrapati Shivaji Maharaj is the primary storyteller across the curriculum.
- In background lessons (Lessons 1-3, 5), Shivaji guides students through Maharashtra's history before his birth without claiming to witness pre-1630 events.
- In Swaraj lessons (Lessons 4, 6-18), Shivaji narrates in first-person educational roleplay based on textbook evidence.
- Stage-aware interaction loop with adaptive response formatting:
  story, figure profile, chronological timeline, cause and effect, comparison, recap, and interactive quiz.
- Dynamic, non-repetitive choices derived from textbook content and learning objectives.
- Permanent custom question composer with contextual pronoun resolution and return-to-story resumption.
- Strict citation deduplication and zero false citations for general knowledge.
"""
from __future__ import annotations

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import re
import uuid
from datetime import datetime
import requests
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.config import settings
from backend.services.history_indexing import (
    get_history_collection,
    embed_query,
    get_lesson_for_pdf_page,
)
from backend.services.history_map import (
    HISTORY_LEARNING_MAP,
    LessonNode,
    LessonStage,
    ChoiceOption,
    QuizCheck,
    TimelineEvent,
    FigureProfile,
    ComparisonItem,
    ComparisonData,
    CauseEffectData,
    get_lesson,
    get_all_lessons,
    get_lesson_stage,
)


# ── Schemas for History Experience ───────────────────────────────────────────


class HistorySourceRef(BaseModel):
    source: str = "History.pdf"
    pdf_page: int
    book_page: int
    lesson_title: str
    snippet: str = ""


class HistoryChatMessage(BaseModel):
    id: str
    role: str  # "assistant" | "user"
    content: str
    format_type: str = "story"  # "story" | "explanation" | "figure" | "timeline" | "cause_effect" | "comparison" | "quiz" | "recap" | "chat"
    highlights: list[str] = []
    figure_profile: Optional[FigureProfile] = None
    timeline_events: Optional[list[TimelineEvent]] = None
    comparison: Optional[ComparisonData] = None
    cause_effect: Optional[CauseEffectData] = None
    recap_points: Optional[list[str]] = None
    persona: Optional[str] = None
    persona_name: Optional[str] = None
    persona_avatar: Optional[str] = None
    persona_role: Optional[str] = None
    citations: list[HistorySourceRef] = []
    choices: list[ChoiceOption] = []
    quiz: Optional[QuizCheck] = None
    quiz_feedback: Optional[str] = None
    quiz_passed: Optional[bool] = None
    is_custom_answer: bool = False
    can_resume: bool = False
    timestamp: str = ""


class HistorySessionState(BaseModel):
    session_id: str
    current_lesson_id: str
    lesson_title: str
    lesson_number: int
    total_lessons: int = 18
    completed_lessons: list[str] = []
    current_stage: str  # "INTRO" | "STORY" | "EXPLORE" | "CAUSE" | "QUIZ" | "FEEDBACK" | "CUSTOM_ANSWER"
    persona: str = "SHIVAJI"
    persona_name: str = "Chhatrapati Shivaji Maharaj"
    persona_avatar: str = "/avatars/shivaji-maharaj.png"
    persona_role: str = "Hero of Swaraj"
    narration: str
    choices: list[ChoiceOption] = []
    quiz: Optional[QuizCheck] = None
    quiz_feedback: Optional[str] = None
    quiz_passed: bool = False
    citations: list[HistorySourceRef] = []
    can_resume_lesson: bool = False
    progress_percentage: int = 0
    messages: list[HistoryChatMessage] = []


# ── Citation Deduplication ───────────────────────────────────────────────────


def deduplicate_citations(citations: list[HistorySourceRef]) -> list[HistorySourceRef]:
    """Deduplicate citations by (source, pdf_page) and sort chronologically."""
    seen: set[tuple[str, int]] = set()
    unique_refs: list[HistorySourceRef] = []
    for c in citations:
        key = (c.source, c.pdf_page)
        if key not in seen:
            seen.add(key)
            unique_refs.append(c)
    return sorted(unique_refs, key=lambda x: x.pdf_page)


# ── In-Memory Session Store ───────────────────────────────────────────────────


class SessionData:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_lesson_id = "HIST_L01"
        self.current_stage_id = "L01_S1_INTRO"
        self.completed_lessons: set[str] = set()
        self.current_stage = "INTRO"
        self.narration = ""
        self.choices: list[ChoiceOption] = []
        self.quiz: Optional[QuizCheck] = None
        self.quiz_feedback: Optional[str] = None
        self.quiz_passed: bool = False
        self.citations: list[HistorySourceRef] = []
        self.saved_state: Optional[dict] = None  # To restore after custom question
        self.messages: list[HistoryChatMessage] = []


_SESSIONS: dict[str, SessionData] = {}


def get_or_create_session(session_id: Optional[str] = None) -> SessionData:
    """Retrieve existing session or instantiate a new isolated session."""
    if not session_id or session_id not in _SESSIONS:
        new_id = session_id or f"hist_{uuid.uuid4().hex[:12]}"
        sess = SessionData(new_id)
        _SESSIONS[new_id] = sess
        # Initialize with first lesson
        _init_lesson_state(sess, "HIST_L01")
        return sess
    return _SESSIONS[session_id]


# ── Persona Configuration ────────────────────────────────────────────────────


def get_persona_info(lesson: LessonNode) -> tuple[str, str, str, str]:
    """
    Returns (persona_key, name, avatar_url, role_description).
    Chhatrapati Shivaji Maharaj is the primary storyteller across the curriculum.
    For background lessons before his birth (Lessons 1-3, 5), he guides students through Maharashtra's heritage.
    """
    if lesson.lesson_number in (1, 2, 3, 5):
        return (
            "SHIVAJI",
            "Chhatrapati Shivaji Maharaj",
            "/avatars/shivaji-maharaj.png",
            "Historical Storyteller & Guide of Maharashtra"
        )
    return (
        "SHIVAJI",
        "Chhatrapati Shivaji Maharaj",
        "/avatars/shivaji-maharaj.png",
        "Hero of Swaraj · Educational First-Person Storyteller"
    )


# ── Ollama Helper ─────────────────────────────────────────────────────────────


def _clean_output_text(text: str) -> str:
    """Clean model generation artifacts, think tags, and accidental labels."""
    clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    clean = re.sub(r"^(Student|Tutor|Shivaji|Assistant|User):\s*", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\n*(Would you like to (practice|learn|ask) [^?\n]+\?)\s*$", "", clean, flags=re.IGNORECASE).strip()
    return clean


def call_llm(messages: list[dict], temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Send chat messages to local Ollama qwen3:1.7b."""
    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=settings.ollama_timeout)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("message", {}).get("content", "").strip()
        return _clean_output_text(raw)
    except Exception as e:
        print(f"Ollama call warning: {e}")
        return ""


# ── Textbook Retrieval ────────────────────────────────────────────────────────


def retrieve_history_chunks(query: str, top_k: int = 4, lesson_num: Optional[int] = None) -> list[dict]:
    """
    Query the dedicated history_master ChromaDB collection.
    Optionally filter by lesson_number if exploring a specific lesson.
    """
    collection = get_history_collection()
    query_emb = embed_query(query)

    where_filter = None
    if lesson_num is not None and lesson_num >= 1:
        where_filter = {"lesson_number": lesson_num}

    try:
        kwargs = {
            "query_embeddings": [query_emb],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        res = collection.query(**kwargs)
    except Exception as e:
        print(f"ChromaDB retrieval warning: {e}")
        res = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    passages = []
    if res and res.get("documents") and res["documents"][0]:
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]

        for doc, meta, dist in zip(docs, metas, dists):
            passages.append({
                "text": doc,
                "pdf_page": meta.get("pdf_page", 11),
                "book_page": meta.get("book_page", 1),
                "lesson_title": meta.get("lesson_title", "History"),
                "lesson_number": meta.get("lesson_number", 1),
                "distance": dist,
            })

    return passages


def retrieve_lesson_opening(lesson_num: int) -> list[dict]:
    """Retrieve opening passages for a lesson from ChromaDB."""
    collection = get_history_collection()
    try:
        res = collection.get(
            where={"lesson_number": lesson_num},
            limit=3,
            include=["documents", "metadatas"],
        )
        if not res or not res["documents"]:
            return []
        return [
            {
                "text": d,
                "pdf_page": m.get("pdf_page", 11),
                "book_page": m.get("book_page", 1),
                "lesson_title": m.get("lesson_title", "History"),
                "lesson_number": m.get("lesson_number", lesson_num),
            }
            for d, m in zip(res["documents"], res["metadatas"])
        ]
    except Exception as e:
        print(f"Error getting lesson opening: {e}")
        return []


# ── Query Contextualization ───────────────────────────────────────────────────


def contextualize_history_query(question: str, persona_key: str, lesson_title: str) -> str:
    """
    Contextualize user questions like 'how strong were you' or 'why did you do that'
    using active persona and current lesson context.
    Avoids polluting standalone general knowledge questions with lesson keywords.
    """
    q_lower = question.lower().strip()
    is_second_person = bool(re.search(r"\b(you|your|yours|yourself|u)\b", q_lower)) or q_lower.startswith(
        ("were you", "are you", "how were you", "how strong were you", "how strong you", "did you", "can you", "who are you")
    )

    if is_second_person:
        cleaned = re.sub(r"\b(you|your|yourself|yours)\b", "Shivaji Maharaj", question, flags=re.IGNORECASE)
        if any(w in q_lower for w in ["strong", "strength", "brave", "courage", "powerful", "fight", "weapon"]):
            return f"Chhatrapati Shivaji Maharaj physical training education martial skills swordsmanship wrestling warfare Pratapgad {cleaned}"
        if any(w in q_lower for w in ["why did you", "why did u", "decision", "treaty", "escape"]):
            return f"Chhatrapati Shivaji Maharaj strategic decision statecraft Swaraj {cleaned} {lesson_title}"
        return f"Chhatrapati Shivaji Maharaj {cleaned} {lesson_title}"

    # Only append lesson_title if the question is an explicit anaphoric follow-up about the ongoing topic
    is_followup = bool(re.search(r"\b(this|that|these|those|here|why did this|what happened next|tell me more|explain more|who was he|who was she)\b", q_lower))
    if is_followup:
        return f"{question} {lesson_title}"

    # Otherwise return the clean question without contaminating it with unrelated history titles!
    return question


# ── Lesson Initialization & Progression ──────────────────────────────────────


def _init_lesson_state(session: SessionData, lesson_id: str):
    """Set up initial state and welcome message for a lesson using structured stages."""
    lesson = get_lesson(lesson_id)
    if not lesson:
        lesson = get_lesson("HIST_L01")
        lesson_id = "HIST_L01"

    session.current_lesson_id = lesson_id
    session.current_stage = "INTRO"
    session.quiz_feedback = None
    session.quiz_passed = False
    session.saved_state = None

    persona_key, persona_name, persona_avatar, persona_role = get_persona_info(lesson)
    opening_passages = retrieve_lesson_opening(lesson.lesson_number)

    # Use first stage if defined in curriculum map
    if lesson.stages:
        first_stage = lesson.stages[0]
        session.current_stage_id = first_stage.stage_id
        session.narration = f"{first_stage.narration}\n\n**{first_stage.pause_prompt}**"
        session.choices = first_stage.choices
        format_type = first_stage.format_type
        figure_profile = first_stage.figure_profile
        timeline_events = first_stage.timeline_events
        comparison = first_stage.comparison
        cause_effect = first_stage.cause_effect
        recap_points = first_stage.recap_points
    else:
        session.current_stage_id = "intro"
        if lesson.lesson_number in (1, 2, 3, 5):
            intro_text = (
                f"Welcome, my young friend! In our land of Maharashtra, long before my time, "
                f"great events and noble figures shaped the destiny of our people.\n\n"
                f"Today, let us explore **Lesson {lesson.lesson_number}: {lesson.title}**.\n\n"
                f"{lesson.summary}\n\n"
                f"**How shall we begin our historical adventure?**"
            )
        else:
            intro_text = (
                f"Greetings, my brave young friend! Welcome to our journey of Swaraj.\n\n"
                f"Here, we explore **Lesson {lesson.lesson_number}: {lesson.title}**.\n\n"
                f"{lesson.summary}\n\n"
                f"**What would you like us to discover first?**"
            )
        session.narration = intro_text
        session.choices = lesson.starter_choices
        format_type = "story"
        figure_profile = None
        timeline_events = None
        comparison = None
        cause_effect = None
        recap_points = None

    session.quiz = lesson.knowledge_check
    session.citations = deduplicate_citations([
        HistorySourceRef(
            source="History.pdf",
            pdf_page=p["pdf_page"],
            book_page=p["book_page"],
            lesson_title=lesson.title,
            snippet=p["text"][:140] + "..."
        )
        for p in opening_passages[:2]
    ])

    first_msg = HistoryChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="assistant",
        content=session.narration,
        format_type=format_type,
        figure_profile=figure_profile,
        timeline_events=timeline_events,
        comparison=comparison,
        cause_effect=cause_effect,
        recap_points=recap_points,
        persona=persona_key,
        persona_name=persona_name,
        persona_avatar=persona_avatar,
        persona_role=persona_role,
        citations=session.citations,
        choices=session.choices,
        timestamp=datetime.now().strftime("%I:%M %p"),
    )
    session.messages = [first_msg]


# ── Action Dispatcher ─────────────────────────────────────────────────────────


def process_lesson_action(session_id: str, action: dict) -> HistorySessionState:
    """
    Process interactive student choices or quiz answers:
    action: {
        "action_type": "choice" | "quiz_answer" | "next_lesson" | "select_lesson" | "return_to_lesson",
        "choice_id": str (optional),
        "selected_index": int (optional),
        "lesson_id": str (optional)
    }
    """
    session = get_or_create_session(session_id)
    action_type = action.get("action_type", "choice")
    lesson = get_lesson(session.current_lesson_id) or get_lesson("HIST_L01")
    persona_key, persona_name, persona_avatar, persona_role = get_persona_info(lesson)
    now_ts = datetime.now().strftime("%I:%M %p")

    # 1. Return to ongoing lesson from a custom question
    if action_type == "return_to_lesson":
        if session.saved_state:
            session.current_stage = session.saved_state.get("current_stage", "STORY")
            session.current_stage_id = session.saved_state.get("current_stage_id", session.current_stage_id)
            session.narration = session.saved_state.get("narration", session.narration)
            session.choices = session.saved_state.get("choices", session.choices)
            session.quiz = session.saved_state.get("quiz", session.quiz)
            session.quiz_feedback = session.saved_state.get("quiz_feedback")
            session.quiz_passed = session.saved_state.get("quiz_passed", False)
            session.citations = session.saved_state.get("citations", session.citations)
            session.saved_state = None

            user_msg = HistoryChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="user",
                content="⬅️ Let's return to our story",
                timestamp=now_ts,
            )
            session.messages.append(user_msg)

            assistant_msg = HistoryChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="assistant",
                content=f"Welcome back to our lesson on **{lesson.title}**! Let us resume where we paused:\n\n{session.narration}",
                persona=persona_key,
                persona_name=persona_name,
                persona_avatar=persona_avatar,
                persona_role=persona_role,
                citations=session.citations,
                choices=session.choices,
                timestamp=now_ts,
            )
            session.messages.append(assistant_msg)
            return build_session_response(session)

    # 2. Select Lesson directly from Curriculum Map
    if action_type == "select_lesson":
        target_id = action.get("lesson_id", "HIST_L01")
        _init_lesson_state(session, target_id)
        return build_session_response(session)

    # 3. Next Lesson Progression
    if action_type == "next_lesson":
        session.completed_lessons.add(session.current_lesson_id)
        next_id = lesson.next_lesson_id or "HIST_L01"
        _init_lesson_state(session, next_id)
        return build_session_response(session)

    # 4. Interactive Quiz Submission
    if action_type == "quiz_answer":
        selected_idx = action.get("selected_index", 0)
        quiz = session.quiz or lesson.knowledge_check
        is_correct = (selected_idx == quiz.correct_index)

        user_msg = HistoryChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role="user",
            content=f"Selected option: {StringOptionLabel(selected_idx)}: {quiz.options[selected_idx] if selected_idx < len(quiz.options) else ''}",
            timestamp=now_ts,
        )
        session.messages.append(user_msg)

        session.current_stage = "FEEDBACK"
        session.quiz_passed = is_correct

        if is_correct:
            session.completed_lessons.add(session.current_lesson_id)
            feedback = (
                f"🎉 **Magnificent, young explorer! That is completely correct!**\n\n"
                f"{quiz.explanation}\n\n"
                f"You have demonstrated true mastery of **Lesson {lesson.lesson_number}: {lesson.title}**."
            )
            session.choices = [
                ChoiceOption(id="next_lesson", label="➡️ Advance to Next Lesson", type="next"),
                ChoiceOption(id="story_review", label="📖 Review Key Insights", type="story"),
            ]
        else:
            feedback = (
                f"💡 **Good try! Let's learn from the textbook:**\n\n"
                f"{quiz.explanation}\n\n"
                f"Don't worry—every true explorer learns by trying! Would you like to review this topic or try again?"
            )
            session.choices = [
                ChoiceOption(id="quiz", label="🔄 Try the Quiz Again", type="quiz"),
                ChoiceOption(id="story_review", label="📖 Revisit the Story", type="story"),
            ]

        session.narration = feedback
        session.quiz_feedback = feedback
        assistant_msg = HistoryChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=feedback,
            persona=persona_key,
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            persona_role=persona_role,
            quiz=quiz,
            quiz_feedback=feedback,
            quiz_passed=is_correct,
            choices=session.choices,
            timestamp=now_ts,
        )
        session.messages.append(assistant_msg)
        return build_session_response(session)

    # 5. Clickable Choice Progression
    choice_id = action.get("choice_id", "story")

    # Resolve choice label for user message
    user_choice_text = "Explore this topic"
    for c in session.choices:
        if c.id == choice_id:
            user_choice_text = c.label
            break

    user_msg = HistoryChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="user",
        content=user_choice_text,
        timestamp=now_ts,
    )
    session.messages.append(user_msg)

    # Quiz choice
    if choice_id.startswith("quiz") or choice_id in ("quiz", "quiz_check"):
        session.current_stage = "QUIZ"
        session.quiz = lesson.knowledge_check
        session.quiz_feedback = None
        quiz_intro = (
            f"**Knowledge Challenge: Lesson {lesson.lesson_number} — {lesson.title}**\n\n"
            f"Let us test what you have discovered on our journey!"
        )
        session.narration = quiz_intro
        session.choices = []

        assistant_msg = HistoryChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=quiz_intro,
            format_type="quiz",
            persona=persona_key,
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            persona_role=persona_role,
            quiz=session.quiz,
            timestamp=now_ts,
        )
        session.messages.append(assistant_msg)
        return build_session_response(session)

    if choice_id == "next_lesson":
        session.completed_lessons.add(session.current_lesson_id)
        next_id = lesson.next_lesson_id or "HIST_L01"
        _init_lesson_state(session, next_id)
        return build_session_response(session)

    # Check if a matching stage is defined in the lesson
    target_stage: Optional[LessonStage] = None
    if lesson.stages:
        for stage in lesson.stages:
            s_id = stage.stage_id.lower()
            c_id = choice_id.lower()
            if c_id == s_id or c_id.endswith(s_id) or s_id.endswith(c_id) or any(part in s_id for part in c_id.split("_") if len(part) >= 3):
                target_stage = stage
                break

    # If no stage matched, pick stage by choice intent
    if not target_stage and lesson.stages:
        if any(k in choice_id for k in ["dnyaneshwar", "armor", "mavla", "shahaji", "figures", "figure"]):
            target_stage = next((s for s in lesson.stages if s.format_type == "figure"), lesson.stages[1] if len(lesson.stages) > 1 else lesson.stages[0])
        elif any(k in choice_id for k in ["timeline", "step", "encounter", "raid", "escape"]):
            target_stage = next((s for s in lesson.stages if s.format_type == "timeline"), lesson.stages[1] if len(lesson.stages) > 1 else lesson.stages[0])
        elif any(k in choice_id for k in ["recap", "summary", "review"]):
            target_stage = next((s for s in lesson.stages if s.format_type == "recap"), lesson.stages[-1])
        elif any(k in choice_id for k in ["compare", "rulers", "sultans"]):
            target_stage = next((s for s in lesson.stages if s.format_type == "comparison"), lesson.stages[1] if len(lesson.stages) > 1 else lesson.stages[0])
        elif any(k in choice_id for k in ["cause", "why", "jiva", "ramdas", "swaraj"]):
            target_stage = next((s for s in lesson.stages if s.format_type == "cause_effect"), lesson.stages[1] if len(lesson.stages) > 1 else lesson.stages[0])
        else:
            target_stage = lesson.stages[1] if len(lesson.stages) > 1 else lesson.stages[0]

    # Retrieve grounding context for chosen path
    passages = retrieve_history_chunks(
        f"{lesson.title} {choice_id} {lesson.key_concepts[0]}",
        top_k=3,
        lesson_num=lesson.lesson_number
    )
    context_text = "\n\n".join([f"[Page {p['pdf_page']}] {p['text']}" for p in passages])

    # Dynamic generation prompt tailored to Shivaji as primary storyteller
    is_background_lesson = (lesson.lesson_number in (1, 2, 3, 5))
    if is_background_lesson:
        sys_prompt = (
            f"You are Chhatrapati Shivaji Maharaj speaking as the wise, inspiring historical storyteller "
            f"guiding a 10-year-old school student through the history of Maharashtra before your time.\n"
            f"Lesson: {lesson.title} (Lesson {lesson.lesson_number})\n"
            f"TEXTBOOK CONTEXT:\n{context_text}\n\n"
            f"GUIDELINES:\n"
            f"- Speak warmly as the storyteller guiding the student through your land's history ('In our land of Maharashtra, great saints walked before my time...').\n"
            f"- CRITICAL: Never claim to have witnessed or participated in events that occurred before your lifetime (pre-1630).\n"
            f"- Ground your narration strictly in the provided textbook context.\n"
            f"- Keep the explanation engaging, concise (2 to 4 sentences), and suitable for a 10-year-old.\n"
            f"- Do NOT prepend labels like 'Shivaji:' or 'Tutor:'."
        )
    else:
        sys_prompt = (
            f"You are Chhatrapati Shivaji Maharaj engaging in a warm, first-person educational roleplay "
            f"for a 10-year-old Class 5 school student.\n"
            f"Lesson: {lesson.title} (Lesson {lesson.lesson_number})\n"
            f"TEXTBOOK CONTEXT:\n{context_text}\n\n"
            f"GUIDELINES:\n"
            f"- Speak warmly, courageously, and in the FIRST PERSON ('I, Shivaji...', 'We climbed the hills of Maval...').\n"
            f"- Ground your narration strictly in the provided textbook context.\n"
            f"- Never invent fake events, fake quotes, or claims not found in the textbook.\n"
            f"- Keep the explanation engaging, concise (2 to 4 sentences), and age-appropriate.\n"
            f"- Do NOT prepend labels like 'Shivaji:' or 'Tutor:'."
        )

    user_prompt = f"Explain the historical significance of {user_choice_text} from {lesson.title} clearly."
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if target_stage and target_stage.narration:
        llm_output = f"{target_stage.narration}\n\n**{target_stage.pause_prompt}**"
    else:
        llm_output = call_llm(messages, temperature=0.3, max_tokens=350)
        if not llm_output or len(llm_output) < 30:
            if target_stage:
                llm_output = f"{target_stage.narration}\n\n**{target_stage.pause_prompt}**"
            else:
                llm_output = lesson.summary

    session.narration = llm_output
    session.citations = deduplicate_citations([
        HistorySourceRef(
            source="History.pdf",
            pdf_page=p["pdf_page"],
            book_page=p["book_page"],
            lesson_title=lesson.title,
            snippet=p["text"][:140] + "..."
        )
        for p in passages
    ])

    # Dynamic stage choices
    if target_stage and target_stage.choices:
        session.choices = target_stage.choices
        format_type = target_stage.format_type
        figure_profile = target_stage.figure_profile
        timeline_events = target_stage.timeline_events
        comparison = target_stage.comparison
        cause_effect = target_stage.cause_effect
        recap_points = target_stage.recap_points
    else:
        # Meaningful next choices based on lesson
        session.choices = [
            ChoiceOption(id=f"explore_{lesson.id}", label=f"🔍 Explore key figures in {lesson.title}", type="explore"),
            ChoiceOption(id=f"cause_{lesson.id}", label=f"❓ Why was this significant for Swaraj?", type="cause"),
            ChoiceOption(id="quiz", label="🎯 Take the Knowledge Check", type="quiz"),
            ChoiceOption(id="next_lesson", label="➡️ Advance to next lesson", type="next"),
        ]
        format_type = "story"
        figure_profile = None
        timeline_events = None
        comparison = None
        cause_effect = None
        recap_points = None

    assistant_msg = HistoryChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="assistant",
        content=llm_output,
        format_type=format_type,
        figure_profile=figure_profile,
        timeline_events=timeline_events,
        comparison=comparison,
        cause_effect=cause_effect,
        recap_points=recap_points,
        persona=persona_key,
        persona_name=persona_name,
        persona_avatar=persona_avatar,
        persona_role=persona_role,
        citations=session.citations,
        choices=session.choices,
        timestamp=now_ts,
    )
    session.messages.append(assistant_msg)
    return build_session_response(session)


# ── Custom Question Handling ──────────────────────────────────────────────────


_GREETINGS = {"hi", "hello", "hey", "good morning", "good afternoon", "how are you", "who are you"}


def handle_custom_question(session_id: str, question: str) -> HistorySessionState:
    """
    Handle student's custom questions at any time without resetting their lesson progression.
    Supports 3 modes:
    1. Guided learning: relates to ongoing lesson topic or Shivaji Maharaj
    2. Master textbook search: searches entire History.pdf with accurate, deduplicated citations
    3. General knowledge / casual chat: natural answer without false textbook citations
    """
    session = get_or_create_session(session_id)
    lesson = get_lesson(session.current_lesson_id) or get_lesson("HIST_L01")
    persona_key, persona_name, persona_avatar, persona_role = get_persona_info(lesson)
    now_ts = datetime.now().strftime("%I:%M %p")

    # Add User Message to conversation timeline
    user_msg = HistoryChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="user",
        content=question,
        timestamp=now_ts,
    )
    session.messages.append(user_msg)

    # Preserve current state if not already saved
    if not session.saved_state:
        session.saved_state = {
            "current_stage": session.current_stage,
            "current_stage_id": session.current_stage_id,
            "narration": session.narration,
            "choices": session.choices,
            "quiz": session.quiz,
            "quiz_feedback": session.quiz_feedback,
            "quiz_passed": session.quiz_passed,
            "citations": session.citations,
        }

    q_lower = question.strip().lower()

    # Case 1: Casual Greeting or Chit-chat
    if any(q_lower == g or q_lower.startswith(g + " ") for g in _GREETINGS) or (len(q_lower.split()) <= 2 and q_lower in ("hi", "hello", "namaste", "bye")):
        reply = (
            "Jai Bhavani! Greetings, my brave young friend! I am Chhatrapati Shivaji Maharaj. "
            "I am pleased to walk this path of history with you. You can ask me anything about our battles, "
            "our forts, our saints, or continue our lesson whenever you are ready!"
        )
        session.current_stage = "CUSTOM_ANSWER"
        session.narration = reply
        session.citations = []
        session.choices = [
            ChoiceOption(id="return", label="⬅️ Return to Story", type="story"),
            ChoiceOption(id="continue_lesson", label="📖 Continue Current Lesson", type="story"),
        ]

        assistant_msg = HistoryChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=reply,
            format_type="chat",
            persona=persona_key,
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            persona_role=persona_role,
            choices=session.choices,
            is_custom_answer=True,
            can_resume=True,
            timestamp=now_ts,
        )
        session.messages.append(assistant_msg)
        return build_session_response(session)

    # Case 2: Textbook RAG Search across the ENTIRE History.pdf
    contextual_query = contextualize_history_query(question, persona_key, lesson.title)
    retrieved = retrieve_history_chunks(contextual_query, top_k=4)
    min_dist = min([p["distance"] for p in retrieved]) if retrieved else 1.0

    # Verify that substantive keywords from question actually appear in the retrieved textbook context
    _common_sw = {"what", "is", "was", "are", "were", "where", "when", "why", "how", "who", "whom", "did", "does", "the", "and", "our", "book", "textbook", "say", "tell", "about", "this", "that", "with", "from", "have", "been", "there", "much", "many", "some"}
    substantive_q_words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", q_lower) if w not in _common_sw]
    is_second_person = bool(re.search(r"\b(you|your|yours|yourself|u)\b", q_lower))

    if substantive_q_words and not is_second_person:
        all_retrieved_text = " ".join([p["text"].lower() for p in retrieved])
        keyword_match = any(w in all_retrieved_text for w in substantive_q_words)
    else:
        keyword_match = True

    is_historically_relevant = (min_dist <= 0.185) and keyword_match
    relevant_passages = [
        p for p in retrieved
        if p["distance"] <= 0.185 and p["lesson_number"] >= 1
    ] if is_historically_relevant else []

    asks_textbook = any(k in q_lower for k in ["textbook", "book say", "according to book", "in our book", "lesson", "syllabus"])

    if relevant_passages:
        context_str = "\n\n".join([
            f"[PDF Page {p['pdf_page']} / Book Page {p['book_page']} - {p['lesson_title']}]\n{p['text']}"
            for p in relevant_passages
        ])

        sys_prompt = (
            f"You are Chhatrapati Shivaji Maharaj in a first-person educational roleplay for a Class 5 student.\n"
            f"TEXTBOOK EVIDENCE (from History.pdf):\n{context_str}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Answer the student's question directly and courageously in the first person ('I...', 'Our brave soldiers...').\n"
            f"- Base your answer strictly on the facts in the textbook evidence provided (for example, physical training in swordsmanship, wrestling, horse riding, and armor at Pratapgad).\n"
            f"- Never invent dates, quotes, or claims not found in the context.\n"
            f"- Keep it clear, engaging, and suitable for a 10-year-old child (2 to 4 sentences).\n"
            f"- Do NOT prepend 'Shivaji:' or other labels."
        )

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question},
        ]

        ans = call_llm(messages, temperature=0.25, max_tokens=350)
        if not ans or len(ans) < 20:
            ans = f"According to our History textbook ({relevant_passages[0]['lesson_title']}): {relevant_passages[0]['text'][:250]}..."

        session.current_stage = "CUSTOM_ANSWER"
        session.narration = ans
        session.citations = deduplicate_citations([
            HistorySourceRef(
                source="History.pdf",
                pdf_page=p["pdf_page"],
                book_page=p["book_page"],
                lesson_title=p["lesson_title"],
                snippet=p["text"][:140] + "..."
            )
            for p in relevant_passages
        ])
        session.choices = [
            ChoiceOption(id="return", label="⬅️ Return to Story", type="story"),
            ChoiceOption(id="deeper", label="🔍 Tell me more about this", type="explore"),
            ChoiceOption(id="quiz", label="🎯 Try a quiz on this chapter", type="quiz"),
        ]

        assistant_msg = HistoryChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=ans,
            format_type="explanation",
            persona=persona_key,
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            persona_role=persona_role,
            citations=session.citations,
            choices=session.choices,
            is_custom_answer=True,
            can_resume=True,
            timestamp=now_ts,
        )
        session.messages.append(assistant_msg)
        return build_session_response(session)

    # Case 3: Honest Absence for Uncovered Topics
    if asks_textbook:
        reply = (
            f"The Class 5 History textbook (*Shivachhatrapati*) focuses on Maharashtra and the life and times of "
            f"Chhatrapati Shivaji Maharaj. It does not provide information about '{question.strip()}'.\n\n"
            f"If you'd like, I can share general knowledge about this, or we can return to our history story!"
        )
        session.current_stage = "CUSTOM_ANSWER"
        session.narration = reply
        session.citations = []
        session.choices = [
            ChoiceOption(id="return", label="⬅️ Return to Story", type="story"),
        ]

        assistant_msg = HistoryChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=reply,
            format_type="chat",
            persona=persona_key,
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            persona_role=persona_role,
            choices=session.choices,
            is_custom_answer=True,
            can_resume=True,
            timestamp=now_ts,
        )
        session.messages.append(assistant_msg)
        return build_session_response(session)

    # Case 4: General Knowledge Question (No False Citations)
    sys_prompt = (
        "You are an encouraging and accurate educational companion for Class 5 students (about 10 years old).\n"
        "The student is asking a general knowledge question.\n"
        "Answer warmly, accurately, and simply in 2 to 3 sentences suitable for a 10-year-old child.\n"
        "Do not invent textbook citations or claim this is from the history textbook."
    )
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": question},
    ]

    ans = call_llm(messages, temperature=0.3, max_tokens=250)
    if not ans or len(ans) < 20:
        ans = "That is a fascinating question! I'm happy to help you discover new things both inside and outside our history lessons."

    session.current_stage = "CUSTOM_ANSWER"
    session.narration = ans
    session.citations = []
    session.choices = [
        ChoiceOption(id="return", label="⬅️ Return to Story", type="story"),
    ]

    assistant_msg = HistoryChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="assistant",
        content=ans,
        format_type="explanation",
        persona=persona_key,
        persona_name=persona_name,
        persona_avatar=persona_avatar,
        persona_role=persona_role,
        citations=[],
        choices=session.choices,
        is_custom_answer=True,
        can_resume=True,
        timestamp=now_ts,
    )
    session.messages.append(assistant_msg)
    return build_session_response(session)


# ── Response Builder ──────────────────────────────────────────────────────────


def build_session_response(session: SessionData) -> HistorySessionState:
    """Serialize internal session state into API response schema."""
    lesson = get_lesson(session.current_lesson_id) or get_lesson("HIST_L01")
    persona_key, persona_name, persona_avatar, persona_role = get_persona_info(lesson)

    total_lessons = 18
    completed_count = len(session.completed_lessons)
    progress_pct = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

    return HistorySessionState(
        session_id=session.session_id,
        current_lesson_id=session.current_lesson_id,
        lesson_title=lesson.title,
        lesson_number=lesson.lesson_number,
        total_lessons=total_lessons,
        completed_lessons=sorted(list(session.completed_lessons)),
        current_stage=session.current_stage,
        persona=persona_key,
        persona_name=persona_name,
        persona_avatar=persona_avatar,
        persona_role=persona_role,
        narration=session.narration,
        choices=session.choices,
        quiz=session.quiz,
        quiz_feedback=session.quiz_feedback,
        quiz_passed=session.quiz_passed,
        citations=session.citations,
        can_resume_lesson=(session.saved_state is not None),
        progress_percentage=progress_pct,
        messages=session.messages,
    )


def StringOptionLabel(idx: int) -> str:
    """Format index 0, 1, 2 into A, B, C."""
    return chr(65 + idx) if 0 <= idx < 26 else str(idx)
