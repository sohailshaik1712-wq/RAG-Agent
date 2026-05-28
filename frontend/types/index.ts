// types/index.ts — mirrors backend Pydantic schemas exactly

export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Document {
  id: string;
  filename: string;
  chunks_created: number;
  uploaded_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  documents: Document[];
}

export interface MessageRecord {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: MessageRecord[];
}

// Local UI message (includes streaming state)
export interface UIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  isStreaming?: boolean;
  nodesVisited?: string[];
}

export interface ChatStreamEvent {
  type: "token" | "metadata" | "done" | "error";
  data: string | Record<string, unknown>;
}

export interface IngestResponse {
  status: "success" | "error";
  filename: string;
  chunks_created: number;
  message: string;
}

export const NODE_LABELS: Record<string, string> = {
  query_rewriter: "Rewriting query",
  retriever: "Searching documents",
  relevance_grader: "Grading relevance",
  generator: "Generating answer",
  judge: "Auditing answer",
};
