"use client";

import { useState, useEffect } from "react";
import { useRouter }           from "next/navigation";
import { Menu, X }             from "lucide-react";
import { Sidebar }             from "@/components/layout/Sidebar";
import { useAuthStore }        from "@/store/authStore";
import { setApiTokens, onTokenRefresh } from "@/lib/api";
import type { TokenResponse }  from "@/types";

export function ChatShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [hydrated,    setHydrated]    = useState(false);
  const auth   = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // Wait for Zustand to hydrate from localStorage before checking auth
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;

    if (!auth.accessToken) {
      router.replace("/login");
      return;
    }
    // Sync tokens into API client immediately after hydration
    setApiTokens(auth.accessToken, auth.refreshToken ?? "");
    onTokenRefresh((tokens: TokenResponse) => auth.setTokens(tokens));
  }, [hydrated, auth.accessToken, auth.refreshToken]);

  // Don't render children until hydrated — prevents flash of unauthenticated content
  if (!hydrated) return null;
  if (!auth.accessToken) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-paper">
      <aside className="hidden md:flex md:w-72 lg:w-80 flex-col border-r border-border bg-cream shrink-0">
        <Sidebar />
      </aside>

      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-ink/30 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <aside className="relative z-50 w-72 flex flex-col bg-cream border-r border-border animate-slide-in">
            <button onClick={() => setSidebarOpen(false)} className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-border/60 transition-colors">
              <X size={18} className="text-mist" />
            </button>
            <Sidebar onNavigate={() => setSidebarOpen(false)} />
          </aside>
        </div>
      )}

      <main className="flex-1 flex flex-col min-w-0">
        <div className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-border bg-cream/80 backdrop-blur-sm shrink-0">
          <button onClick={() => setSidebarOpen(true)} className="p-1.5 rounded-lg hover:bg-border/60 transition-colors">
            <Menu size={20} className="text-ink" />
          </button>
          <span className="font-display text-lg text-ink">RAG Agent</span>
        </div>
        <div className="flex-1 overflow-hidden">{children}</div>
      </main>
    </div>
  );
}
