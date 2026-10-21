"""
Pydantic request and response schemas for the chatbot API.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Subject / Chapter catalog schemas ─────────────────────────────────────────


class ChapterSchema(BaseModel):
    chapter_id: str
    chapter_number: int
    title: str
    subject_id: str
    available: bool          # PDF is present
    indexed: bool            # PDF has been embedded in ChromaDB
    pdf_filename: Optional[str] = None
    slug: Optional[str] = None
    source_pdf: Optional[str] = None
    source_pdf_page_start_1based: Optional[int] = None
    source_pdf_page_end_1based: Optional[int] = None
    printed_book_page_start: Optional[int] = None
    printed_book_page_end: Optional[int] = None
    chapter_pdf_page_count: Optional[int] = None
    validation_status: Optional[str] = None


class SubjectSchema(BaseModel):
    subject_id: str
    name: str
    icon: str                # emoji used by the frontend
    color: str               # visual theme key, e.g. "amber", "navy", "emerald"
    available: bool          # has real PDFs
    textbook_title: Optional[str] = None
    textbook_part: Optional[str] = None
    standard: Optional[int] = None
    cover_image: Optional[str] = None
    description: Optional[str] = None
    complete_pdf: Optional[str] = None
    source_page_count: Optional[int] = None
    chapters: list[ChapterSchema] = []
    demo_chapters: list[ChapterSchema] = []   # static demo data for unavailable subjects


class PersonaSchema(BaseModel):
    persona_id: str
    name: str
    subject_id: str
    persona_type: str        # "historical_figure" | "scientist" | "mentor_coach"
    card_summary: str
    primary_topics: list[str] = []
    avatar_url: Optional[str] = None



# ── Chat schemas ───────────────────────────────────────────────────────────────


class HistoryMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    chapter_id: str = Field(..., description="Chapter ID like EVS_CH01 or subject chat id")
    message: str = Field(..., min_length=1)
    history: list[HistoryMessage] = Field(default_factory=list)
    mode: str = Field("study", description="'study' or 'general'")
    persona_id: Optional[str] = Field(None, description="Active persona ID, e.g. 'pythagoras', 'charles_darwin'")
    subject_id: Optional[str] = Field(None, description="Subject ID like 'history', 'mathematics', 'evs'")
    response_mode: Optional[str] = Field(None, description="'documented' | 'persona_inspired' | 'imaginative'")
    question_format: Optional[str] = Field(None, description="Format directive: who, what, why, how, when, compare, solve, story, quiz, summarise")


class SourceReference(BaseModel):
    chapter_title: str
    pdf_filename: str
    page_number: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference] = []
    mode: str
    retrieved_count: int = 0
    persona_id: Optional[str] = None
    suggested_choices: list[str] = []


# ── Indexing schemas ───────────────────────────────────────────────────────────


class IndexRequest(BaseModel):
    subject_id: str = "EVS"
    force: bool = False      # if True, re-index even if already indexed


class IndexStatusResponse(BaseModel):
    collection_name: str
    total_chunks: int
    indexed_chapters: list[str]
    status: str


# ── History Experience Schemas ────────────────────────────────────────────────


class HistoryActionRequest(BaseModel):
    session_id: str
    action_type: str = Field("choice", description="'choice' | 'quiz_answer' | 'next_lesson' | 'select_lesson' | 'return_to_lesson'")
    choice_id: Optional[str] = None
    selected_index: Optional[int] = None
    lesson_id: Optional[str] = None


class HistoryAskRequest(BaseModel):
    session_id: str
    question: str = Field(..., min_length=1)

