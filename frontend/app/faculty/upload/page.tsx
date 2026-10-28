"use client";

import { useEffect, useState, useRef, ChangeEvent, DragEvent } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  Trash2,
  RefreshCw,
  MessageCircle,
  ArrowRight,
  ShieldAlert,
  Layers,
  BookOpen,
  Sparkles,
  ChevronRight,
  Check,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api } from "@/lib/api";
import type { UploadedResource, Subject } from "@/types";

interface SubjectOption {
  id: string;
  name: string;
  defaultClass: number;
  icon: string;
  color: string;
}

const AVAILABLE_SUBJECTS: SubjectOption[] = [
  { id: "evs", name: "Environmental Studies", defaultClass: 5, icon: "🏺", color: "emerald" },
  { id: "history", name: "History (Shivachhatrapati)", defaultClass: 4, icon: "⚔️", color: "amber" },
  { id: "mathematics", name: "Mathematics (Part II)", defaultClass: 10, icon: "📐", color: "blue" },
];

export default function FacultyUploadPage() {
  // Form State
  const [selectedSubject, setSelectedSubject] = useState<string>("evs");
  const [classNumber, setClassNumber] = useState<number>(5);
  const [chapterNumber, setChapterNumber] = useState<number>(11);
  const [chapterName, setChapterName] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState<boolean>(false);

  // Status & Progress State
  const [uploading, setUploading] = useState<boolean>(false);
  const [activeResource, setActiveResource] = useState<UploadedResource | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Recent Uploads List State
  const [recentUploads, setRecentUploads] = useState<UploadedResource[]>([]);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Load recent uploads on mount
  useEffect(() => {
    loadRecentUploads();
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  // Update default class when subject changes
  const handleSubjectChange = (subjId: string) => {
    setSelectedSubject(subjId);
    const found = AVAILABLE_SUBJECTS.find((s) => s.id === subjId);
    if (found) {
      setClassNumber(found.defaultClass);
      // Sensible default chapter numbers beyond existing textbooks
      if (subjId === "evs") setChapterNumber(11);
      else if (subjId === "history") setChapterNumber(19);
      else if (subjId === "mathematics") setChapterNumber(8);
    }
  };

  const loadRecentUploads = async () => {
    try {
      const data = await api.listUploadedResources();
      setRecentUploads(data);
    } catch (err: any) {
      console.error("Failed to load recent uploads:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      validateAndSetFile(selected);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setErrorMessage("Please select a valid PDF file (.pdf).");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setErrorMessage(`Selected file is too large (${(f.size / (1024 * 1024)).toFixed(1)} MB). Max limit is 50 MB.`);
      return;
    }
    setFile(f);
    // Autofill chapter name if blank
    if (!chapterName) {
      const cleanBase = f.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ");
      setChapterName(cleanBase.charAt(0).toUpperCase() + cleanBase.slice(1));
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!file) {
      setErrorMessage("Please select a PDF file to upload.");
      return;
    }
    if (!chapterName.trim()) {
      setErrorMessage("Please provide a meaningful chapter name.");
      return;
    }
    if (chapterNumber < 1) {
      setErrorMessage("Chapter number must be greater than 0.");
      return;
    }

    const formData = new FormData();
    formData.append("subject_id", selectedSubject);
    formData.append("class_number", String(classNumber));
    formData.append("chapter_number", String(chapterNumber));
    formData.append("chapter_name", chapterName.trim());
    formData.append("file", file);
    formData.append("background", "true");

    setUploading(true);
    try {
      const res = await api.uploadFacultyPDF(formData);
      setActiveResource(res.resource);
      setSuccessMessage(res.message);

      // Start polling for indexing completion
      startPolling(res.resource.resource_id);
      loadRecentUploads();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to upload document.");
      setUploading(false);
    }
  };

  const startPolling = (resourceId: string) => {
    let attempts = 0;
    const maxAttempts = 60; // 90 seconds (1.5s * 60)

    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      attempts++;
      try {
        const updated = await api.getUploadedResource(resourceId);
        setActiveResource(updated);

        if (updated.processing_status === "indexed") {
          clearInterval(pollTimerRef.current!);
          setUploading(false);
          setSuccessMessage(`Success! Chapter successfully indexed (${updated.chunk_count} semantic chunks). Ready for student queries!`);
          loadRecentUploads();
        } else if (updated.processing_status === "failed") {
          clearInterval(pollTimerRef.current!);
          setUploading(false);
          setErrorMessage(updated.error_message || "Ingestion pipeline failed.");
          loadRecentUploads();
        } else if (attempts >= maxAttempts) {
          clearInterval(pollTimerRef.current!);
          setUploading(false);
          setErrorMessage("Ingestion is taking longer than expected. Please check back in a few moments.");
        }
      } catch (err: any) {
        console.error("Polling error:", err);
      }
    }, 1500);
  };

  const handleDeleteResource = async (resourceId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"? This will remove its vectors and local PDF.`)) {
      return;
    }
    setActionInProgress(resourceId);
    try {
      await api.deleteUploadedResource(resourceId);
      if (activeResource?.resource_id === resourceId) {
        setActiveResource(null);
      }
      loadRecentUploads();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReindexResource = async (resourceId: string) => {
    setActionInProgress(resourceId);
    try {
      const res = await api.reindexUploadedResource(resourceId);
      alert(`Re-indexed successfully: ${res.chunk_count} chunks.`);
      loadRecentUploads();
    } catch (err: any) {
      alert(`Reindex failed: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  };

  const resetForm = () => {
    setFile(null);
    setChapterName("");
    setActiveResource(null);
    setErrorMessage(null);
    setSuccessMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Breadcrumb & Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            <Link href="/" className="hover:text-blue-600 transition-colors">Classroom</Link>
            <ChevronRight size={14} />
            <span className="text-indigo-600">Faculty Workspace</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
                <span className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-lg shadow-sm">
                  <UploadCloud size={22} />
                </span>
                Faculty PDF Upload & Knowledge Ingestion
              </h1>
              <p className="text-sm text-slate-600 mt-1 max-w-3xl">
                Upload subject-specific PDF textbooks, teacher lecture notes, or supplementary reading materials. Documents are processed locally, embedded with <code className="px-1.5 py-0.5 rounded bg-slate-100 text-indigo-700 font-mono text-xs font-bold">multilingual-e5-small</code>, and immediately made available to students in chapter-isolated chats.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                100% Local & Offline
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload Form */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-7">
              <h2 className="text-base font-bold text-slate-900 mb-5 flex items-center gap-2">
                <BookOpen size={18} className="text-indigo-600" />
                Document Metadata & Target Curriculum
              </h2>

              <form onSubmit={handleUploadSubmit} className="space-y-5">
                {/* Subject Selector */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    Subject Selection
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {AVAILABLE_SUBJECTS.map((sub) => {
                      const isSelected = selectedSubject === sub.id;
                      return (
                        <button
                          key={sub.id}
                          type="button"
                          onClick={() => handleSubjectChange(sub.id)}
                          className={`flex items-center gap-2 p-3 rounded-xl border text-left transition-all ${
                            isSelected
                              ? "border-indigo-600 bg-indigo-50/60 ring-2 ring-indigo-500/20 shadow-2xs"
                              : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
                          }`}
                        >
                          <span className="text-xl">{sub.icon}</span>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-bold text-slate-900 truncate">{sub.name}</p>
                            <p className="text-[11px] text-slate-500 font-medium">Class {sub.defaultClass}</p>
                          </div>
                          {isSelected && <Check size={16} className="text-indigo-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Class & Chapter Number Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Class / Standard
                    </label>
                    <select
                      value={classNumber}
                      onChange={(e) => setClassNumber(parseInt(e.target.value) || 5)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-sm font-medium text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-colors"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((num) => (
                        <option key={num} value={num}>
                          Class {num} ({num === 4 ? "Std IV History" : num === 5 ? "Std V EVS" : num === 10 ? "Std X Geometry" : `Standard ${num}`})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Chapter Number
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={99}
                      value={chapterNumber}
                      onChange={(e) => setChapterNumber(parseInt(e.target.value) || 1)}
                      required
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-sm font-medium text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-colors"
                      placeholder="e.g. 11"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">
                      Must not conflict with active official or uploaded chapters.
                    </p>
                  </div>
                </div>

                {/* Chapter Name Input */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Chapter / Unit Name
                  </label>
                  <input
                    type="text"
                    value={chapterName}
                    onChange={(e) => setChapterName(e.target.value)}
                    required
                    placeholder="e.g. Modern Conservation & Renewable Energy"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-sm font-medium text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-colors"
                  />
                </div>

                {/* PDF Dropzone */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Select PDF Document (Max 50 MB)
                  </label>
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragOver(true);
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                      dragOver
                        ? "border-indigo-600 bg-indigo-50/50 scale-[0.99]"
                        : file
                        ? "border-emerald-300 bg-emerald-50/20"
                        : "border-slate-300 hover:border-slate-400 hover:bg-slate-50/50"
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={handleFileSelect}
                      className="hidden"
                    />

                    {file ? (
                      <div className="flex items-center justify-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                          <FileText size={22} />
                        </div>
                        <div className="text-left min-w-0">
                          <p className="text-xs font-bold text-slate-900 truncate max-w-xs">{file.name}</p>
                          <p className="text-[11px] text-slate-500 font-medium">
                            {(file.size / (1024 * 1024)).toFixed(2)} MB · Click to change file
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                          <UploadCloud size={24} />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-800">
                            Click to upload or drag & drop a PDF
                          </p>
                          <p className="text-[11px] text-slate-500 font-medium">
                            Digital text-extractable PDFs only (scanned image PDFs without OCR will be rejected)
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Submit Action */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={uploading || !file || !chapterName.trim()}
                    className={`w-full py-3 px-4 rounded-xl font-bold text-sm text-white flex items-center justify-center gap-2 shadow-sm transition-all ${
                      uploading || !file || !chapterName.trim()
                        ? "bg-slate-300 cursor-not-allowed text-slate-500"
                        : "bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99] shadow-indigo-600/20"
                    }`}
                  >
                    {uploading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Uploading & Indexing Chunks...</span>
                      </>
                    ) : (
                      <>
                        <UploadCloud size={18} />
                        <span>Upload & Ingest to Vector Store</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Right Column: Ingestion Status & Success Card */}
          <div className="lg:col-span-5 space-y-6">
            {/* Live Progress Card */}
            {activeResource && (
              <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Ingestion Pipeline Status
                  </h3>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                      activeResource.processing_status === "indexed"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : activeResource.processing_status === "failed"
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                    }`}
                  >
                    {activeResource.processing_status === "indexed" ? (
                      <>
                        <CheckCircle2 size={13} className="text-emerald-600" />
                        Indexed & Ready
                      </>
                    ) : activeResource.processing_status === "failed" ? (
                      <>
                        <AlertCircle size={13} className="text-rose-600" />
                        Failed
                      </>
                    ) : (
                      <>
                        <div className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
                        Processing Embeddings
                      </>
                    )}
                  </span>
                </div>

                <div className="space-y-3.5 bg-slate-50/70 p-4 rounded-xl border border-slate-200/60 mb-5">
                  <div>
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Chapter Title</span>
                    <p className="text-sm font-bold text-slate-900">{activeResource.chapter_name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[11px] font-semibold text-slate-500 uppercase">Subject / Class</span>
                      <p className="font-bold text-slate-800 capitalize">
                        {activeResource.subject_id} · Class {activeResource.class_number}
                      </p>
                    </div>
                    <div>
                      <span className="text-[11px] font-semibold text-slate-500 uppercase">Chapter ID</span>
                      <p className="font-mono text-[11px] font-bold text-indigo-700">{activeResource.chapter_id}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[11px] font-semibold text-slate-500 uppercase">Indexed Chunks</span>
                      <p className="font-bold text-slate-800">{activeResource.chunk_count} passages</p>
                    </div>
                    <div>
                      <span className="text-[11px] font-semibold text-slate-500 uppercase">Vector Store</span>
                      <p className="font-bold text-slate-800">ChromaDB (faculty_uploads)</p>
                    </div>
                  </div>
                </div>

                {/* Error message */}
                {errorMessage && (
                  <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-start gap-2.5 mb-4">
                    <ShieldAlert size={16} className="text-rose-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold">Error encountered:</p>
                      <p>{errorMessage}</p>
                    </div>
                  </div>
                )}

                {/* Success message */}
                {successMessage && !errorMessage && (
                  <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-start gap-2.5 mb-4">
                    <CheckCircle2 size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold">Ingestion Status:</p>
                      <p>{successMessage}</p>
                    </div>
                  </div>
                )}

                {/* Direct Action Buttons on Indexed */}
                {activeResource.processing_status === "indexed" && (
                  <div className="space-y-2 pt-2">
                    <Link
                      href={`/chat/${activeResource.chapter_id}?subject=${activeResource.subject_id}`}
                      className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
                    >
                      <MessageCircle size={15} />
                      <span>Start Student Chat with this Chapter</span>
                      <ArrowRight size={14} />
                    </Link>

                    <Link
                      href={`/subjects/${activeResource.subject_id}`}
                      className="w-full py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
                    >
                      <span>View in Subject Explorer</span>
                    </Link>

                    <button
                      type="button"
                      onClick={resetForm}
                      className="w-full py-2 text-center text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
                    >
                      Upload Another Chapter
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Architecture Explainer Card */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Sparkles size={14} className="text-amber-500" />
                How Dynamic Ingestion Works
              </h3>
              <ul className="space-y-3 text-xs text-slate-600 leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-[10px]">1</span>
                  <span><strong>Safe Local Storage:</strong> PDFs are stored in <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">data/uploads/</code> with path traversal guards.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-[10px]">2</span>
                  <span><strong>Semantic Chunking:</strong> Extracted page-by-page using PyMuPDF (800 chars / 150 overlap) preserving page numbers.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-[10px]">3</span>
                  <span><strong>E5 Vectors:</strong> Embedded with the <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">passage: </code> prefix and stored in ChromaDB (<code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">faculty_uploads</code>).</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-[10px]">4</span>
                  <span><strong>Scope Isolation:</strong> Chapter queries only search this chapter; subject chats seamlessly integrate both official and uploaded materials.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Section: Recently Uploaded Materials Table */}
        <div className="mt-12 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-7">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Layers size={18} className="text-indigo-600" />
                Active Faculty Uploads ({recentUploads.length})
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                All uploaded materials currently registered in SQLite and persistent ChromaDB.
              </p>
            </div>
            <button
              onClick={loadRecentUploads}
              className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw size={13} className={loadingList ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>

          {loadingList ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading resources...</div>
          ) : recentUploads.length === 0 ? (
            <div className="py-12 text-center space-y-2">
              <FileText size={32} className="mx-auto text-slate-300" />
              <p className="text-xs font-bold text-slate-700">No faculty materials uploaded yet</p>
              <p className="text-xs text-slate-500">Use the form above to upload your first textbook or chapter PDF.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/50 text-slate-500 uppercase tracking-wider font-bold text-[10px]">
                    <th className="py-3 px-3">Subject / Class</th>
                    <th className="py-3 px-3">Chapter # & Title</th>
                    <th className="py-3 px-3">Original File</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Chunks</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentUploads.map((res) => {
                    const isIndexed = res.processing_status === "indexed";
                    const isBusy = actionInProgress === res.resource_id;

                    return (
                      <tr key={res.resource_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3.5 px-3">
                          <span className="font-bold text-slate-900 capitalize">{res.subject_id}</span>
                          <span className="text-[11px] text-slate-500 block">Class {res.class_number}</span>
                        </td>
                        <td className="py-3.5 px-3">
                          <span className="font-bold text-slate-900 block">
                            Ch. {res.chapter_number}: {res.chapter_name}
                          </span>
                          <span className="font-mono text-[10px] text-indigo-600 block">{res.chapter_id}</span>
                        </td>
                        <td className="py-3.5 px-3">
                          <span className="font-medium text-slate-700 block truncate max-w-xs">{res.original_filename}</span>
                          <span className="text-[10px] text-slate-400">
                            {(res.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                          </span>
                        </td>
                        <td className="py-3.5 px-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold ${
                              isIndexed
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : res.processing_status === "failed"
                                ? "bg-rose-50 text-rose-700 border border-rose-200"
                                : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                            }`}
                          >
                            {isIndexed ? (
                              <CheckCircle2 size={11} className="text-emerald-600" />
                            ) : res.processing_status === "failed" ? (
                              <AlertCircle size={11} className="text-rose-600" />
                            ) : (
                              <Clock size={11} className="text-indigo-600 animate-spin" />
                            )}
                            <span className="capitalize">{res.processing_status}</span>
                          </span>
                        </td>
                        <td className="py-3.5 px-3">
                          <span className="font-bold text-slate-800">{res.chunk_count}</span>
                        </td>
                        <td className="py-3.5 px-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {isIndexed && (
                              <Link
                                href={`/chat/${res.chapter_id}?subject=${res.subject_id}`}
                                className="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-[11px] flex items-center gap-1 transition-colors"
                              >
                                <MessageCircle size={12} />
                                Chat
                              </Link>
                            )}

                            <button
                              onClick={() => handleReindexResource(res.resource_id)}
                              disabled={isBusy}
                              title="Re-index document"
                              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 transition-colors disabled:opacity-50"
                            >
                              <RefreshCw size={12} className={isBusy ? "animate-spin" : ""} />
                            </button>

                            <button
                              onClick={() => handleDeleteResource(res.resource_id, res.chapter_name)}
                              disabled={isBusy}
                              title="Delete resource"
                              className="p-1.5 rounded-lg border border-rose-200 hover:bg-rose-50 text-rose-600 transition-colors disabled:opacity-50"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
