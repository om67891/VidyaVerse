"""
RAG (Retrieval-Augmented Generation) service for Class 5 Learning Hub.

Handles:
  - Chapter-isolated retrieval from ChromaDB (strict `where={"chapter_id": ...}` filter)
  - Generic chapter overview & reference strategy (main topics, summary, importance, key concepts)
  - 4-way intent routing: general_chat, chapter_question, general_knowledge, chapter_plus_general
  - Robust follow-up resolution & anti-poisoning history handling
  - Structured chat with Ollama (`/api/chat` with thinking suppression and output cleaning)
  - Verified source citation filtering (zero fabricated citations, honest textbook coverage)
"""
from __future__ import annotations

import re
from typing import Optional

import requests

from backend.config import settings
from backend.schemas import ChatRequest, ChatResponse, HistoryMessage, SourceReference
from backend.services.indexing import get_embedding_model, get_chroma_collection


# ── Retrieval ──────────────────────────────────────────────────────────────────


def embed_query(text: str) -> list[float]:
    """Embed a query string with the query: E5 prefix."""
    model = get_embedding_model()
    vector = model.encode(f"query: {text}", normalize_embeddings=True)
    return vector.tolist()


def _normalize_chroma_chapter_id(chapter_id: str) -> str:
    clean = chapter_id.strip()
    if clean.lower().startswith("evs_chapter_"):
        try:
            num = int(clean.split("_")[-1])
            return f"EVS_CH{num:02d}"
        except ValueError:
            pass
    return clean.upper()


def retrieve_passages(
    chapter_id: str,
    query: str,
    top_k: Optional[int] = None,
    subject_id: Optional[str] = None,
) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for the given query,
    strictly filtered to the specified chapter_id.

    Returns list of dicts: {text, chapter_name, source, page_number, distance}
    """
    top_k = top_k or settings.rag_top_k
    clean = (chapter_id or "").strip().lower()

    # Determine subject
    sub = (subject_id or "").strip().lower()
    if not sub:
        if clean.startswith("hist"):
            sub = "history"
        elif clean.startswith("math"):
            sub = "mathematics"
        else:
            sub = "evs"

    is_upload = clean.startswith("upload_")
    if is_upload or sub in ("history", "mathematics"):
        try:
            from backend.services.retrieval_service import get_retrieval_service
            rs = get_retrieval_service()
            res = rs.retrieve(
                subject_id=sub,
                query=query,
                chat_scope="chapter",
                chapter_id=chapter_id,
                top_k=top_k,
            )
            if res.status == "ok" and res.evidences:
                return [
                    {
                        "text": ev.content,
                        "chapter_name": ev.chapter_title,
                        "source": ev.source_document,
                        "page_number": ev.book_page if ev.book_page > 0 else ev.pdf_page,
                        "distance": ev.distance,
                    }
                    for ev in res.evidences
                ]
        except Exception as e:
            print(f"RetrievalService fallback warning: {e}")

    collection = get_chroma_collection()

    if collection.count() == 0:
        return []

    query_vector = embed_query(query)
    target_id = _normalize_chroma_chapter_id(chapter_id)

    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where={"chapter_id": target_id},
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"ChromaDB query error: {e}")
        return []

    passages = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        if doc and dist <= settings.rag_similarity_threshold:
            passages.append({
                "text": doc,
                "chapter_name": meta.get("chapter_name", ""),
                "source": meta.get("source", ""),
                "page_number": meta.get("page_number", 0),
                "distance": dist,
            })

    return passages


def retrieve_chapter_overview(chapter_id: str, chapter_title: str) -> list[dict]:
    """
    Generic chapter-overview retrieval strategy:
    Combines opening section chunks (headings, outlines, introductory definitions)
    with top semantic chunks for the chapter's main concepts.
    Strictly isolated to chapter_id.
    """
    collection = get_chroma_collection()
    if collection.count() == 0:
        return []

    target_id = _normalize_chroma_chapter_id(chapter_id)

    # 1. Fetch opening chunks of the chapter by ordering chunk IDs
    try:
        res = collection.get(
            where={"chapter_id": target_id},
            include=["documents", "metadatas"],
        )
    except Exception as e:
        print(f"ChromaDB get error: {e}")
        return []

    ids = res.get("ids", [])
    docs = res.get("documents", [])
    metas = res.get("metadatas", [])

    if not ids:
        return []

    # Sort chunks by id (e.g. EVS_CH09_chunk_0000, 0001 ...)
    sorted_chunks = sorted(zip(ids, docs, metas), key=lambda x: x[0])
    opening_passages: list[dict] = []
    seen_texts: set[str] = set()

    for _, doc, meta in sorted_chunks[:2]:
        if doc:
            snippet = doc[:60]
            seen_texts.add(snippet)
            opening_passages.append({
                "text": doc,
                "chapter_name": meta.get("chapter_name", chapter_title),
                "source": meta.get("source", ""),
                "page_number": meta.get("page_number", 1),
                "distance": 0.15,
            })

    # 2. Semantic query for key topics and summary
    overview_query = f"{chapter_title} overview main topics key concepts summary"
    query_vector = embed_query(overview_query)

    try:
        sem_res = collection.query(
            query_embeddings=[query_vector],
            n_results=4,
            where={"chapter_id": target_id},
            include=["documents", "metadatas", "distances"],
        )
        sem_docs = sem_res.get("documents", [[]])[0]
        sem_metas = sem_res.get("metadatas", [[]])[0]
        sem_dists = sem_res.get("distances", [[]])[0]

        for doc, meta, dist in zip(sem_docs, sem_metas, sem_dists):
            if doc and doc[:60] not in seen_texts:
                seen_texts.add(doc[:60])
                opening_passages.append({
                    "text": doc,
                    "chapter_name": meta.get("chapter_name", chapter_title),
                    "source": meta.get("source", ""),
                    "page_number": meta.get("page_number", 1),
                    "distance": dist,
                })
    except Exception as e:
        print(f"ChromaDB overview query error: {e}")

    return opening_passages


# ── Intent & Follow-up Patterns ────────────────────────────────────────────────

_GENERAL_CHAT_PATTERNS = [
    re.compile(r"^\s*(hi+|he+y+|hello+|howdy|hola|greetings|good\s+(morning|afternoon|evening|night|day))\b", re.IGNORECASE),
    re.compile(r"\b(how are you|how('s| is) it going|what('s| is) up|who are you|what('s| is) your name|what can you do|are you (an AI|a bot|real|human)|tell me about yourself|nice to meet you)\b", re.IGNORECASE),
    re.compile(r"\b(tell me a joke|make me laugh|tell a joke|say something funny|tell me a riddle|sing a song|do you like jokes|joke please)\b", re.IGNORECASE),
    re.compile(r"^\s*(thanks|thank you|thank you so much|thx|bye|goodbye|see you|see ya|cya|ok|okay|cool|nice|great|awesome|got it|understood|haha|hahaha|lol|rofl)\W*$", re.IGNORECASE),
]

_CHAPTER_OVERVIEW_PATTERNS = re.compile(
    r"\b("
    r"(summary|summarize|summarise|overview)\s+(of\s+)?(this\s+)?chapter|"
    r"give\s+me\s+a\s+summary|"
    r"what\s+is\s+this\s+chapter\s+about|"
    r"what\s+are\s+the\s+(\w+\s+)?(main|key)\s+(topics|concepts|points|lessons|things)\s+(taught|discussed|covered|in|here)|"
    r"why\s+is\s+(the\s+topic\s+of\s+)?this\s+chapter\s+important|"
    r"key\s+concepts\s+discussed\s+here|"
    r"what\s+do\s+we\s+learn\s+in\s+this\s+chapter"
    r")\b",
    re.IGNORECASE,
)

_COVERAGE_CHECK_PATTERNS = re.compile(
    r"\b("
    r"what\s+does\s+(this|the)\s+chapter\s+say\s+about|"
    r"what\s+does\s+(this|the)\s+chapter\s+tell\s+us\s+about|"
    r"does\s+(this|the)\s+chapter\s+(mention|say|talk\s+about|discuss|cover)|"
    r"is\s+there\s+any\s+mention\s+of|"
    r"which\s+[a-z\s]+\s+are\s+mentioned\s+in\s+(this|the)\s+chapter|"
    r"who\s+are\s+the\s+[a-z\s]+\s+mentioned\s+in\s+(this|the)\s+chapter|"
    r"are\s+there\s+any\s+[a-z\s]+\s+in\s+(this|the)\s+chapter"
    r")\b",
    re.IGNORECASE,
)

_ROLEPLAY_PATTERNS = re.compile(
    r"\b(act like|roleplay as|pretend to be|respond as|speak like|speak as|teach like|as if you were)\b",
    re.IGNORECASE,
)

_HYBRID_COMPARISON_PATTERNS = re.compile(
    r"\b(difference between|differ from|compare|comparison|versus|\bvs\b|how does .+ relate to|"
    r"connection between|in real life|today's world|modern day|applied to|in everyday life)\b",
    re.IGNORECASE,
)

_PERSONA_BIO_PATTERNS = re.compile(
    r"\b("
    r"your\s+(family|father|mother|parents|wife|wives|children|sons?|daughters?|brother|ancestors?|childhood|birthplace|fort|birth)|"
    r"tell\s+me\s+about\s+(yourself|your\s+family|your\s+parents|your\s+life|your\s+childhood)|"
    r"who\s+(are\s+you|were\s+your\s+parents|is\s+your\s+father|is\s+your\s+mother|was\s+your\s+father|was\s+your\s+mother)|"
    r"what\s+is\s+your\s+father'?s?\s+name|what\s+is\s+your\s+mother'?s?\s+name|"
    r"family\s+with\s+names"
    r")\b",
    re.IGNORECASE,
)


def is_persona_autobiographical_query(message: str) -> bool:
    """Check if query asks about persona's identity, family, background, or childhood."""
    return bool(_PERSONA_BIO_PATTERNS.search(message.strip()))

