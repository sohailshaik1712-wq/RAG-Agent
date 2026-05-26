/**
 * store/conversationStore.ts
 * ────────────────────────────
 * Persisted store for conversation list and active conversation.
 * Syncs with the backend on load; local copy used for instant UI updates.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Conversation } from "@/types";

interface ConversationState {
  conversations:      Conversation[];
  activeId:           string | null;
  setConversations:   (convs: Conversation[]) => void;
  addConversation:    (conv: Conversation) => void;
  updateConversation: (id: string, patch: Partial<Conversation>) => void;
  removeConversation: (id: string) => void;
  setActiveId:        (id: string | null) => void;
  clearConversations: () => void;
}

export const useConversationStore = create<ConversationState>()(
  persist(
    (set) => ({
      conversations: [],
      activeId:      null,

      setConversations: (convs) => set({ conversations: convs }),

      addConversation: (conv) =>
        set((s) => ({ conversations: [conv, ...s.conversations] })),

      updateConversation: (id, patch) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === id ? { ...c, ...patch } : c
          ),
        })),

      removeConversation: (id) =>
        set((s) => ({
          conversations: s.conversations.filter((c) => c.id !== id),
          activeId: s.activeId === id ? (s.conversations.find(c => c.id !== id)?.id ?? null) : s.activeId,
        })),

      setActiveId: (id) => set({ activeId: id }),

      clearConversations: () => set({ conversations: [], activeId: null }),
    }),
    {
      name: "rag-conversations",
      partialize: (s) => ({ conversations: s.conversations, activeId: s.activeId }),
    },
  ),
);
