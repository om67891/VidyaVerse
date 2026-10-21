"use client";

import { useState } from "react";
import { CheckCircle2, ChevronDown, ChevronUp, BookOpen, Calculator } from "lucide-react";

interface ProofStep {
  step: number;
  statement: string;
  reason: string;
  formula?: string;
}

interface MathProofRendererProps {
  title: string;
  theorem?: string;
  given?: string;
  toprove?: string;
  steps: ProofStep[];
  conclusion?: string;
  chapterTitle?: string;
}

export default function MathProofRenderer({
  title,
  theorem,
  given,
  toprove,
  steps,
  conclusion,
  chapterTitle,
}: MathProofRendererProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([0]));
  const [showAll, setShowAll] = useState(false);

  const toggle = (idx: number) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const visibleSteps = showAll ? steps : steps.slice(0, 4);

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #EFF6FF 0%, #F0F9FF 100%)",
        border: "1.5px solid #BFDBFE",
        borderRadius: "16px",
        overflow: "hidden",
        fontFamily: "inherit",
        marginBottom: "1rem",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(90deg, #1D4ED8 0%, #2563EB 100%)",
          padding: "1rem 1.25rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <div
          style={{
            width: "36px",
            height: "36px",
            background: "rgba(255,255,255,0.15)",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <Calculator size={18} color="white" />
        </div>
        <div>
          <p style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.7)", fontWeight: 600, margin: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {chapterTitle || "Mathematical Proof"}
          </p>
          <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "white", margin: 0 }}>{title}</h3>
        </div>
      </div>

      <div style={{ padding: "1.25rem" }}>
        {/* Theorem */}
        {theorem && (
          <div
            style={{
              background: "white",
              border: "1px solid #BFDBFE",
              borderLeft: "4px solid #2563EB",
              borderRadius: "10px",
              padding: "0.85rem 1.1rem",
              marginBottom: "1rem",
            }}
          >
            <p style={{ fontSize: "0.72rem", fontWeight: 700, color: "#2563EB", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.3rem" }}>
              Theorem
            </p>
            <p style={{ fontSize: "0.92rem", color: "#0F172A", lineHeight: 1.5, margin: 0 }}>{theorem}</p>
          </div>
        )}

        {/* Given / To Prove */}
        {(given || toprove) && (
          <div style={{ display: "grid", gridTemplateColumns: given && toprove ? "1fr 1fr" : "1fr", gap: "0.75rem", marginBottom: "1rem" }}>
            {given && (
              <div
                style={{
                  background: "#ECFDF5",
                  border: "1px solid #A7F3D0",
                  borderRadius: "10px",
                  padding: "0.75rem 1rem",
                }}
              >
                <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "#059669", textTransform: "uppercase", marginBottom: "0.3rem" }}>Given</p>
                <p style={{ fontSize: "0.88rem", color: "#0F172A", margin: 0 }}>{given}</p>
              </div>
            )}
            {toprove && (
              <div
                style={{
                  background: "#FFF7ED",
                  border: "1px solid #FED7AA",
                  borderRadius: "10px",
                  padding: "0.75rem 1rem",
                }}
              >
                <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "#C2410C", textTransform: "uppercase", marginBottom: "0.3rem" }}>To Prove</p>
                <p style={{ fontSize: "0.88rem", color: "#0F172A", margin: 0 }}>{toprove}</p>
              </div>
            )}
          </div>
        )}

        {/* Proof Steps */}
        <div style={{ marginBottom: "0.75rem" }}>
          <p style={{ fontSize: "0.72rem", fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.6rem" }}>
            Proof ({steps.length} steps)
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {visibleSteps.map((step, idx) => {
              const isExpanded = expandedSteps.has(idx);
              return (
                <div
                  key={idx}
                  style={{
                    background: "white",
                    border: `1px solid ${isExpanded ? "#93C5FD" : "#E2E8F0"}`,
                    borderRadius: "10px",
                    overflow: "hidden",
                    transition: "border-color 0.15s ease",
                  }}
                >
                  <button
                    onClick={() => toggle(idx)}
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.75rem",
                      padding: "0.75rem 1rem",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <div
                      style={{
                        width: "26px",
                        height: "26px",
                        borderRadius: "50%",
                        background: isExpanded ? "#2563EB" : "#EFF6FF",
                        border: `2px solid ${isExpanded ? "#2563EB" : "#BFDBFE"}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                        transition: "all 0.15s ease",
                      }}
                    >
                      <span style={{ fontSize: "0.7rem", fontWeight: 700, color: isExpanded ? "white" : "#2563EB" }}>
                        {step.step}
                      </span>
                    </div>
                    <span style={{ flex: 1, fontSize: "0.88rem", color: "#0F172A", fontWeight: 500, lineHeight: 1.4 }}>
                      {step.statement}
                    </span>
                    {isExpanded ? (
                      <ChevronUp size={15} color="#94A3B8" />
                    ) : (
                      <ChevronDown size={15} color="#94A3B8" />
                    )}
                  </button>

                  {isExpanded && (
                    <div
                      style={{
                        padding: "0 1rem 0.85rem 3.25rem",
                        borderTop: "1px solid #F1F5F9",
                      }}
                    >
                      {step.formula && (
                        <div
                          style={{
                            background: "#F8FAFC",
                            border: "1px solid #E2E8F0",
                            borderRadius: "8px",
                            padding: "0.5rem 0.85rem",
                            marginBottom: "0.5rem",
                            fontFamily: "monospace",
                            fontSize: "0.9rem",
                            color: "#1E40AF",
                            fontWeight: 600,
                          }}
                        >
                          {step.formula}
                        </div>
                      )}
                      <div style={{ display: "flex", alignItems: "flex-start", gap: "0.4rem" }}>
                        <BookOpen size={13} color="#2563EB" style={{ marginTop: "2px", flexShrink: 0 }} />
                        <p style={{ fontSize: "0.82rem", color: "#475569", margin: 0, lineHeight: 1.5 }}>
                          <strong style={{ color: "#2563EB" }}>Reason: </strong>
                          {step.reason}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {steps.length > 4 && (
            <button
              onClick={() => setShowAll(!showAll)}
              style={{
                marginTop: "0.5rem",
                width: "100%",
                padding: "0.5rem",
                background: "transparent",
                border: "1px dashed #BFDBFE",
                borderRadius: "8px",
                fontSize: "0.8rem",
                color: "#2563EB",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              {showAll ? `Hide ${steps.length - 4} steps` : `Show all ${steps.length} steps`}
            </button>
          )}
        </div>

        {/* Conclusion */}
        {conclusion && (
          <div
            style={{
              background: "linear-gradient(135deg, #ECFDF5, #D1FAE5)",
              border: "1.5px solid #A7F3D0",
              borderRadius: "12px",
              padding: "0.85rem 1.1rem",
              display: "flex",
              alignItems: "flex-start",
              gap: "0.6rem",
            }}
          >
            <CheckCircle2 size={18} color="#059669" style={{ flexShrink: 0, marginTop: "2px" }} />
            <div>
              <p style={{ fontSize: "0.72rem", fontWeight: 700, color: "#059669", textTransform: "uppercase", marginBottom: "0.25rem" }}>
                QED — Conclusion
              </p>
              <p style={{ fontSize: "0.9rem", color: "#0F172A", margin: 0, fontWeight: 500 }}>{conclusion}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