_FOLLOWUP_FORMAT_BULLETS = re.compile(
    r"\b(bullet\s*points?|in\s*points?|at\s*least\s*\d+|give\s*me\s*\d+\s*points?|\d+\s*points)\b",
    re.IGNORECASE,
)
_FOLLOWUP_FORMAT_DETAIL = re.compile(
    r"\b(detailed\s*answer|in\s*detail|explain\s*in\s*detail|elaborate|give\s*a\s*detailed|more\s*details?|expand\s*on\s*this)\b",
    re.IGNORECASE,
)
_FOLLOWUP_FORMAT_SIMPLIFY = re.compile(
    r"\b(make\s*it\s*shorter|shorter|simplify|explain\s*more\s*simply|in\s*simple\s*words|simple\s*explanation|explain\s*like\s*a\s*5\s*year\s*old)\b",
    re.IGNORECASE,
)
_FOLLOWUP_FORMAT_ADD_MORE = re.compile(
    r"^\s*(add\s*more|give\s*more|tell\s*more|more\s*names|who\s*else|what\s*else|continue\s*the\s*list|more\s*examples?|more\s*please)\W*$",
    re.IGNORECASE,
)
_FOLLOWUP_FORMAT_ORDINAL = re.compile(
    r"\b(the\s*(first|second|third|fourth|fifth|last|next)|(first|second|third|fourth|fifth|last|next)\s*one|explain\s*the\s*(first|second|third|fourth|fifth|last))\b",
    re.IGNORECASE,
)
_FOLLOWUP_FORMAT_EXAMPLE = re.compile(
    r"\b(example\s*of\s*that|give\s*me\s*an\s*example|give\s*an\s*example|another\s*example|can\s*you\s*give\s*an\s*example|teach\s*me\s*with\s*an\s*example)\b",
    re.IGNORECASE,
)
_FOLLOWUP_ANAPHORA = re.compile(
    r"\b(that|this|it|they|them|these|those|explain\s*that|why\s*is\s*that|what\s*about\s*that|why\s*so|how\s*so)\b",
    re.IGNORECASE,
)

_STOPWORDS = {
    "what", "is", "was", "are", "were", "and", "the", "of", "in", "to", "a", "an", "for", "from", "with",
    "chapter", "tell", "about", "me", "does", "did", "say", "how", "why", "there", "any", "which", "who", "our",
    "been", "have", "has", "had", "this", "that", "these", "those", "some", "many", "much", "their", "they", "will", "would"
}


def extract_chapter_keywords(chapter_title: str) -> set[str]:
    """Extract key substantive words from a chapter title."""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", chapter_title.lower())
    return {w for w in words if w not in _STOPWORDS}


def is_conversational_chat(message: str) -> bool:
    """Check if the user is making casual small talk, greeting, or asking for a joke."""
    clean = message.strip()
    for pat in _GENERAL_CHAT_PATTERNS:
        if pat.search(clean):
            # Guard against combined educational questions e.g. "Hi, what is history?"
            if not re.search(r"\b(what|why|how|explain|describe|who|where|when)\b", clean, re.IGNORECASE):
                return True
            if len(clean.split()) <= 4:
                return True
    return False


