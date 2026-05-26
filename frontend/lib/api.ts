/**
 * lib/api.ts
 * ──────────
 * Typed API client for all backend calls.
 * Handles JWT auth headers and automatic token refresh.
 */
import type {
  User,
  TokenResponse,
  Conversation,
  ConversationWithMessages,
  IngestResponse,
  ChatStreamEvent,
} from "@/types";

// In Docker: NEXT_PUBLIC_API_URL is empty, browser calls /api/* → rewrite proxy → backend:8000
// In local dev: NEXT_PUBLIC_API_URL=http://localhost:8000, browser calls directly
const NEXT_PUBLIC = process.env.NEXT_PUBLIC_API_URL;
const BASE =
  NEXT_PUBLIC !== undefined && NEXT_PUBLIC !== ""
    ? NEXT_PUBLIC
    : "https://rag-backend-128608771917.us-central1.run.app";

// ── Token management ──────────────────────────────────────────

let _accessToken: string | null = null;
let _refreshToken: string | null = null;
let _onTokenRefresh: ((tokens: TokenResponse) => void) | null = null;

export function setApiTokens(access: string, refresh: string) {
  _accessToken = access;
  _refreshToken = refresh;
}

export function clearApiTokens() {
  _accessToken = null;
  _refreshToken = null;
}

export function onTokenRefresh(cb: (tokens: TokenResponse) => void) {
  _onTokenRefresh = cb;
}

async function refreshAccessToken(): Promise<boolean> {
  if (!_refreshToken) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: _refreshToken }),
    });
    if (!res.ok) return false;
    const tokens: TokenResponse = await res.json();
    _accessToken = tokens.access_token;
    _refreshToken = tokens.refresh_token;
    _onTokenRefresh?.(tokens);
    return true;
  } catch {
    return false;
  }
}

// ── Core fetch with auto-refresh ──────────────────────────────

async function apiFetch(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<Response> {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string>),
  };
  if (_accessToken) headers["Authorization"] = `Bearer ${_accessToken}`;

  const res = await fetch(`${BASE}${path}`, { ...init, headers });

  if (res.status === 401 && retry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiFetch(path, init, false);
  }

  return res;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await apiFetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Request failed: ${res.status}`);
  return data as T;
}

// ── Auth ──────────────────────────────────────────────────────

export async function apiRegister(
  email: string,
  username: string,
  password: string,
): Promise<User> {
  return json("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
  });
}

export async function apiLogin(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return json("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function apiRefresh(refreshToken: string): Promise<TokenResponse> {
  return json("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export async function apiMe(): Promise<User> {
  return json("/auth/me");
}

// ── Conversations ─────────────────────────────────────────────

export async function apiListConversations(): Promise<Conversation[]> {
  return json("/conversations");
}

export async function apiCreateConversation(
  title = "New conversation",
): Promise<Conversation> {
  return json("/conversations", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function apiGetConversation(
  id: string,
): Promise<ConversationWithMessages> {
  return json(`/conversations/${id}`);
}

export async function apiRenameConversation(
  id: string,
  title: string,
): Promise<Conversation> {
  return json(`/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export async function apiDeleteConversation(id: string): Promise<void> {
  const res = await apiFetch(`/conversations/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({ detail: "Delete failed" }));
    throw new Error(err.detail);
  }
}

// ── Ingest ────────────────────────────────────────────────────

export async function apiIngest(
  convId: string,
  file: File,
): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await apiFetch(`/conversations/${convId}/ingest`, {
    method: "POST",
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}

// ── Chat streaming ────────────────────────────────────────────

export interface StreamCallbacks {
  onToken: (t: string) => void;
  onMetadata: (d: { node: string; status: string }) => void;
  onDone: () => void;
  onError: (e: string) => void;
}

export function apiStreamChat(
  convId: string,
  message: string,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (_accessToken) headers["Authorization"] = `Bearer ${_accessToken}`;

      const res = await apiFetch(`/conversations/${convId}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ conversation_id: convId, message }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        const err = await res
          .json()
          .catch(() => ({ detail: "Request failed" }));
        callbacks.onError(err.detail);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.slice(5).trim();
          if (!jsonStr) continue;
          try {
            const event: ChatStreamEvent = JSON.parse(jsonStr);
            if (event.type === "token") callbacks.onToken(event.data as string);
            else if (event.type === "metadata")
              callbacks.onMetadata(
                event.data as { node: string; status: string },
              );
            else if (event.type === "done") callbacks.onDone();
            else if (event.type === "error")
              callbacks.onError(event.data as string);
          } catch {
            /* skip malformed */
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name === "AbortError") return;
      callbacks.onError(e instanceof Error ? e.message : "Unknown error");
    }
  })();

  return controller;
}

export async function apiDeleteDocument(
  convId: string,
  docId: string,
): Promise<void> {
  const res = await apiFetch(`/conversations/${convId}/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({ detail: "Delete failed" }));
    throw new Error(err.detail);
  }
}
