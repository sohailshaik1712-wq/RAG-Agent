"use client";

import { Loader2 } from "lucide-react";

interface ThinkingBarProps {
  label:   string | null;
  visible: boolean;
}

export function ThinkingBar({ label, visible }: ThinkingBarProps) {
  if (!visible || !label) return null;
  return (
    <div className="flex items-center gap-2.5 px-6 py-2 border-t border-border bg-amber-light/60 animate-fade-in shrink-0">
      <Loader2 size={13} className="text-amber animate-spin shrink-0" />
      <span className="text-xs text-amber font-medium">{label}…</span>
      <div className="flex-1 h-0.5 rounded-full overflow-hidden bg-amber/20 ml-2">
        <div
          className="h-full rounded-full bg-amber/50"
          style={{
            width: "40%",
            animation: "shimmer 1.8s linear infinite",
            backgroundImage: "linear-gradient(90deg, transparent 0%, #D97706 50%, transparent 100%)",
            backgroundSize: "200% 100%",
          }}
        />
      </div>
    </div>
  );
}
