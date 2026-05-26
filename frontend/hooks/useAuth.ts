"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useConversationStore } from "@/store/conversationStore";
import { setApiTokens, clearApiTokens, onTokenRefresh, apiLogin, apiRegister, apiMe } from "@/lib/api";
import type { TokenResponse } from "@/types";

export function useAuth() {
  const store  = useAuthStore();
  const conversations = useConversationStore();
  const router = useRouter();

  // Sync tokens into the API client whenever they change (e.g. after hydration)
  useEffect(() => {
    if (store.accessToken && store.refreshToken) {
      setApiTokens(store.accessToken, store.refreshToken);
    }
    onTokenRefresh((tokens: TokenResponse) => {
      store.setTokens(tokens);
    });
  }, [store.accessToken, store.refreshToken]);

  const login = async (email: string, password: string) => {
    const tokens = await apiLogin(email, password);
    setApiTokens(tokens.access_token, tokens.refresh_token);
    const user = await apiMe();
    store.setAuth(user, tokens);
  };

  const register = async (email: string, username: string, password: string) => {
    await apiRegister(email, username, password);
    await login(email, password);
  };

  const logout = () => {
    store.clearAuth();
    conversations.clearConversations();
    clearApiTokens();
    router.push("/login");
  };

  return {
    user:      store.user,
    isLogged:  store.isLoggedIn(),
    login,
    register,
    logout,
  };
}
