"use client";

import dynamic from "next/dynamic";
import type { ForceGraphMethods } from "react-force-graph-3d";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildRepoGraphData,
  dirTouchesEvidence,
  fileMatchesEvidence,
  type RepoGraphLink,
  type RepoGraphNode,
} from "@/lib/repo-graph";

const ForceGraph3D = dynamic(
  () => import("react-force-graph-3d").then((m) => m.default),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[min(420px,55vh)] min-h-[280px] items-center justify-center rounded-2xl border border-white/10 bg-black/25 text-sm text-white/50 backdrop-blur-md">
        Loading Repo Galaxy…
      </div>
    ),
  },
);

export type RepoGalaxy3DProps = {
  fileTree: string[];
  apiPaths?: string[];
  highlightPaths?: string[];
  height?: number;
  className?: string;
};

export function RepoGalaxy3D({
  fileTree,
  apiPaths,
  highlightPaths = [],
  height = 440,
  className,
}: RepoGalaxy3DProps) {
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [pulse, setPulse] = useState(0);

  const evidence = useMemo(() => new Set(highlightPaths), [highlightPaths.join("|")]);

  useEffect(() => {
    if (!evidence.size) return;
    const id = window.setInterval(() => setPulse((p) => (p + 1) % 10_000), 140);
    return () => clearInterval(id);
  }, [evidence.size]);

  const graphData = useMemo(() => {
    const built = buildRepoGraphData(fileTree, { maxFiles: 110, apiPaths });
    return {
      nodes: built.nodes as unknown as RepoGraphNode[],
      links: built.links.map((l) => ({ ...l })) as RepoGraphLink[],
    };
  }, [fileTree, apiPaths?.join("|")]);

  useEffect(() => {
    const t = window.setTimeout(() => fgRef.current?.zoomToFit?.(400), 80);
    return () => clearTimeout(t);
  }, [graphData]);

  const nodeColor = useCallback(
    (node: object) => {
      const n = node as RepoGraphNode;
      const id = n.id;
      const accentBright = pulse % 2 === 0 ? "#FBBF24" : "#FDE68A";
      const fileBase = "#4F9CF9";
      const dirBase = "rgba(148,163,184,0.75)";
      const dirGlow = "rgba(251,191,36,0.55)";

      if (n.nodeType === "dir") {
        return dirTouchesEvidence(id, evidence) ? dirGlow : dirBase;
      }
      return fileMatchesEvidence(id, evidence) ? accentBright : fileBase;
    },
    [evidence, pulse],
  );

  const linkColor = useCallback(() => "rgba(255,255,255,0.14)", []);

  if (!fileTree.length) {
    return (
      <div
        className={`flex items-center justify-center rounded-2xl border border-white/10 bg-black/20 p-8 text-sm text-white/50 backdrop-blur-md ${className ?? ""}`}
        style={{ height }}
      >
        No file tree yet — run an analysis first.
      </div>
    );
  }

  return (
    <div
      className={`glass-panel relative overflow-hidden rounded-2xl border border-white/10 shadow-[0_0_0_1px_rgba(255,255,255,0.04)] ${className ?? ""}`}
      style={{ height }}
    >
      <div className="pointer-events-none absolute left-3 top-3 z-10 rounded-lg border border-white/10 bg-black/35 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-white/50 backdrop-blur-md">
        Repo Galaxy · 3D
      </div>
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        backgroundColor="rgba(0,0,0,0)"
        nodeId="id"
        nodeLabel={(n: object) => (n as RepoGraphNode).id}
        nodeVal={(n: object) => (n as RepoGraphNode).val}
        nodeColor={nodeColor}
        linkColor={linkColor}
        linkWidth={0.35}
        linkDirectionalParticles={evidence.size ? 1 : 0}
        linkDirectionalParticleWidth={0.35}
        linkDirectionalParticleSpeed={0.006}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.35}
        warmupTicks={40}
        cooldownTicks={120}
        showNavInfo={false}
      />
    </div>
  );
}
