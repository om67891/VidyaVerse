// Scoped Chat Storage for VidyaVerse
// Preserves conversations strictly scoped by subject-wide or individual chapter
// Enforces Persona Identity Lock within a conversation

import type { UIMessage } from "@/types";

export interface SavedConversation {
  id: string;
  scopeType: "subject" | "chapter";
  scopeId: string; // e.g. "mathematics" or "EVS_CH01"
  subjectId: string;
  title: string;
  personaId: string;
  personaName: string;
  personaAvatar?: string;
  createdAt: string;
  updatedAt: string;
  messages: UIMessage[];
}

const STORAGE_KEY = "vidyaverse_chat_conversations_v1";

function loadAll(): SavedConversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (e) {
    console.error("Failed to load saved conversations:", e);
    return [];
  }
}

function persistAll(convs: SavedConversation[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
  } catch (e) {
    console.error("Failed to save conversations:", e);
  }
}

export const chatStorage = {
  getScopedConversations(scopeType: "subject" | "chapter", scopeId: string): SavedConversation[] {
    const cleanScope = scopeId.trim().toLowerCase();
    const all = loadAll();
    return all
      .filter((c) => c.scopeType === scopeType && c.scopeId.trim().toLowerCase() === cleanScope)
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
  },

  getConversation(id: string): SavedConversation | null {
    const all = loadAll();
    return all.find((c) => c.id === id) || null;
  },

  saveConversation(conv: SavedConversation): void {
    const all = loadAll();
    const idx = all.findIndex((c) => c.id === conv.id);
    conv.updatedAt = new Date().toISOString();
    if (idx >= 0) {
      all[idx] = conv;
    } else {
      all.unshift(conv);
    }
    persistAll(all);
  },

  createConversation(params: {
    scopeType: "subject" | "chapter";
    scopeId: string;
    subjectId: string;
    personaId: string;
    personaName: string;
    personaAvatar?: string;
    initialTitle?: string;
    initialMessages?: UIMessage[];
  }): SavedConversation {
    const id = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const now = new Date().toISOString();
    const newConv: SavedConversation = {
      id,
      scopeType: params.scopeType,
      scopeId: params.scopeId,
      subjectId: params.subjectId,
      title: params.initialTitle || `Chat with ${params.personaName}`,
      personaId: params.personaId,
      personaName: params.personaName,
      personaAvatar: params.personaAvatar,
      createdAt: now,
      updatedAt: now,
      messages: params.initialMessages || [],
    };
    const all = loadAll();
    all.unshift(newConv);
    persistAll(all);
    return newConv;
  },

  deleteConversation(id: string): void {
    const all = loadAll().filter((c) => c.id !== id);
    persistAll(all);
  },
};
