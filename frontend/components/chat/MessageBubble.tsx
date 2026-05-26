"use client";

import ReactMarkdown    from "react-markdown";
import remarkGfm        from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark }      from "react-syntax-highlighter/dist/esm/styles/prism";
import { cn }           from "@/lib/utils";
import { NODE_LABELS }  from "@/types";
import type { UIMessage } from "@/types";

interface Props {
  message:  UIMessage;
  isLatest: boolean;
}

export function MessageBubble({ message, isLatest }: Props) {
  const isUser      = message.role === "user";
  const isStreaming = message.isStreaming;

  return (
    <div className={cn("flex gap-3 animate-fade-up", isUser ? "flex-row-reverse" : "flex-row")}>

      {/* Avatar */}
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5",
        isUser ? "bg-ink text-paper" : "bg-amber text-white",
      )}>
        {isUser ? "U" : "AI"}
      </div>

      {/* Content */}
      <div className={cn("flex flex-col gap-1.5 max-w-[80%]", isUser && "items-end")}>
        <div className={cn(
          "rounded-2xl px-4 py-3",
          isUser
            ? "bg-ink text-paper rounded-tr-sm text-[15px] leading-relaxed"
            : "bg-white border border-border rounded-tl-sm shadow-sm",
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-rag">
              {message.content ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // @ts-expect-error react-markdown types
                    code({ inline, className, children, ...props }) {
                      const lang = /language-(\w+)/.exec(className || "")?.[1];
                      return !inline && lang ? (
                        <SyntaxHighlighter
                          style={oneDark}
                          language={lang}
                          PreTag="div"
                          customStyle={{ margin: 0, borderRadius: 8, fontSize: 13, padding: 16 }}
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>{children}</code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              ) : isStreaming ? (
                <TypingDots />
              ) : null}

              {/* Streaming cursor */}
              {isStreaming && message.content && (
                <span className="inline-block w-0.5 h-4 bg-amber ml-0.5 animate-pulse align-middle" />
              )}
            </div>
          )}
        </div>

        {/* Node badges — shown after stream completes */}
        {!isUser && !isStreaming && !!message.nodesVisited?.length && (
          <div className="flex flex-wrap gap-1 px-1">
            {message.nodesVisited.map((n) => (
              <span
                key={n}
                className="text-[10px] px-2 py-0.5 rounded-full bg-cream border border-border text-mist font-mono"
              >
                {NODE_LABELS[n] ?? n}
              </span>
            ))}
          </div>
        )}

        <span className="text-[11px] text-mist px-1">
          {new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span key={i} className="typing-dot w-2 h-2 rounded-full bg-mist" />
      ))}
    </div>
  );
}
