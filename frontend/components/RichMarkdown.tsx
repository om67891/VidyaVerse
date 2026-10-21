"use client";

/**
 * RichMarkdown — lightweight markdown renderer for VidyaVerse chat messages.
 * Supports: headings, bold, italic, inline code, fenced code blocks,
 * ordered/unordered lists, blockquotes, horizontal rules, and tables.
 * No external dependencies.
 */

import React from "react";
import {
  HistoricalTimeline,
  MathProofRenderer,
  InteractiveQuizCard,
  ConceptMap,
} from "./VisualLearning";

interface RichMarkdownProps {
  content: string;
  isUser?: boolean;
  subjectId?: string;
}

// ── Token types ────────────────────────────────────────────────────────────────

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "code"; lang: string; code: string }
  | { type: "ol"; items: string[] }
  | { type: "ul"; items: string[] }
  | { type: "blockquote"; text: string }
  | { type: "hr" }
  | { type: "table"; headers: string[]; rows: string[][] };

// ── Block Parser ───────────────────────────────────────────────────────────────

function parseBlocks(md: string): Block[] {
  const lines = md.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    if (line.startsWith("```") || line.startsWith("~~~")) {
      const fence = line.slice(0, 3);
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith(fence)) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing fence
      blocks.push({ type: "code", lang, code: codeLines.join("\n") });
      continue;
    }

    // Heading
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      blocks.push({ type: "heading", level: headingMatch[1].length, text: headingMatch[2] });
      i++;
      continue;
    }

    // HR
    if (/^[-*_]{3,}$/.test(line.trim())) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith(">")) {
        quoteLines.push(lines[i].slice(1).trim());
        i++;
      }
      blocks.push({ type: "blockquote", text: quoteLines.join(" ") });
      continue;
    }

    // Table (detect | ... | ... |)
    if (line.includes("|") && i + 1 < lines.length && /^\|[-| :]+\|$/.test(lines[i + 1].trim())) {
      const headers = line
        .split("|")
        .filter((_, ci) => ci > 0 && ci < line.split("|").length - 1)
        .map((h) => h.trim());
      i += 2; // skip header + separator row
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|")) {
        const rowCells = lines[i]
          .split("|")
          .filter((_, ci) => ci > 0 && ci < lines[i].split("|").length - 1)
          .map((c) => c.trim());
        rows.push(rowCells);
        i++;
      }
      blocks.push({ type: "table", headers, rows });
      continue;
    }

    // Ordered list
    if (/^\d+[.)]\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+[.)]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+[.)]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    // Unordered list
    if (/^[-*+]\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*+]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*+]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    // Empty line — skip
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Paragraph — collect consecutive non-empty, non-special lines
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].startsWith("#") &&
      !lines[i].startsWith(">") &&
      !/^[-*+]\s/.test(lines[i]) &&
      !/^\d+[.)]\s/.test(lines[i]) &&
      !lines[i].startsWith("```") &&
      !lines[i].startsWith("~~~") &&
      !/^[-*_]{3,}$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      blocks.push({ type: "paragraph", text: paraLines.join("\n") });
    }
  }

  return blocks;
}

// ── Inline Renderer ────────────────────────────────────────────────────────────

function renderInline(text: string, isUser: boolean): React.ReactNode[] {
  // Handle **bold**, *italic*, `code`, and line breaks
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\n)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} style={{ fontWeight: 700, color: isUser ? "#FFFFFF" : "#0F172A" }}>
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={idx}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code
          key={idx}
          style={{
            fontFamily: "'Fira Code', 'Cascadia Code', monospace",
            fontSize: "0.85em",
            background: isUser ? "rgba(255,255,255,0.2)" : "#F1F5F9",
            color: isUser ? "#FFFFFF" : "#DC2626",
            borderRadius: "4px",
            padding: "0.1em 0.35em",
            border: isUser ? "1px solid rgba(255,255,255,0.3)" : "1px solid #E2E8F0",
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part === "\n") {
      return <br key={idx} />;
    }
    return part;
  });
}

// ── Subject accent color helper ─────────────────────────────────────────────

