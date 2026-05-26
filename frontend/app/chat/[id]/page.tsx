"use client";

import { useEffect, useState } from "react";
import { useParams }                    from "next/navigation";
import { apiGetConversation }           from "@/lib/api";
import { useChat }                      from "@/hooks/useChat";
import { useConversations }             from "@/hooks/useConversations";
import { useAuthStore }                 from "@/store/authStore";
import { setApiTokens }                 from "@/lib/api";
import { ChatMessages }                 from "@/components/chat/ChatMessages";
import { ChatInput }                    from "@/components/chat/ChatInput";
import { ThinkingBar }                  from "@/components/chat/ThinkingBar";
import { Loader2 }                      from "lucide-react";

export default function ConversationPage() {
  const params  = useParams<{ id: string }>();
  const convId  = params.id;

  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const { updateConversation } = useConversations();
  const auth = useAuthStore();

  // useChat no longer takes initialMessages — we call loadMessages after fetch
  const chat = useChat(convId);

  useEffect(() => {
    if (!convId || convId === "new") { setLoading(false); return; }
    if (!auth.accessToken) return;

    setApiTokens(auth.accessToken, auth.refreshToken ?? "");
    setLoading(true);
    setError(null);

    apiGetConversation(convId)
      .then((data) => {
        // Feed loaded messages into the chat hook once they arrive
        chat.loadMessages(data.messages);
        updateConversation(convId, { title: data.title, documents: data.documents });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [convId, auth.accessToken]);

  // Suggestion events from /chat/new
  useEffect(() => {
    const handler = (e: Event) => {
      const { convId: targetId, text } = (e as CustomEvent).detail;
      if (targetId === convId) chat.sendMessage(text);
    };
    window.addEventListener("rag:send-message", handler);
    return () => window.removeEventListener("rag:send-message", handler);
  }, [convId, chat.sendMessage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-mist" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-danger">Failed to load conversation: {error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <ChatMessages messages={chat.messages} isStreaming={chat.isStreaming} />
      <ThinkingBar label={chat.activeNodeLabel} visible={chat.isStreaming && !!chat.activeNodeLabel} />
      <div className="border-t border-border bg-paper/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput isStreaming={chat.isStreaming} onSend={chat.sendMessage} onStop={chat.stop} />
        </div>
      </div>
    </div>
  );
}