def is_chapter_overview_query(message: str) -> bool:
    """Check if query requests a broad chapter overview, summary, main topics, or importance."""
    return bool(_CHAPTER_OVERVIEW_PATTERNS.search(message.strip()))


def extract_coverage_subject(message: str) -> str:
    """Extract the specific topic or entity being queried for chapter coverage."""
    clean = message.strip()
    m1 = re.search(r"\bwhat\s+does\s+(?:this|the)\s+chapter\s+(?:say|tell\s+us)\s+about\s+(.+?)(?:\?|$)", clean, re.IGNORECASE)
    if m1:
        return m1.group(1).strip()
    m2 = re.search(r"\bdoes\s+(?:this|the)\s+chapter\s+(?:mention|say|talk\s+about|discuss|cover)\s+(.+?)(?:\?|$)", clean, re.IGNORECASE)
    if m2:
        return m2.group(1).strip()
    m3 = re.search(r"\b(?:which|who|are there any)\s+([a-zA-Z\s]+?)\s+(?:are\s+)?(?:mentioned|in\s+(?:this|the)\s+chapter)", clean, re.IGNORECASE)
    if m3:
        return m3.group(1).strip()
    return clean


def classify_followup(message: str, history: list[HistoryMessage]) -> tuple[bool, str]:
    """
    Determine if message is a follow-up and what type:
    Returns (is_followup: bool, followup_type: str).
    Types: 'bullet_points', 'detail', 'simplify', 'add_more', 'ordinal', 'example', 'anaphora', 'general', ''
    """
    if not history:
        return False, ""

    clean = message.strip().lower()

    # Guard: If message explicitly refers to "this chapter" or is a chapter overview,
    # it is an explicit chapter question, NOT an anaphoric follow-up to the previous turn!
    if re.search(r"\b(this|the|our)\s+chapter\b|\btopic\s+of\s+this\s+chapter\b", clean):
        return False, ""

    if _FOLLOWUP_FORMAT_ADD_MORE.search(clean):
        return True, "add_more"
    if _FOLLOWUP_FORMAT_BULLETS.search(clean):
        return True, "bullet_points"
    if _FOLLOWUP_FORMAT_DETAIL.search(clean):
        return True, "detail"
    if _FOLLOWUP_FORMAT_SIMPLIFY.search(clean):
        return True, "simplify"
    if _FOLLOWUP_FORMAT_ORDINAL.search(clean):
        return True, "ordinal"
    if _FOLLOWUP_FORMAT_EXAMPLE.search(clean):
        return True, "example"
    if _FOLLOWUP_ANAPHORA.search(clean):
        return True, "anaphora"

    # Short query starting with question word or conjunction
    words = clean.split()
    if len(words) <= 5 and words[0] in ("why", "how", "what", "and", "give", "can", "explain", "tell", "more"):
        return True, "general"

    return False, ""


def is_followup(message: str, history: list[HistoryMessage]) -> bool:
    """Convenience boolean check for follow-up detection."""
    is_f, _ = classify_followup(message, history)
    return is_f


def get_last_meaningful_turn(history: list[HistoryMessage]) -> tuple[str, str]:
    """Return the last substantive user query and assistant response from history."""
    last_user = ""
    last_assistant = ""
    for m in reversed(history):
        if m.role == "user" and not last_user:
            if not is_conversational_chat(m.content):
                last_user = m.content
        elif m.role == "assistant" and not last_assistant:
            last_assistant = m.content
        if last_user and last_assistant:
            break

    if not last_user:
        last_user = next((m.content for m in reversed(history) if m.role == "user"), "")
    if not last_assistant:
        last_assistant = next((m.content for m in reversed(history) if m.role == "assistant"), "")

    return last_user, last_assistant


def extract_list_names(text: str) -> list[str]:
    """Extract list item names or titles from a previous assistant response."""
    names: list[str] = []
    for line in text.split("\n"):
        m = re.match(r"^\s*\d+\.\s*(?:\*\*)?([^*:\n–\-]+?)(?:\*\*)?\s*[-–:]", line)
        if m:
            val = m.group(1).strip()
            if len(val) > 2:
                names.append(val)
    return names


def resolve_contextual_query(
    message: str,
    history: list[HistoryMessage],
    chapter_title: str = "",
) -> str:
    """
    Create a standalone retrieval query for vector search by combining
    the substantive topic with the student's latest instruction.
    Does NOT replace the student's prompt for generation.
    """
    if is_chapter_overview_query(message):
        return f"{chapter_title} overview main topics key concepts summary".strip()

    is_f, f_type = classify_followup(message, history)
    if not is_f:
        return message

    last_user, last_assistant = get_last_meaningful_turn(history)

    if f_type == "bullet_points":
        return f"{last_user} definition main points features scientific method sources".strip()

    if f_type == "ordinal":
        if last_assistant:
            items = re.findall(r"(?:\d+\.|\*|-)\s*([^\n\.\,]+)", last_assistant)
            ordinal_map = {
                "first": 0, "second": 1, "third": 2, "fourth": 3,
                "1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "last": -1
            }
            matched_idx = None
            msg_lower = message.lower()
            for word, idx in ordinal_map.items():
                if word in msg_lower:
                    matched_idx = idx
                    break
            if matched_idx is not None and 0 <= matched_idx < len(items):
                selected_item = items[matched_idx].strip()
                return f"{last_user}. {selected_item} explanation examples".strip()
            summary_snippet = " ".join(last_assistant.split()[:35])
            return f"{last_user}. {summary_snippet}. {message}".strip()

    if f_type == "example":
        return f"{last_user} concrete examples real life illustrations past events".strip()

    if f_type == "detail":
        return f"{last_user} detailed explanation facts mechanisms in detail".strip()

    if f_type == "add_more":
        return f"{last_user} additional examples more names continue".strip()

    if last_user:
        return f"{last_user} {message}".strip()

    return message


# ── Intent Routing ─────────────────────────────────────────────────────────────