function getSubjectAccent(subjectId?: string) {
  if (!subjectId) return { color: "#2563EB", bg: "#EFF6FF", border: "#BFDBFE" };
  const id = subjectId.toLowerCase();
  if (id.includes("hist")) return { color: "#B45309", bg: "#FEF3C7", border: "#FCD34D" };
  if (id.includes("math")) return { color: "#2563EB", bg: "#EFF6FF", border: "#BFDBFE" };
  if (id.includes("evs") || id.includes("env")) return { color: "#059669", bg: "#ECFDF5", border: "#A7F3D0" };
  return { color: "#2563EB", bg: "#EFF6FF", border: "#BFDBFE" };
}

// ── Block Renderer ────────────────────────────────────────────────────────────

function renderBlock(block: Block, idx: number, isUser: boolean, subjectId?: string): React.ReactNode {
  const accent = getSubjectAccent(subjectId);

  switch (block.type) {
    case "heading": {
      const sizes = ["1.2rem", "1.05rem", "0.95rem", "0.9rem", "0.88rem", "0.85rem"];
      return (
        <div
          key={idx}
          style={{
            fontSize: sizes[block.level - 1] || "0.9rem",
            fontWeight: 700,
            color: isUser ? "#FFFFFF" : "#0F172A",
            marginTop: idx > 0 ? "0.85rem" : 0,
            marginBottom: "0.3rem",
            lineHeight: 1.3,
            borderBottom: block.level <= 2 && !isUser ? `1px solid ${accent.border}` : "none",
            paddingBottom: block.level <= 2 && !isUser ? "0.3rem" : "0",
          }}
        >
          {block.level <= 2 && !isUser && (
            <span style={{ color: accent.color, marginRight: "0.4rem" }}>
              {"#".repeat(block.level)}
            </span>
          )}
          {renderInline(block.text, isUser)}
        </div>
      );
    }

    case "paragraph":
      return (
        <p
          key={idx}
          style={{
            margin: "0.3rem 0",
            lineHeight: 1.6,
            color: isUser ? "#FFFFFF" : "var(--text-primary)",
            fontSize: "0.92rem",
          }}
        >
          {renderInline(block.text, isUser)}
        </p>
      );

    case "code": {
      const normalizedLang = (block.lang || "").toLowerCase().trim();
      if (!isUser) {
        if (normalizedLang === "timeline" || normalizedLang === "history-timeline") {
          try {
            const data = JSON.parse(block.code);
            return <HistoricalTimeline key={idx} {...data} />;
          } catch {}
        }
        if (normalizedLang === "proof" || normalizedLang === "math-proof") {
          try {
            const data = JSON.parse(block.code);
            return <MathProofRenderer key={idx} {...data} />;
          } catch {}
        }
        if (normalizedLang === "quiz" || normalizedLang === "quiz-card") {
          try {
            const data = JSON.parse(block.code);
            return <InteractiveQuizCard key={idx} {...data} />;
          } catch {}
        }
        if (normalizedLang === "conceptmap" || normalizedLang === "concept-map") {
          try {
            const data = JSON.parse(block.code);
            return <ConceptMap key={idx} {...data} />;
          } catch {}
        }
      }

      return (
        <div
          key={idx}
          style={{
            margin: "0.6rem 0",
            borderRadius: "10px",
            overflow: "hidden",
            border: "1px solid #E2E8F0",
          }}
        >
          {block.lang && (
            <div
              style={{
                background: "#1E293B",
                padding: "0.3rem 0.85rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span style={{ fontSize: "0.72rem", color: "#94A3B8", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {block.lang}
              </span>
            </div>
          )}
          <pre
            style={{
              background: "#0F172A",
              color: "#E2E8F0",
              padding: "0.85rem 1rem",
              margin: 0,
              overflowX: "auto",
              fontFamily: "'Fira Code', 'Cascadia Code', 'Courier New', monospace",
              fontSize: "0.85rem",
              lineHeight: 1.5,
              whiteSpace: "pre",
            }}
          >
            <code>{block.code}</code>
          </pre>
        </div>
      );
    }

    case "ul":
      return (
        <ul
          key={idx}
          style={{
            margin: "0.35rem 0",
            paddingLeft: "1.4rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.25rem",
            listStyle: "none",
          }}
        >
          {block.items.map((item, iIdx) => (
            <li
              key={iIdx}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "0.5rem",
                fontSize: "0.9rem",
                color: isUser ? "rgba(255,255,255,0.95)" : "var(--text-secondary)",
                lineHeight: 1.5,
              }}
            >
              <span
                style={{
                  color: isUser ? "rgba(255,255,255,0.7)" : accent.color,
                  fontWeight: 700,
                  flexShrink: 0,
                  marginTop: "0.1rem",
                }}
              >
                •
              </span>
              <span>{renderInline(item, isUser)}</span>
            </li>
          ))}
        </ul>
      );

    case "ol":
      return (
        <ol
          key={idx}
          style={{
            margin: "0.35rem 0",
            paddingLeft: "0",
            display: "flex",
            flexDirection: "column",
            gap: "0.25rem",
            listStyle: "none",
          }}
        >
          {block.items.map((item, iIdx) => (
            <li
              key={iIdx}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "0.6rem",
                fontSize: "0.9rem",
                color: isUser ? "rgba(255,255,255,0.95)" : "var(--text-secondary)",
                lineHeight: 1.5,
              }}
            >
              <span
                style={{
                  minWidth: "22px",
                  height: "22px",
                  borderRadius: "50%",
                  background: isUser ? "rgba(255,255,255,0.2)" : accent.bg,
                  border: `1px solid ${isUser ? "rgba(255,255,255,0.3)" : accent.border}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  color: isUser ? "white" : accent.color,
                  flexShrink: 0,
                  marginTop: "0.05rem",
                }}
              >
                {iIdx + 1}
              </span>
              <span style={{ flex: 1 }}>{renderInline(item, isUser)}</span>
            </li>
          ))}
        </ol>
      );

    case "blockquote":
      return (
        <div
          key={idx}
          style={{
            margin: "0.5rem 0",
            padding: "0.65rem 1rem",
            borderLeft: `3px solid ${isUser ? "rgba(255,255,255,0.5)" : accent.color}`,
            background: isUser ? "rgba(255,255,255,0.1)" : accent.bg,
            borderRadius: "0 8px 8px 0",
            fontSize: "0.88rem",
            fontStyle: "italic",
            color: isUser ? "rgba(255,255,255,0.9)" : accent.color,
            lineHeight: 1.55,
          }}
        >
          {renderInline(block.text, isUser)}
        </div>
      );

    case "hr":
      return (
        <hr
          key={idx}
          style={{
            border: "none",
            borderTop: `1px solid ${isUser ? "rgba(255,255,255,0.25)" : "#E2E8F0"}`,
            margin: "0.6rem 0",
          }}
        />
      );

    case "table":
      return (
        <div
          key={idx}
          style={{ margin: "0.5rem 0", overflowX: "auto", borderRadius: "10px", border: "1px solid #E2E8F0" }}
        >
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ background: accent.bg }}>
                {block.headers.map((h, hIdx) => (
                  <th
                    key={hIdx}
                    style={{
                      padding: "0.5rem 0.85rem",
                      textAlign: "left",
                      fontWeight: 700,
                      color: accent.color,
                      borderBottom: `1.5px solid ${accent.border}`,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row, rIdx) => (
                <tr key={rIdx} style={{ background: rIdx % 2 === 0 ? "white" : "#F8FAFC" }}>
                  {row.map((cell, cIdx) => (
                    <td
                      key={cIdx}
                      style={{
                        padding: "0.45rem 0.85rem",
                        color: "#475569",
                        borderBottom: rIdx < block.rows.length - 1 ? "1px solid #F1F5F9" : "none",
                      }}
                    >
                      {renderInline(cell, false)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    default:
      return null;
  }
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function RichMarkdown({ content, isUser = false, subjectId }: RichMarkdownProps) {
  const blocks = parseBlocks(content);

  if (blocks.length === 0) {
    return <span style={{ color: isUser ? "#FFFFFF" : "var(--text-primary)", fontSize: "0.92rem" }}>{content}</span>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.05rem" }}>
      {blocks.map((block, idx) => renderBlock(block, idx, isUser, subjectId))}
    </div>
  );
}
