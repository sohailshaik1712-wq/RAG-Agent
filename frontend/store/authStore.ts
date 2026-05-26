/**
 * store/authStore.ts
 * ───────────────────
 * Persisted Zustand store for auth state.
 * Tokens survive page refresh and logout/login cycles.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, TokenResponse } from "@/types";

interface AuthState {
  user:          User | null;
  accessToken:   string | null;
  refreshToken:  string | null;
  setAuth:       (user: User, tokens: TokenResponse) => void;
  setTokens:     (tokens: TokenResponse) => void;
  clearAuth:     () => void;
  isLoggedIn:    () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user:         null,
      accessToken:  null,
      refreshToken: null,

      setAuth: (user, tokens) =>
        set({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),

      setTokens: (tokens) =>
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),

      clearAuth: () => set({ user: null, accessToken: null, refreshToken: null }),

      isLoggedIn: () => !!get().accessToken,
    }),
    {
      name: "rag-auth",   // localStorage key
      partialize: (s) => ({
        user:         s.user,
        accessToken:  s.accessToken,
        refreshToken: s.refreshToken,
      }),
    },
  ),
);
