"use client";

import { useEffect, useState, useRef, useCallback, KeyboardEvent, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Send,
  Sparkles,
  RotateCcw,
  BookOpen,
  User,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import PersonaSelectionModal from "@/components/personas/PersonaSelectionModal";
import ChatSidebar from "@/components/ChatSidebar";
import { SinglePersonaAvatar } from "@/components/Avatar";
import { chatStorage, type SavedConversation } from "@/lib/chatStorage";
import { api } from "@/lib/api";
import type { Subject, Persona, UIMessage, HistoryMessage } from "@/types";

function genId(): string {
  return Math.random().toString(36).slice(2, 9);
}

function makeWelcome(subject: Subject, persona?: Persona | null): UIMessage {
  const guideName = persona?.name || `${subject.name} AI Tutor`;
  return {
    id: "welcome",
    role: "assistant",
    content: `Welcome to the **${subject.name} Learning Studio**! I am **${guideName}**.\n\nYou can ask me about any chapter, concept, proof, or historical event across the entire **${subject.name}** curriculum. What would you like to explore today?`,
    timestamp: new Date(),
    persona_id: persona?.persona_id,
    persona_name: guideName,
    persona_avatar: persona?.avatar_url,
  };
}

function SubjectChatContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const subjectId = ((params.subjectId as string) || "mathematics").toLowerCase();
  const personaIdParam = searchParams.get("persona") || "";

  const [subject, setSubject] = useState<Subject | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [availablePersonas, setAvailablePersonas] = useState<Persona[]>([]);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scoped Conversation History & Modal
  const [conversations, setConversations] = useState<SavedConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [personaModalOpen, setPersonaModalOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    let mounted = true;
    async function init() {
      try {
        const subData = await api.getSubject(subjectId);
        if (!mounted) return;
        setSubject(subData);

        const personas = await api.getPersonas(subjectId);
        if (!mounted) return;
        setAvailablePersonas(personas);

        // Load existing conversations strictly scoped to this subject-wide scope
        const savedConvs = chatStorage.getScopedConversations("subject", subjectId);
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
          const welcomeMsg = makeWelcome(subData, chosen);
          const newConv = chatStorage.createConversation({
            scopeType: "subject",
            scopeId: subjectId,
            subjectId: subjectId,
            personaId: chosen?.persona_id || "default",
            personaName: chosen?.name || `${subData.name} Tutor`,
            personaAvatar: chosen?.avatar_url,
            initialMessages: [welcomeMsg],
          });
          setActiveConvId(newConv.id);
          setMessages([welcomeMsg]);
          setConversations([newConv]);
        }
      } catch (err: any) {
        if (mounted) {
          console.error("Failed to initialize subject chat:", err);
          setError("Could not connect to subject service.");
        }
      }
    }
    init();
    return () => {
      mounted = false;
    };
  }, [subjectId, personaIdParam]);

  const handleSendMessageWithText = useCallback(
    async (textToSend: string) => {
      const userText = textToSend.trim();
      if (!userText || loading || !subject) return;

      setInputMessage("");
      if (textareaRef.current) textareaRef.current.style.height = "auto";

      const userMsg: UIMessage = {
        id: genId(),
        role: "user",
        content: userText,
        timestamp: new Date(),
      };

      const newMessages = [...messages, userMsg];
      setMessages(newMessages);
      setLoading(true);

      const historyPayload: HistoryMessage[] = messages
        .filter((m) => m.id !== "welcome" && !m.isError)
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        const anchorChapterId = subject.chapters[0]?.chapter_id || `${subjectId}_all`;

        const res = await api.chat({
          chapter_id: anchorChapterId,
          subject_id: subjectId,
          persona_id: selectedPersona?.persona_id,
          message: userText,
          history: historyPayload,
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
          persona_name: selectedPersona?.name || `${subject.name} AI Tutor`,
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
              currentConv.title = userText.length > 38 ? `${userText.slice(0, 38)}...` : userText;
            }
            chatStorage.saveConversation(currentConv);
            setConversations(chatStorage.getScopedConversations("subject", subjectId));
          }
        }
      } catch (err: any) {
        const errorMsg: UIMessage = {
          id: genId(),
          role: "assistant",
          content: `I encountered an issue retrieving the response: ${err.message}. Please check that the local AI engine is running.`,
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
    [loading, subject, subjectId, messages, activeConvId, selectedPersona]
  );

  const handleSendMessage = () => {
    handleSendMessageWithText(inputMessage);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    if (!subject) return;
    const initialMsg = makeWelcome(subject, selectedPersona);
    const newConv = chatStorage.createConversation({
      scopeType: "subject",
      scopeId: subjectId,
      subjectId: subjectId,
      personaId: selectedPersona?.persona_id || "default",
      personaName: selectedPersona?.name || `${subject.name} Tutor`,
      personaAvatar: selectedPersona?.avatar_url,
      initialMessages: [initialMsg],
    });
    setActiveConvId(newConv.id);
    setMessages([initialMsg]);
    setConversations(chatStorage.getScopedConversations("subject", subjectId));
    setInputMessage("");
  };

  const handleSelectConversation = (conv: SavedConversation) => {
    setActiveConvId(conv.id);
    setMessages(conv.messages);
    const matchedP = availablePersonas.find((p) => p.persona_id === conv.personaId) || selectedPersona;
    setSelectedPersona(matchedP);
  };

  const handleDeleteConversation = (id: string) => {
    chatStorage.deleteConversation(id);
    const remaining = chatStorage.getScopedConversations("subject", subjectId);
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
    if (subject) {
      const initialMsg = makeWelcome(subject, chosen);
      const newConv = chatStorage.createConversation({
        scopeType: "subject",
        scopeId: subjectId,
        subjectId: subjectId,
        personaId: newPersonaId,
        personaName: chosen?.name || `${subject.name} Tutor`,
        personaAvatar: chosen?.avatar_url,
        initialMessages: [initialMsg],
      });
      setActiveConvId(newConv.id);
      setMessages([initialMsg]);
      setConversations(chatStorage.getScopedConversations("subject", subjectId));
      setInputMessage("");
    }
  };

  return (
    <div className="h-screen bg-slate-50 flex flex-col font-sans overflow-hidden">
      <Navbar />

      <div className="flex-1 flex overflow-hidden">
        {/* Scoped Sidebar */}
        <ChatSidebar
          conversations={conversations}
          activeConversationId={activeConvId || undefined}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
          onDeleteConversation={handleDeleteConversation}
          onChangeGuide={() => setPersonaModalOpen(true)}
          scopeTitle={`${subject?.name || "Subject"} Studio`}
          scopeSubtitle="Subject-Wide Learning Scope"
          currentPersonaName={selectedPersona?.name || "AI Tutor"}
          currentPersonaAvatar={selectedPersona?.avatar_url}
          subjectId={subjectId}
        />

        {/* Chat Main Container */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50">
          {/* Header */}
          <div className="bg-white border-b border-slate-200 px-4 py-3 shadow-2xs flex-shrink-0">
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <a
                  href={`/subjects/${subjectId}`}
                  className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
                >
                  <ArrowLeft size={18} />
                </a>

                {/* Persona Avatar */}
                <SinglePersonaAvatar
                  src={selectedPersona?.avatar_url}
                  name={selectedPersona?.name}
                  subjectId={subjectId}
                  size={38}
                />

                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-sm font-bold text-slate-900">
                      {selectedPersona?.name || `${subject?.name || ""} Tutor`}
                    </h1>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      Subject-Wide Chat (Locked)
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
                  onClick={handleNewChat}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                  title="Start New Chat"
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
                    <SinglePersonaAvatar
                      src={msg.persona_avatar || selectedPersona?.avatar_url}
                      name={msg.persona_name || selectedPersona?.name}
                      subjectId={subjectId}
                      size={32}
                    />
                  )}

                  <div
                    className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                      isUser
                        ? "bg-blue-600 text-white rounded-tr-xs shadow-xs"
                        : "bg-white text-slate-800 border border-slate-200/90 rounded-tl-xs shadow-2xs space-y-2"
                    }`}
                  >
                    {!isUser && msg.persona_name && (
                      <span className="text-[11px] font-bold text-blue-700 block uppercase tracking-wider">
                        {msg.persona_name}
                      </span>
                    )}
                    <div className="whitespace-pre-wrap">{msg.content}</div>

                    {/* Contextual Suggested Choices */}
                    {msg.suggested_choices && msg.suggested_choices.length > 0 && (
                      <div className="pt-2 flex flex-wrap gap-1.5 border-t border-slate-100 mt-2">
                        {msg.suggested_choices.map((choice, i) => (
                          <button
                            key={i}
                            onClick={() => handleSendMessageWithText(choice)}
                            className="text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200/60 transition-colors inline-flex items-center gap-1 cursor-pointer"
                          >
                            <Sparkles size={11} />
                            <span>{choice}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    <div
                      className={`text-[10px] text-right mt-1 ${
                        isUser ? "text-blue-100" : "text-slate-400"
                      }`}
                    >
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-start gap-3">
                <SinglePersonaAvatar
                  src={selectedPersona?.avatar_url}
                  name={selectedPersona?.name}
                  subjectId={subjectId}
                  size={32}
                />
                <div className="bg-white border border-slate-200 rounded-2xl p-3 shadow-2xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
                    <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse delay-75" />
                    <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse delay-150" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Composer */}
          <div className="bg-white border-t border-slate-200 p-4 shadow-sm flex-shrink-0">
            <div className="max-w-4xl mx-auto flex items-end gap-2">
              <div className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all p-2 flex items-center">
                <textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={`Ask ${selectedPersona?.name || "your guide"} across ${subject?.name || "this subject"}...`}
                  rows={1}
                  className="w-full bg-transparent resize-none outline-none text-sm text-slate-800 placeholder:text-slate-400 px-2 max-h-32"
                />
              </div>

              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || loading}
                className="p-3 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white shadow-xs transition-all cursor-pointer flex-shrink-0"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="text-[11px] text-center text-slate-400 mt-2">
              Conversing with {selectedPersona?.name || "Subject Guide"}. Persona identity is locked for this conversation.
            </p>
          </div>
        </div>
      </div>

      {/* Guide Selection Modal */}
      {subject && (
        <PersonaSelectionModal
          isOpen={personaModalOpen}
          onClose={() => setPersonaModalOpen(false)}
          subjectId={subjectId}
          subjectName={subject.name}
          onSelectPersona={handlePersonaSelected}
        />
      )}
    </div>
  );
}

export default function SubjectChatPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <SubjectChatContent />
    </Suspense>
  );
}
