"use client";

import Link from "next/navigation";
import { useEffect, useState } from "react";
import { BookOpen, Sparkles, GraduationCap, Compass, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

export default function Navbar() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const h = await api.health();
        setBackendOk(h.status === "ok");
      } catch {
        setBackendOk(false);
      }
    }
    checkHealth();
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <a href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <GraduationCap size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">Learning Hub</span>
              <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                Offline
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">Textbook-Grounded Interactive Learning</p>
          </div>
        </a>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-1 sm:gap-2">
          <a
            href="/"
            className="px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-700 hover:text-blue-600 hover:bg-slate-100 transition-colors"
          >
            Classroom
          </a>
          <a
            href="/subjects/history"
            className="px-3 py-1.5 rounded-lg text-sm font-semibold text-amber-800 hover:bg-amber-50 transition-colors flex items-center gap-1.5"
          >
            <span>⚔️</span> History
          </a>
          <a
            href="/subjects/mathematics"
            className="px-3 py-1.5 rounded-lg text-sm font-semibold text-blue-800 hover:bg-blue-50 transition-colors flex items-center gap-1.5"
          >
            <span>📐</span> Mathematics
          </a>
          <a
            href="/subjects/evs"
            className="px-3 py-1.5 rounded-lg text-sm font-semibold text-emerald-800 hover:bg-emerald-50 transition-colors flex items-center gap-1.5"
          >
            <span>🏺</span> Environmental Studies
          </a>
        </nav>

        {/* Status Pill */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              backendOk === true
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : backendOk === false
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : "bg-slate-100 text-slate-600 border-slate-200"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendOk === true ? "bg-emerald-500 animate-pulse" : backendOk === false ? "bg-rose-500" : "bg-slate-400"
              }`}
            />
            <span>{backendOk === true ? "Engine Ready" : backendOk === false ? "Engine Offline" : "Checking..."}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
