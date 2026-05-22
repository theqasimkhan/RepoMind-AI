"use client";

import { useState } from "react";
import { queryRepositoryChat } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function ArchitectPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [feature, setFeature] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim() || !feature.trim() || loading) return;
    setError(null);
    setAnswer(null);
    setLoading(true);
    try {
      const question = [
        "[Architect mode — staff engineer]",
        "",
        `Feature / change: ${feature.trim()}`,
        "",
        "Respond with: (1) proposed approach, (2) modules and key files likely touched, (3) risks and edge cases, (4) incremental rollout / validation steps.",
        "Keep it concise and actionable for this repository.",
      ].join("\n");
      const res = await queryRepositoryChat({ repo_url: repoUrl.trim(), question });
      setAnswer(res.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto max-w-3xl space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Architect</h1>
        <p className="text-sm leading-relaxed text-white/55 sm:text-base">
          Staff-engineer style prompts over your existing RAG chat API — structured output without a
          separate simulation backend.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel space-y-5 rounded-2xl p-6 sm:p-8">
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-white/45">
            Repository URL
          </label>
          <input
            className="w-full rounded-xl border border-white/12 bg-black/35 px-4 py-2.5 text-sm text-white outline-none ring-cyan-400/0 transition placeholder:text-white/35 focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20"
            placeholder="https://github.com/org/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-white/45">
            Feature or change
          </label>
          <textarea
            className="min-h-[128px] w-full rounded-xl border border-white/12 bg-black/35 px-4 py-3 text-sm text-white outline-none ring-cyan-400/0 transition placeholder:text-white/35 focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20"
            placeholder="Describe what you want to build or change…"
            value={feature}
            onChange={(e) => setFeature(e.target.value)}
            disabled={loading}
          />
        </div>
        <Button type="submit" disabled={loading || !repoUrl.trim() || !feature.trim()}>
          {loading ? "Thinking…" : "Propose architecture"}
        </Button>
        {error ? (
          <p className="rounded-lg border border-red-500/25 bg-red-950/35 px-3 py-2 text-sm text-red-200">
            {error}
          </p>
        ) : null}
      </form>

      {answer ? (
        <div className="glass-panel rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.05] to-transparent p-6 sm:p-8">
          <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200/70">
            Proposal
          </h2>
          <pre className="mt-4 whitespace-pre-wrap font-sans text-sm leading-relaxed text-white/85">
            {answer}
          </pre>
        </div>
      ) : null}
    </section>
  );
}
