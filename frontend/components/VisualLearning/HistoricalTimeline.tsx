"use client";

import { useState } from "react";
import { Scroll, MapPin, ChevronRight, ChevronDown } from "lucide-react";

interface TimelineEvent {
  year: string;
  title: string;
  description: string;
  significance?: string;
  people?: string[];
  location?: string;
  icon?: string;
}

interface HistoricalTimelineProps {
  title: string;
  events: TimelineEvent[];
  period?: string;
}

export default function HistoricalTimeline({ title, events, period }: HistoricalTimelineProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #FAF7F0 0%, #FDF8EF 100%)",
        border: "1.5px solid #E7DEC8",
        borderRadius: "16px",
        overflow: "hidden",
        fontFamily: "inherit",
        marginBottom: "1rem",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(90deg, #92400E 0%, #B45309 100%)",
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
          <Scroll size={18} color="white" />
        </div>
        <div>
          {period && (
            <p style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.7)", fontWeight: 600, margin: 0, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {period}
            </p>
          )}
          <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "white", margin: 0 }}>{title}</h3>
        </div>
      </div>

      <div style={{ padding: "1.25rem" }}>
        <div style={{ position: "relative" }}>
          {/* Vertical line */}
          <div
            style={{
              position: "absolute",
              left: "20px",
              top: "12px",
              bottom: "12px",
              width: "2px",
              background: "linear-gradient(to bottom, #D97706, #B45309)",
              borderRadius: "2px",
            }}
          />

          <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
            {events.map((event, idx) => {
              const isExpanded = expandedIdx === idx;
              const isLast = idx === events.length - 1;

              return (
                <div key={idx} style={{ position: "relative", paddingLeft: "52px", paddingBottom: isLast ? 0 : "1rem" }}>
                  {/* Year dot */}
                  <div
                    onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                    style={{
                      position: "absolute",
                      left: "8px",
                      top: "8px",
                      width: "26px",
                      height: "26px",
                      borderRadius: "50%",
                      background: isExpanded
                        ? "linear-gradient(135deg, #D97706, #B45309)"
                        : "linear-gradient(135deg, #FFFDF9, #FEF3C7)",
                      border: `2px solid ${isExpanded ? "#D97706" : "#E7DEC8"}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      zIndex: 2,
                      transition: "all 0.15s ease",
                      boxShadow: isExpanded ? "0 2px 8px rgba(217,119,6,0.3)" : "none",
                    }}
                  >
                    <span style={{ fontSize: "0.65rem", fontWeight: 700, color: isExpanded ? "white" : "#B45309" }}>
                      {event.icon || "⚔"}
                    </span>
                  </div>

                  {/* Card */}
                  <div
                    onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                    style={{
                      background: isExpanded ? "white" : "rgba(255,253,249,0.7)",
                      border: `1.5px solid ${isExpanded ? "#D97706" : "#E7DEC8"}`,
                      borderRadius: "12px",
                      padding: "0.75rem 1rem",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                      boxShadow: isExpanded ? "0 4px 12px rgba(92,64,51,0.1)" : "none",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", minWidth: 0 }}>
                        <span
                          style={{
                            background: "#FEF3C7",
                            border: "1px solid #FCD34D",
                            borderRadius: "6px",
                            padding: "0.15rem 0.5rem",
                            fontSize: "0.72rem",
                            fontWeight: 700,
                            color: "#92400E",
                            flexShrink: 0,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {event.year}
                        </span>
                        <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#1A130B", margin: 0 }}>
                          {event.title}
                        </h4>
                      </div>
                      {isExpanded ? (
                        <ChevronDown size={14} color="#B45309" style={{ flexShrink: 0 }} />
                      ) : (
                        <ChevronRight size={14} color="#B45309" style={{ flexShrink: 0 }} />
                      )}
                    </div>

                    {!isExpanded && (
                      <p style={{ fontSize: "0.8rem", color: "#6E5F4E", margin: "0.35rem 0 0", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {event.description}
                      </p>
                    )}

                    {isExpanded && (
                      <div style={{ marginTop: "0.75rem", borderTop: "1px solid #F4EFE6", paddingTop: "0.75rem" }}>
                        <p style={{ fontSize: "0.88rem", color: "#2A2118", lineHeight: 1.6, margin: 0 }}>
                          {event.description}
                        </p>

                        {event.significance && (
                          <div
                            style={{
                              background: "#FEF3C7",
                              border: "1px solid #FCD34D",
                              borderRadius: "8px",
                              padding: "0.6rem 0.85rem",
                              marginTop: "0.6rem",
                            }}
                          >
                            <p style={{ fontSize: "0.72rem", fontWeight: 700, color: "#92400E", marginBottom: "0.2rem", textTransform: "uppercase" }}>
                              Historical Significance
                            </p>
                            <p style={{ fontSize: "0.85rem", color: "#78350F", margin: 0, lineHeight: 1.5 }}>
                              {event.significance}
                            </p>
                          </div>
                        )}

                        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.6rem", flexWrap: "wrap" }}>
                          {event.location && (
                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.25rem",
                                background: "#F3EFE6",
                                border: "1px solid #DFD5C3",
                                borderRadius: "6px",
                                padding: "0.2rem 0.55rem",
                                fontSize: "0.75rem",
                                color: "#5C4A33",
                              }}
                            >
                              <MapPin size={11} />
                              {event.location}
                            </span>
                          )}
                          {event.people?.map((person, pIdx) => (
                            <span
                              key={pIdx}
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                background: "#FFFBEB",
                                border: "1px solid #FDE68A",
                                borderRadius: "6px",
                                padding: "0.2rem 0.55rem",
                                fontSize: "0.75rem",
                                color: "#78350F",
                                fontWeight: 500,
                              }}
                            >
                              {person}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
