"use client";

import { useState } from "react";
import Image from "next/image";
import { Shield, Sparkles, User, Award } from "lucide-react";

interface AvatarProps {
  src: string;
  name: string;
  role: string;
  persona: string;
  subjectId?: string;
  size?: "sm" | "md" | "lg";
}

export function PersonaAvatar({
  src,
  name,
  role,
  persona,
  subjectId,
  size = "md",
}: AvatarProps) {
  const [imageError, setImageError] = useState(false);

  const dimension = size === "lg" ? 84 : size === "md" ? 64 : 48;
  const isShivaji = persona === "SHIVAJI" || persona === "shivaji_maharaj";

  // Determine theme by subject or persona name
  const sub = (subjectId || (src.includes("mathematics") ? "mathematics" : src.includes("evs") ? "evs" : "history")).toLowerCase();
  const theme = sub.includes("math")
    ? { border: "#2563EB", bg: "#EFF6FF", text: "#1D4ED8", badge: "📐", label: "Math" }
    : sub.includes("evs")
    ? { border: "#059669", bg: "#ECFDF5", text: "#047857", badge: "🌿", label: "EVS" }
    : { border: "#D97706", bg: "#FFFBEB", text: "#B45309", badge: isShivaji ? "👑" : "📜", label: "History" };

  return (
    <div className="flex items-center gap-3.5">
      <div
        className="storybook-avatar-frame relative flex items-center justify-center transition-transform hover:scale-105"
        style={{
          width: `${dimension}px`,
          height: `${dimension}px`,
          borderColor: theme.border,
        }}
      >
        {!imageError && src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt={name}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover rounded-full"
            loading="eager"
          />
        ) : (
          <div
            className="w-full h-full flex flex-col items-center justify-center text-center p-1.5 rounded-full"
            style={{
              background: `linear-gradient(135deg, ${theme.bg} 0%, white 100%)`,
              color: theme.text,
            }}
          >
            {isShivaji ? (
              <Shield className="w-6 h-6 stroke-[2.2]" />
            ) : (
              <Award className="w-6 h-6 stroke-[2.2]" />
            )}
            <span className="text-[9px] font-bold tracking-tight uppercase mt-0.5 truncate max-w-full px-1">
              {name.split(" ")[0]}
            </span>
          </div>
        )}

        {/* Small badge icon at bottom right */}
        <div
          className="absolute -bottom-0.5 -right-0.5 w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] shadow"
          style={{
            background: theme.border,
          }}
          title={isShivaji ? "First-Person Roleplay" : `${theme.label} Guide`}
        >
          {theme.badge}
        </div>
      </div>

      <div className="flex flex-col">
        <div className="flex items-center gap-1.5">
          <h2 className="text-base sm:text-lg font-bold tracking-tight text-[#2A2118] leading-tight">
            {name}
          </h2>
          {isShivaji && (
            <span
              className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full"
              style={{ background: "#FEF3C7", color: "#B45309", border: "1px solid #FCD34D" }}
            >
              Roleplay
            </span>
          )}
        </div>
        <p className="text-xs text-[#786C5E] font-medium leading-normal mt-0.5 max-w-sm">
          {role}
        </p>
      </div>
    </div>
  );
}

export function SinglePersonaAvatar({
  src,
  name,
  subjectId,
  size = 36,
}: {
  src?: string;
  name?: string;
  subjectId?: string;
  size?: number;
}) {
  const [error, setError] = useState(false);
  const sub = (subjectId || (src?.includes("mathematics") ? "mathematics" : src?.includes("evs") ? "evs" : "history")).toLowerCase();
  const theme = sub.includes("math")
    ? { border: "#2563EB", bg: "#EFF6FF", icon: "📐" }
    : sub.includes("evs")
    ? { border: "#059669", bg: "#ECFDF5", icon: "🌿" }
    : { border: "#D97706", bg: "#FFFBEB", icon: "📜" };

  if (src && !error) {
    return (
      <div
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: "10px",
          overflow: "hidden",
          border: `1.5px solid ${theme.border}`,
          flexShrink: 0,
          background: theme.bg,
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={name || "Persona Avatar"}
          onError={() => setError(true)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "10px",
        border: `1.5px solid ${theme.border}`,
        background: theme.bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: `${Math.round(size * 0.45)}px`,
        flexShrink: 0,
      }}
    >
      {theme.icon}
    </div>
  );
}
