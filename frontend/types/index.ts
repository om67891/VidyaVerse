// Shared TypeScript types matching the backend Pydantic schemas

export interface Chapter {
  chapter_id: string;
  chapter_number: number;
  title: string;
  subject_id: string;
  available: boolean;
  indexed: boolean;
  pdf_filename: string | null;
  slug?: string;
  source_pdf?: string;
  source_pdf_page_start_1based?: number;
  source_pdf_page_end_1based?: number;
  printed_book_page_start?: number;
  printed_book_page_end?: number;
  chapter_pdf_page_count?: number;
  validation_status?: string;
}

export interface Subject {
  subject_id: string;
  name: string;
  icon: string;
  color: string;
  available: boolean;
  textbook_title?: string;
  textbook_part?: string;
  standard?: number;
  cover_image?: string;
  description?: string;
  complete_pdf?: string;
  source_page_count?: number;
  chapters: Chapter[];
  demo_chapters: Chapter[];
}

export interface Persona {
  persona_id: string;
  name: string;
  subject_id: string;
  persona_type: string;
  card_summary: string;
  primary_topics: string[];
  avatar_url?: string;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  chapter_id: string;
  message: string;
  history: HistoryMessage[];
  mode?: string;
  persona_id?: string;
  subject_id?: string;
  response_mode?: string;
  question_format?: string;
}

export interface SourceReference {
  chapter_title: string;
  pdf_filename: string;
  page_number: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceReference[];
  mode: string;
  retrieved_count: number;
  persona_id?: string;
  suggested_choices?: string[];
}

export interface HealthResponse {
  status: string;
  ollama_running: boolean;
  model_available: boolean;
  model: string;
  collection: string;
}

export interface IndexStatusResponse {
  collection_name: string;
  total_chunks: number;
  indexed_chapters: string[];
  status: string;
}

// Frontend-only UI message type
export interface UIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
  mode?: string;
  timestamp: Date;
  isError?: boolean;
  persona_id?: string;
  persona_name?: string;
  persona_avatar?: string;
  suggested_choices?: string[];
}

// ── Interactive History Learning Types ───────────────────────────────────────

export interface ChoiceOption {
  id: string;
  label: string;
  type: string;
}

export interface QuizCheck {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface HistorySourceRef {
  source: string;
  pdf_page: number;
  book_page: number;
  lesson_title: string;
  snippet?: string;
}

export interface TimelineEvent {
  step: number;
  title: string;
  description: string;
}

export interface FigureProfile {
  name: string;
  title?: string;
  contribution: string;
  key_teachings?: string[];
  place?: string;
}

export interface ComparisonItem {
  feature: string;
  itemA: string;
  itemB: string;
}

export interface ComparisonData {
  labelA: string;
  labelB: string;
  rows: ComparisonItem[];
}

export interface CauseEffectData {
  cause: string;
  event: string;
  significance: string;
}

export type ResponseFormatType =
  | "story"
  | "explanation"
  | "figure"
  | "timeline"
  | "cause_effect"
  | "comparison"
  | "quiz"
  | "recap"
  | "chat";

export interface HistoryChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  format_type?: ResponseFormatType | string;
  highlights?: string[];
  figure_profile?: FigureProfile | null;
  timeline_events?: TimelineEvent[] | null;
  comparison?: ComparisonData | null;
  cause_effect?: CauseEffectData | null;
  recap_points?: string[] | null;
  persona?: string;
  persona_name?: string;
  persona_avatar?: string;
  persona_role?: string;
  citations?: HistorySourceRef[];
  choices?: ChoiceOption[];
  quiz?: QuizCheck | null;
  quiz_feedback?: string | null;
  quiz_passed?: boolean | null;
  is_custom_answer?: boolean;
  can_resume?: boolean;
  timestamp?: string;
}

export interface HistorySessionState {
  session_id: string;
  current_lesson_id: string;
  lesson_title: string;
  lesson_number: number;
  total_lessons: number;
  completed_lessons: string[];
  current_stage: string; // "INTRO" | "STORY" | "EXPLORE" | "CAUSE" | "QUIZ" | "FEEDBACK" | "CUSTOM_ANSWER"
  persona: string;       // "SHIVAJI"
  persona_name: string;
  persona_avatar: string;
  persona_role: string;
  narration: string;
  choices: ChoiceOption[];
  quiz?: QuizCheck | null;
  quiz_feedback?: string | null;
  quiz_passed: boolean;
  citations: HistorySourceRef[];
  can_resume_lesson: boolean;
  progress_percentage: number;
  messages: HistoryChatMessage[];
}

export interface LessonNode {
  id: string;
  lesson_number: number;
  title: string;
  book_pages: [number, number];
  pdf_pages: [number, number];
  persona: string;
  summary: string;
  major_figures: string[];
  key_places: string[];
  key_concepts: string[];
  starter_choices: ChoiceOption[];
  knowledge_check: QuizCheck;
  next_lesson_id?: string | null;
}

// ── Faculty Upload Types ──────────────────────────────────────────────────────

export interface UploadedResource {
  resource_id: string;
  subject_id: string;
  class_number: number;
  chapter_id: string;
  chapter_number: number;
  chapter_name: string;
  source_type: string;
  original_filename: string;
  file_size_bytes: number;
  processing_status: "uploaded" | "processing" | "indexed" | "failed";
  chunk_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  indexed_at?: string | null;
}

export interface FacultyUploadResponse {
  status: "uploaded" | "processing" | "indexed" | "failed";
  message: string;
  resource: UploadedResource;
}

export interface FacultyReindexResponse {
  status: string;
  message: string;
  resource_id: string;
  chunk_count: number;
}