def route_intent(
    message: str,
    history: list[HistoryMessage],
    chapter_id: str,
    chapter_title: str,
    requested_mode: str = "study",
) -> tuple[str, list[dict], str, dict]:
    """
    Intelligently route the message into one of four categories:
      - 'general_chat'         : greetings, jokes, small talk (no RAG)
      - 'chapter_question'     : questions grounded in the selected chapter
      - 'general_knowledge'    : questions outside the selected chapter (no forced RAG)
      - 'chapter_plus_general' : questions linking the chapter with general knowledge / comparison

    Returns: (route_name, retrieved_passages, effective_query, flags)
    """
    flags: dict = {}

    if requested_mode == "general":
        return "general_chat", [], message, flags

    # 1. Normal conversational chat (greetings, jokes, pleasantries)
    if is_conversational_chat(message):
        return "general_chat", [], message, flags

    # 2. Generic Chapter overview / summary / importance / main topics
    if is_chapter_overview_query(message):
        passages = retrieve_chapter_overview(chapter_id, chapter_title)
        flags["is_summary"] = True
        return "chapter_question", passages, message, flags

    # 3. Roleplay requests: distinguish chapter roleplay vs external persona
    if _ROLEPLAY_PATTERNS.search(message):
        mentions_chapter = bool(re.search(r"\b(this|the|our)\s+chapter\b|\btopic\s+of\s+this\s+chapter\b", message, re.IGNORECASE))
        ch_kw = extract_chapter_keywords(chapter_title)
        msg_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", message.lower()))
        is_chapter_roleplay = mentions_chapter or bool(msg_words & ch_kw)

        if is_chapter_roleplay:
            flags["is_chapter_roleplay"] = True
            passages = retrieve_chapter_overview(chapter_id, chapter_title)
            return "chapter_question", passages, message, flags
        else:
            flags["is_roleplay"] = True
            return "general_knowledge", [], message, flags

    # 4. Absence / Coverage check: "What does this chapter say about smartphones?" / "Which social workers are mentioned in this chapter?"
    if _COVERAGE_CHECK_PATTERNS.search(message):
        subject_term = extract_coverage_subject(message)
        probe = retrieve_passages(chapter_id, subject_term, top_k=3)
        best_p_dist = probe[0]["distance"] if probe else 999.0
        subj_words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", subject_term.lower()) if w not in _STOPWORDS]
        found_in_text = any(w in p["text"].lower() for p in probe for w in subj_words) if subj_words else False

        if best_p_dist > 0.35 and not found_in_text:
            flags["not_covered"] = True
            flags["uncovered_subject"] = subject_term
            # Honest absence: route to chapter_question but return EMPTY passages so no citations are created
            return "chapter_question", [], message, flags

    # 5. Follow-up routing check against previous conversation turn
    is_f, f_type = classify_followup(message, history)
    last_user, last_assistant = get_last_meaningful_turn(history) if is_f else ("", "")

    if is_f and last_user:
        last_kw = set(re.findall(r"\b[a-zA-Z]{3,}\b", last_user.lower())) - _STOPWORDS
        ch_kw = extract_chapter_keywords(chapter_title)

        # Probe previous user turn to check if it was general knowledge
        prev_passages = retrieve_passages(chapter_id, last_user, top_k=2)
        prev_dist = prev_passages[0]["distance"] if prev_passages else 999.0

        if prev_dist > 0.32 and not (last_kw & ch_kw):
            flags["followup_type"] = f_type
            flags["previous_topic"] = last_user
            flags["previous_answer"] = last_assistant
            return "general_knowledge", [], message, flags

    # 6. Contextual query expansion for follow-up retrieval
    effective_query = resolve_contextual_query(message, history, chapter_title)

    # 7. Chapter title keyword overlap check
    chapter_kw = extract_chapter_keywords(chapter_title)
    message_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", message.lower()))
    has_chapter_keyword = bool(chapter_kw & message_words)
    is_comparison = bool(_HYBRID_COMPARISON_PATTERNS.search(message))

    # 8. Probe retrieval with strict chapter isolation
    passages = retrieve_passages(chapter_id, effective_query, top_k=settings.rag_top_k)
    best_dist = passages[0]["distance"] if passages else 999.0

    # 9. Hybrid comparison check
    if is_comparison and (has_chapter_keyword or best_dist <= 0.32):
        if best_dist > 0.30:
            passages = retrieve_passages(chapter_id, f"{chapter_title}: {effective_query}", top_k=settings.rag_top_k)
        return "chapter_plus_general", passages, effective_query, flags

    # 10. Outside chapter threshold check
    RELEVANCE_THRESHOLD = 0.32
    if best_dist > RELEVANCE_THRESHOLD and not has_chapter_keyword:
        return "general_knowledge", [], effective_query, flags

    if is_comparison:
        return "chapter_plus_general", passages, effective_query, flags

    # 11. Grounded selected chapter question
    return "chapter_question", passages, effective_query, flags


def detect_question_format(query: str) -> str:
    """Classify user query into format directive per Part 03 specification."""
    clean = query.strip().lower()
    if re.search(r"^\s*(who\s+was|who\s+is|who\s+were|who\s+are|tell\s+me\s+about\s+(sant|chhatrapati|king|queen|scientist|darwin|pythagoras|baji|apollonius|linnaeus|leakey|thomsen))\b", clean):
        return "who"
    if re.search(r"^\s*(why\s+did|why\s+is|why\s+was|why\s+do|why\s+are|what\s+caused|reasons?\s+for)\b", clean):
        return "why"
    if re.search(r"^\s*(how\s+did|how\s+do|how\s+to|how\s+can|steps?\s+to|procedure|method\s+to)\b", clean):
        return "how"
    if re.search(r"^\s*(when\s+did|when\s+was|timeline|which\s+year|dates?\s+of)\b", clean):
        return "when"
    if re.search(r"\b(compare|difference\s+between|distinguish|versus|\bvs\b|similarity\s+and\s+difference)\b", clean):
        return "compare"
    if re.search(r"\b(solve|calculate|find\s+the\s+value|proof|prove\s+that|area\s+of|volume\s+of|hypotenuse|ratio)\b", clean):
        return "solve"
    if re.search(r"\b(tell\s+me\s+a\s+story|narrate|story\s+of|tale\s+of|legend\s+of)\b", clean):
        return "story"
    if re.search(r"\b(quiz\s+me|ask\s+me\s+a\s+question|test\s+my\s+knowledge|give\s+me\s+a\s+quiz)\b", clean):
        return "quiz"
    if re.search(r"\b(summarise|summarize|summary|recap|key\s+takeaways|in\s+short)\b", clean):
        return "summarise"
    if re.search(r"\b(explain\s+simply|in\s+simple\s+words|simple\s+terms|like\s+i'm\s+5|child\s+friendly)\b", clean):
        return "explain_simply"
    if re.search(r"^\s*(what\s+is|what\s+are|what\s+was|define|meaning\s+of)\b", clean):
        return "what"
    return "general_chat"


