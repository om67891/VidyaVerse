"use client";

import { useEffect, useState } from "react";
import { X, Sparkles, UserCheck, BookOpen, Compass, Check } from "lucide-react";
import { api } from "@/lib/api";
import type { Persona } from "@/types";

interface PersonaSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  subjectId: string;
  subjectName: string;
  chapterId?: string;
  chapterTitle?: string;
  onSelectPersona: (personaId: string) => void;
}

export default function PersonaSelectionModal({
  isOpen,
  onClose,
  subjectId,
  subjectName,
  chapterId,
  chapterTitle,
  onSelectPersona,
}: PersonaSelectionModalProps) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    async function load() {
      setLoading(true);
      try {
        const data = await api.getPersonas(subjectId, chapterId);
        setPersonas(data);
        if (data.length > 0 && !selectedId) {
          setSelectedId(data[0].persona_id);
        }
      } catch (err) {
        console.error("Failed to load personas:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [isOpen, subjectId, chapterId]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (selectedId) {
      onSelectPersona(selectedId);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-blue-100 text-blue-700">
                <Sparkles size={16} />
              </span>
              <h2 className="text-lg font-bold text-slate-900">Choose Your Learning Guide</h2>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              {chapterTitle ? (
                <>For <span className="font-semibold text-slate-800">{chapterTitle}</span> ({subjectName})</>
              ) : (
                <>For <span className="font-semibold text-slate-800">{subjectName}</span> (Subject-wide learning)</>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-3">
          {loading ? (
            <div className="py-12 text-center text-slate-500">
              <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm font-medium">Discovering registered guides...</p>
            </div>
          ) : personas.length === 0 ? (
            <div className="py-8 text-center text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <p className="text-sm">Default AI Subject Tutor will guide this session.</p>
            </div>
          ) : (
            personas.map((persona) => {
              const isSelected = selectedId === persona.persona_id;
              const matchesTopic =
                chapterTitle &&
                persona.primary_topics.some(
                  (t) =>
                    t.toLowerCase().includes(chapterTitle.toLowerCase()) ||
                    chapterTitle.toLowerCase().includes(t.toLowerCase())
                );

              return (
                <div
                  key={persona.persona_id}
                  onClick={() => setSelectedId(persona.persona_id)}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-4 ${
                    isSelected
                      ? "border-blue-600 bg-blue-50/60 shadow-xs ring-2 ring-blue-500/20"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  {/* Avatar / Portrait */}
                  <div className="w-13 h-13 rounded-xl bg-slate-100 border border-slate-200 overflow-hidden flex-shrink-0 flex items-center justify-center relative">
                    {persona.avatar_url ? (
                      <img
                        src={persona.avatar_url}
                        alt={persona.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = "none";
                        }}
                      />
                    ) : (
                      <span className="text-xl">🎓</span>
                    )}
                  </div>

                  {/* Persona Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-base font-bold text-slate-900 truncate">{persona.name}</h3>
                      {matchesTopic && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          Recommended for this chapter
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider block mt-0.5">
                      {persona.persona_type.replace(/_/g, " ")}
                    </span>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{persona.card_summary}</p>

                    {persona.primary_topics && persona.primary_topics.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {persona.primary_topics.slice(0, 3).map((topic, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-600"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Radio Check Indicator */}
                  <div className="pt-1">
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center border transition-colors ${
                        isSelected ? "bg-blue-600 border-blue-600 text-white" : "border-slate-300 bg-white"
                      }`}
                    >
                      {isSelected && <Check size={12} strokeWidth={3} />}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Selected guide identity is locked for the duration of this conversation.
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-200/50 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selectedId}
              className="px-5 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl shadow-xs transition-colors"
            >
              Start Learning Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
