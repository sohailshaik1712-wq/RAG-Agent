"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import { v4 as uuid } from "uuid";
import { apiStreamChat } from "@/lib/api";
import type { UIMessage, MessageRecord } from "@/types";
import { NODE_LABELS } from "@/types";

export function useChat(convId: string) {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [isStreaming,  setIsStreaming]  = useState(false);
  const [activeNode,   setActiveNode]   = useState<string | null>(null);
  const abortRef       = useRef<AbortController | null>(null);
  const streamingIdRef = useRef<string | null>(null);

  // Reset messages when conversation changes — the page will load and set them
  useEffect(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsStreaming(false);
    setActiveNode(null);
    streamingIdRef.current = null;
  }, [convId]);

  // Called by the page once apiGetConversation resolves
  const loadMessages = useCallback((records: MessageRecord[]) => {
    setMessages(records.map(m => ({
      id: m.id, role: m.role, content: m.content,
      createdAt: m.created_at, isStreaming: false,
    })));
  }, []);

  const sendMessage = useCallback((text: string) => {
    if (isStreaming || !text.trim()) return;

    const userMsg: UIMessage = { id: uuid(), role: "user",      content: text.trim(), createdAt: new Date().toISOString() };
    const asstId = uuid();
    const asstMsg: UIMessage = { id: asstId, role: "assistant", content: "",          createdAt: new Date().toISOString(), isStreaming: true, nodesVisited: [] };

    streamingIdRef.current = asstId;
    setMessages(prev => [...prev, userMsg, asstMsg]);
    setIsStreaming(true);

    abortRef.current = apiStreamChat(convId, text.trim(), {
      onToken: (token) =>
        setMessages(prev => prev.map(m => m.id === asstId ? { ...m, content: m.content + token } : m)),

      onMetadata: ({ node, status }) => {
        if (status === "started") setActiveNode(node);
        else {
          setActiveNode(null);
          setMessages(prev => prev.map(m =>
            m.id === asstId ? { ...m, nodesVisited: [...(m.nodesVisited ?? []), node] } : m
          ));
        }
      },

      onDone: () => {
        setIsStreaming(false); setActiveNode(null); streamingIdRef.current = null;
        setMessages(prev => prev.map(m => m.id === asstId ? { ...m, isStreaming: false } : m));
      },

      onError: (err) => {
        setIsStreaming(false); setActiveNode(null); streamingIdRef.current = null;
        setMessages(prev => prev.map(m =>
          m.id === asstId ? { ...m, content: m.content || `⚠ Error: ${err}`, isStreaming: false } : m
        ));
      },
    });
  }, [convId, isStreaming]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false); setActiveNode(null);
    if (streamingIdRef.current) {
      setMessages(prev => prev.map(m => m.id === streamingIdRef.current ? { ...m, isStreaming: false } : m));
      streamingIdRef.current = null;
    }
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  return {
    messages, isStreaming,
    activeNode,
    activeNodeLabel: activeNode ? (NODE_LABELS[activeNode] ?? activeNode) : null,
    loadMessages, sendMessage, stop,
  };
}
