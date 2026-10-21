"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  MessageCircle,
  Sparkles,
  BookOpen,
  CheckCircle2,
  ListOrdered,
  Lightbulb,
  Compass,
  Layers,
  Clock,
  ChevronRight,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import PersonaSelectionModal from "@/components/personas/PersonaSelectionModal";
import { api } from "@/lib/api";
import type { Subject, Chapter } from "@/types";

function ChapterOverviewContent() {
  const params = useParams();
  const router = useRouter();
  const subjectId = (params.subjectId as string) || "history";
  const chapterId = (params.chapterId as string) || "";

  const [subject, setSubject] = useState<Subject | null>(null);
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Persona Modal State
  const [personaModalOpen, setPersonaModalOpen] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [subData, chData] = await Promise.all([
          api.getSubject(subjectId),
          api.getChapter(chapterId),
        ]);
        setSubject(subData);
        setChapter(chData);
      } catch (err: any) {
        console.error("Failed to load chapter overview:", err);
        setError(err.message || "Failed to load chapter data");
      } finally {
        setLoading(false);
      }
    }
    if (chapterId) loadData();
  }, [subjectId, chapterId]);

  const handleStartChat = () => {
    setPersonaModalOpen(true);
  };

  const handlePersonaSelected = (personaId: string) => {
    router.push(`/chat/${chapterId}?persona=${personaId}&subject=${subjectId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        <Navbar />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center space-y-3">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-semibold text-slate-600">Loading Chapter Overview...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !chapter || !subject) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        <Navbar />
        <div className="flex-1 max-w-xl mx-auto px-4 py-16 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto text-2xl font-bold">
            ⚠️
          </div>
          <h2 className="text-xl font-bold text-slate-900">Chapter Not Found</h2>
          <p className="text-sm text-slate-600">{error || "Could not resolve chapter metadata."}</p>
          <a
            href={`/subjects/${subjectId}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft size={16} /> Return to {subject?.name || "Subject"}
          </a>
        </div>
      </div>
    );
  }

  const isHistory = subject.subject_id.toLowerCase() === "history";
  const isMaths = subject.subject_id.toLowerCase() === "mathematics";
  const isEvs = subject.subject_id.toLowerCase() === "evs";

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full space-y-6">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <a href="/" className="hover:text-blue-600 transition-colors">Classroom</a>
          <span>/</span>
          <a href={`/subjects/${subjectId}`} className="hover:text-blue-600 transition-colors">{subject.name}</a>
          <span>/</span>
          <span className="text-slate-900 font-bold truncate">Chapter {chapter.chapter_number}</span>
        </div>

        {/* Chapter Header Banner */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
                Chapter {chapter.chapter_number}
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700">
                Standard {subject.standard}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
              {chapter.printed_book_page_start && (
                <span>Textbook Book pp. {chapter.printed_book_page_start}–{chapter.printed_book_page_end}</span>
              )}
              {chapter.source_pdf_page_start_1based && (
                <>
                  <span>•</span>
                  <span>Physical PDF pp. {chapter.source_pdf_page_start_1based}–{chapter.source_pdf_page_end_1based}</span>
                </>
              )}
            </div>
          </div>

          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {chapter.title}
            </h1>
            <p className="text-sm font-medium text-slate-600 mt-1">
              From textbook: <span className="italic">{subject.textbook_title}</span> ({subject.textbook_part})
            </p>
          </div>

          {/* Primary Action Button */}
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              onClick={handleStartChat}
              className="py-3 px-6 rounded-xl font-bold text-sm bg-blue-600 hover:bg-blue-700 text-white shadow-xs flex items-center gap-2 transition-all"
            >
              <MessageCircle size={18} />
              <span>Start Chapter Chat</span>
            </button>
            <a
              href={`/subjects/${subjectId}`}
              className="py-3 px-5 rounded-xl font-semibold text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              Back to Chapter Explorer
            </a>
          </div>
        </div>

        {/* Visual Topic Diagram / Illustration Card */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Lightbulb size={20} className="text-amber-500" />
            <span>Visual Concept & Learning Overview</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            {/* Visual Graphic */}
            <div className="md:col-span-5 bg-slate-50 rounded-2xl p-6 border border-slate-200/80 flex items-center justify-center min-h-[220px]">
              {isMaths ? (
                /* Programmatic SVG diagram for Mathematics */
                <svg viewBox="0 0 200 160" className="w-48 h-40 text-blue-600">
                  <polygon points="30,130 170,130 30,30" fill="none" stroke="currentColor" strokeWidth="3" />
                  <rect x="30" y="115" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" />
                  <text x="18" y="85" fontSize="11" fontWeight="bold" fill="#1E293B">a</text>
                  <text x="100" y="146" fontSize="11" fontWeight="bold" fill="#1E293B">b</text>
                  <text x="108" y="75" fontSize="11" fontWeight="bold" fill="#2563EB">c</text>
                  <text x="65" y="25" fontSize="10" fontStyle="italic" fill="#64748B">a² + b² = c²</text>
                </svg>
              ) : isHistory ? (
                /* History illustration preview */
                <div className="text-center space-y-2">
                  <div className="w-16 h-16 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center text-3xl mx-auto shadow-2xs">
                    ⚔️
                  </div>
                  <p className="text-xs font-bold text-amber-900">Historical Scene & Swaraj Fort</p>
                  <p className="text-[11px] text-slate-500">First-person narration with Chhatrapati Shivaji Maharaj</p>
                </div>
              ) : (
                /* EVS illustration preview */
                <div className="text-center space-y-2">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center text-3xl mx-auto shadow-2xs">
                    🏺
                  </div>
                  <p className="text-xs font-bold text-emerald-900">Archaeological & Evolutionary Evidence</p>
                  <p className="text-[11px] text-slate-500">How We Came to Be · Standard V</p>
                </div>
              )}
            </div>

            {/* Core Objectives */}
            <div className="md:col-span-7 space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Chapter Learning Objectives</h3>
              <ul className="space-y-2 text-xs text-slate-700">
                <li className="flex items-start gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Study official textbook concepts with page-isolated citations and verified summaries.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Interact with dedicated domain guides and subject mentors tailored to this chapter.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Practice textbook knowledge checks and problem-solving exercises grounded in original source material.</span>
                </li>
              </ul>

              <div className="pt-2">
                <span className="text-[11px] text-slate-500 font-medium">
                  Verified PDF source: <code className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 font-mono text-[10px]">{chapter.pdf_filename || "chapter.pdf"}</code>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Prior Conversations for this Chapter */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Clock size={16} className="text-slate-500" />
              <span>Previous Conversations for this Chapter</span>
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Independent chat histories are preserved separately for this chapter.
          </p>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
            Click <strong className="text-slate-700">Start Chapter Chat</strong> to begin a new conversation.
          </div>
        </div>
      </main>

      {/* Persona Selection Modal */}
      <PersonaSelectionModal
        isOpen={personaModalOpen}
        onClose={() => setPersonaModalOpen(false)}
        subjectId={subject.subject_id}
        subjectName={subject.name}
        chapterId={chapter.chapter_id}
        chapterTitle={chapter.title}
        onSelectPersona={handlePersonaSelected}
      />
    </div>
  );
}

export default function ChapterOverviewPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Chapter Overview...</div>}>
      <ChapterOverviewContent />
    </Suspense>
  );
}
