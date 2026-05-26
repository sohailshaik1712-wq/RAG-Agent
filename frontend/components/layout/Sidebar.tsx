"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter, usePathname }        from "next/navigation";
import { useDropzone }                   from "react-dropzone";
import Link                              from "next/link";
import {
  Plus, MessageSquare, Trash2, Upload, FileText,
  CheckCircle, AlertCircle, Loader2, Cpu,
  LogOut, Pencil, ChevronRight, User,
} from "lucide-react";
import { cn }                       from "@/lib/utils";
import { useConversations }         from "@/hooks/useConversations";
import { useAuth }                  from "@/hooks/useAuth";
import { apiIngest, apiDeleteDocument } from "@/lib/api";
import { useConversationStore }     from "@/store/conversationStore";
import type { Conversation }        from "@/types";

interface SidebarProps {
  onNavigate?: () => void;
}

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "success"; filename: string; chunks: number }
  | { status: "error"; message: string };

export function Sidebar({ onNavigate }: SidebarProps) {
  const router    = useRouter();
  const pathname  = usePathname();
  const { user, logout }                  = useAuth();
  const { conversations, createNew, remove, rename, refresh, updateConversation } = useConversations();
  const { activeId, setActiveId }         = useConversationStore();

  const [uploadState, setUploadState]     = useState<UploadState>({ status: "idle" });
  const [renamingId,  setRenamingId]      = useState<string | null>(null);
  const [renameValue, setRenameValue]     = useState("");
  const renameInputRef = useRef<HTMLInputElement>(null);

  // Active conv id from URL
  const urlId = pathname?.split("/chat/")?.[1] ?? null;
  const currentId = urlId && urlId !== "new" ? urlId : null;

  // ── Upload via dropzone ───────────────────────────────────
  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file || !currentId) {
      if (!currentId) {
        alert("Please open or create a conversation before uploading.");
      }
      return;
    }
    setUploadState({ status: "uploading" });
    try {
      const result = await apiIngest(currentId, file);
      await refresh();
      setUploadState({ status: "success", filename: result.filename, chunks: result.chunks_created });
      setTimeout(() => setUploadState({ status: "idle" }), 4000);
    } catch (err: unknown) {
      setUploadState({ status: "error", message: err instanceof Error ? err.message : "Upload failed" });
      setTimeout(() => setUploadState({ status: "idle" }), 4000);
    }
  }, [currentId, refresh]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "text/plain": [".txt"], "text/markdown": [".md"] },
    maxFiles: 1,
    disabled: uploadState.status === "uploading",
  });

  // ── Rename helpers ────────────────────────────────────────
  const startRename = (conv: Conversation) => {
    setRenamingId(conv.id);
    setRenameValue(conv.title);
    setTimeout(() => renameInputRef.current?.focus(), 50);
  };

  const commitRename = async (id: string) => {
    if (renameValue.trim() && renameValue.trim() !== conversations.find(c => c.id === id)?.title) {
      await rename(id, renameValue.trim());
    }
    setRenamingId(null);
  };

  return (
    <div className="flex flex-col h-full">

      {/* ── Header ─────────────────────────────────────── */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-8 h-8 rounded-lg bg-ink flex items-center justify-center shrink-0">
            <Cpu size={15} className="text-amber" />
          </div>
          <div>
            <h1 className="font-display text-lg text-ink leading-none">RAG Agent</h1>
            <p className="text-[10px] text-mist">Gemini Flash 2.5 · LangGraph</p>
          </div>
        </div>

        {/* New Chat button */}
        <button
          onClick={async () => { await createNew(); onNavigate?.(); }}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl
                     bg-ink text-paper text-sm font-medium
                     hover:bg-ink/85 transition-colors shadow-sm"
        >
          <Plus size={15} />
          New Chat
        </button>
      </div>

      {/* ── Conversations list ──────────────────────────── */}
      <div className="flex-1 overflow-y-auto py-3 px-2">
        {conversations.length === 0 ? (
          <p className="text-xs text-mist text-center py-6 px-4">
            No conversations yet. Click New Chat to start.
          </p>
        ) : (
          <div className="space-y-0.5">
            <p className="text-[10px] font-semibold tracking-widest uppercase text-mist px-2 pb-1">
              Recent Chats
            </p>
            {conversations.map((conv) => {
              const isActive = conv.id === currentId;
              return (
                <div
                  key={conv.id}
                  className={cn(
                    "group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-all duration-100",
                    isActive
                      ? "bg-cream border border-border"
                      : "hover:bg-cream/60",
                  )}
                >
                  <MessageSquare size={13} className={cn("shrink-0", isActive ? "text-amber" : "text-mist")} />

                  {renamingId === conv.id ? (
                    <input
                      ref={renameInputRef}
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => commitRename(conv.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter")  commitRename(conv.id);
                        if (e.key === "Escape") setRenamingId(null);
                      }}
                      className="flex-1 bg-white border border-border rounded px-1.5 py-0.5 text-xs text-ink focus:outline-none focus:border-amber/60"
                    />
                  ) : (
                    <span
                      className="flex-1 text-sm text-ink truncate"
                      onClick={() => {
                        router.push(`/chat/${conv.id}`);
                        setActiveId(conv.id);
                        onNavigate?.();
                      }}
                    >
                      {conv.title}
                    </span>
                  )}

                  {/* Action buttons — shown on hover */}
                  {renamingId !== conv.id && (
                    <div className="hidden group-hover:flex items-center gap-1 shrink-0">
                      <button
                        onClick={(e) => { e.stopPropagation(); startRename(conv); }}
                        className="p-1 rounded hover:bg-border transition-colors"
                        title="Rename"
                      >
                        <Pencil size={11} className="text-mist" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); remove(conv.id); }}
                        className="p-1 rounded hover:bg-red-100 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={11} className="text-mist hover:text-danger" />
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Document upload ─────────────────────────────── */}
      <div className="px-3 py-3 border-t border-border">
        <p className="text-[10px] font-semibold tracking-widest uppercase text-mist mb-2 px-1">
          Knowledge Base
        </p>

        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all duration-150",
            isDragActive
              ? "border-amber bg-amber-light"
              : "border-border hover:border-mist hover:bg-cream/60",
            uploadState.status === "uploading" && "pointer-events-none opacity-60",
            !currentId && "opacity-40 cursor-not-allowed",
          )}
        >
          <input {...getInputProps()} />

          {uploadState.status === "uploading" ? (
            <div className="flex items-center justify-center gap-2">
              <Loader2 size={16} className="text-amber animate-spin" />
              <span className="text-xs text-mist">Embedding…</span>
            </div>
          ) : uploadState.status === "success" ? (
            <div className="flex items-center justify-center gap-2">
              <CheckCircle size={16} className="text-sage" />
              <div className="text-left">
                <p className="text-xs font-medium text-sage truncate max-w-[140px]">{uploadState.filename}</p>
                <p className="text-[10px] text-mist">{uploadState.chunks} chunks indexed</p>
              </div>
            </div>
          ) : uploadState.status === "error" ? (
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="text-danger shrink-0" />
              <p className="text-xs text-danger line-clamp-2">{uploadState.message}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1.5">
              <Upload size={18} className={isDragActive ? "text-amber" : "text-mist"} />
              <p className="text-xs text-ink font-medium">
                {isDragActive ? "Drop to upload" : currentId ? "Upload document" : "Open a chat first"}
              </p>
              <p className="text-[10px] text-mist">PDF · TXT · MD</p>
            </div>
          )}
        </div>

        {/* Docs list for current conversation */}
        {currentId && (() => {
          const conv = conversations.find(c => c.id === currentId);
          return conv?.documents?.length ? (
            <div className="mt-2 space-y-1">
              {conv.documents.map((doc) => (
                <div key={doc.id} className="group flex items-center gap-1.5 px-1">
                  <FileText size={11} className="text-mist shrink-0" />
                  <span className="text-[11px] text-mist truncate flex-1">{doc.filename}</span>
                  <span className="text-[10px] text-mist/60 shrink-0 group-hover:hidden">{doc.chunks_created}c</span>
                  <button
                    onClick={async () => {
                      if (!confirm(`Delete "${doc.filename}"?`)) return;
                      try {
                        await apiDeleteDocument(currentId, doc.id);
                        // Remove doc from local store immediately
                        updateConversation(currentId, {
                          documents: conv.documents.filter(d => d.id !== doc.id),
                        });
                      } catch (e: unknown) {
                        alert(e instanceof Error ? e.message : "Delete failed");
                      }
                    }}
                    className="hidden group-hover:flex items-center justify-center w-4 h-4 rounded hover:bg-red-100 transition-colors shrink-0"
                    title="Delete document"
                  >
                    <Trash2 size={10} className="text-danger" />
                  </button>
                </div>
              ))}
            </div>
          ) : null;
        })()}
      </div>

      {/* ── User footer ─────────────────────────────────── */}
      <div className="px-3 pb-3 pt-2 border-t border-border">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg">
          <div className="w-7 h-7 rounded-full bg-ink flex items-center justify-center shrink-0">
            <User size={13} className="text-paper" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-ink truncate">{user?.username ?? "…"}</p>
            <p className="text-[10px] text-mist truncate">{user?.email ?? ""}</p>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="p-1.5 rounded-lg hover:bg-cream transition-colors"
          >
            <LogOut size={14} className="text-mist hover:text-danger transition-colors" />
          </button>
        </div>
      </div>

    </div>
  );
}