def generate_suggested_choices(
    persona: Optional[dict],
    chapter_name: str,
    question_format: str,
    mode: str,
) -> list[str]:
    """Generate 3-4 context-aware educational next-step options suited to the persona and lesson scope."""
    if not persona:
        return [
            f"Explain {chapter_name} more simply",
            "Give me a key example",
            "Quiz me on this concept",
            "Ask a custom question",
        ]

    p_id = persona.get("persona_id", "")
    subj = persona.get("subject_id", "").lower()
    topics = persona.get("expertise_topics", [])
    topic_hint = topics[0] if topics else chapter_name

    if subj == "history":
        if p_id == "shivaji_maharaj":
            return [
                "Explain the strategic decision behind this",
                "What was the consequence for Swaraj?",
                "Test my knowledge with a quick question",
                "Ask a custom question",
            ]
        elif "sant" in p_id or p_id == "samarth_ramdas":
            return [
                "What is the deeper message for our daily lives?",
                "How does this connect to the Bhakti movement?",
                "Give me a reflection question",
                "Ask a custom question",
            ]
        elif p_id == "baji_prabhu_deshpande":
            return [
                "Walk through the timeline of Ghodkhind",
                "Why was this defense vital for Shivaji Maharaj?",
                "Quiz me on the Battle of Ghodkhind",
                "Ask a custom question",
            ]
        elif p_id == "moro_trimbak_pingle":
            return [
                "How were ministerial duties divided in Swaraj?",
                "How did revenue administration help the people?",
                "Check my understanding with a question",
                "Ask a custom question",
            ]

    if subj == "mathematics":
        if p_id == "pythagoras":
            return [
                "Show me a step-by-step worked example",
                "How is this proven geometrically?",
                "Give me a right-triangle problem to solve",
                "Ask a custom question",
            ]
        elif p_id == "apollonius":
            return [
                "Show the proof using medians",
                "How do we apply this in a triangle problem?",
                "Check my understanding with a problem",
                "Ask a custom question",
            ]
        else:
            return [
                f"Show a step-by-step worked solution for {topic_hint}",
                "Give me a practice problem to test my skills",
                "Explain the core theorem more simply",
                "Ask a custom question",
            ]

    if subj == "evs":
        if p_id == "charles_darwin":
            return [
                "What evidence supported this observation?",
                "How did natural selection shape this trait?",
                "Quiz me on evolution and adaptation",
                "Ask a custom question",
            ]
        elif p_id == "carl_linnaeus":
            return [
                "How do we classify these organisms into categories?",
                "What are the distinct characteristics used?",
                "Give me an organism to classify",
                "Ask a custom question",
            ]
        elif p_id == "archaeologist":
            return [
                "What physical artifacts were discovered here?",
                "How do archaeologists interpret this evidence?",
                "What remains uncertain about this site?",
                "Ask a custom question",
            ]
        elif p_id == "human_evolution_scientist":
            return [
                "Walk through the timeline of early human species",
                "What do skull fossils tell us about brain size?",
                "Test my knowledge with an evolution quiz",
                "Ask a custom question",
            ]
        else:
            return [
                f"What evidence is available for {topic_hint}?",
                "How was life different during that period?",
                "Quiz me on this concept",
                "Ask a custom question",
            ]

    return [
        f"Explain {topic_hint} in simpler terms",
        "Give me a concrete real-world example",
        "Check my understanding with a question",
        "Ask a custom question",
    ]


# ── Structured Chat Message Building ───────────────────────────────────────────


