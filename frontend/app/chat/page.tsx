"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ChatInterface } from "@/components/chat-interface";
import { CodeDnaViz } from "@/components/code-dna-viz";
import { getLatestRepositoryAnalysis } from "@/lib/api";
import type { AnalysisResponse } from "@/lib/types";
import Link from "next/link";
import { Button } from "@/components/ui/button";

function ChatContent() {
  const searchParams = useSearchParams();
  const repoUrl = searchParams.get("repo_url");
  const repoName = searchParams.get("repo_name") || "this repository";
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisHint, setAnalysisHint] = useState<string | null>(null);
  const [highlightPaths, setHighlightPaths] = useState<string[]>([]);

  useEffect(() => {
    if (!repoUrl) return;
    let cancelled = false;
    setAnalysisHint(null);
    void (async () => {
      try {
        const snap = await getLatestRepositoryAnalysis(repoUrl);
        if (!cancelled) {
          setAnalysis(snap);
          if (!snap) {
            setAnalysisHint("No completed analysis for this URL yet — Galaxy appears after a successful dashboard run.");
          }
        }
      } catch {
        if (!cancelled) {
          setAnalysis(null);
          setAnalysisHint("Could not load analysis metadata (check API base URL and auth).");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [repoUrl]);

  if (!repoUrl) {
    return (
      <div className="flex flex-col items-center justify-center space-y-6 py-16 text-center">
        <div className="max-w-md rounded-2xl border border-white/10 bg-white/[0.03] px-8 py-10 shadow-2xl shadow-black/30 backdrop-blur-md">
          <h1 className="text-2xl font-bold tracking-tight text-white">Pick a repository</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/55">
            Open chat from the dashboard after an analysis job, or append{" "}
            <code className="rounded bg-black/40 px-1.5 py-0.5 text-xs text-cyan-200/90">
              ?repo_url=…&repo_name=…
            </code>{" "}
            to the URL.
          </p>
          <div className="mt-8">
            <Link href="/dashboard">
              <Button>Go to dashboard</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Repository chat</h1>
        <p className="max-w-3xl text-sm text-white/55 sm:text-base">
          Citations and traces are grounded in retrieval from{" "}
          <span className="font-medium text-cyan-200/90">{repoName}</span>.
        </p>
      </div>
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(280px,440px)]">
        <ChatInterface
          repoUrl={repoUrl}
          repoName={repoName}
          onAssistantEvidence={(paths) => setHighlightPaths(paths)}
        />
        <div className="space-y-4">
          {analysis ? (
            <>
              <CodeDnaViz fileTree={analysis.file_tree} className="glass-panel rounded-2xl p-4" />
            </>
          ) : (
            <div className="glass-panel rounded-2xl p-5 text-sm text-white/60">
              <p className="font-medium text-white/80">Code DNA</p>
              <p className="mt-2 leading-relaxed">
                {analysisHint ??
                  "Run analysis from the dashboard for this repository URL to unlock the Code DNA panel."}
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/15 border-t-cyan-400" />
          <p className="text-sm text-white/50">Loading chat…</p>
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
