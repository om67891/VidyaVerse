"use client";

import { useState } from "react";
import Image from "next/image";
import { Shield, Sparkles, User, Award } from "lucide-react";

interface AvatarProps {
  src: string;
  name: string;
  role: string;
  persona: string;
  size?: "sm" | "md" | "lg";
}

export function PersonaAvatar({
  src,
  name,
  role,
  persona,
  size = "md",
}: AvatarProps) {
  const [imageError, setImageError] = useState(false);

  const dimension = size === "lg" ? 84 : size === "md" ? 64 : 48;
  const isShivaji = persona === "SHIVAJI";

  return (
    <div className="flex items-center gap-3.5">
      <div
        className="storybook-avatar-frame relative flex items-center justify-center transition-transform hover:scale-105"
        style={{
          width: `${dimension}px`,
          height: `${dimension}px`,
          borderColor: isShivaji ? "#D97706" : "#4F46E5",
        }}
      >
        {!imageError ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt={name}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover rounded-full"
            loading="eager"
          />
        ) : (
          // Graceful fallback if asset is missing or fails to load
          <div
            className="w-full h-full flex flex-col items-center justify-center text-center p-1.5"
            style={{
              background: isShivaji
                ? "linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)"
                : "linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)",
              color: isShivaji ? "#92400E" : "#3730A3",
            }}
          >
            {isShivaji ? (
              <Shield className="w-6 h-6 stroke-[2.2]" />
            ) : (
              <Award className="w-6 h-6 stroke-[2.2]" />
            )}
            <span className="text-[9px] font-bold tracking-tight uppercase mt-0.5">
              {isShivaji ? "Shivaji" : "Tutor"}
            </span>
          </div>
        )}

        {/* Small badge icon at bottom right */}
        <div
          className="absolute -bottom-0.5 -right-0.5 w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] shadow"
          style={{
            background: isShivaji ? "#D97706" : "#4F46E5",
          }}
          title={isShivaji ? "First-Person Roleplay" : "Educational Guide"}
        >
          {isShivaji ? "👑" : "📚"}
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
