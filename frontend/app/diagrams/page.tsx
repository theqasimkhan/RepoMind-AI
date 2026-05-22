"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";

import { MermaidDiagram } from "@/components/mermaid-diagram";
import { Button } from "@/components/ui/button";

const DEFAULT_CHART = `graph TD
A[Frontend] --> B[Backend]
B --> C[(PostgreSQL)]
B --> D[(Vector Store)]
B --> E[AI Engine]`;

function DiagramsContent() {
  const params = useSearchParams();
  const initialChart = params.get("chart") || DEFAULT_CHART;
  const [chart, setChart] = useState(initialChart);

  const copyShareLink = async () => {
    const baseUrl = window.location.origin;
    const url = `${baseUrl}/diagrams?chart=${encodeURIComponent(chart)}`;
    await navigator.clipboard.writeText(url);
  };

  return (
    <section className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Diagram viewer</h1>
        <p className="max-w-2xl text-sm text-white/55 sm:text-base">
          Edit Mermaid in real time, preview, and copy a shareable link for your README or PR.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card space-y-2">
          <h2 className="text-lg font-semibold">Mermaid Source</h2>
          <p className="text-sm text-white/70">
            Paste or edit Mermaid syntax to preview architecture diagrams in real time.
          </p>
          <Button variant="outline" onClick={copyShareLink} type="button">
            Copy Share Link
          </Button>
          <textarea
            value={chart}
            onChange={(event) => setChart(event.target.value)}
            className="h-[360px] w-full rounded-xl border border-white/12 bg-black/35 p-4 text-sm text-white/90 outline-none ring-cyan-400/0 transition focus:border-cyan-400/45 focus:ring-2 focus:ring-cyan-400/15"
          />
        </div>
        <div className="card">
          <MermaidDiagram chart={chart} title="Live Preview" />
        </div>
      </div>
    </section>
  );
}

export default function DiagramsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[30vh] items-center justify-center gap-3 text-sm text-white/50">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/15 border-t-cyan-400" />
          Loading diagram…
        </div>
      }
    >
      <DiagramsContent />
    </Suspense>
  );
}
