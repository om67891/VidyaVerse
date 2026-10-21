"""
Persona-Aware Tutoring & Conversational Orchestrator for VidyaVerse Learning Hub.

Pipeline:
1. Conversation & Persona Resolution (enforced authoritatively from SQLite repository)
2. Intent Routing & Scope Determination (textbook_grounded vs general_knowledge vs action)
3. Scope-Isolated Retrieval (via RetrievalService)
4. Dynamic System Prompt Construction (via PersonaManager)
5. Structured LLM Generation (via Ollama) with thinking suppression
6. Citations & Biographical Guardrails (via CitationValidator)
7. Deterministic Mathematical Validation (via MathValidator)
8. Tap-to-Reveal Glossary Detection (via GlossaryService)
9. Progress Tracking ("You've explored X of Y learning moments")
10. Transactional SQLite Persistence (Messages and Learning State)
"""
from __future__ import annotations

import re
import uuid
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field

from backend.config import settings
from backend.repositories.conversation_repository import get_conversation_repository
from backend.services.persona_manager import get_persona_manager
from backend.services.retrieval_service import get_retrieval_service, RetrievalEvidence
from backend.services.citation_validator import get_citation_validator, ValidatedCitation
from backend.services.math_validator import get_math_validator
from backend.services.learning_map_service import get_learning_map_service
from backend.services.glossary_service import get_glossary_service, GlossaryTerm
from backend.services.quiz_service import get_quiz_service
from backend.services.rag import generate_with_ollama_chat


# ── Schemas ────────────────────────────────────────────────────────────────────


class SuggestedAction(BaseModel):
    action_id: str
    action_type: str  # "moment_select" | "quiz" | "resume_lesson" | "explore_topic" | "custom_question"
    label: str
    payload: dict[str, Any] = {}


class TutoringMessageRequest(BaseModel):
    conversation_id: str
    message: str = Field(..., min_length=1)
    action_payload: Optional[dict[str, Any]] = None
    response_mode: Optional[str] = None  # "documented" | "persona_inspired" | "imaginative"
    question_format: Optional[str] = None


class TutoringResponse(BaseModel):
    conversation_id: str
    persona_id: str
    persona_name: str
    persona_avatar: str
    subject_id: str
    chat_scope: Literal["subject", "chapter"]
    chapter_id: Optional[str] = None
    intent: str
    response_mode: str
    format_type: str
    answer: str
    citations: list[ValidatedCitation] = []
    suggested_actions: list[SuggestedAction] = []
    glossary_chips: list[GlossaryTerm] = []
    progress: dict[str, Any] = {}
    learning_state: dict[str, Any] = {}


# ── Tutoring Service ──────────────────────────────────────────────────────────


