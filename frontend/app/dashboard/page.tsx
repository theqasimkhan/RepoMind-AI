"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { AnalysisResult } from "@/components/analysis-result";
import { RepositoryForm } from "@/components/repository-form";
import {
  getRepositoryAnalysisStatus,
  listRepositoryAnalysisJobs,
  startRepositoryAnalysis,
} from "@/lib/api";
import { AnalysisJobStatusResponse, AnalysisResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [history, setHistory] = useState<AnalysisJobStatusResponse[]>([]);

  const refreshHistory = async () => {
    const jobs = await listRepositoryAnalysisJobs(10);
    setHistory(jobs);
  };

  const handleAnalyze = async (repoUrl: string) => {
    setError(null);
    setAnalysis(null);
    setStatus("Submitting job");
    setProgress(2);
    try {
      const job = await startRepositoryAnalysis({ repo_url: repoUrl });
      let finished = false;

      while (!finished) {
        // Simple polling for Phase 1 live progress.
        await new Promise((resolve) => setTimeout(resolve, 1200));
        const current = await getRepositoryAnalysisStatus(job.job_id);
        setStatus(current.stage);
        setProgress(current.progress);

        if (current.status === "failed") {
          throw new Error(current.error || "Analysis job failed");
        }

        if (current.status === "completed" && current.result) {
          setAnalysis(current.result);
          setStatus("Completed");
          await refreshHistory();
          finished = true;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setStatus("Failed");
    }
  };

  useEffect(() => {
    void refreshHistory();
  }, []);

  return (
    <section className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Dashboard</h1>
        <p className="max-w-2xl text-sm text-white/55 sm:text-base">
          Run async analysis jobs, inspect snapshots, then open{" "}
          <Link href="/diagrams" className="font-medium text-cyan-400/90 hover:text-cyan-300">
            diagrams
          </Link>{" "}
          or{" "}
          <Link href="/chat" className="font-medium text-cyan-400/90 hover:text-cyan-300">
            chat
          </Link>{" "}
          grounded in your repo. Try{" "}
          <Link href="/architect" className="font-medium text-violet-300/90 hover:text-violet-200">
            Architect
          </Link>{" "}
          for structured design prompts.
        </p>
      </div>
      <RepositoryForm onSubmit={handleAnalyze} />
      {status ? (
        <div className="card space-y-2">
          <p className="text-sm text-white/70">Analysis Status: {status}</p>
          <div className="h-2 w-full rounded-full bg-white/10">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-cyan-400 to-violet-400 transition-all shadow-md shadow-cyan-500/20"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-white/60">{progress}%</p>
        </div>
      ) : null}
      {error ? (
        <p className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </p>
      ) : null}
      <AnalysisResult data={analysis} />
      <section className="card space-y-3">
        <h2 className="text-lg font-semibold">Recent Analysis Jobs</h2>
        {history.length === 0 ? <p className="text-white/70">No job history yet.</p> : null}
        <div className="space-y-2">
          {history.map((job) => (
            <div
              key={job.job_id}
              className="rounded-xl border border-white/10 bg-white/[0.02] p-4 transition hover:border-cyan-500/20"
            >
              <p className="text-xs text-white/60">{job.job_id}</p>
              <p className="text-xs text-white/50">{job.repo_url || "Unknown repo"}</p>
              <p className="text-sm">
                {job.status} - {job.stage} ({job.progress}%)
              </p>
              <p className="text-xs text-white/50">Updated: {job.updated_at || "-"}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={!job.result}
                  onClick={() => {
                    if (job.result) {
                      setAnalysis(job.result);
                    }
                  }}
                >
                  Load Snapshot
                </Button>
                {job.result ? (
                  <Link href={`/diagrams?chart=${encodeURIComponent(job.result.mermaid_diagram)}`}>
                    <Button type="button" variant="outline">
                      Open Diagram
                    </Button>
                  </Link>
                ) : (
                  <Button type="button" variant="outline" disabled>
                    Open Diagram
                  </Button>
                )}
                {job.repo_url && job.status === "completed" && (
                  <Link
                    href={`/chat?repo_url=${encodeURIComponent(job.result?.repo_clone_url ?? job.repo_url)}&repo_name=${encodeURIComponent((job.result?.repo_clone_url ?? job.repo_url).split("/").filter(Boolean).pop() || "Repo")}`}
                  >
                    <Button type="button" variant="outline">
                      Chat
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
