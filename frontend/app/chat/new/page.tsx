/**
 * app/chat/new/page.tsx
 * ──────────────────────
 * Landing route for authenticated users. Shows the empty state
 * with suggestions. Clicking "New Chat" in the sidebar creates
 * a conversation and navigates to /chat/[id].
 */
"use client";

import { Sparkles } from "lucide-react";
import { useConversations } from "@/hooks/useConversations";

const SUGGESTIONS = [
  "What are the main topics covered in my documents?",
  "Summarise the key points from the uploaded files.",
  "What is the refund or return policy?",
  "Explain the most important concepts simply.",
];

export default function NewChatPage() {
  const { createNew } = useConversations();

  const handleSuggestion = async (text: string) => {
    const conv = await createNew();
    // Small delay so navigation happens before sendMessage
    setTimeout(() => {
      const event = new CustomEvent("rag:send-message", { detail: { convId: conv.id, text } });
      window.dispatchEvent(event);
    }, 300);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4 py-16 gap-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="w-14 h-14 rounded-2xl bg-ink flex items-center justify-center shadow-lg">
          <Sparkles size={24} className="text-amber" />
        </div>
        <div>
          <h2 className="font-display text-3xl text-ink mb-2">Ask your documents</h2>
          <p className="text-mist text-sm max-w-sm leading-relaxed">
            Create a new conversation, upload a PDF or text file, then ask
            anything. The agent retrieves, grades, and generates a grounded answer.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSuggestion(s)}
            className="text-left px-4 py-3 rounded-xl border border-border bg-white
                       hover:border-amber/50 hover:bg-amber-light/30 hover:shadow-sm
                       text-sm text-ink transition-all duration-150 group"
          >
            <span className="text-amber mr-1.5">→</span>{s}
          </button>
        ))}
      </div>
    </div>
  );
}