class TutoringService:
    def __init__(self):
        self.repo = get_conversation_repository()
        self.persona_mgr = get_persona_manager()
        self.retrieval = get_retrieval_service()
        self.citation_val = get_citation_validator()
        self.math_val = get_math_validator()
        self.learning_maps = get_learning_map_service()
        self.glossary = get_glossary_service()
        self.quiz = get_quiz_service()

    def process_message(self, request: TutoringMessageRequest) -> TutoringResponse:
        # 1. Authoritative conversation resolution from SQLite
        conv = self.repo.get_conversation(request.conversation_id)
        if not conv:
            raise ValueError(f"Conversation '{request.conversation_id}' not found.")

        # Locked parameters from database
        subject_id = conv["subject_id"]
        chat_scope = conv["chat_scope"]
        chapter_id = conv["chapter_id"]
        persona_id = conv["persona_id"]
        learning_state = conv["learning_state"] or {}

        # Ensure explored_moment_ids list exists
        explored_moments: list[str] = learning_state.get("explored_moment_ids", [])
        suspended_moment_id: Optional[str] = learning_state.get("suspended_moment_id")

        persona = self.persona_mgr.get_persona(persona_id)
        persona_name = persona["display_name"] if persona else "VidyaVerse Tutor"
        persona_avatar = persona.get("avatar_path", "/avatars/default.svg") if persona else "/avatars/default.svg"

        raw_query = request.message.strip()
        action_payload = request.action_payload or {}

        # ── Check for structured action execution ─────────────────────────────
        action_type = action_payload.get("action_type")
        if action_type == "resume_lesson" and suspended_moment_id:
            # Resume previous moment
            return self._handle_moment_selection(
                conv=conv,
                moment_id=suspended_moment_id,
                persona=persona,
                is_resumption=True,
            )
        elif action_type == "moment_select" and action_payload.get("moment_id"):
            return self._handle_moment_selection(
                conv=conv,
                moment_id=action_payload["moment_id"],
                persona=persona,
                is_resumption=False,
            )
        elif action_type == "quiz_answer":
            return self._handle_quiz_answer(
                conv=conv,
                persona=persona,
                payload=action_payload,
            )

        # 2. Intent Routing & Scope Determination
        is_gk = self._detect_general_knowledge(raw_query)
        detected_format = request.question_format or self._detect_format_type(raw_query)

        # 3. Retrieval
        retrieved_evidences: list[RetrievalEvidence] = []
        citations: list[ValidatedCitation] = []
        retrieval_status = "ok"

        if not is_gk:
            ret_res = self.retrieval.retrieve(
                subject_id=subject_id,
                query=raw_query,
                chat_scope=chat_scope,
                chapter_id=chapter_id,
                top_k=4,
            )
            retrieval_status = ret_res.status
            if ret_res.status == "ok":
                retrieved_evidences = ret_res.evidences
                # Validate citations
                citations = self.citation_val.validate_citations(
                    candidate_chunk_ids=[ev.chunk_id for ev in retrieved_evidences[:2]],
                    retrieved_evidences=retrieved_evidences,
                    chat_scope=chat_scope,
                    current_chapter_id=chapter_id,
                    is_general_knowledge=False,
                )
            elif ret_res.status == "unindexed_chapter":
                return self._build_error_response(
                    conv,
                    persona,
                    f"The requested chapter '{chapter_id}' has not been indexed yet.",
                )

        # 4. Prompt Assembly
        recent_messages = self.repo.get_recent_messages(conv["conversation_id"], limit=4)
        history_msgs = [{"role": m["role"], "content": m["content"]} for m in recent_messages]

        context_str = ""
        if retrieved_evidences:
            context_str = "\n\n".join(
                f"[Source: {e.source_document}, p. {e.book_page}]\n{e.content}"
                for e in retrieved_evidences
            )

        system_prompt = self.persona_mgr.build_system_prompt(
            persona_id=persona_id,
            subject_name=subject_id.capitalize(),
            chapter_name=chapter_id or f"All {subject_id.capitalize()}",
            context_str=context_str,
            response_mode=request.response_mode or ("persona_inspired" if is_gk else "documented"),
            question_format=detected_format,
        )

        llm_messages = [
            {"role": "system", "content": system_prompt},
            *history_msgs,
            {"role": "user", "content": raw_query},
        ]

        # 5. LLM Generation
        answer_text = generate_with_ollama_chat(llm_messages, temperature=0.25)

        # 6. Post-processing & Guardrails
        # Biographical guardrails
        _, answer_text, _ = self.citation_val.validate_biographical_content(
            persona_id=persona_id,
            answer_text=answer_text,
            retrieved_evidences=retrieved_evidences,
        )

        # Mathematical verification
        if subject_id == "mathematics":
            math_ok, correction = self.math_val.verify_answer_calculation(answer_text)
            if not math_ok and correction:
                answer_text += f"\n\n*Note on calculation:* {correction}"

        # Glossary term detection
        glossary_chips = self.glossary.detect_terms_in_text(answer_text, subject_id)

        # 7. Check if this query interrupts an active learning moment
        cur_moment_id = learning_state.get("current_moment_id")
        if cur_moment_id and cur_moment_id not in explored_moments:
            # Save as suspended so student can resume
            learning_state["suspended_moment_id"] = cur_moment_id

        # 8. Suggested Next Actions
        suggested_actions = self._generate_suggested_actions(
            subject_id=subject_id,
            chat_scope=chat_scope,
            chapter_id=chapter_id,
            persona_id=persona_id,
            format_type=detected_format,
            suspended_moment_id=learning_state.get("suspended_moment_id"),
        )

        # 9. Compute Progress
        progress = {}
        if chapter_id:
            progress = self.learning_maps.compute_progress(
                subject_id=subject_id,
                chapter_id=chapter_id,
                explored_moment_ids=explored_moments,
            )

        # 10. Persist to SQLite
        self.repo.add_message(
            conversation_id=conv["conversation_id"],
            role="user",
            content=raw_query,
        )
        self.repo.add_message(
            conversation_id=conv["conversation_id"],
            role="assistant",
            content=answer_text,
            response_format=detected_format,
            response_mode="general_knowledge" if is_gk else "textbook_grounded",
            citations=[c.model_dump() for c in citations],
            suggested_actions=[a.model_dump() for a in suggested_actions],
        )
        self.repo.update_learning_state(conv["conversation_id"], learning_state)

        return TutoringResponse(
            conversation_id=conv["conversation_id"],
            persona_id=persona_id,
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            subject_id=subject_id,
            chat_scope=chat_scope,
            chapter_id=chapter_id,
            intent="general_knowledge" if is_gk else "textbook_question",
            response_mode="general_knowledge" if is_gk else "textbook_grounded",
            format_type=detected_format,
            answer=answer_text,
            citations=citations,
            suggested_actions=suggested_actions,
            glossary_chips=glossary_chips,
            progress=progress,
            learning_state=learning_state,
        )

    def _handle_moment_selection(
        self,
        conv: dict,
        moment_id: str,
        persona: Optional[dict],
        is_resumption: bool = False,
    ) -> TutoringResponse:
        """Presents a structured learning moment from the chapter learning map."""
        subject_id = conv["subject_id"]
        chapter_id = conv["chapter_id"]
        learning_state = conv["learning_state"] or {}
        explored_moments: list[str] = learning_state.get("explored_moment_ids", [])

        ch_map = self.learning_maps.get_chapter_map(subject_id, chapter_id or "")
        target_moment = None
        if ch_map:
            for m in ch_map.moments:
                if m.moment_id == moment_id:
                    target_moment = m
                    break

        if not target_moment:
            # Fallback
            return self.process_message(
                TutoringMessageRequest(
                    conversation_id=conv["conversation_id"],
                    message=f"Tell me about moment {moment_id}",
                )
            )

        # Mark moment explored
        if moment_id not in explored_moments:
            explored_moments.append(moment_id)
            learning_state["explored_moment_ids"] = explored_moments

        learning_state["current_moment_id"] = moment_id
        learning_state.pop("suspended_moment_id", None)  # clear suspension

        prefix = "Resuming where we left off: " if is_resumption else ""
        content = f"{prefix}**{target_moment.title}**\n\n{target_moment.summary}\n\n*Key Concepts:* {', '.join(target_moment.key_concepts)}"

        # Citations
        citations = [
            ValidatedCitation(
                chunk_id=f"moment_{moment_id}",
                subject_id=subject_id,
                chapter_id=chapter_id or "",
                chapter_title=ch_map.chapter_title if ch_map else "",
                source_document=f"{subject_id.capitalize()}.pdf",
                book_page=target_moment.book_page,
                pdf_page=target_moment.book_page,
                display_label=f"{ch_map.chapter_title if ch_map else subject_id}, p. {target_moment.book_page}",
            )
        ]

        # Next actions
        actions = []
        for opt in target_moment.action_options:
            actions.append(
                SuggestedAction(
                    action_id=f"act_{uuid.uuid4().hex[:6]}",
                    action_type="explore_topic",
                    label=opt,
                    payload={"topic": opt},
                )
            )
        actions.append(
            SuggestedAction(
                action_id=f"act_{uuid.uuid4().hex[:6]}",
                action_type="custom_question",
                label="Ask a custom question",
                payload={},
            )
        )

        progress = self.learning_maps.compute_progress(
            subject_id=subject_id,
            chapter_id=chapter_id or "",
            explored_moment_ids=explored_moments,
        )

        persona_name = persona["display_name"] if persona else "VidyaVerse Tutor"
        persona_avatar = persona.get("avatar_path", "/avatars/default.svg") if persona else "/avatars/default.svg"

        # Persist
        self.repo.add_message(
            conversation_id=conv["conversation_id"],
            role="assistant",
            content=content,
            response_format=target_moment.format_type,
            response_mode="textbook_grounded",
            citations=[c.model_dump() for c in citations],
            suggested_actions=[a.model_dump() for a in actions],
        )
        self.repo.update_learning_state(conv["conversation_id"], learning_state)

        return TutoringResponse(
            conversation_id=conv["conversation_id"],
            persona_id=conv["persona_id"],
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            subject_id=subject_id,
            chat_scope=conv["chat_scope"],
            chapter_id=chapter_id,
            intent="learning_moment",
            response_mode="textbook_grounded",
            format_type=target_moment.format_type,
            answer=content,
            citations=citations,
            suggested_actions=actions,
            glossary_chips=self.glossary.detect_terms_in_text(content, subject_id),
            progress=progress,
            learning_state=learning_state,
        )

    def _handle_quiz_answer(
        self,
        conv: dict,
        persona: Optional[dict],
        payload: dict[str, Any],
    ) -> TutoringResponse:
        question_id = payload.get("question_id", "")
        selected_index = int(payload.get("selected_index", 0))

        val = self.quiz.validate_answer(question_id, selected_index)
        if not val:
            return self._build_error_response(conv, persona, "Question not found.")

        result_text = f"**Quiz Feedback:**\n\n{val.feedback}\n\n*Explanation:* {val.explanation}"

        actions = [
            SuggestedAction(
                action_id=f"act_{uuid.uuid4().hex[:6]}",
                action_type="explore_topic",
                label="Explore the next concept",
                payload={},
            ),
            SuggestedAction(
                action_id=f"act_{uuid.uuid4().hex[:6]}",
                action_type="custom_question",
                label="Ask a custom question",
                payload={},
            ),
        ]

        persona_name = persona["display_name"] if persona else "VidyaVerse Tutor"
        persona_avatar = persona.get("avatar_path", "/avatars/default.svg") if persona else "/avatars/default.svg"

        self.repo.add_message(
            conversation_id=conv["conversation_id"],
            role="assistant",
            content=result_text,
            response_format="feedback",
            response_mode="textbook_grounded",
            citations=[],
            suggested_actions=[a.model_dump() for a in actions],
        )

        return TutoringResponse(
            conversation_id=conv["conversation_id"],
            persona_id=conv["persona_id"],
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            subject_id=conv["subject_id"],
            chat_scope=conv["chat_scope"],
            chapter_id=conv["chapter_id"],
            intent="quiz_feedback",
            response_mode="textbook_grounded",
            format_type="feedback",
            answer=result_text,
            citations=[],
            suggested_actions=actions,
            glossary_chips=[],
            progress={},
            learning_state=conv["learning_state"] or {},
        )

    def _detect_general_knowledge(self, query: str) -> bool:
        """Determines if query is genuinely about general knowledge outside the school curriculum."""
        clean = query.lower()
        gk_patterns = [
            r"\b(photosynthesis|black hole|solar system|speed of light|who was isaac newton|quantum|gravity|dna|mars rover|atmosphere)\b",
            r"\b(what is a computer|artificial intelligence|robotics|internet|electricity)\b",
            r"\b(capital of france|who invented the telephone|mount everest height)\b",
        ]
        return any(re.search(p, clean) for p in gk_patterns)

    def _detect_format_type(self, query: str) -> str:
        clean = query.lower()
        if re.search(r"\b(who was|who is|biography|about him|about her)\b", clean):
            return "figure_profile"
        if re.search(r"\b(timeline|chronology|when did|dates|sequence of events)\b", clean):
            return "timeline"
        if re.search(r"\b(why did|cause|consequence|reason for|result of)\b", clean):
            return "cause_effect"
        if re.search(r"\b(compare|difference between|versus|vs|distinguish)\b", clean):
            return "comparison"
        if re.search(r"\b(solve|calculate|find the|formula|proof|prove)\b", clean):
            return "worked_solution"
        if re.search(r"\b(story|tell me a story|narrate)\b", clean):
            return "story"
        if re.search(r"\b(quiz|test my knowledge|ask me a question)\b", clean):
            return "quiz"
        if re.search(r"\b(summarise|summarize|recap|summary)\b", clean):
            return "recap"
        if re.search(r"\b(define|meaning of|what is)\b", clean):
            return "definition"
        return "explanation"

    def _generate_suggested_actions(
        self,
        subject_id: str,
        chat_scope: str,
        chapter_id: Optional[str],
        persona_id: str,
        format_type: str,
        suspended_moment_id: Optional[str] = None,
    ) -> list[SuggestedAction]:
        actions: list[SuggestedAction] = []

        # If previous learning stage was interrupted, offer resume as #1 action
        if suspended_moment_id:
            actions.append(
                SuggestedAction(
                    action_id=f"act_resume_{suspended_moment_id}",
                    action_type="resume_lesson",
                    label="Return to previous lesson stage",
                    payload={"moment_id": suspended_moment_id},
                )
            )

        if subject_id == "history":
            actions.extend([
                SuggestedAction(
                    action_id=f"act_hist_{uuid.uuid4().hex[:6]}",
                    action_type="explore_topic",
                    label="Explore the next historical event",
                    payload={},
                ),
                SuggestedAction(
                    action_id=f"act_quiz_{uuid.uuid4().hex[:6]}",
                    action_type="quiz",
                    label="Test your knowledge with a quiz",
                    payload={"chapter_id": chapter_id},
                ),
            ])
        elif subject_id == "mathematics":
            actions.extend([
                SuggestedAction(
                    action_id=f"act_math_{uuid.uuid4().hex[:6]}",
                    action_type="explore_topic",
                    label="Try a similar worked problem",
                    payload={},
                ),
                SuggestedAction(
                    action_id=f"act_quiz_{uuid.uuid4().hex[:6]}",
                    action_type="quiz",
                    label="Check understanding with a quick check",
                    payload={"chapter_id": chapter_id},
                ),
            ])
        else:  # EVS
            actions.extend([
                SuggestedAction(
                    action_id=f"act_evs_{uuid.uuid4().hex[:6]}",
                    action_type="explore_topic",
                    label="Examine the scientific evidence",
                    payload={},
                ),
                SuggestedAction(
                    action_id=f"act_quiz_{uuid.uuid4().hex[:6]}",
                    action_type="quiz",
                    label="Take a chapter knowledge check",
                    payload={"chapter_id": chapter_id},
                ),
            ])

        actions.append(
            SuggestedAction(
                action_id=f"act_custom_{uuid.uuid4().hex[:6]}",
                action_type="custom_question",
                label="Ask a custom question",
                payload={},
            )
        )
        return actions[:4]

    def _build_error_response(
        self,
        conv: dict,
        persona: Optional[dict],
        message: str,
    ) -> TutoringResponse:
        persona_name = persona["display_name"] if persona else "VidyaVerse Tutor"
        persona_avatar = persona.get("avatar_path", "/avatars/default.svg") if persona else "/avatars/default.svg"
        return TutoringResponse(
            conversation_id=conv["conversation_id"],
            persona_id=conv["persona_id"],
            persona_name=persona_name,
            persona_avatar=persona_avatar,
            subject_id=conv["subject_id"],
            chat_scope=conv["chat_scope"],
            chapter_id=conv["chapter_id"],
            intent="error",
            response_mode="insufficient_evidence",
            format_type="explanation",
            answer=message,
            citations=[],
            suggested_actions=[],
            glossary_chips=[],
            progress={},
            learning_state=conv["learning_state"] or {},
        )


_tutoring_service: Optional[TutoringService] = None


def get_tutoring_service() -> TutoringService:
    global _tutoring_service
    if _tutoring_service is None:
        _tutoring_service = TutoringService()
    return _tutoring_service
