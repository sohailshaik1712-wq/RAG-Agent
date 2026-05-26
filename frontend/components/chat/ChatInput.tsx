"use client";

import { useState, useRef, useCallback, KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  isStreaming: boolean;
  onSend:      (text: string) => void;
  onStop:      () => void;
}

export function ChatInput({ isStreaming, onSend, onStop }: ChatInputProps) {
  const [value, setValue]   = useState("");
  const textareaRef         = useRef<HTMLTextAreaElement>(null);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 192)}px`;
  }, []);

  const handleSend = useCallback(() => {
    if (!value.trim() || isStreaming) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [value, isStreaming, onSend]);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }, [handleSend]);

  return (
    <div className="flex items-end gap-3 bg-white border border-border rounded-2xl px-4 py-3 shadow-sm
                    focus-within:border-amber/60 focus-within:shadow-amber/10 focus-within:shadow-md transition-all duration-200">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything about your documents…"
        rows={1}
        disabled={isStreaming}
        className="flex-1 resize-none bg-transparent text-[15px] text-ink placeholder:text-mist
                   focus:outline-none leading-relaxed disabled:opacity-60"
        style={{ maxHeight: "192px" }}
      />
      {isStreaming ? (
        <button
          onClick={onStop}
          className="shrink-0 w-9 h-9 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center hover:bg-red-100 transition-colors"
          title="Stop"
        >
          <Square size={14} className="text-danger fill-danger" />
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          className={cn(
            "shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150",
            value.trim() ? "bg-ink text-paper hover:bg-ink/80 shadow-sm" : "bg-cream text-mist cursor-not-allowed",
          )}
          title="Send (Enter)"
        >
          <Send size={15} />
        </button>
      )}
    </div>
  );
}
