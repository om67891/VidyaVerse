// API client — all calls go through here.
// Backend URL is read from NEXT_PUBLIC_API_URL (defaults to http://localhost:8000)

import type {
  Subject,
  Chapter,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  IndexStatusResponse,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  health(): Promise<HealthResponse> {
    return apiFetch("/api/health");
  },

  getSubjects(): Promise<Subject[]> {
    return apiFetch("/api/subjects");
  },

  getSubject(subjectId: string): Promise<Subject> {
    return apiFetch(`/api/subjects/${subjectId}`);
  },

  getChapters(subjectId: string): Promise<Chapter[]> {
    return apiFetch(`/api/subjects/${subjectId}/chapters`);
  },

  getChapter(chapterId: string): Promise<Chapter> {
    return apiFetch(`/api/chapters/${chapterId}`);
  },

  chat(req: ChatRequest): Promise<ChatResponse> {
    return apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  indexStatus(): Promise<IndexStatusResponse> {
    return apiFetch("/api/index/status");
  },

  getPersonas(subjectId?: string, chapterId?: string): Promise<import("@/types").Persona[]> {
    const params = new URLSearchParams();
    if (subjectId) params.set("subject_id", subjectId);
    if (chapterId) params.set("chapter_id", chapterId);
    const q = params.toString() ? `?${params.toString()}` : "";
    return apiFetch(`/api/personas${q}`);
  },

  // ── History Learning Prototype ─────────────────────────────────────────────

  startHistorySession(sessionId?: string): Promise<import("@/types").HistorySessionState> {
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
    return apiFetch(`/api/history/session/start${query}`);
  },

  historyAction(req: {
    session_id: string;
    action_type: string;
    choice_id?: string;
    selected_index?: number;
    lesson_id?: string;
  }): Promise<import("@/types").HistorySessionState> {
    return apiFetch("/api/history/action", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  historyAsk(req: { session_id: string; question: string }): Promise<import("@/types").HistorySessionState> {
    return apiFetch("/api/history/ask", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  getHistoryMap(): Promise<import("@/types").LessonNode[]> {
    return apiFetch("/api/history/map");
  },

  historyStatus(): Promise<{
    collection_name: string;
    total_chunks: number;
    pdf_path: string;
    pdf_exists: boolean;
    status: string;
  }> {
    return apiFetch("/api/history/status");
  },

  // ── Part 04: Persistent Conversations & Interactive Tutoring ───────────────

  createConversation(req: {
    subject_id: string;
    chat_scope: "subject" | "chapter";
    chapter_id?: string | null;
    persona_id: string;
    title?: string;
  }): Promise<any> {
    return apiFetch("/api/conversations", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  listConversations(params?: {
    subject_id?: string;
    chat_scope?: string;
    chapter_id?: string;
    limit?: number;
  }): Promise<any[]> {
    const q = new URLSearchParams();
    if (params?.subject_id) q.set("subject_id", params.subject_id);
    if (params?.chat_scope) q.set("chat_scope", params.chat_scope);
    if (params?.chapter_id) q.set("chapter_id", params.chapter_id);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString() ? `?${q.toString()}` : "";
    return apiFetch(`/api/conversations${qs}`);
  },

  getConversation(conversationId: string): Promise<any> {
    return apiFetch(`/api/conversations/${encodeURIComponent(conversationId)}`);
  },

  sendMessage(
    conversationId: string,
    req: {
      message: string;
      action_payload?: any;
      response_mode?: string;
      question_format?: string;
    }
  ): Promise<any> {
    return apiFetch(`/api/conversations/${encodeURIComponent(conversationId)}/messages`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  deleteConversation(conversationId: string): Promise<any> {
    return apiFetch(`/api/conversations/${encodeURIComponent(conversationId)}`, {
      method: "DELETE",
    });
  },

  getLearningMap(subjectId: string, chapterId: string): Promise<any> {
    return apiFetch(`/api/learning-map/${encodeURIComponent(subjectId)}/${encodeURIComponent(chapterId)}`);
  },

  getGlossary(subjectId: string, chapterId?: string): Promise<any[]> {
    const q = chapterId ? `?chapter_id=${encodeURIComponent(chapterId)}` : "";
    return apiFetch(`/api/glossary/${encodeURIComponent(subjectId)}${q}`);
  },

  getQuiz(subjectId: string, chapterId: string): Promise<any[]> {
    return apiFetch(`/api/quiz/${encodeURIComponent(subjectId)}/${encodeURIComponent(chapterId)}`);
  },

  validateQuiz(req: { question_id: string; selected_index: number }): Promise<any> {
    return apiFetch("/api/quiz/validate", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  validateMath(req: { operation: string; params: any }): Promise<any> {
    return apiFetch("/api/math/validate", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
};


