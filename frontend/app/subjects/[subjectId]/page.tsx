"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  MessageCircle,
  Sparkles,
  Layers,
  FileText,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Shield,
  Compass,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import PersonaSelectionModal from "@/components/personas/PersonaSelectionModal";
import { api } from "@/lib/api";
import type { Subject, Chapter } from "@/types";

function SubjectDashboardContent() {
  const params = useParams();
  const router = useRouter();
  const subjectId = (params.subjectId as string) || "history";

  const [subject, setSubject] = useState<Subject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Persona Selection Modal State
  const [personaModalOpen, setPersonaModalOpen] = useState(false);
  const [targetChapter, setTargetChapter] = useState<{ id?: string; title?: string }>({});

  useEffect(() => {
    async function loadSubject() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getSubject(subjectId);
        setSubject(data);
      } catch (err: any) {
        console.error("Failed to load subject:", err);
        setError(err.message || "Failed to load subject");
      } finally {
        setLoading(false);
      }
    }
    loadSubject();
  }, [subjectId]);

  const handleStartSubjectChat = () => {
    setTargetChapter({});
    setPersonaModalOpen(true);
  };

  const handleStartChapterChat = (chapter: Chapter) => {
    setTargetChapter({ id: chapter.chapter_id, title: chapter.title });
    setPersonaModalOpen(true);
  };

  const handlePersonaSelected = (personaId: string) => {
    if (targetChapter.id) {
      // Navigate to chapter chat with persona
      router.push(`/chat/${targetChapter.id}?persona=${personaId}&subject=${subjectId}`);
    } else {
      // Navigate to subject-wide chat
      if (subjectId.toLowerCase() === "history" && personaId === "shivaji_maharaj") {
        router.push("/subjects/history/story");
      } else {
        router.push(`/chat/subject/${subjectId}?persona=${personaId}`);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        <Navbar />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center space-y-3">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-semibold text-slate-600">Loading Subject Catalogue...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !subject) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        <Navbar />
        <div className="flex-1 max-w-xl mx-auto px-4 py-16 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto text-2xl font-bold">
            ⚠️
          </div>
          <h2 className="text-xl font-bold text-slate-900">Subject Not Found</h2>
          <p className="text-sm text-slate-600">{error || "The requested subject is not configured."}</p>
          <a
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft size={16} /> Return to Classroom
          </a>
        </div>
      </div>
    );
  }

  const isHistory = subject.subject_id.toLowerCase() === "history";
  const isMaths = subject.subject_id.toLowerCase() === "mathematics";
  const isEvs = subject.subject_id.toLowerCase() === "evs";

  const themeClasses = isHistory
    ? {
        accent: "text-amber-800",
        badgeBg: "bg-amber-100 text-amber-900 border-amber-300",
        btnPrimary: "bg-amber-700 hover:bg-amber-800 text-white",
        btnSecondary: "bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300",
        panelBg: "bg-amber-50/40 border-amber-200/80",
      }
    : isMaths
    ? {
        accent: "text-blue-800",
        badgeBg: "bg-blue-100 text-blue-900 border-blue-300",
        btnPrimary: "bg-blue-600 hover:bg-blue-700 text-white",
        btnSecondary: "bg-blue-50 hover:bg-blue-100 text-blue-900 border border-blue-300",
        panelBg: "bg-blue-50/30 border-blue-200/80",
      }
    : {
        accent: "text-emerald-800",
        badgeBg: "bg-emerald-100 text-emerald-900 border-emerald-300",
        btnPrimary: "bg-emerald-700 hover:bg-emerald-800 text-white",
        btnSecondary: "bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-300",
        panelBg: "bg-emerald-50/30 border-emerald-200/80",
      };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex flex-col">
        {/* Breadcrumb Bar */}
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-4">
          <a href="/" className="hover:text-blue-600 flex items-center gap-1 transition-colors">
            <ArrowLeft size={14} /> Classroom Dashboard
          </a>
          <span>/</span>
          <span className="text-slate-900 font-bold">{subject.name}</span>
        </div>

        {/* 2-Panel Split Layout (Cover on Left, Scrollable Chapters on Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start flex-1">
          {/* ── LEFT PANEL: Subject Identity & Authentic Book Cover ── */}
          <div
            className={`lg:col-span-5 rounded-3xl p-6 border-2 shadow-xs space-y-6 lg:sticky lg:top-20 ${themeClasses.panelBg}`}
          >
            {/* Book Cover Image */}
            <div className="w-full flex justify-center">
              <div className="w-56 sm:w-64 aspect-[3/4] rounded-2xl overflow-hidden shadow-xl border-4 border-white bg-slate-200 relative group">
                {subject.cover_image ? (
                  <img
                    src={subject.cover_image}
                    alt={`${subject.name} Textbook Cover`}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-102"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-5xl">
                    {subject.icon}
                  </div>
                )}
              </div>
            </div>

            {/* Subject Metadata */}
            <div className="space-y-3 text-center sm:text-left">
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${themeClasses.badgeBg}`}>
                  Standard {subject.standard}
                </span>
                {subject.textbook_part && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-white text-slate-700 border border-slate-200">
                    {subject.textbook_part}
                  </span>
                )}
              </div>

              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center justify-center sm:justify-start gap-2">
                  <span>{subject.icon}</span> {subject.name}
                </h1>
                <p className="text-sm font-semibold text-slate-700 italic mt-0.5">
                  {subject.textbook_title}
                </p>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {subject.description}
              </p>

              {/* Master Book Metrics */}
              <div className="grid grid-cols-2 gap-2 pt-2 text-center text-xs">
                <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 shadow-2xs">
                  <span className="text-[10px] text-slate-400 block uppercase font-bold">Total Lessons</span>
                  <span className="text-base font-extrabold text-slate-900">{subject.chapters.length}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 shadow-2xs">
                  <span className="text-[10px] text-slate-400 block uppercase font-bold">Textbook Pages</span>
                  <span className="text-base font-extrabold text-slate-900">{subject.source_page_count || "Full"}</span>
                </div>
              </div>
            </div>

            {/* Prominent Subject-Wide Chat Button */}
            <div className="space-y-2 pt-2">
              <button
                onClick={handleStartSubjectChat}
                className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm shadow-md flex items-center justify-center gap-2 transition-all ${themeClasses.btnPrimary}`}
              >
                <MessageCircle size={18} />
                <span>Chat with Entire {subject.name} Subject</span>
              </button>

              {isHistory && (
                <a
                  href="/subjects/history/story"
                  className={`w-full py-2.5 px-4 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${themeClasses.btnSecondary}`}
                >
                  <Sparkles size={15} />
                  <span>Launch Guided Shivaji Maharaj Story Journey</span>
                </a>
              )}
            </div>
          </div>

          {/* ── RIGHT PANEL: Chapter Explorer (Independently Scrollable) ── */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div>
                <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <Layers size={20} className="text-slate-600" />
                  <span>Chapter Explorer</span>
                </h2>
                <p className="text-xs text-slate-500">
                  {subject.chapters.length} verified chapters with isolated citations & dedicated learning guides
                </p>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                100% Manifest Verified
              </span>
            </div>

            {/* Scrollable Chapter List Container */}
            <div className="space-y-3 lg:max-h-[calc(100vh-180px)] lg:overflow-y-auto pr-1">
              {subject.chapters.map((ch) => {
                const chapterOverviewUrl = `/subjects/${subjectId}/chapters/${ch.chapter_id}`;

                return (
                  <div
                    key={ch.chapter_id}
                    className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-2xs hover:border-blue-300 hover:shadow-xs transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
                  >
                    {/* Chapter Info */}
                    <div className="flex items-start gap-3.5 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 text-slate-800 font-extrabold text-sm flex items-center justify-center flex-shrink-0 group-hover:bg-blue-50 group-hover:text-blue-700 group-hover:border-blue-200 transition-colors">
                        {String(ch.chapter_number).padStart(2, "0")}
                      </div>

                      <div className="flex-1 min-w-0 space-y-1">
                        <a
                          href={chapterOverviewUrl}
                          className="text-sm font-bold text-slate-900 hover:text-blue-600 transition-colors block leading-snug truncate"
                        >
                          {ch.title}
                        </a>

                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 font-medium">
                          {ch.printed_book_page_start && (
                            <span>
                              Book pp. {ch.printed_book_page_start}–{ch.printed_book_page_end}
                            </span>
                          )}
                          {ch.source_pdf_page_start_1based && (
                            <>
                              <span>•</span>
                              <span>
                                PDF pp. {ch.source_pdf_page_start_1based}–{ch.source_pdf_page_end_1based}
                              </span>
                            </>
                          )}
                          <span>•</span>
                          <span className="text-emerald-700 font-semibold flex items-center gap-0.5">
                            <CheckCircle2 size={11} /> AI-Ready
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="flex items-center gap-2 self-end sm:self-center flex-shrink-0">
                      <a
                        href={chapterOverviewUrl}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                      >
                        Overview
                      </a>
                      <button
                        onClick={() => handleStartChapterChat(ch)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold shadow-2xs flex items-center gap-1 transition-all ${themeClasses.btnPrimary}`}
                      >
                        <MessageCircle size={13} />
                        <span>Chat</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>

      {/* Persona Selection Modal */}
      <PersonaSelectionModal
        isOpen={personaModalOpen}
        onClose={() => setPersonaModalOpen(false)}
        subjectId={subject.subject_id}
        subjectName={subject.name}
        chapterId={targetChapter.id}
        chapterTitle={targetChapter.title}
        onSelectPersona={handlePersonaSelected}
      />
    </div>
  );
}

export default function SubjectDashboard() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Subject Dashboard...</div>}>
      <SubjectDashboardContent />
    </Suspense>
  );
}
