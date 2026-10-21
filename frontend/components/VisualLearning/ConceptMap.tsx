"use client";

import { useState } from "react";
import { Leaf, MapPin, Clock, Layers } from "lucide-react";

interface ConceptNode {
  id: string;
  label: string;
  description: string;
  details?: string[];
  children?: string[]; // ids of child nodes
  icon?: string;
  color?: "green" | "blue" | "amber" | "rose";
}

interface ConceptMapProps {
  title: string;
  subtitle?: string;
  nodes: ConceptNode[];
  rootId: string;
  subject?: "evs" | "history" | "mathematics";
}

const COLOR_SCHEMES = {
  green: {
    bg: "#ECFDF5",
    border: "#6EE7B7",
    text: "#065F46",
    headerBg: "#059669",
    dot: "#10B981",
  },
  blue: {
    bg: "#EFF6FF",
    border: "#93C5FD",
    text: "#1E40AF",
    headerBg: "#2563EB",
    dot: "#3B82F6",
  },
  amber: {
    bg: "#FFFBEB",
    border: "#FCD34D",
    text: "#78350F",
    headerBg: "#D97706",
    dot: "#F59E0B",
  },
  rose: {
    bg: "#FFF1F2",
    border: "#FCA5A5",
    text: "#881337",
    headerBg: "#E11D48",
    dot: "#F43F5E",
  },
};

const SUBJECT_ICONS = {
  evs: "🌿",
  history: "⚔️",
  mathematics: "📐",
};

function ConceptNodeCard({ node, allNodes, depth = 0 }: { node: ConceptNode; allNodes: Map<string, ConceptNode>; depth?: number }) {
  const [expanded, setExpanded] = useState(depth === 0);
  const colors = COLOR_SCHEMES[node.color || "blue"];
  const children = (node.children || [])
    .map((id) => allNodes.get(id))
    .filter(Boolean) as ConceptNode[];

  return (
    <div style={{ marginBottom: depth === 0 ? "1rem" : "0.5rem" }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          background: expanded ? colors.bg : "white",
          border: `1.5px solid ${expanded ? colors.border : "#E2E8F0"}`,
          borderRadius: "12px",
          padding: "0.75rem 1rem",
          cursor: children.length > 0 || node.details?.length ? "pointer" : "default",
          transition: "all 0.15s ease",
          boxShadow: expanded ? `0 2px 8px ${colors.border}40` : "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem" }}>
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: colors.dot,
              flexShrink: 0,
              marginTop: "6px",
            }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: depth === 0 ? "0.95rem" : "0.88rem", fontWeight: 700, color: colors.text, margin: "0 0 0.2rem" }}>
              {node.label}
            </p>
            {expanded && (
              <p style={{ fontSize: "0.82rem", color: "#475569", margin: 0, lineHeight: 1.5 }}>
                {node.description}
              </p>
            )}
          </div>
        </div>

        {expanded && node.details && node.details.length > 0 && (
          <div style={{ marginTop: "0.6rem", paddingLeft: "1.4rem" }}>
            <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              {node.details.map((detail, idx) => (
                <li key={idx} style={{ display: "flex", alignItems: "flex-start", gap: "0.4rem", fontSize: "0.8rem", color: "#64748B", lineHeight: 1.4 }}>
                  <span style={{ color: colors.dot, fontWeight: 700, flexShrink: 0 }}>•</span>
                  {detail}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {expanded && children.length > 0 && (
        <div
          style={{
            marginLeft: "1.5rem",
            marginTop: "0.4rem",
            paddingLeft: "1rem",
            borderLeft: `2px solid ${colors.border}80`,
            display: "flex",
            flexDirection: "column",
            gap: "0.35rem",
          }}
        >
          {children.map((child) => (
            <ConceptNodeCard key={child.id} node={child} allNodes={allNodes} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ConceptMap({ title, subtitle, nodes, rootId, subject }: ConceptMapProps) {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const rootNode = nodeMap.get(rootId);
  if (!rootNode) return null;

  const subjectHeaderBg =
    subject === "history"
      ? "linear-gradient(90deg, #92400E 0%, #B45309 100%)"
      : subject === "mathematics"
      ? "linear-gradient(90deg, #1D4ED8 0%, #2563EB 100%)"
      : "linear-gradient(90deg, #065F46 0%, #059669 100%)";

  const SubjectIcon = subject === "evs" ? Leaf : subject === "history" ? Layers : MapPin;

  return (
    <div
      style={{
        background: "white",
        border: "1.5px solid #E2E8F0",
        borderRadius: "16px",
        overflow: "hidden",
        fontFamily: "inherit",
        marginBottom: "1rem",
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: subjectHeaderBg,
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
          <SubjectIcon size={18} color="white" />
        </div>
        <div>
          {subtitle && (
            <p style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.7)", fontWeight: 600, margin: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {subtitle}
            </p>
          )}
          <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "white", margin: 0 }}>{title}</h3>
        </div>
      </div>

      <div style={{ padding: "1.25rem" }}>
        <ConceptNodeCard node={rootNode} allNodes={nodeMap} depth={0} />
      </div>
    </div>
  );
}
