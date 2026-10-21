"use client";

import {
  useEffect,
  useState,
  useRef,
  useCallback,
  KeyboardEvent,
  Suspense,
} from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Send,
  Plus,
  BookOpen,
  AlertTriangle,
  FileText,
  Bot,
  User,
  Info,
  Sparkles,
  HelpCircle,
  Lightbulb,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Chapter, UIMessage, HistoryMessage, Persona } from "@/types";

function genId(): string {
  return Math.random().toString(36).slice(2, 9);
}

function makeWelcome(chapter: Chapter, persona?: Persona | null): UIMessage {
  const guideName = persona?.name || "your AI tutor";
  return {
    id: "welcome",
    role: "assistant",
    content: `Hi! I'm **${guideName}**, guiding you through **${chapter.title}** (Chapter ${chapter.chapter_number}).\n\nYou can chat with me naturally like ChatGPT! Ask me anything from this chapter, request examples, explore definitions, or ask questions about the lesson.`,
    timestamp: new Date(),
  };
}

function MessageBubble({ msg }: { msg: UIMessage }) {
  const isUser = msg.role === "user";

  // Simple markdown renderer for headings, bold text, lists, and line breaks
  const renderContent = (text: string) => {
    const lines = text.split("\n");
    return lines.map((line, lineIdx) => {
      // Check for markdown headings
      const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
      let content = line;
      let isHeading = false;
      let headingLevel = 0;
      if (headingMatch) {
        isHeading = true;
        headingLevel = headingMatch[1].length;
        content = headingMatch[2];
      }

      // Bold rendering
      const parts = content.split(/(\*\*[^*]+\*\*)/g);
      const renderedParts = parts.map((part, pIdx) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={pIdx} style={{ fontWeight: 700, color: isUser ? "#FFFFFF" : "var(--text-primary)" }}>
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });

      if (isHeading) {
        return (
          <span
            key={lineIdx}
            style={{
              display: "block",
              fontWeight: 700,
              fontSize: headingLevel === 1 ? "1.1rem" : headingLevel === 2 ? "1.0rem" : "0.92rem",
              marginTop: lineIdx > 0 ? "0.5rem" : "0",
              marginBottom: "0.2rem",
              color: isUser ? "#FFFFFF" : "var(--text-primary)",
            }}
          >
            {renderedParts}
          </span>
        );
      }

      return (
        <span key={lineIdx} style={{ display: "block", minHeight: line === "" ? "0.6rem" : "auto" }}>
          {renderedParts}
        </span>
      );
    });
  };

  if (isUser) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "flex-end",
          gap: "0.6rem",
          marginBottom: "1.25rem",
          width: "100%",
        }}
      >
        <div
          style={{
            maxWidth: "75%",
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-end",
            gap: "0.25rem",
          }}
        >
          <div
            className="bubble-user"
            style={{
              minWidth: "fit-content",
              whiteSpace: "pre-wrap",
              wordBreak: "normal",
              overflowWrap: "break-word",
            }}
          >
            {renderContent(msg.content)}
          </div>
          <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", paddingRight: "0.25rem" }}>
            {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            background: "var(--accent)",
            color: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 2px 4px rgba(37,99,235,0.2)",
          }}
        >
          <User size={15} />
        </div>
      </div>
    );
  }

  // Assistant Message
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "0.75rem",
        marginBottom: "1.5rem",
        width: "100%",
      }}
    >
      {/* Bot Avatar */}
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "10px",
          background: "var(--accent-soft)",
          border: "1px solid var(--accent-border)",
          color: "var(--accent)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          boxShadow: "var(--neu-raised-sm)",
          marginTop: "2px",
        }}
      >
        <Bot size={18} />
      </div>

      {/* Content Column */}
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: "0.45rem" }}>
        <div className={`bubble-assistant${msg.isError ? " error-bubble" : ""}`}>
          {msg.isError && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                color: "var(--red)",
                fontWeight: 600,
                fontSize: "0.85rem",
                marginBottom: "0.35rem",
              }}
            >
              <AlertTriangle size={14} />
              Error
            </div>
          )}
          {renderContent(msg.content)}
        </div>

        {/* Verified Textbook Citations */}
        {msg.sources && msg.sources.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginTop: "0.15rem" }}>
            {msg.sources.map((s, i) => (
              <span key={i} className="source-chip">
                <FileText size={11} />
                <span>{s.pdf_filename} · Page {s.page_number}</span>
              </span>
            ))}
          </div>
        )}

        {/* Mode Indicators */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          {msg.mode === "general_knowledge" && (
            <span
              style={{
                fontSize: "0.72rem",
                color: "var(--accent)",
                background: "var(--accent-soft)",
                border: "1px solid var(--accent-border)",
                padding: "0.15rem 0.55rem",
                borderRadius: "9999px",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
                fontWeight: 500,
              }}
            >
              <Info size={11} /> General knowledge
            </span>
          )}
          {msg.mode === "chapter_plus_general" && (
            <span
              style={{
                fontSize: "0.72rem",
                color: "var(--green)",
                background: "var(--green-soft)",
                border: "1px solid var(--green-border)",
                padding: "0.15rem 0.55rem",
                borderRadius: "9999px",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
                fontWeight: 500,
              }}
            >
              <Sparkles size={11} /> Textbook + General knowledge
            </span>
          )}
          <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
            {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div
      style={{
        display: "flex",
        gap: "0.75rem",
        alignItems: "flex-start",
        marginBottom: "1.25rem",
      }}
    >
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "10px",
          background: "var(--accent-soft)",
          border: "1px solid var(--accent-border)",
          color: "var(--accent)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Bot size={18} />
      </div>
      <div className="bubble-assistant" style={{ padding: "0.75rem 1rem" }}>
        <div className="dot-pulse">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}

function ChatContent() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const chapterId = (params.chapterId as string);
  const personaIdParam = searchParams.get("persona") || "";

  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const ch = await api.getChapter(chapterId);
        if (!mounted) return;
        setChapter(ch);

        const personas = await api.getPersonas(ch.subject_id, ch.chapter_id);
        const chosen =
          personas.find((p) => p.persona_id === personaIdParam) || personas[0] || null;
        setSelectedPersona(chosen);
        setMessages([makeWelcome(ch, chosen)]);
      } catch (e: unknown) {
        if (mounted) {
          setPageError(e instanceof Error ? e.message : "Failed to load chapter.");
        }
      } finally {
        if (mounted) setPageLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [chapterId, personaIdParam]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  const sendMessageWithText = useCallback(
    async (textToSend: string) => {
      const text = textToSend.trim();
      if (!text || loading) return;

      const userMsg: UIMessage = {
        id: genId(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      const history: HistoryMessage[] = messages
        .filter((m) => m.id !== "welcome" && !m.isError)
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        const res = await api.chat({
          chapter_id: chapterId,
          message: text,
          history,
          mode: "study",
        });

        const assistantMsg: UIMessage = {
          id: genId(),
          role: "assistant",
          content: res.answer,
          sources: res.sources,
          mode: res.mode,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (e: unknown) {
        const errorMsg: UIMessage = {
          id: genId(),
          role: "assistant",
          content: e instanceof Error ? e.message : "Something went wrong. Please try again.",
          timestamp: new Date(),
          isError: true,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [loading, chapter, chapterId, messages]
  );

  const sendMessage = useCallback(() => {
    sendMessageWithText(input);
  }, [input, sendMessageWithText]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleNewChat = () => {
    if (chapter) setMessages([makeWelcome(chapter)]);
    setInput("");
  };

  const subjectId = chapterId.split("_")[0];

  const suggestedPrompts = [
    `What is ${chapter?.title ?? "this chapter"} about?`,
    "What are the main concepts covered in this chapter?",
    "Give me an interesting example from this lesson",
    "Tell me a fun joke to start learning!",
  ];

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--bg-primary)",
      }}
    >
      {/* ── Top Bar ── */}
      <header
        style={{
          background: "var(--bg-secondary)",
          borderBottom: "1px solid var(--border)",
          padding: "0.75rem 1.75rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
          flexShrink: 0,
          zIndex: 50,
          boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
          <button
            className="btn-ghost"
            onClick={() => router.push(`/subjects/${subjectId}/chapters/${chapterId}`)}
            style={{ padding: "0.4rem 0.75rem", fontSize: "0.82rem" }}
          >
            <ArrowLeft size={14} />
            Overview
          </button>
          <span style={{ color: "var(--border-light)" }}>|</span>
          {chapter && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              {selectedPersona?.avatar_url && (
                <div style={{ width: "28px", height: "28px", borderRadius: "8px", overflow: "hidden", border: "1px solid var(--border)", flexShrink: 0 }}>
                  <img src={selectedPersona.avatar_url} alt={selectedPersona.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                </div>
              )}
              <span
                style={{
                  background: "var(--accent-soft)",
                  border: "1px solid var(--accent-border)",
                  borderRadius: "6px",
                  padding: "0.2rem 0.5rem",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  color: "var(--accent)",
                }}
              >
                Ch. {chapter.chapter_number}
              </span>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <h1
                  style={{
                    fontSize: "0.92rem",
                    fontWeight: 700,
                    color: "var(--text-primary)",
                    margin: 0,
                    maxWidth: "360px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {chapter.title}
                </h1>
                {selectedPersona && (
                  <span style={{ fontSize: "0.68rem", color: "var(--accent)", fontWeight: 600 }}>
                    Guide: {selectedPersona.name}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        <button
          className="btn-ghost"
          onClick={handleNewChat}
          style={{ padding: "0.4rem 0.85rem", fontSize: "0.82rem" }}
          title="Start a new chat"
        >
          <Plus size={14} />
          New chat
        </button>
      </header>

      {/* ── Page Error Banner ── */}
      {pageError && (
        <div
          style={{
            background: "var(--red-soft)",
            borderBottom: "1px solid var(--red-border)",
            padding: "0.75rem 1.75rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            color: "var(--red)",
            fontSize: "0.85rem",
            fontWeight: 500,
            flexShrink: 0,
          }}
        >
          <AlertTriangle size={15} />
          {pageError}
        </div>
      )}

      {/* ── Chat Messages Container (Wide, ChatGPT-style) ── */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "1.75rem 1.5rem",
          maxWidth: "880px",
          width: "100%",
          margin: "0 auto",
        }}
      >
        {/* Loading State */}
        {pageLoading && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem", padding: "4rem 0" }}>
            <div className="dot-pulse">
              <span />
              <span />
              <span />
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Loading chapter context…
            </p>
          </div>
        )}

        {/* Message Stream */}
        {!pageLoading && messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)}

        {/* Suggested Prompts (when only welcome message is present) */}
        {!pageLoading && messages.length === 1 && (
          <div style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>
            <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Lightbulb size={14} style={{ color: "var(--amber)" }} />
              Suggested questions to ask:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {suggestedPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessageWithText(p)}
                  className="classroom-card text-left p-3 hover:border-blue-300 transition-all cursor-pointer"
                  style={{
                    background: "#FFFFFF",
                    fontSize: "0.85rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.4,
                  }}
                >
                  <span style={{ color: "var(--accent)", fontWeight: 600 }}>• </span>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Typing indicator */}
        {loading && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>

      {/* ── Fixed / Sticky Composer at Bottom ── */}
      <div
        style={{
          borderTop: "1px solid var(--border)",
          background: "var(--bg-secondary)",
          padding: "0.85rem 1.5rem 1rem",
          flexShrink: 0,
          boxShadow: "0 -2px 10px rgba(0, 0, 0, 0.03)",
        }}
      >
        <div style={{ maxWidth: "880px", margin: "0 auto" }}>
          <div style={{ display: "flex", gap: "0.6rem", alignItems: "flex-end" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <textarea
                ref={textareaRef}
                className="chat-input"
                rows={1}
                placeholder={
                  `Ask ${selectedPersona?.name || "your guide"} about ${chapter?.title || "this chapter"}...`
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                style={{
                  minHeight: "48px",
                  maxHeight: "140px",
                  paddingRight: "5rem",
                }}
              />
              <span
                style={{
                  position: "absolute",
                  bottom: "8px",
                  right: "12px",
                  fontSize: "0.68rem",
                  color: "var(--text-subtle)",
                  pointerEvents: "none",
                }}
              >
                ↵ send · ⇧↵ newline
              </span>
            </div>

            <button
              className="btn-primary"
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              style={{
                height: "48px",
                width: "48px",
                padding: 0,
                borderRadius: "12px",
                justifyContent: "center",
                flexShrink: 0,
              }}
              title="Send message"
            >
              {loading ? (
                <div
                  style={{
                    width: "16px",
                    height: "16px",
                    border: "2px solid rgba(255,255,255,0.3)",
                    borderTop: "2px solid white",
                    borderRadius: "50%",
                    animation: "spin 0.7s linear infinite",
                  }}
                />
              ) : (
                <Send size={17} />
              )}
            </button>
          </div>

          <p
            style={{
              textAlign: "center",
              fontSize: "0.7rem",
              color: "var(--text-subtle)",
              margin: "0.5rem 0 0",
            }}
          >
            AI answers are grounded in the Class 5 textbook curriculum. Verify important facts with your teacher.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-primary)" }}>
          <div className="dot-pulse">
            <span />
            <span />
            <span />
          </div>
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
