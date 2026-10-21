"use client";

import { useEffect, useState } from "react";
import {
  BookOpen,
  ArrowRight,
  Sparkles,
  GraduationCap,
  Clock,
  MessageCircle,
  Shield,
  Layers,
  CheckCircle2,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api } from "@/lib/api";
import type { Subject } from "@/types";

interface RecentChat {
  id: string;
  title: string;
  subjectId: string;
  subjectName: string;
  chapterTitle?: string;
  personaName: string;
  lastActive: string;
  href: string;
}

export default function ClassroomDashboard() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [recentChats, setRecentChats] = useState<RecentChat[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        const subData = await api.getSubjects();
        setSubjects(subData);
      } catch (err) {
        console.error("Failed to load subjects:", err);
      } finally {
        setLoading(false);
      }

      // Load any existing session from localStorage
      try {
        const chats: RecentChat[] = [];
        const savedHistorySession = localStorage.getItem("history_session_id");
        if (savedHistorySession) {
          chats.push({
            id: savedHistorySession,
            title: "Guided Swaraj Journey",
            subjectId: "history",
            subjectName: "History",
            personaName: "Chhatrapati Shivaji Maharaj",
            lastActive: "Active Session",
            href: "/subjects/history/story",
          });
        }
        setRecentChats(chats);
      } catch {}
    }
    loadData();
  }, []);

  const subjectMeta: Record<
    string,
    {
      badge: string;
      colorClass: string;
      btnBg: string;
      tagline: string;
      href: string;
      icon: string;
    }
  > = {
    history: {
      badge: "Standard IV · Environmental Studies Part Two",
      colorClass: "border-amber-200 hover:border-amber-400 bg-amber-50/30",
      btnBg: "bg-amber-700 hover:bg-amber-800",
      tagline: "Explore Swaraj, forts, battles & Maharashtra's saints through first-person historical storytelling.",
      href: "/subjects/history",
      icon: "⚔️",
    },
    mathematics: {
      badge: "Standard X · Part II (Geometry)",
      colorClass: "border-blue-200 hover:border-blue-400 bg-blue-50/30",
      btnBg: "bg-blue-600 hover:bg-blue-700",
      tagline: "Master similarity, circle theorems, coordinate geometry & trigonometry with visual proofs.",
      href: "/subjects/mathematics",
      icon: "📐",
    },
    evs: {
      badge: "Standard V · Environmental Studies Part Two",
      colorClass: "border-emerald-200 hover:border-emerald-400 bg-emerald-50/30",
      btnBg: "bg-emerald-700 hover:bg-emerald-800",
      tagline: "Investigate human origins, stone age tools, settled agriculture & early urban river civilizations.",
      href: "/subjects/evs",
      icon: "🏺",
    },
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-10">
        {/* Welcome Hero Area */}
        <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-3xl p-6 sm:p-10 text-white shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-200 text-xs font-semibold">
              <Sparkles size={14} />
              <span>Offline-First Educational Learning Hub</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Ready to explore?</h1>
            <p className="text-base text-slate-200 leading-relaxed">
              Choose a subject and continue your learning journey. Learn from authentic textbooks with interactive
              AI guides, verified chapter citations, and step-by-step visual lessons.
            </p>
          </div>
        </div>

        {/* Subjects Grid */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Select a Subject</h2>
              <p className="text-xs text-slate-500">Curriculum-aligned complete textbooks with verified chapter manifests</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-200 text-slate-700 rounded-lg">
              3 Subjects Available
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {loading ? (
              [1, 2, 3].map((i) => (
                <div key={i} className="h-80 bg-white rounded-2xl border border-slate-200 animate-pulse p-6" />
              ))
            ) : (
              subjects.map((sub) => {
                const subKey = sub.subject_id.toLowerCase();
                const meta = subjectMeta[subKey] || {
                  badge: `Standard ${sub.standard || "V"}`,
                  colorClass: "border-slate-200 hover:border-slate-300",
                  btnBg: "bg-blue-600 hover:bg-blue-700",
                  tagline: sub.description || "Interactive textbook learning.",
                  href: `/subjects/${subKey}`,
                  icon: sub.icon || "📚",
                };

                return (
                  <div
                    key={sub.subject_id}
                    className={`classroom-card p-5 rounded-2xl border-2 transition-all duration-200 hover:shadow-lg flex flex-col justify-between ${meta.colorClass}`}
                  >
                    <div>
                      {/* Top Bar with Book Cover thumbnail & Subject Title */}
                      <div className="flex items-start gap-4">
                        <div className="w-18 h-24 rounded-lg overflow-hidden bg-slate-200 shadow-sm border border-slate-300/80 flex-shrink-0 relative">
                          {sub.cover_image ? (
                            <img
                              src={sub.cover_image}
                              alt={sub.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-2xl">
                              {meta.icon}
                            </div>
                          )}
                        </div>

                        <div className="flex-1 min-w-0">
                          <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                            {meta.badge}
                          </span>
                          <h3 className="text-lg font-bold text-slate-900 truncate flex items-center gap-1.5">
                            <span>{meta.icon}</span> {sub.name}
                          </h3>
                          <p className="text-xs font-semibold text-slate-600 italic truncate mt-0.5">
                            {sub.textbook_title}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700">
                              <Layers size={11} /> {sub.chapters?.length || 0} Lessons
                            </span>
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700">
                              <CheckCircle2 size={11} /> Verified
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-xs text-slate-600 mt-4 leading-relaxed line-clamp-3">
                        {meta.tagline}
                      </p>
                    </div>

                    {/* Action Button */}
                    <div className="mt-5 pt-4 border-t border-slate-200/60">
                      <a
                        href={meta.href}
                        className={`w-full py-2.5 px-4 rounded-xl text-white font-bold text-sm shadow-xs flex items-center justify-center gap-2 transition-all ${meta.btnBg}`}
                      >
                        <span>Open {sub.name}</span>
                        <ArrowRight size={16} />
                      </a>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* Continue Learning Section */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Clock size={18} className="text-slate-500" /> Continue Learning
            </h2>
          </div>

          {recentChats.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recentChats.map((chat) => (
                <div
                  key={chat.id}
                  className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between hover:border-blue-300 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-lg">
                      ⚔️
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{chat.title}</h4>
                      <p className="text-xs text-slate-500">
                        {chat.subjectName} · Guide: <span className="font-medium text-slate-700">{chat.personaName}</span>
                      </p>
                    </div>
                  </div>
                  <a
                    href={chat.href}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
                  >
                    Resume
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500 space-y-2">
              <MessageCircle size={28} className="mx-auto text-slate-400" />
              <p className="text-sm font-semibold text-slate-700">No active conversations yet.</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Select one of the three subjects above to start exploring lessons, chatting with historical or scientific
                guides, and solving practice questions!
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
