"use client";

import { useState } from "react";
import {
  MessageSquare,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
  Sparkles,
  BookOpen,
  Lock,
} from "lucide-react";
import { SinglePersonaAvatar } from "@/components/Avatar";
import type { SavedConversation } from "@/lib/chatStorage";

interface ChatSidebarProps {
  conversations: SavedConversation[];
  activeConversationId?: string;
  onSelectConversation: (conv: SavedConversation) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => void;
  onChangeGuide: () => void;
  scopeTitle: string;
  scopeSubtitle: string;
  currentPersonaName: string;
  currentPersonaAvatar?: string;
  subjectId: string;
}

export default function ChatSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  onChangeGuide,
  scopeTitle,
  scopeSubtitle,
  currentPersonaName,
  currentPersonaAvatar,
  subjectId,
}: ChatSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <div className="bg-slate-900 border-r border-slate-800 p-2 flex flex-col items-center justify-between z-40 transition-all w-14 flex-shrink-0">
        <div className="flex flex-col items-center gap-3 w-full">
          <button
            onClick={() => setCollapsed(false)}
            className="p-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Open conversation history"
          >
            <PanelLeftOpen size={18} />
          </button>
          <button
            onClick={onNewChat}
            className="p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-500 transition-colors shadow-sm"
            title="Start new chat"
          >
            <Plus size={18} />
          </button>
        </div>

        <div className="mb-2">
          <SinglePersonaAvatar
            src={currentPersonaAvatar}
            name={currentPersonaName}
            subjectId={subjectId}
            size={32}
          />
        </div>
      </div>
    );
  }

  return (
    <aside className="w-72 bg-slate-900 text-slate-100 border-r border-slate-800 flex flex-col flex-shrink-0 h-full z-40 transition-all select-none">
      {/* Sidebar Header */}
      <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400">
            <BookOpen size={16} />
          </span>
          <div className="min-w-0">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider truncate">
              {scopeTitle}
            </h2>
            <p className="text-[11px] text-slate-400 truncate">{scopeSubtitle}</p>
          </div>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title="Collapse sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      {/* Primary Actions: New Chat & Active Guide Lock */}
      <div className="p-3 space-y-2 border-b border-slate-800">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-xs transition-colors"
        >
          <Plus size={15} />
          <span>New Chat</span>
        </button>

        {/* Current Locked Persona info */}
        <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <SinglePersonaAvatar
              src={currentPersonaAvatar}
              name={currentPersonaName}
              subjectId={subjectId}
              size={30}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-xs font-bold text-slate-100 truncate">
                  {currentPersonaName}
                </span>
                <span title="Persona locked to conversation" className="text-amber-400">
                  <Lock size={10} />
                </span>
              </div>
              <span className="text-[10px] text-slate-400 block">Active Guide</span>
            </div>
          </div>
          <button
            onClick={onChangeGuide}
            className="text-[10px] font-semibold text-blue-400 hover:text-blue-300 px-2 py-1 rounded bg-slate-700/60 hover:bg-slate-700 transition-colors flex-shrink-0"
            title="Start a new chat with a different guide"
          >
            Change
          </button>
        </div>
      </div>

      {/* Conversation History List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <div className="px-2 py-1 text-[10px] font-bold tracking-wider text-slate-400 uppercase">
          Scoped Chat History
        </div>

        {conversations.length === 0 ? (
          <div className="py-8 px-3 text-center text-slate-500 text-xs">
            <MessageSquare className="w-6 h-6 mx-auto mb-2 opacity-40" />
            <p>No previous conversations in this scope.</p>
            <p className="text-[10px] mt-1 text-slate-400">Ask a question to start!</p>
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === activeConversationId;
            return (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv)}
                className={`group flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl cursor-pointer text-xs transition-all ${
                  isActive
                    ? "bg-slate-800 text-white font-medium shadow-xs border border-slate-700"
                    : "text-slate-300 hover:bg-slate-800/50 hover:text-white"
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <SinglePersonaAvatar
                    src={conv.personaAvatar}
                    name={conv.personaName}
                    subjectId={subjectId}
                    size={22}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs leading-tight">{conv.title}</p>
                    <span className="text-[10px] text-slate-400 font-normal">
                      {conv.personaName}
                    </span>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-red-400 transition-all"
                  title="Delete chat"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer info */}
      <div className="p-3 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
        <span>VidyaVerse Persona System</span>
        <span className="font-semibold text-slate-400">Part 05</span>
      </div>
    </aside>
  );
}
