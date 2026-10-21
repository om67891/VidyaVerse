"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, HelpCircle, Trophy, RotateCcw } from "lucide-react";

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  subject?: string;
  chapter?: string;
}

interface InteractiveQuizCardProps {
  question: QuizQuestion;
  questionNumber?: number;
  totalQuestions?: number;
  onAnswered?: (isCorrect: boolean) => void;
}

export default function InteractiveQuizCard({
  question,
  questionNumber,
  totalQuestions,
  onAnswered,
}: InteractiveQuizCardProps) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [revealed, setRevealed] = useState(false);

  const handleSelect = (idx: number) => {
    if (revealed) return;
    setSelectedIdx(idx);
    setRevealed(true);
    onAnswered?.(idx === question.correct_index);
  };

  const reset = () => {
    setSelectedIdx(null);
    setRevealed(false);
  };

  const isCorrect = selectedIdx === question.correct_index;

  const getOptionStyle = (idx: number) => {
    const base: React.CSSProperties = {
      width: "100%",
      padding: "0.75rem 1rem",
      borderRadius: "10px",
      border: "1.5px solid",
      fontSize: "0.88rem",
      textAlign: "left",
      cursor: revealed ? "default" : "pointer",
      display: "flex",
      alignItems: "center",
      gap: "0.65rem",
      transition: "all 0.15s ease",
      background: "white",
      fontWeight: 500,
      lineHeight: 1.4,
    };

    if (!revealed) {
      return {
        ...base,
        borderColor: "#E2E8F0",
        color: "#0F172A",
      };
    }

    if (idx === question.correct_index) {
      return {
        ...base,
        borderColor: "#059669",
        background: "#ECFDF5",
        color: "#065F46",
      };
    }

    if (idx === selectedIdx && idx !== question.correct_index) {
      return {
        ...base,
        borderColor: "#DC2626",
        background: "#FEF2F2",
        color: "#991B1B",
      };
    }

    return {
      ...base,
      borderColor: "#F1F5F9",
      color: "#94A3B8",
      opacity: 0.6,
    };
  };

  const optionLabels = ["A", "B", "C", "D"];

  return (
    <div
      style={{
        background: "white",
        border: `1.5px solid ${revealed ? (isCorrect ? "#A7F3D0" : "#FECACA") : "#E2E8F0"}`,
        borderRadius: "16px",
        overflow: "hidden",
        fontFamily: "inherit",
        marginBottom: "1rem",
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        transition: "border-color 0.2s ease",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "0.85rem 1.25rem",
          borderBottom: "1px solid #F1F5F9",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#F8FAFC",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <HelpCircle size={16} color="#2563EB" />
          <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#2563EB", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Quiz
          </span>
          {questionNumber && totalQuestions && (
            <span style={{ fontSize: "0.75rem", color: "#94A3B8", fontWeight: 500 }}>
              {questionNumber} / {totalQuestions}
            </span>
          )}
        </div>
        {revealed && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {isCorrect ? (
              <span style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.78rem", fontWeight: 700, color: "#059669" }}>
                <Trophy size={14} /> Correct!
              </span>
            ) : (
              <span style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.78rem", fontWeight: 700, color: "#DC2626" }}>
                <XCircle size={14} /> Incorrect
              </span>
            )}
            <button
              onClick={reset}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.3rem",
                padding: "0.25rem 0.6rem",
                borderRadius: "6px",
                border: "1px solid #E2E8F0",
                background: "white",
                fontSize: "0.75rem",
                color: "#64748B",
                cursor: "pointer",
              }}
            >
              <RotateCcw size={12} /> Try again
            </button>
          </div>
        )}
      </div>

      <div style={{ padding: "1.1rem 1.25rem" }}>
        {/* Question */}
        <p style={{ fontSize: "0.95rem", fontWeight: 600, color: "#0F172A", lineHeight: 1.5, marginBottom: "1rem" }}>
          {question.question}
        </p>

        {/* Options */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {question.options.map((option, idx) => {
            const optStyle = getOptionStyle(idx);
            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                style={optStyle}
              >
                <span
                  style={{
                    width: "24px",
                    height: "24px",
                    borderRadius: "6px",
                    background:
                      revealed && idx === question.correct_index
                        ? "#059669"
                        : revealed && idx === selectedIdx && !isCorrect
                        ? "#DC2626"
                        : "#EFF6FF",
                    border: `1px solid ${
                      revealed && idx === question.correct_index
                        ? "#059669"
                        : revealed && idx === selectedIdx && !isCorrect
                        ? "#DC2626"
                        : "#BFDBFE"
                    }`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    color:
                      revealed && (idx === question.correct_index || (idx === selectedIdx && !isCorrect))
                        ? "white"
                        : "#2563EB",
                    flexShrink: 0,
                    transition: "all 0.15s ease",
                  }}
                >
                  {revealed && idx === question.correct_index ? (
                    <CheckCircle2 size={13} />
                  ) : revealed && idx === selectedIdx && !isCorrect ? (
                    <XCircle size={13} />
                  ) : (
                    optionLabels[idx]
                  )}
                </span>
                <span style={{ flex: 1 }}>{option}</span>
              </button>
            );
          })}
        </div>

        {/* Explanation */}
        {revealed && (
          <div
            style={{
              marginTop: "1rem",
              background: isCorrect ? "#ECFDF5" : "#EFF6FF",
              border: `1px solid ${isCorrect ? "#A7F3D0" : "#BFDBFE"}`,
              borderRadius: "10px",
              padding: "0.85rem 1rem",
            }}
          >
            <p style={{ fontSize: "0.72rem", fontWeight: 700, color: isCorrect ? "#059669" : "#1D4ED8", textTransform: "uppercase", marginBottom: "0.35rem" }}>
              Explanation
            </p>
            <p style={{ fontSize: "0.88rem", color: "#0F172A", margin: 0, lineHeight: 1.5 }}>
              {question.explanation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
