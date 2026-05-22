"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { queryRepositoryChat } from "@/lib/api";
import { collectEvidencePaths } from "@/lib/evidence-paths";
import { SourceCitation, TraceStep } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { MermaidDiagram } from "@/components/mermaid-diagram";

type Message = {
  role: "user" | "assistant";
  content: string;
  references?: string[];
  citations?: SourceCitation[];
  traceSteps?: TraceStep[];
  agentEnabled?: boolean;
  agentDegraded?: boolean;
  diagramMermaid?: string | null;
};

type ChatInterfaceProps = {
  repoUrl: string;
  repoName: string;
  onAssistantEvidence?: (paths: string[]) => void;
};

export function ChatInterface({ repoUrl, repoName, onAssistantEvidence }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await queryRepositoryChat({
        repo_url: repoUrl,
        question: userMessage,
      });

      const evidencePaths = collectEvidencePaths(
        response.citations,
        response.references,
        response.trace?.trace_steps,
      );
      onAssistantEvidence?.(evidencePaths);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          references: response.references,
          citations: response.citations,
          traceSteps: response.trace?.trace_steps,
          agentEnabled: response.trace?.agent_enabled,
          agentDegraded: response.trace?.agent_degraded,
          diagramMermaid: response.diagram_mermaid ?? undefined,
        },
      ]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel flex h-[600px] flex-col overflow-hidden rounded-2xl">
      {/* Header */}
      <div className="border-b border-white/10 bg-gradient-to-r from-cyan-500/[0.07] via-transparent to-violet-500/[0.06] p-4 backdrop-blur-md">
        <h3 className="text-sm font-semibold text-white">Chatting with {repoName}</h3>
        <p className="mt-0.5 truncate text-xs text-white/50">{repoUrl}</p>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10"
      >
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center space-y-2 opacity-50">
            <div className="rounded-full bg-accent/20 p-3">
              <svg
                className="h-6 w-6 text-accent"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <p className="text-sm">Ask anything about this repository's code or architecture.</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                  m.role === "user"
                    ? "bg-accent text-white"
                    : "bg-white/10 text-white/90"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>
                {m.citations && m.citations.length > 0 && (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">
                      Citations
                    </p>
                    <div className="mt-1 flex flex-col gap-1">
                      {m.citations.map((c, idx) => (
                        <span
                          key={idx}
                          className="rounded bg-black/30 px-1.5 py-0.5 text-[10px] font-mono text-white/70"
                        >
                          {c.file_path}
                          {c.start_line != null && c.end_line != null
                            ? ` (${c.start_line}–${c.end_line})`
                            : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {m.references && m.references.length > 0 && !m.citations?.length && (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">
                      References
                    </p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {m.references.map((ref, idx) => (
                        <span
                          key={idx}
                          className="rounded bg-black/30 px-1.5 py-0.5 text-[10px] font-mono text-white/60"
                        >
                          {ref.split("/").pop()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {m.traceSteps && m.traceSteps.length > 0 && (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <details className="group text-left">
                      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wider text-white/40 hover:text-white/60">
                        {m.agentEnabled ? "Agent steps" : "Trace steps"}
                        {m.agentEnabled && m.agentDegraded ? (
                          <span className="ml-2 normal-case text-amber-400/90">(degraded)</span>
                        ) : null}
                      </summary>
                      <ol className="mt-2 max-h-40 list-decimal space-y-1 overflow-y-auto pl-4 text-[10px] text-white/55">
                        {m.traceSteps.map((s, idx) => (
                          <li key={idx} className="font-mono">
                            <span className="text-white/70">{s.name}</span>
                            <span className="text-white/35"> · {s.kind}</span>
                            {s.latency_ms != null ? (
                              <span className="text-white/35"> · {s.latency_ms}ms</span>
                            ) : null}
                          </li>
                        ))}
                      </ol>
                    </details>
                  </div>
                )}
                {m.diagramMermaid && m.diagramMermaid.trim().length > 0 && (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-white/40">
                      Agent diagram
                    </p>
                    <MermaidDiagram chart={m.diagramMermaid} title="" enableExport={false} />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="rounded-2xl bg-white/10 px-4 py-2">
              <div className="flex space-x-1">
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40 [animation-delay:-0.3s]"></div>
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40 [animation-delay:-0.15s]"></div>
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40"></div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-white/10 bg-white/[0.03] p-4 backdrop-blur-md">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            className="flex-1 rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/50"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </div>
      </form>
    </div>
  );
}