def build_chat_messages(
    mode: str,
    query: str,
    passages: list[dict],
    history: list[HistoryMessage],
    chapter_name: str,
    flags: dict,
    persona_id: Optional[str] = None,
    subject_name: Optional[str] = None,
    question_format: Optional[str] = None,
    response_mode: Optional[str] = None,
) -> list[dict]:
    """
    Build structured messages for Ollama's /api/chat endpoint.
    Strictly separates system instructions, bounded conversation history, and current request.
    Maintains the original user message as the generation instruction.
    When persona_id is provided, dynamically constructs tailored persona instructions.
    """
    recent_history = history[-4:] if history else []
    history_messages = [
        {"role": m.role, "content": m.content}
        for m in recent_history
    ]

    # Persona dynamic prompt construction
    if persona_id:
        from backend.services.persona_manager import get_persona_manager
        pm = get_persona_manager()
        persona = pm.get_persona(persona_id)
        if persona:
            context_parts = [
                f"[Page {p['page_number']}]\n{p['text']}"
                for p in passages
            ]
            context_str = "\n\n".join(context_parts) if context_parts else ""
            res_mode = response_mode or ("imaginative" if flags.get("is_chapter_roleplay") or flags.get("is_roleplay") else ("documented" if passages else "persona_inspired"))
            system_content = pm.build_system_prompt(
                persona_id=persona_id,
                subject_name=subject_name or persona.get("subject_id", "General"),
                chapter_name=chapter_name,
                context_str=context_str,
                response_mode=res_mode,
                question_format=question_format,
            )
            # Include 1 exemplar if this is the start of the chat (empty history) to ground voice & tone
            exemplar_messages = []
            if not history_messages:
                ex_list = pm.examples.get(persona_id, [])
                if ex_list:
                    exemplar_messages = [
                        {"role": "user", "content": ex_list[0]["user_prompt"]},
                        {"role": "assistant", "content": ex_list[0]["example_response"]},
                    ]
            # Anchor generation to eliminate Ollama Qwen3 thinking latency and keep persona strictly in character
            p_display = persona.get("display_name", persona_id)
            if is_persona_autobiographical_query(query):
                if persona_id == "shivaji_maharaj" and re.search(r"\b(family|father|mother|parents|wives|sons?)\b", query, re.IGNORECASE):
                    anchor = f"Greetings! I am {p_display}. Regarding my family, my father is "
                else:
                    anchor = f"Greetings! I am {p_display}. "
            elif not history_messages:
                anchor = f"Greetings! I am {p_display}. "
            else:
                anchor = f"As {p_display}, "

            return [
                {"role": "system", "content": system_content},
                *exemplar_messages,
                *history_messages,
                {"role": "user", "content": query},
                {"role": "assistant", "content": anchor},
            ]

    # --- Mode: general_chat ---
    if mode == "general_chat":
        system_content = (
            "You are a friendly, encouraging, and cheerful AI tutor chatting with a Class 5 student (around 10 years old).\n"
            "You are having a casual conversation. Be natural, warm, and conversational like ChatGPT.\n"
            "Do NOT force textbook citations or talk about lessons unless the student specifically asks.\n"
            "If the student says hi, greet them warmly.\n"
            "If the student asks for a joke, tell a fun, clean, kid-friendly joke.\n"
            "Keep answers concise (1-3 sentences) and engaging.\n"
            "Do NOT prepend 'Student:' or 'Tutor:'. Do NOT add generic closing lines."
        )
        return [
            {"role": "system", "content": system_content},
            *history_messages,
            {"role": "user", "content": query},
        ]

    # --- Mode: general_knowledge ---
    if mode == "general_knowledge":
        # External persona roleplay
        if flags.get("is_roleplay"):
            system_content = (
                "You are an educational AI tutor for Class 5 students.\n"
                "The student has asked you to engage in an educational roleplay.\n\n"
                "ROLEPLAY INSTRUCTIONS:\n"
                "- Respond warmly in the first person, embodying the requested historical or scientific persona.\n"
                "- Present the persona educationally, respectfully, and accurately for a 10-year-old child.\n"
                "- Do NOT present invented dialogue as authentic historical quotations.\n"
                "- Do NOT prepend 'Student:' or 'Tutor:'. Do NOT append generic closing questions."
            )
            return [
                {"role": "system", "content": system_content},
                *history_messages,
                {"role": "user", "content": query},
            ]

        # Follow-up: Add more to a list (generic non-duplication across all categories)
        if flags.get("followup_type") == "add_more":
            prev_ans = flags.get("previous_answer", "")
            already_mentioned = extract_list_names(prev_ans)
            already_str = ", ".join(already_mentioned) if already_mentioned else "the previously mentioned items"
            system_content = (
                "You are a knowledgeable, factually precise educational tutor for Class 5 students.\n"
                "The student has asked to add more entries to the previous list.\n\n"
                "RULES FOR CONTINUING THE LIST:\n"
                f"- Do NOT repeat any of the previously mentioned items: {already_str}.\n"
                "- Provide brand-new, factually verified entries strictly belonging to the exact same category, time period, and geographic region as the previous list.\n"
                "- Verify historical, geographical, and scientific accuracy. Never include items from unrelated categories, wrong eras, or incorrect locations.\n"
                "- Number each new item clearly on its own line.\n"
                "- Do NOT prepend 'Student:' or 'Tutor:'. Do NOT append generic closing lines."
            )
            return [
                {"role": "system", "content": system_content},
                *history_messages,
                {"role": "user", "content": f"Continue the list by adding more entries. Do not repeat any of: {already_str}."},
            ]

        # Follow-up: Detailed expansion
        if flags.get("followup_type") == "detail":
            prev_topic = flags.get("previous_topic", "this topic")
            system_content = (
                f"You are a knowledgeable, clear tutor for Class 5 students.\n"
                f"The student wants a detailed, comprehensive explanation of: {prev_topic}.\n\n"
                "INSTRUCTIONS:\n"
                "- Provide a fascinating, well-structured, and detailed explanation for a 10-year-old child.\n"
                "- Do NOT repeat the previous short answer verbatim; expand with clear sections, real-world examples, and fascinating facts.\n"
                "- Prioritize scientific and factual accuracy.\n"
                "- Do NOT prepend 'Student:' or 'Tutor:'. Do NOT append generic closing lines."
            )
            return [
                {"role": "system", "content": system_content},
                *history_messages,
                {"role": "user", "content": f"Give a detailed and comprehensive explanation of {prev_topic} for a Class 5 student."},
            ]

        # Standard General Knowledge with generic factual accuracy
        system_content = (
            "You are a helpful, factually precise educational tutor for Class 5 students (about 10 years old).\n\n"
            "CRITICAL RULES FOR FACTUAL ACCURACY:\n"
            "- Prioritize strict factual correctness above all else. Never invent or misclassify historical figures, geographic locations, scientific concepts, events, or dates.\n"
            "- Strictly adhere to all geographic, temporal, and categorical constraints in the student's question. For example, if asked for rivers, mountains, or cities in a specific country, name only those that genuinely exist in that country; if asked about a specific historical era, include only authentic figures from that era.\n"
            "- Answer directly, clearly, and engagingly in clean, well-formatted Markdown.\n"
            "- Keep answers concise (2 to 4 sentences or a clean numbered list) and age-appropriate.\n"
            "- Do NOT prepend 'Student:' or 'Tutor:'. Do NOT append generic closing lines."
        )
        return [
            {"role": "system", "content": system_content},
            *history_messages,
            {"role": "user", "content": query},
        ]

    # --- Mode: chapter_plus_general ---
    if mode == "chapter_plus_general":
        context_parts = [
            f"[Page {p['page_number']}]\n{p['text']}"
            for p in passages
        ]
        context_str = "\n\n".join(context_parts) if context_parts else "(No specific passages)"

        system_content = (
            f"You are a friendly tutor helping a Class 5 student (about 10 years old) with Environmental Studies.\n"
            f"Current Chapter: {chapter_name}\n\n"
            f"TEXTBOOK CONTEXT (from {chapter_name}):\n{context_str}\n\n"
            "INSTRUCTIONS:\n"
            "- The student's question connects the chapter with general knowledge or asks for a comparison.\n"
            "- Ground the chapter's part strictly in the provided textbook passages.\n"
            "- Supplement with general knowledge to explain the comparison or external concept.\n"
            "- Clearly distinguish between what the textbook says and the additional general knowledge explanation.\n"
            "- Keep the explanation simple, focused, and age-appropriate for a 10-year-old child.\n"
            "- Do NOT prepend 'Student:' or 'Tutor:' or 'According to Passage 1:'. Do NOT append generic closing lines."
        )
        return [
            {"role": "system", "content": system_content},
            *history_messages,
            {"role": "user", "content": query},
        ]

    # --- Mode: chapter_question (honest absence) ---
    if flags.get("not_covered"):
        subject = flags.get("uncovered_subject", "this topic")
        system_content = (
            f"You are a clear and honest educational tutor for Class 5 Environmental Studies.\n"
            f"Current Chapter: {chapter_name}\n\n"
            f"IMPORTANT NOTE: The student is asking what {chapter_name} says about '{subject}'. "
            f"This chapter does NOT mention, discuss, or cover '{subject}'.\n\n"
            "INSTRUCTIONS:\n"
            f"- State clearly, honestly, and directly that {chapter_name} does not discuss or cover '{subject}'.\n"
            f"- Briefly explain what {chapter_name} is actually about based on its title and subject matter.\n"
            "- Do NOT invent names, facts, page numbers, or fake citations.\n"
            "- Do NOT prepend 'Student:' or 'Tutor:'."
        )
        return [
            {"role": "system", "content": system_content},
            *history_messages,
            {"role": "user", "content": f"What does '{chapter_name}' say about {subject}? (Be completely honest if this topic is not discussed in the chapter.)"},
        ]

    # --- Mode: chapter_question (chapter roleplay) ---
    context_parts = [
        f"[Page {p['page_number']}]\n{p['text']}"
        for p in passages
    ]
    context_str = "\n\n".join(context_parts) if context_parts else "(No passages available)"

    if flags.get("is_chapter_roleplay"):
        system_content = (
            f"You are engaging in an educational roleplay for a Class 5 student (about 10 years old).\n"
            f"Current Chapter: {chapter_name}\n\n"
            f"TEXTBOOK CONTEXT (from {chapter_name}):\n{context_str}\n\n"
            "ROLEPLAY INSTRUCTIONS:\n"
            f"- Adopt the requested persona (such as an archaeologist, scientist, or researcher studying {chapter_name}).\n"
            "- Speak warmly, enthusiastically, and in the FIRST PERSON ('I excavate ancient settlements...', 'In my daily research...').\n"
            f"- Ground your daily activities, findings, and tools strictly in the topics and evidence of {chapter_name} (from the textbook context).\n"
            "- Never invent authentic historical quotes or claim invented dialogue is real.\n"
            "- Do NOT reference unrelated topics from previous conversation turns (like smartphones or modern computers) unless the chapter actually covers them.\n"
            "- Keep the tone inspiring, vivid, and suitable for a 10-year-old child.\n"
            "- Do NOT prepend 'Student:' or 'Tutor:'."
        )
        return [
            {"role": "system", "content": system_content},
            *history_messages,
            {"role": "user", "content": query},
        ]

    # --- Mode: chapter_question (standard grounded textbook query) ---
    system_content = (
        f"You are a friendly and clear tutor helping a Class 5 student (about 10 years old) with Environmental Studies.\n"
        f"Current Chapter: {chapter_name}\n\n"
        f"TEXTBOOK CONTEXT (from {chapter_name}):\n{context_str}\n\n"
        "INSTRUCTIONS:\n"
        "- Answer the student's actual question directly, grounded strictly in the provided textbook context.\n"
        "- Explain simply and clearly, suitable for a 10-year-old child.\n"
        "- If the student asks for bullet points or a specific count (e.g. 'at least 10 bullet points'): "
        "provide at least that number of distinct, informative bullet points drawn from the textbook context.\n"
        "- If the student asks for a chapter summary or main topics: provide a well-organized, coherent explanation of the main concepts in the chapter based on the textbook context.\n"
        "- If the student asks for an example: give a concrete, relatable example grounded in the chapter.\n"
        "- If the student asks to arrange events in chronological order: examine the sequence of events described in the textbook context and arrange them strictly in that chronological order.\n"
        "- For follow-up questions, answer directly without re-explaining the entire prior response from scratch.\n"
        "- Do NOT invent facts, dates, quotations, or citations not present in the context.\n"
        "- Do NOT say 'Student:' or 'Tutor:' or 'According to Passage 1:'. Do NOT append generic closing questions."
    )
    return [
        {"role": "system", "content": system_content},
        *history_messages,
        {"role": "user", "content": query},
    ]


