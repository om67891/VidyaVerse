"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Send,
  Sparkles,
  RotateCcw,
  BookOpen,
  User,
  Bot,
  GraduationCap,
  Layers,
  HelpCircle,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import PersonaSelectionModal from "@/components/personas/PersonaSelectionModal";
import { api } from "@/lib/api";
import type { Subject, Persona } from "@/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  personaName?: string;
}

function SubjectChatContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const subjectId = (params.subjectId as string) || "mathematics";
  const personaIdParam = searchParams.get("persona") || "";

  const [subject, setSubject] = useState<Subject | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [personaModalOpen, setPersonaModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    async function init() {
      try {
        const subData = await api.getSubject(subjectId);
        setSubject(subData);

        const personas = await api.getPersonas(subjectId);
        const chosen =
          personas.find((p) => p.persona_id === personaIdParam) || personas[0] || null;
        setSelectedPersona(chosen);

        const guideName = chosen?.name || `${subData.name} AI Tutor`;
        const initialMsg: ChatMessage = {
          id: "welcome",
          role: "assistant",
          content: `Welcome to the **${subData.name} Learning Studio**! I am **${guideName}**.\n\nYou can ask me about any chapter, concept, proof, or historical event across the entire **${subData.name}** curriculum. What would you like to explore today?`,
          timestamp: new Date(),
          personaName: guideName,
        };
        setMessages([initialMsg]);
      } catch (err: any) {
        console.error("Failed to initialize subject chat:", err);
        setError("Could not connect to subject service.");
      }
    }
    init();
  }, [subjectId, personaIdParam]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading || !subject) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).slice(2),
      role: "user",
      content: userText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      // Pick first chapter as anchor for model context if needed, or query subject
      const anchorChapterId = subject.chapters[0]?.chapter_id || "evs_chapter_01";
      const historyPayload = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await api.chat({
        chapter_id: anchorChapterId,
        message: userText,
        history: historyPayload,
        mode: "study",
      });

      const assistantMsg: ChatMessage = {
        id: Math.random().toString(36).slice(2),
        role: "assistant",
        content: res.answer,
        timestamp: new Date(),
        personaName: selectedPersona?.name || `${subject.name} AI Tutor`,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Math.random().toString(36).slice(2),
        role: "assistant",
        content: `I encountered an issue retrieving the response: ${err.message}. Please check that the local AI engine is running.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handlePersonaSelected = (newPersonaId: string) => {
    router.push(`/chat/subject/${subjectId}?persona=${newPersonaId}`);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      {/* Scoped Chat Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 shadow-2xs">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a
              href={`/subjects/${subjectId}`}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              <ArrowLeft size={18} />
            </a>

            {/* Persona Avatar */}
            <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 overflow-hidden flex items-center justify-center flex-shrink-0">
              {selectedPersona?.avatar_url ? (
                <img
                  src={selectedPersona.avatar_url}
                  alt={selectedPersona.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = "none";
                  }}
                />
              ) : (
                <span className="text-xl">🎓</span>
              )}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold text-slate-900">
                  {selectedPersona?.name || `${subject?.name || ""} Tutor`}
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  Subject-Wide Chat
                </span>
              </div>
              <p className="text-xs text-slate-500 truncate">
                {subject?.name} · Entire Textbook Curriculum Scope
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPersonaModalOpen(true)}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              Change Guide
            </button>
            <button
              onClick={() => setMessages([])}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title="Reset Chat"
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Message Timeline */}
      <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 space-y-4 overflow-y-auto">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? "justify-end" : "justify-start"}`}
            >
              {!isUser && (
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center flex-shrink-0 text-sm font-bold shadow-2xs mt-1">
                  🎓
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                  isUser
                    ? "bg-blue-600 text-white rounded-tr-xs shadow-xs"
                    : "bg-white text-slate-800 border border-slate-200/90 rounded-tl-xs shadow-2xs space-y-2"
                }`}
              >
                {!isUser && msg.personaName && (
                  <span className="text-[11px] font-bold text-blue-700 block uppercase tracking-wider">
                    {msg.personaName}
                  </span>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
                <div
                  className={`text-[10px] text-right mt-1 ${
                    isUser ? "text-blue-100" : "text-slate-400"
                  }`}
                >
                  {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-lg bg-blue-700 text-white flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-2xs mt-1">
                  <User size={14} />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center flex-shrink-0">
              🎓
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-3 text-xs text-slate-500 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
              <span>Consulting textbook knowledge...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Composer Input Bar */}
      <div className="bg-white border-t border-slate-200 p-4 sticky bottom-0">
        <div className="max-w-4xl mx-auto flex items-end gap-2">
          <div className="flex-1 bg-slate-100 rounded-2xl border border-slate-300 focus-within:border-blue-500 focus-within:bg-white transition-all px-4 py-2">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputMessage}
              onChange={(e) => {
                setInputMessage(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
              }}
              onKeyDown={handleKeyDown}
              placeholder={`Ask ${selectedPersona?.name || "your guide"} anything about ${subject?.name || "this subject"}...`}
              className="w-full bg-transparent resize-none outline-none text-sm text-slate-800 placeholder-slate-400 max-h-32"
            />
          </div>

          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || loading}
            className="p-3 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white shadow-xs transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* Persona Selection Modal */}
      {subject && (
        <PersonaSelectionModal
          isOpen={personaModalOpen}
          onClose={() => setPersonaModalOpen(false)}
          subjectId={subject.subject_id}
          subjectName={subject.name}
          onSelectPersona={handlePersonaSelected}
        />
      )}
    </div>
  );
}

export default function SubjectChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading learning session...</div>}>
      <SubjectChatContent />
    </Suspense>
  );
}
