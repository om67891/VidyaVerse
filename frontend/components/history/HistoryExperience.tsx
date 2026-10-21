"use client";

import { useEffect, useState, useRef } from "react";
import {
  BookOpen,
  Compass,
  ArrowLeft,
  Send,
  HelpCircle,
  RotateCcw,
  Volume2,
  VolumeX,
  Scroll,
  X,
  Check,
  ChevronRight,
  Shield,
  Award,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import type { HistorySessionState, LessonNode, HistoryChatMessage } from "@/types";

export default function HistoryChatbotApp() {
  const [session, setSession] = useState<HistorySessionState | null>(null);
  const [loading, setLoading] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [curriculumMap, setCurriculumMap] = useState<LessonNode[]>([]);
  const [showMapModal, setShowMapModal] = useState(false);
  const [selectedQuizOption, setSelectedQuizOption] = useState<number | null>(null);
  const [expandedCitationKey, setExpandedCitationKey] = useState<string | null>(null);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize or resume session
  useEffect(() => {
    async function init() {
      try {
        const savedSessionId = localStorage.getItem("history_session_id");
        const res = await api.startHistorySession(savedSessionId || undefined);
        setSession(res);
        localStorage.setItem("history_session_id", res.session_id);

        const mapData = await api.getHistoryMap();
        setCurriculumMap(mapData);
      } catch (err) {
        console.error("Failed to initialize History session:", err);
        setErrorMsg("Unable to connect to the History backend. Make sure the backend server is running.");
      }
    }
    init();
  }, []);

  // Auto-scroll when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages, loading]);

  // Adjust textarea height dynamically
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  // Text-to-speech reading
  const toggleSpeech = (msgId: string, text: string) => {
    if (!window.speechSynthesis) return;

    if (speakingMsgId === msgId) {
      window.speechSynthesis.cancel();
      setSpeakingMsgId(null);
    } else {
      window.speechSynthesis.cancel();
      const cleanText = text
        .replace(/\*\*/g, "")
        .replace(/#/g, "")
        .replace(/\[.*?\]/g, "");

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.onend = () => setSpeakingMsgId(null);
      utterance.onerror = () => setSpeakingMsgId(null);
      window.speechSynthesis.speak(utterance);
      setSpeakingMsgId(msgId);
    }
  };

  // Clickable choice in conversation
  const handleChoice = async (choiceId: string) => {
    if (!session || loading) return;
    setLoading(true);
    setErrorMsg(null);
    setSelectedQuizOption(null);

    try {
      const updated = await api.historyAction({
        session_id: session.session_id,
        action_type: "choice",
        choice_id: choiceId,
      });
      setSession(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process choice");
    } finally {
      setLoading(false);
    }
  };

  // Quiz submission in conversation
  const handleQuizAnswer = async () => {
    if (!session || loading || selectedQuizOption === null) return;
    setLoading(true);
    setErrorMsg(null);

    try {
      const updated = await api.historyAction({
        session_id: session.session_id,
        action_type: "quiz_answer",
        selected_index: selectedQuizOption,
      });
      setSession(updated);
      setSelectedQuizOption(null);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit quiz answer");
    } finally {
      setLoading(false);
    }
  };

  // Send custom question from composer
  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!session || !inputMessage.trim() || loading) return;

    const q = inputMessage.trim();
    setInputMessage("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const updated = await api.historyAsk({
        session_id: session.session_id,
        question: q,
      });
      setSession(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to answer custom question");
    } finally {
      setLoading(false);
    }
  };

  // Return to ongoing lesson after custom question
  const handleReturnToLesson = async () => {
    if (!session || loading) return;
    setLoading(true);
    setErrorMsg(null);

    try {
      const updated = await api.historyAction({
        session_id: session.session_id,
        action_type: "return_to_lesson",
      });
      setSession(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to return to story");
    } finally {
      setLoading(false);
    }
  };

  // Jump to specific lesson from map
  const handleSelectLesson = async (lessonId: string) => {
    if (!session || loading) return;
    setLoading(true);
    setErrorMsg(null);
    setShowMapModal(false);

    try {
      const updated = await api.historyAction({
        session_id: session.session_id,
        action_type: "select_lesson",
        lesson_id: lessonId,
      });
      setSession(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to switch lesson");
    } finally {
      setLoading(false);
    }
  };

  // Restart session with confirmation
  const handleRestart = async () => {
    if (!session || loading) return;
    if (confirm("Restart the History learning journey from Lesson 1?")) {
      handleSelectLesson("HIST_L01");
    }
  };

  const messages: HistoryChatMessage[] = session?.messages || [];
  const latestMessageId = messages.length > 0 ? messages[messages.length - 1].id : null;

  return (
    <div className="storybook-container flex flex-col h-screen overflow-hidden">
      {/* ── Compact Sticky Header ── */}
      <header className="sticky top-0 z-30 bg-[#FAF7F0]/95 backdrop-blur-md border-b border-[#E7DEC8] px-4 py-2.5 sm:px-6 shrink-0 shadow-2xs">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
          {/* Brand & Subject Badge */}
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-[#D97706] text-white flex items-center justify-center font-bold text-sm shadow-2xs shrink-0">
              <BookOpen className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-sm font-bold text-[#2A2118] tracking-tight">
                  Shivachhatrapati
                </span>
                <span className="text-[10px] uppercase font-bold px-2 py-0.2 rounded-full bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D]">
                  Class 4 History
                </span>
              </div>
              {session && (
                <div className="text-[11px] text-[#6E5F4E] font-medium truncate mt-0.5">
                  Lesson {session.lesson_number} of {session.total_lessons}: <span className="font-semibold text-[#2A2118]">{session.lesson_title}</span>
                </div>
              )}
            </div>
          </div>

          {/* Right Controls: Progress, Curriculum Map, Reset */}
          <div className="flex items-center gap-2 shrink-0">
            {session && (
              <div className="hidden sm:flex items-center gap-2 mr-1">
                <div className="w-24 bg-[#E5DBCA] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#D97706] h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(session.progress_percentage, 5)}%` }}
                  />
                </div>
                <span className="text-[11px] font-semibold text-[#6E5F4E]">
                  {session.completed_lessons.length}/{session.total_lessons}
                </span>
              </div>
            )}

            <button
              onClick={() => setShowMapModal(true)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[#D4C3A3] bg-[#FFFDF9] text-xs font-semibold text-[#5C4A33] hover:bg-[#F3EFE6] transition-colors shadow-2xs"
              title="Open 18-Lesson Curriculum Map"
            >
              <Compass className="w-3.5 h-3.5 text-[#D97706]" />
              <span className="hidden md:inline">Curriculum Map</span>
            </button>

            <button
              onClick={handleRestart}
              className="p-1.5 rounded-lg border border-[#D4C3A3] bg-[#FFFDF9] text-[#6E5F4E] hover:text-[#991B1B] hover:bg-[#F3EFE6] transition-colors shadow-2xs"
              title="Restart from Lesson 1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* ── Scrollable Conversation Timeline ── */}
      <main className="flex-1 overflow-y-auto px-3 sm:px-6 py-5">
        <div className="max-w-3xl mx-auto space-y-5">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B] text-xs flex items-center justify-between shadow-xs">
              <span>{errorMsg}</span>
              <button onClick={() => setErrorMsg(null)} className="font-bold underline ml-2">
                Dismiss
              </button>
            </div>
          )}

          {/* Conversation History */}
          {messages.map((msg, index) => {
            const isAssistant = msg.role === "assistant";
            const isShivaji = msg.persona === "SHIVAJI";
            const isLatest = msg.id === latestMessageId;

            return (
              <div
                key={msg.id || index}
                className={`flex flex-col ${isAssistant ? "items-start" : "items-end"} animate-in fade-in duration-200`}
              >
                {/* Message Header (for assistant) */}
                {isAssistant && (
                  <div className="flex items-center gap-2 mb-1.5 pl-1">
                    <div
                      className="w-7 h-7 rounded-full overflow-hidden border border-[#D97706] bg-[#FFFDF9] flex items-center justify-center shrink-0 shadow-2xs"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={msg.persona_avatar || (isShivaji ? "/avatars/shivaji-maharaj.png" : "/avatars/history-tutor.png")}
                        alt={msg.persona_name || "Tutor"}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = "none";
                        }}
                      />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-[#2A2118]">
                        {msg.persona_name || (isShivaji ? "Chhatrapati Shivaji Maharaj" : "History Master")}
                      </span>
                      {isShivaji ? (
                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 rounded bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D]">
                          Roleplay
                        </span>
                      ) : (
                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 rounded bg-[#EEF2FF] text-[#4338CA] border border-[#C7D2FE]">
                          Guide
                        </span>
                      )}
                      {msg.timestamp && (
                        <span className="text-[10px] text-[#9A8D7E] ml-1">
                          {msg.timestamp}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`relative max-w-[92%] sm:max-w-[85%] rounded-2xl px-4 py-3.5 text-sm leading-relaxed ${
                    isAssistant
                      ? "storybook-card bg-[#FFFDF9] text-[#2A2118] border border-[#E7DEC8]"
                      : "bg-[#854D0E] text-white shadow-xs rounded-tr-xs"
                  }`}
                >
                  {/* Lesson Illustration Banner (shown on first assistant message or introductory story) */}
                  {isAssistant && index === 0 && session?.current_lesson_id && (
                    (() => {
                      const LESSON_ILLUSTRATIONS: Record<string, { url: string; title: string; caption: string }> = {
                        HIST_L01: {
                          url: "/illustrations/history/saints_pandharpur.svg",
                          title: "Pilgrimage to Pandharpur & The Saints",
                          caption: "Devotees uniting at Pandharpur in love and equality"
                        },
                        HIST_L02: {
                          url: "/illustrations/history/saints_pandharpur.svg",
                          title: "Pilgrimage to Pandharpur & The Saints",
                          caption: "Devotees uniting at Pandharpur in love and equality"
                        },
                        HIST_L04: {
                          url: "/illustrations/history/shivneri_fort.svg",
                          title: "Fort Shivneri near Junnar",
                          caption: "The historic birthplace of Chhatrapati Shivaji Maharaj"
                        },
                        HIST_L08: {
                          url: "/illustrations/history/pratapgad_fort.svg",
                          title: "Fort Pratapgad & The Sahyadri Hills",
                          caption: "The mountain stronghold where Afzalkhan was defeated"
                        },
                        HIST_L09: {
                          url: "/illustrations/history/pratapgad_fort.svg",
                          title: "Fort Pratapgad & The Sahyadri Hills",
                          caption: "The mountain stronghold where Afzalkhan was defeated"
                        },
                        HIST_L14: {
                          url: "/illustrations/history/sindhudurg_fort.svg",
                          title: "Sea Fort of Sindhudurg (Malvan)",
                          caption: "Shivaji Maharaj's naval bastion in the Arabian Sea"
                        },
                        HIST_L17: {
                          url: "/illustrations/history/sindhudurg_fort.svg",
                          title: "Sea Fort of Sindhudurg (Malvan)",
                          caption: "Shivaji Maharaj's naval bastion in the Arabian Sea"
                        },
                      };
                      const ill = LESSON_ILLUSTRATIONS[session.current_lesson_id];
                      if (!ill) return null;
                      return (
                        <div className="mb-3 rounded-xl overflow-hidden border border-[#E7DEC8] bg-[#FAF7F0] shadow-2xs">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={ill.url}
                            alt={ill.title}
                            className="w-full h-36 sm:h-44 object-cover"
                          />
                          <div className="p-2 sm:px-3 sm:py-1.5 flex items-center justify-between text-[11px] text-[#6E5F4E] border-t border-[#E7DEC8] bg-[#FFFDF9]">
                            <span className="font-semibold text-[#2A2118]">🏛️ {ill.title}</span>
                            <span className="hidden sm:inline text-[#9A8D7E]">{ill.caption}</span>
                          </div>
                        </div>
                      );
                    })()
                  )}

                  {/* Message Content */}
                  <div className="whitespace-pre-line prose prose-sm max-w-none text-inherit leading-relaxed">
                    {msg.content}
                  </div>

                  {/* Adaptive Format: Key Highlights / Badges */}
                  {isAssistant && msg.highlights && msg.highlights.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {msg.highlights.map((h, hIdx) => (
                        <span
                          key={hIdx}
                          className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FEF3C7] text-[#92400E] border border-[#FCD34D]"
                        >
                          ⭐ {h}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Adaptive Format: Historical Figure Profile */}
                  {isAssistant && msg.figure_profile && (
                    <div className="mt-3 p-3.5 rounded-xl border border-[#FCD34D] bg-[#FFFBEB] text-[#2A2118] shadow-2xs">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <Award className="w-4 h-4 text-[#D97706]" />
                          <span className="font-bold text-sm text-[#92400E]">{msg.figure_profile.name}</span>
                        </div>
                        {msg.figure_profile.place && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D]">
                            📍 {msg.figure_profile.place}
                          </span>
                        )}
                      </div>
                      {msg.figure_profile.title && (
                        <div className="text-xs font-semibold text-[#B45309] mb-1">
                          {msg.figure_profile.title}
                        </div>
                      )}
                      <p className="text-xs text-[#451A03] mb-2 leading-relaxed">
                        <strong>Contribution:</strong> {msg.figure_profile.contribution}
                      </p>
                      {msg.figure_profile.key_teachings && msg.figure_profile.key_teachings.length > 0 && (
                        <div className="pt-2 border-t border-[#FDE68A] text-xs">
                          <span className="font-bold text-[#92400E] block mb-1">Key Teachings:</span>
                          <ul className="list-disc list-inside space-y-0.5 text-[#78350F]">
                            {msg.figure_profile.key_teachings.map((t, tIdx) => (
                              <li key={tIdx}>{t}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Adaptive Format: Chronological Sequence / Timeline */}
                  {isAssistant && msg.timeline_events && msg.timeline_events.length > 0 && (
                    <div className="mt-3 p-3.5 rounded-xl border border-[#CBD5E1] bg-[#F8FAFC] shadow-2xs">
                      <div className="text-xs font-bold text-[#334155] uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                        <span>⏳ Chronological Sequence:</span>
                      </div>
                      <div className="space-y-2.5">
                        {msg.timeline_events.map((evt, eIdx) => (
                          <div key={eIdx} className="flex items-start gap-2.5">
                            <div className="w-5 h-5 rounded-full bg-[#D97706] text-white flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                              {evt.step}
                            </div>
                            <div className="text-xs text-[#1E293B]">
                              <strong className="text-[#0F172A] block font-semibold">{evt.title}</strong>
                              <span className="text-[#475569]">{evt.description}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Adaptive Format: Cause and Effect Card */}
                  {isAssistant && msg.cause_effect && (
                    <div className="mt-3 p-3.5 rounded-xl border border-[#FDE68A] bg-[#FFFDF5] space-y-2 text-xs shadow-2xs">
                      <div className="font-bold text-[#92400E] uppercase text-[11px] tracking-wider mb-1">
                        ⚡ Cause &amp; Effect Breakdown
                      </div>
                      <div className="p-2 rounded-lg bg-[#FEF3C7] border border-[#FCD34D]">
                        <strong className="text-[#92400E] block text-[11px]">The Cause:</strong>
                        <span className="text-[#78350F]">{msg.cause_effect.cause}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-[#FFFBEB] border border-[#FDE68A]">
                        <strong className="text-[#B45309] block text-[11px]">Historical Turning Point:</strong>
                        <span className="text-[#78350F]">{msg.cause_effect.event}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-[#ECFDF5] border border-[#A7F3D0]">
                        <strong className="text-[#065F46] block text-[11px]">Lasting Significance:</strong>
                        <span className="text-[#047857]">{msg.cause_effect.significance}</span>
                      </div>
                    </div>
                  )}

                  {/* Adaptive Format: Comparison Card */}
                  {isAssistant && msg.comparison && (
                    <div className="mt-3 rounded-xl border border-[#E2E8F0] overflow-hidden bg-white text-xs shadow-2xs">
                      <div className="grid grid-cols-3 bg-[#F1F5F9] p-2 font-bold text-[#334155] border-b border-[#E2E8F0] text-[11px]">
                        <div>Aspect</div>
                        <div>{msg.comparison.labelA}</div>
                        <div>{msg.comparison.labelB}</div>
                      </div>
                      {msg.comparison.rows.map((row, rIdx) => (
                        <div key={rIdx} className="grid grid-cols-3 p-2 border-b border-[#F1F5F9] last:border-0 hover:bg-[#F8FAFC]">
                          <div className="font-semibold text-[#475569]">{row.feature}</div>
                          <div className="text-[#1E293B] pr-1">{row.itemA}</div>
                          <div className="text-[#1E293B]">{row.itemB}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Adaptive Format: Recap Points */}
                  {isAssistant && msg.recap_points && msg.recap_points.length > 0 && (
                    <div className="mt-3 p-3.5 rounded-xl border border-[#A7F3D0] bg-[#ECFDF5] shadow-2xs">
                      <div className="text-xs font-bold text-[#065F46] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-[#059669]" />
                        <span>Lesson Takeaways &amp; Key Learnings:</span>
                      </div>
                      <ul className="space-y-1 text-xs text-[#047857]">
                        {msg.recap_points.map((pt, pIdx) => (
                          <li key={pIdx} className="flex items-start gap-1.5">
                            <span className="font-bold text-[#059669]">•</span>
                            <span>{pt}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Audio Listen action for Assistant */}
                  {isAssistant && (
                    <div className="mt-2.5 pt-2 border-t border-[#F3EFE6] flex items-center justify-between text-xs text-[#786C5E]">
                      <button
                        onClick={() => toggleSpeech(msg.id, msg.content)}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-[#786C5E] hover:text-[#B45309] transition-colors"
                        title={speakingMsgId === msg.id ? "Mute reading" : "Read message aloud"}
                      >
                        {speakingMsgId === msg.id ? (
                          <>
                            <VolumeX className="w-3.5 h-3.5 text-[#B45309]" />
                            <span className="text-[#B45309] font-semibold">Mute</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>Listen</span>
                          </>
                        )}
                      </button>

                      {msg.can_resume && isLatest && (
                        <button
                          onClick={handleReturnToLesson}
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#B45309] hover:underline"
                        >
                          <ArrowLeft className="w-3 h-3" />
                          <span>Return to Story</span>
                        </button>
                      )}
                    </div>
                  )}

                  {/* Inline Quiz Check (if present in message) */}
                  {isAssistant && msg.quiz && (
                    <div className="mt-3.5 p-3.5 rounded-xl border border-[#FCD34D] bg-[#FFFDF7]">
                      <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#B45309] mb-2">
                        <span>🎯 Knowledge Challenge</span>
                      </div>
                      <p className="font-bold text-xs sm:text-sm text-[#2A2118] mb-3">
                        {msg.quiz.question}
                      </p>
                      <div className="space-y-2 mb-3">
                        {msg.quiz.options.map((opt, optIdx) => (
                          <button
                            key={optIdx}
                            onClick={() => setSelectedQuizOption(optIdx)}
                            disabled={loading || (msg.quiz_passed !== undefined && msg.quiz_passed !== null)}
                            className={`w-full text-left p-2.5 rounded-lg border text-xs sm:text-sm font-medium transition-colors ${
                              selectedQuizOption === optIdx
                                ? "border-[#D97706] bg-[#FEF3C7] text-[#92400E] font-semibold"
                                : "border-[#E7DEC8] bg-[#FFFDF9] text-[#2A2118] hover:bg-[#FAF6EF]"
                            }`}
                          >
                            <span className="font-bold mr-2 text-[#786C5E]">
                              {String.fromCharCode(65 + optIdx)}.
                            </span>
                            {opt}
                          </button>
                        ))}
                      </div>

                      {/* Quiz Feedback Result */}
                      {msg.quiz_feedback && (
                        <div
                          className={`mt-2.5 p-2.5 rounded-lg border text-xs font-medium ${
                            msg.quiz_passed
                              ? "bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]"
                              : "bg-[#FFFBEB] border-[#FDE68A] text-[#92400E]"
                          }`}
                        >
                          <div className="font-bold mb-0.5">
                            {msg.quiz_passed ? "✅ Splendid Answer!" : "💡 Learning Insight:"}
                          </div>
                          {msg.quiz_feedback}
                        </div>
                      )}

                      {/* Submit Quiz button if not yet answered */}
                      {!msg.quiz_feedback && isLatest && (
                        <div className="flex items-center justify-between pt-1">
                          <button
                            onClick={() => handleChoice("story")}
                            className="text-[11px] text-[#786C5E] hover:underline"
                          >
                            Skip &amp; continue
                          </button>
                          <button
                            onClick={handleQuizAnswer}
                            disabled={selectedQuizOption === null || loading}
                            className="px-4 py-1.5 rounded-lg bg-[#D97706] text-white text-xs font-bold hover:bg-[#B45309] disabled:opacity-50 transition-colors shadow-2xs"
                          >
                            Submit Answer
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Deduplicated Textbook Sources Drawer */}
                  {isAssistant && msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-[#F3EFE6]">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#786C5E] uppercase tracking-wider mb-1.5">
                        <Scroll className="w-3 h-3 text-[#B45309]" />
                        <span>Textbook Sources:</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.citations.map((c, cIdx) => {
                          const citeKey = `${msg.id}_${c.pdf_page}_${cIdx}`;
                          const isExpanded = expandedCitationKey === citeKey;

                          return (
                            <div key={cIdx} className="flex flex-col">
                              <button
                                onClick={() => setExpandedCitationKey(isExpanded ? null : citeKey)}
                                className="storybook-citation-badge text-[11px] cursor-pointer hover:border-[#B45309]"
                                title="Click to view textbook excerpt"
                              >
                                <span>📖 {c.lesson_title}</span>
                                <span className="text-[#B45309] font-bold">
                                  (PDF Page {c.pdf_page})
                                </span>
                              </button>

                              {isExpanded && c.snippet && (
                                <div className="mt-1 p-2 rounded-lg bg-[#FAF4EA] border border-[#E3D7C1] text-[11px] text-[#5C4A33] max-w-sm animate-in fade-in duration-150">
                                  <span className="font-semibold block mb-0.5 text-[#B45309]">Textbook Passage:</span>
                                  &ldquo;{c.snippet}&rdquo;
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Clickable Choice Actions embedded directly under the latest assistant message */}
                {isAssistant && isLatest && msg.choices && msg.choices.length > 0 && !loading && (
                  <div className="mt-3 pl-1 w-full max-w-[92%] sm:max-w-[85%]">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-[#786C5E] mb-2 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-[#D97706]" />
                      <span>Suggested next steps (click to explore):</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {msg.choices.map((choice) => (
                        <button
                          key={choice.id}
                          onClick={() => handleChoice(choice.id)}
                          className="storybook-choice-btn text-xs py-2 px-3 rounded-xl flex items-center gap-1.5 bg-[#FFFDF9] hover:bg-[#FEF3C7] border border-[#E7DEC8] hover:border-[#D97706] transition-all hover:scale-102"
                        >
                          <span className="font-medium text-[#2A2118]">{choice.label}</span>
                          <ChevronRight className="w-3 h-3 text-[#786C5E]" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex items-center gap-2.5 text-xs text-[#786C5E] pl-2 py-2">
              <div
                className="w-6 h-6 rounded-full overflow-hidden border border-[#D97706] bg-[#FFFDF9] flex items-center justify-center shrink-0"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={session?.persona_avatar || "/avatars/shivaji-maharaj.png"}
                  alt="Avatar"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex items-center gap-2 bg-[#FFFDF9] px-3 py-2 rounded-xl border border-[#E7DEC8] shadow-2xs">
                <div className="dot-pulse">
                  <span style={{ background: "#D97706" }} />
                  <span style={{ background: "#D97706" }} />
                  <span style={{ background: "#D97706" }} />
                </div>
                <span className="animate-pulse font-medium">Unfolding history from textbook...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* ── Sticky Bottom Composer ── */}
      <footer className="sticky bottom-0 z-30 bg-[#FAF7F0]/95 backdrop-blur-md border-t border-[#E7DEC8] px-3 sm:px-6 py-3 shrink-0 shadow-lg">
        <div className="max-w-3xl mx-auto flex flex-col gap-1.5">
          {session?.can_resume_lesson && (
            <div className="flex items-center justify-between pb-1">
              <span className="text-[11px] text-[#786C5E]">
                Currently answering a custom question.
              </span>
              <button
                onClick={handleReturnToLesson}
                disabled={loading}
                className="text-[11px] font-bold text-[#B45309] hover:underline flex items-center gap-1"
              >
                <ArrowLeft className="w-3 h-3" />
                <span>Return to Ongoing Story</span>
              </button>
            </div>
          )}

          <form onSubmit={handleSend} className="relative flex items-end gap-2">
            <div className="relative flex-1">
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={handleTextareaChange}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                rows={1}
                placeholder="Ask anything about this topic or the textbook... (e.g., 'How strong was Shivaji?')"
                className="w-full resize-none max-h-32 px-3.5 py-2.5 pr-10 rounded-xl border border-[#D4C3A3] bg-[#FFFDF9] text-sm text-[#2A2118] placeholder-[#9A8D7E] focus:outline-none focus:ring-2 focus:ring-[#D97706]/40 focus:border-[#D97706] shadow-2xs"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || loading}
                className="absolute right-2.5 bottom-2.5 p-1.5 rounded-lg bg-[#2A2118] text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#433626] transition-colors shadow-2xs"
                title="Send message (Enter)"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>

          <div className="flex items-center justify-between text-[10px] text-[#9A8D7E] px-1">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <span>Grounded in complete Maharashtra State Board History textbook</span>
          </div>
        </div>
      </footer>

      {/* ── Curriculum Map Drawer / Modal ── */}
      {showMapModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="storybook-card w-full max-w-2xl max-h-[85vh] flex flex-col bg-[#FAF7F0] border-2 border-[#D4C3A3] overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-4 border-b border-[#E7DEC8] flex items-center justify-between bg-[#FFFDF9]">
              <div className="flex items-center gap-2">
                <Compass className="w-4 h-4 text-[#D97706]" />
                <div>
                  <h3 className="text-sm font-bold text-[#2A2118]">
                    History Curriculum Roadmap
                  </h3>
                  <p className="text-[11px] text-[#6E5F4E]">
                    All 18 lessons from &ldquo;Shivachhatrapati&rdquo; textbook
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowMapModal(false)}
                className="p-1 rounded-lg hover:bg-[#F3EFE6] text-[#786C5E]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Lessons List */}
            <div className="p-4 overflow-y-auto space-y-2 flex-1">
              {curriculumMap.map((node) => {
                const isCurrent = session?.current_lesson_id === node.id;
                const isCompleted = session?.completed_lessons.includes(node.id);

                return (
                  <div
                    key={node.id}
                    onClick={() => handleSelectLesson(node.id)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                      isCurrent
                        ? "border-[#D97706] bg-[#FEF3C7] shadow-2xs"
                        : "border-[#E7DEC8] bg-[#FFFDF9] hover:bg-[#F5EFEB]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${
                          isCompleted
                            ? "bg-[#059669] text-white"
                            : isCurrent
                            ? "bg-[#D97706] text-white"
                            : "bg-[#EAE2D2] text-[#6E5F4E]"
                        }`}
                      >
                        {isCompleted ? <Check className="w-3.5 h-3.5" /> : node.lesson_number}
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <h4 className="text-xs font-bold text-[#2A2118] truncate">
                            {node.title}
                          </h4>
                          {node.persona === "SHIVAJI" && (
                            <span className="text-[9px] uppercase font-bold text-[#B45309] bg-[#FEF3C7] px-1 py-0.2 rounded border border-[#FCD34D]">
                              Shivaji
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#786C5E] line-clamp-1 mt-0.5">
                          {node.summary}
                        </p>
                      </div>
                    </div>

                    <div className="text-right text-[11px] text-[#786C5E] shrink-0 ml-2">
                      <span>PDF P.{node.pdf_pages[0]}&ndash;{node.pdf_pages[1]}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-[#E7DEC8] bg-[#FFFDF9] text-right">
              <button
                onClick={() => setShowMapModal(false)}
                className="px-3.5 py-1.5 rounded-lg border border-[#D4C3A3] text-xs font-semibold text-[#6E5F4E] hover:bg-[#F3EFE6]"
              >
                Close Roadmap
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
