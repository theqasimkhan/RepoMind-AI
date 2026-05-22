"use client";

import { useEffect, useState } from "react";
import { AnalysisResponse } from "@/lib/types";
import { MermaidDiagram } from "@/components/mermaid-diagram";
import { CodeDnaViz } from "@/components/code-dna-viz";
import { CommitTimelineSlider } from "@/components/commit-timeline-slider";
import { RepoGalaxy3D } from "@/components/repo-galaxy-3d";
import Link from "next/link";
import { canonicalGithubRepoUrl } from "@/lib/github-repo";

function analysisChatHref(data: AnalysisResponse): string {
  const clone =
    data.repo_clone_url?.trim() || canonicalGithubRepoUrl(data.repository);
  const name = data.repository.split("/").pop() || data.repository;
  return `/chat?repo_url=${encodeURIComponent(clone)}&repo_name=${encodeURIComponent(name)}`;
}

type AnalysisResultProps = {
  data: AnalysisResponse | null;
};

export function AnalysisResult({ data }: AnalysisResultProps) {
  const [commitIdx, setCommitIdx] = useState(0);

  useEffect(() => {
    setCommitIdx(0);
  }, [data?.repository]);
  if (!data) {
    return (
      <section className="card">
        <p className="text-white/70">Run an analysis to view repository insights.</p>
      </section>
    );
  }

  const commits = data.commit_timeline ?? [];

  return (
    <section className="card space-y-4">
      <h3 className="text-lg font-semibold">{data.repository}</h3>
      <p className="text-white/80">{data.summary}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <TagList title="Frontend" values={data.detected_frontend} />
        <TagList title="Backend" values={data.detected_backend} />
        <TagList title="Databases" values={data.detected_databases} />
        <TagList title="DevOps" values={data.devops_signals} />
      </div>
      <div>
        <h4 className="mb-2 font-medium">Architecture Style</h4>
        <p className="text-white/80">{data.architecture_style}</p>
      </div>
      <TagList title="Architecture Patterns" values={data.architecture_patterns} />
      <TagList title="Dependencies (sample)" values={data.dependencies.slice(0, 20)} />
      <TagList title="API-related files (sample)" values={data.detected_apis.slice(0, 12)} />
      <div>
        <h4 className="mb-2 font-medium">Folder Explanations</h4>
        <div className="space-y-2">
          {Object.entries(data.folder_explanations).map(([folder, explanation]) => (
            <div key={folder} className="rounded-lg border border-white/10 p-3">
              <p className="font-medium">{folder}</p>
              <p className="text-sm text-white/75">{explanation}</p>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h4 className="mb-2 font-medium">File Tree (sample)</h4>
        <pre className="max-h-64 overflow-auto rounded-lg bg-black/40 p-4 text-xs text-white/90">
          {data.file_tree.slice(0, 120).join("\n")}
        </pre>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3">
          <h4 className="font-medium">Repo Galaxy</h4>
          <RepoGalaxy3D fileTree={data.file_tree} apiPaths={data.detected_apis} height={380} />
        </div>
        <div className="space-y-3">
          <CodeDnaViz fileTree={data.file_tree} className="glass-panel h-full rounded-2xl p-4" />
          <CommitTimelineSlider
            commits={commits}
            selectedIndex={commitIdx}
            onChange={setCommitIdx}
            className="glass-panel rounded-2xl p-4"
          />
        </div>
      </div>
      <div>
        <MermaidDiagram chart={data.mermaid_diagram} title="Architecture Diagram" />
        <div className="mt-3 flex gap-4">
          <Link
            href={`/diagrams?chart=${encodeURIComponent(data.mermaid_diagram)}`}
            className="text-sm text-accent underline"
          >
            Open in Diagram Workspace
          </Link>
          <Link href={analysisChatHref(data)} className="text-sm text-accent underline">
            Chat with Repository
          </Link>
        </div>
      </div>
      <div>
        <h4 className="mb-2 font-medium">Mermaid Source</h4>
        <pre className="overflow-auto rounded-lg bg-black/40 p-4 text-sm text-white/90">
          {data.mermaid_diagram}
        </pre>
      </div>
    </section>
  );
}

function TagList({ title, values }: { title: string; values: string[] }) {
  const safeValues = values.length ? values : ["Not detected"];
  return (
    <div>
      <h4 className="mb-1 text-sm font-medium text-white/70">{title}</h4>
      <div className="flex flex-wrap gap-2">
        {safeValues.map((value) => (
          <span
            key={`${title}-${value}`}
            className="rounded-full border border-white/20 px-3 py-1 text-xs"
          >
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}