# ── Ollama Generation ──────────────────────────────────────────────────────────


def _remove_thinking_tags(text: str) -> str:
    """Remove <think>…</think> blocks that some models produce."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _clean_output_text(text: str) -> str:
    """Strip dialog artifacts, prompt leakage, and accidental catchphrases while preserving Markdown formatting."""
    clean = _remove_thinking_tags(text)

    # Cut off accidental internal scratchpad trail-offs
    clean = re.sub(r"\n\n(Wait|Note|Okay|Let me|In summary).*", "", clean, flags=re.DOTALL | re.IGNORECASE).strip()

    # Remove accidental leading role labels
    clean = re.sub(r"^(Student|Tutor|Assistant|User):\s*", "", clean, flags=re.IGNORECASE).strip()

    # Remove 'According to Passage \d+[:\s]*'
    clean = re.sub(r"According to Passage \d+[:\s]*", "", clean, flags=re.IGNORECASE).strip()

    # Remove repetitive catchphrase
    clean = re.sub(
        r"That's an exciting general knowledge question outside of our [^!\n]+!\s*",
        "",
        clean,
        flags=re.IGNORECASE,
    ).strip()

    # Remove generic closing invitations if present at end
    clean = re.sub(
        r"\n*(Would you like to (practice|learn|ask) [^?\n]+\?|Let me know if you (want|would like) [^!\n]+!)\s*$",
        "",
        clean,
        flags=re.IGNORECASE,
    ).strip()

    return clean


def generate_with_ollama_chat(messages: list[dict], temperature: float = 0.25) -> str:
    """
    Send structured chat messages to Ollama's /api/chat endpoint.
    Strips chain-of-thought thinking blocks and dialog artifacts.
    Enforces num_thread, lean num_ctx, num_predict, and assistant prefill anchor for high-speed local inference.
    """
    url = f"{settings.ollama_base_url}/api/chat"
    models_to_try = [settings.ollama_model]
    if "qwen3:4b" not in models_to_try:
        models_to_try.append("qwen3:4b")
    if "qwen3:0.6b" not in models_to_try:
        models_to_try.append("qwen3:0.6b")

    # If the last message is an assistant prefill anchor, extract it to prepend to generation
    prefix_anchor = ""
    effective_messages = list(messages)
    if effective_messages and effective_messages[-1].get("role") == "assistant":
        prefix_anchor = effective_messages[-1].get("content", "")

    last_error = None
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": effective_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 450,
                "num_thread": 6,
                "num_ctx": 2048,
                "stop": [
                    "\n\nWait",
                    "\n\nNote",
                    "\n\nOkay",
                    "\n\nLet me",
                    "\n\nIn summary",
                    "<|im_end|>",
                    "<|im_start|>",
                ],
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=settings.ollama_timeout)
            if resp.status_code == 404 and model_name != models_to_try[-1]:
                # Model not found, try next candidate
                continue
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("message", {}).get("content", "").strip()
            # Clean any internal reasoning tokens if leaked into content
            if raw:
                raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            if prefix_anchor and raw:
                raw = prefix_anchor + raw
            elif prefix_anchor and not raw:
                raw = prefix_anchor
            if raw:
                return _clean_output_text(raw)
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {settings.ollama_base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Ollama timed out after {settings.ollama_timeout}s. "
                "The model may be loading. Try again in a moment."
            )
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 404 and model_name != models_to_try[-1]:
                continue
            raise RuntimeError(f"Ollama HTTP error: {e}")
        except Exception as e:
            last_error = e

    if last_error:
        raise RuntimeError(f"Ollama error: {last_error}")
    raise RuntimeError("Ollama failed to generate response")


# ── Source Citation Assembly ───────────────────────────────────────────────────


def filter_supporting_sources(
    passages: list[dict],
    mode: str,
    flags: dict,
) -> list[SourceReference]:
    """
    Assemble verified, deduplicated source references.
    Returns empty list for general_chat, general_knowledge, or when topic was not covered.
    Only retains passages with distance <= 0.32 (or validated overview passages) that genuinely support claims.
    """
    if mode in ("general_chat", "general_knowledge") or flags.get("not_covered"):
        return []

    seen: set[tuple] = set()
    sources: list[SourceReference] = []

    cutoff = 0.35 if (flags.get("is_summary") or flags.get("is_chapter_roleplay")) else 0.32

    for p in passages:
        if p.get("distance", 1.0) > cutoff:
            continue

        key = (p["source"], p["page_number"])
        if key not in seen:
            seen.add(key)
            sources.append(
                SourceReference(
                    chapter_title=p["chapter_name"],
                    pdf_filename=p["source"],
                    page_number=p["page_number"],
                )
            )

    return sources


# ── Public Chat Entrypoint ─────────────────────────────────────────────────────


def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Main entry point: route intent, retrieve passages if needed, generate answer with persona support.
    """
    from backend.services.catalog import get_chapter
    from backend.services.persona_manager import get_persona_manager

    clean_chap = request.chapter_id.strip()
    is_subject_chat = clean_chap.lower().endswith("_all") or clean_chap.lower() in ("subject", "all", "history", "mathematics", "evs")

    chapter = None
    if not is_subject_chat:
        chapter = get_chapter(clean_chap)
        if chapter is None:
            chapter = get_chapter(clean_chap.upper())
        if chapter is None:
            raise ValueError(f"Unknown chapter_id: {request.chapter_id}")

    chapter_name = chapter.title if chapter else f"{request.subject_id or clean_chap} Curriculum"
    subject_name = chapter.subject_id if chapter else (request.subject_id or "VidyaVerse")

    # 1. Intelligent intent routing
    if is_subject_chat:
        mode = "general_knowledge" if request.mode != "study" else "chapter_question"
        passages = []
        effective_query = request.message
        flags = {}
    elif request.persona_id and is_persona_autobiographical_query(request.message):
        mode = "chapter_question"
        passages = []
        effective_query = request.message
        flags = {"is_persona_inquiry": True}
    else:
        mode, passages, effective_query, flags = route_intent(
            message=request.message,
            history=request.history,
            chapter_id=chapter.chapter_id,
            chapter_title=chapter_name,
            requested_mode=request.mode,
        )

    # 2. Check indexing if chapter_question
    if chapter and mode in ("chapter_question", "chapter_plus_general") and not chapter.indexed:
        return ChatResponse(
            answer=(
                f"The chapter '{chapter_name}' has not been indexed yet. "
                "Please run the indexing pipeline first: `python -m backend.services.indexing`"
            ),
            sources=[],
            mode=mode,
            retrieved_count=0,
            persona_id=request.persona_id,
            suggested_choices=[],
        )

    # Detect question format
    q_format = request.question_format or detect_question_format(request.message)

    # Resolve persona
    pm = get_persona_manager()
    persona = pm.get_persona(request.persona_id) if request.persona_id else None

    # 3. Build structured chat messages (preserving original message for generation)
    messages = build_chat_messages(
        mode=mode,
        query=request.message,
        passages=passages,
        history=request.history,
        chapter_name=chapter_name,
        flags=flags,
        persona_id=request.persona_id,
        subject_name=subject_name,
        question_format=q_format,
        response_mode=request.response_mode,
    )

    # 4. Generate answer with Ollama
    answer = generate_with_ollama_chat(messages, temperature=0.25)

    # 5. Filter supporting source citations
    sources = filter_supporting_sources(passages, mode, flags)

    # 6. Suggested choices
    suggested_choices = generate_suggested_choices(persona, chapter_name, q_format, mode)

    return ChatResponse(
        answer=answer,
        sources=sources,
        mode=mode,
        retrieved_count=len(passages),
        persona_id=persona.get("persona_id") if persona else request.persona_id,
        suggested_choices=suggested_choices,
    )


