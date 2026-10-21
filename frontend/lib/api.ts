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
};

