"use client";
import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useConversationStore } from "@/store/conversationStore";
import { useAuthStore } from "@/store/authStore";
import {
  apiListConversations, apiCreateConversation,
  apiDeleteConversation, apiRenameConversation,
  setApiTokens,
} from "@/lib/api";

export function useConversations() {
  const store    = useConversationStore();
  const auth     = useAuthStore();
  const router   = useRouter();

  const refresh = useCallback(async () => {
    if (!auth.isLoggedIn() || !auth.accessToken) return;
    // Always ensure tokens are synced before any API call
    setApiTokens(auth.accessToken, auth.refreshToken ?? "");
    try {
      const list = await apiListConversations();
      store.setConversations(list);
    } catch { /* silently fail — local cache still shown */ }
  }, [auth.accessToken, auth.refreshToken]);

  useEffect(() => {
    // Re-fetch every time the token changes (login, refresh, page load)
    if (auth.accessToken) {
      refresh();
    }
  }, [auth.accessToken]);

  const createNew = async () => {
    const conv = await apiCreateConversation();
    store.addConversation(conv);
    store.setActiveId(conv.id);
    router.push(`/chat/${conv.id}`);
    return conv;
  };

  const remove = async (id: string) => {
    await apiDeleteConversation(id);
    store.removeConversation(id);
    if (store.activeId === id) {
      const next = store.conversations.find(c => c.id !== id);
      if (next) router.push(`/chat/${next.id}`);
      else      router.push("/chat/new");
    }
  };

  const rename = async (id: string, title: string) => {
    const updated = await apiRenameConversation(id, title);
    store.updateConversation(id, { title: updated.title });
  };

  return {
    conversations:      store.conversations,
    activeId:           store.activeId,
    setActiveId:        store.setActiveId,
    createNew,
    remove,
    rename,
    refresh,
    updateConversation: store.updateConversation,
  };
}
