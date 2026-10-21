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
  User,
  Info,
  Sparkles,
  Lightbulb,
} from "lucide-react";
import { api } from "@/lib/api";
import { chatStorage, type SavedConversation } from "@/lib/chatStorage";
import ChatSidebar from "@/components/ChatSidebar";
import PersonaSelectionModal from "@/components/personas/PersonaSelectionModal";
import { SinglePersonaAvatar } from "@/components/Avatar";
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
    persona_id: persona?.persona_id,
    persona_name: guideName,
    persona_avatar: persona?.avatar_url,
  };
}

function MessageBubble({
  msg,
  onSelectChoice,
  personaAvatar,
  personaName,
  subjectId,
}: {
  msg: UIMessage;
  onSelectChoice?: (choice: string) => void;
  personaAvatar?: string;
  personaName?: string;
  subjectId?: string;
}) {
  const isUser = msg.role === "user";

  const renderContent = (text: string) => {
    const lines = text.split("\n");
    return lines.map((line, lineIdx) => {
      const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
      let content = line;
      let isHeading = false;
      let headingLevel = 0;
      if (headingMatch) {
        isHeading = true;
        headingLevel = headingMatch[1].length;
        content = headingMatch[2];
      }

      const parts = content.split(/(\*\*[^*]+\*\*)/g);
      const renderedParts = parts.map((part, pIdx) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong
              key={pIdx}
              style={{ fontWeight: 700, color: isUser ? "#FFFFFF" : "var(--text-primary)" }}
            >
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
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
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
      {/* Bot Persona Avatar */}
      <SinglePersonaAvatar
        src={msg.persona_avatar || personaAvatar}
        name={msg.persona_name || personaName}
        subjectId={subjectId}
        size={36}
      />

      {/* Content Column */}
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: "0.45rem" }}>
        {msg.persona_name && (
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
            {msg.persona_name}
          </span>
        )}

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
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        {/* Contextual Suggested Next Steps */}
        {msg.suggested_choices && msg.suggested_choices.length > 0 && onSelectChoice && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginTop: "0.4rem" }}>
            {msg.suggested_choices.map((choice, i) => (
              <button
                key={i}
                onClick={() => onSelectChoice(choice)}
                className="btn-ghost"
                style={{
                  fontSize: "0.74rem",
                  padding: "0.25rem 0.65rem",
                  borderRadius: "9999px",
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  color: "var(--text-secondary)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.3rem",
                  cursor: "pointer",
                }}
              >
                <Sparkles size={11} color="var(--accent)" />
                <span>{choice}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator({
  personaAvatar,
  personaName,
  subjectId,
}: {
  personaAvatar?: string;
  personaName?: string;
  subjectId?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        gap: "0.75rem",
        alignItems: "flex-start",
        marginBottom: "1.25rem",
      }}
    >
      <SinglePersonaAvatar
        src={personaAvatar}
        name={personaName}
        subjectId={subjectId}
        size={36}
      />
      <div className="bubble-assistant" style={{ padding: "0.6rem 0.9rem" }}>
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
  const [availablePersonas, setAvailablePersonas] = useState<Persona[]>([]);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  // Scoped Conversation History & Modal
  const [conversations, setConversations] = useState<SavedConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [personaModalOpen, setPersonaModalOpen] = useState(false);

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
        if (!mounted) return;
        setAvailablePersonas(personas);

        // Load existing conversations strictly scoped to this chapter
        const savedConvs = chatStorage.getScopedConversations("chapter", chapterId);
        setConversations(savedConvs);

        if (savedConvs.length > 0) {
          const latest = savedConvs[0];
          setActiveConvId(latest.id);
          setMessages(latest.messages);
          const matchedP = personas.find((p) => p.persona_id === latest.personaId) || personas[0] || null;
          setSelectedPersona(matchedP);
        } else {
          // Initialize fresh conversation with requested or default persona
          const chosen =
            personas.find((p) => p.persona_id === personaIdParam) || personas[0] || null;
          setSelectedPersona(chosen);
          const welcomeMsg = makeWelcome(ch, chosen);
          const newConv = chatStorage.createConversation({
            scopeType: "chapter",
            scopeId: chapterId,
            subjectId: ch.subject_id,
            personaId: chosen?.persona_id || "default",
            personaName: chosen?.name || "AI Tutor",
            personaAvatar: chosen?.avatar_url,
            initialMessages: [welcomeMsg],
          });
          setActiveConvId(newConv.id);
          setMessages([welcomeMsg]);
          setConversations([newConv]);
        }
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
      if (!text || loading || !chapter) return;

      const userMsg: UIMessage = {
        id: genId(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      const newMessages = [...messages, userMsg];
      setMessages(newMessages);
      setInput("");
      setLoading(true);

      const history: HistoryMessage[] = messages
        .filter((m) => m.id !== "welcome" && !m.isError)
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        const res = await api.chat({
          chapter_id: chapterId,
          subject_id: chapter.subject_id,
          persona_id: selectedPersona?.persona_id,
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
          persona_id: res.persona_id || selectedPersona?.persona_id,
          persona_name: selectedPersona?.name,
          persona_avatar: selectedPersona?.avatar_url,
          suggested_choices: res.suggested_choices,
        };

        const updatedMessages = [...newMessages, assistantMsg];
        setMessages(updatedMessages);

        // Update scoped conversation storage
        if (activeConvId) {
          const currentConv = chatStorage.getConversation(activeConvId);
          if (currentConv) {
            currentConv.messages = updatedMessages;
            if (currentConv.title.startsWith("Chat with")) {
              currentConv.title = text.length > 38 ? `${text.slice(0, 38)}...` : text;
            }
            chatStorage.saveConversation(currentConv);
            setConversations(chatStorage.getScopedConversations("chapter", chapterId));
          }
        }
      } catch (e: unknown) {
        const errorMsg: UIMessage = {
          id: genId(),
          role: "assistant",
          content: e instanceof Error ? e.message : "Something went wrong. Please try again.",
          timestamp: new Date(),
          isError: true,
          persona_name: selectedPersona?.name,
          persona_avatar: selectedPersona?.avatar_url,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [loading, chapter, chapterId, messages, activeConvId, selectedPersona]
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
    if (!chapter) return;
    const initialMsg = makeWelcome(chapter, selectedPersona);
    const newConv = chatStorage.createConversation({
      scopeType: "chapter",
      scopeId: chapterId,
      subjectId: chapter.subject_id,
      personaId: selectedPersona?.persona_id || "default",
      personaName: selectedPersona?.name || "AI Tutor",
      personaAvatar: selectedPersona?.avatar_url,
      initialMessages: [initialMsg],
    });
    setActiveConvId(newConv.id);
    setMessages([initialMsg]);
    setConversations(chatStorage.getScopedConversations("chapter", chapterId));
    setInput("");
  };

  const handleSelectConversation = (conv: SavedConversation) => {
    setActiveConvId(conv.id);
    setMessages(conv.messages);
    const matchedP = availablePersonas.find((p) => p.persona_id === conv.personaId) || selectedPersona;
    setSelectedPersona(matchedP);
  };

  const handleDeleteConversation = (id: string) => {
    chatStorage.deleteConversation(id);
    const remaining = chatStorage.getScopedConversations("chapter", chapterId);
    setConversations(remaining);
    if (activeConvId === id) {
      if (remaining.length > 0) {
        handleSelectConversation(remaining[0]);
      } else {
        handleNewChat();
      }
    }
  };

  const handlePersonaSelected = (newPersonaId: string) => {
    const chosen = availablePersonas.find((p) => p.persona_id === newPersonaId) || null;
    setSelectedPersona(chosen);
    setPersonaModalOpen(false);
    // Start fresh new conversation locked to this guide (Section 13 rule)
    if (chapter) {
      const initialMsg = makeWelcome(chapter, chosen);
      const newConv = chatStorage.createConversation({
        scopeType: "chapter",
        scopeId: chapterId,
        subjectId: chapter.subject_id,
        personaId: newPersonaId,
        personaName: chosen?.name || "AI Tutor",
        personaAvatar: chosen?.avatar_url,
        initialMessages: [initialMsg],
      });
      setActiveConvId(newConv.id);
      setMessages([initialMsg]);
      setConversations(chatStorage.getScopedConversations("chapter", chapterId));
      setInput("");
    }
  };

  const subjectId = chapterId.split("_")[0];

  const suggestedPrompts = [
    `What is ${chapter?.title ?? "this chapter"} about?`,
    "What are the main concepts covered in this chapter?",
    "Give me an interesting example from this lesson",
    "Tell me a fun joke to start learning!",
  ];

  return (
    <div style={{ height: "100vh", display: "flex", background: "var(--bg-primary)", overflow: "hidden" }}>
      {/* ── Left Collapsible Scoped Chat Sidebar ── */}
      <ChatSidebar
        conversations={conversations}
        activeConversationId={activeConvId || undefined}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        onChangeGuide={() => setPersonaModalOpen(true)}
        scopeTitle={chapter ? `Chapter ${chapter.chapter_number}` : "Chapter Chat"}
        scopeSubtitle={chapter?.title || ""}
        currentPersonaName={selectedPersona?.name || "AI Tutor"}
        currentPersonaAvatar={selectedPersona?.avatar_url}
        subjectId={subjectId}
      />

      {/* ── Main Chat Area ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
        {/* Top Header */}
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
            zIndex: 30,
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
                <SinglePersonaAvatar
                  src={selectedPersona?.avatar_url}
                  name={selectedPersona?.name}
                  subjectId={subjectId}
                  size={32}
                />
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
                      Guide: {selectedPersona.name} (Locked)
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <button
              className="btn-ghost"
              onClick={() => setPersonaModalOpen(true)}
              style={{ padding: "0.4rem 0.75rem", fontSize: "0.78rem" }}
              title="Start a new chat with a different guide"
            >
              Change Guide
            </button>
            <button
              className="btn-ghost"
              onClick={handleNewChat}
              style={{ padding: "0.4rem 0.85rem", fontSize: "0.82rem" }}
              title="Start a new chat"
            >
              <Plus size={14} />
              New chat
            </button>
          </div>
        </header>

        {/* Page Error Banner */}
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

        {/* Chat Messages Stream */}
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

          {!pageLoading &&
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onSelectChoice={sendMessageWithText}
                personaAvatar={selectedPersona?.avatar_url}
                personaName={selectedPersona?.name}
                subjectId={subjectId}
              />
            ))}

          {!pageLoading && messages.length === 1 && (
            <div style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>
              <div
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  marginBottom: "0.75rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.35rem",
                }}
              >
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

          {loading && (
            <TypingIndicator
              personaAvatar={selectedPersona?.avatar_url}
              personaName={selectedPersona?.name}
              subjectId={subjectId}
            />
          )}

          <div ref={bottomRef} />
        </div>

        {/* Composer */}
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
                  placeholder={`Ask ${selectedPersona?.name || "your guide"} about ${chapter?.title || "this chapter"}...`}
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
              Grounded in the official Maharashtra State Board curriculum. Guided by {selectedPersona?.name || "AI Tutor"}.
            </p>
          </div>
        </div>
      </div>

      {/* Guide Selection Modal */}
      {chapter && (
        <PersonaSelectionModal
          isOpen={personaModalOpen}
          onClose={() => setPersonaModalOpen(false)}
          subjectId={chapter.subject_id}
          subjectName={chapter.subject_id}
          chapterId={chapter.chapter_id}
          chapterTitle={chapter.title}
          onSelectPersona={handlePersonaSelected}
        />
      )}
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
