/**
 * app/chat/layout.tsx
 * ─────────────────────
 * Shared layout for all chat pages. Renders the sidebar alongside content.
 * This is a Server Component wrapper; the actual sidebar is a client component.
 */
import { ChatShell } from "@/components/layout/ChatShell";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <ChatShell>{children}</ChatShell>;
}