def get_diagnostics(
    chapter_id: str,
    query: str,
    history: list[HistoryMessage] | None = None,
) -> dict:
    """
    Development diagnostic function for inspecting internal RAG pipeline states.
    """
    from backend.services.catalog import get_chapter
    from backend.services.indexing import get_chroma_collection

    hist = history or []
    chapter = get_chapter(chapter_id)
    chapter_title = chapter.title if chapter else "Unknown"

    col = get_chroma_collection()
    ch_chunks = col.get(where={"chapter_id": chapter_id}, include=["metadatas"])
    chunk_count = len(ch_chunks.get("ids", []))

    effective_query = resolve_contextual_query(query, hist, chapter_title)
    mode, passages, _, flags = route_intent(query, hist, chapter_id, chapter_title)

    sources = filter_supporting_sources(passages, mode, flags)

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "indexed_chunks_count": chunk_count,
        "input_query": query,
        "effective_query": effective_query,
        "is_followup": is_followup(query, hist),
        "route": mode,
        "flags": flags,
        "chapter_filter_applied": True,
        "retrieved_count": len(passages),
        "passages": [
            {
                "source": p["source"],
                "page_number": p["page_number"],
                "distance": round(p["distance"], 4),
                "text_preview": p["text"][:120].replace("\n", " ") + "...",
            }
            for p in passages
        ],
        "sources": [
            {"pdf": s.pdf_filename, "page": s.page_number}
            for s in sources
        ],
    }
