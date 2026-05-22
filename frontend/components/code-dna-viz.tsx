"use client";

import { useMemo } from "react";

type CodeDnaVizProps = {
  fileTree: string[];
  className?: string;
};

const EXT_COLORS: Record<string, string> = {
  ts: "#4F9CF9",
  tsx: "#38BDF8",
  js: "#FBBF24",
  jsx: "#F59E0B",
  py: "#A78BFA",
  md: "#94A3B8",
  json: "#34D399",
  yml: "#22D3EE",
  yaml: "#22D3EE",
  css: "#F472B6",
  html: "#FB7185",
  go: "#60A5FA",
  rs: "#F97316",
  java: "#EF4444",
  other: "#64748B",
};

function extensionOf(path: string): string {
  const base = path.split("/").pop() ?? path;
  const dot = base.lastIndexOf(".");
  if (dot <= 0 || dot === base.length - 1) return "other";
  return base.slice(dot + 1).toLowerCase() || "other";
}

export function CodeDnaViz({ fileTree, className }: CodeDnaVizProps) {
  const buckets = useMemo(() => {
    const counts = new Map<string, number>();
    for (const f of fileTree) {
      const ext = extensionOf(f);
      counts.set(ext, (counts.get(ext) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12);
  }, [fileTree]);

  const total = useMemo(() => buckets.reduce((s, [, n]) => s + n, 0), [buckets]);

  if (!total) {
    return (
      <div className={className}>
        <p className="text-xs text-white/50">No file extensions to chart yet.</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-white/40">Code DNA</p>
      <p className="mb-3 text-xs text-white/55">
        Extension mix from the indexed file tree ({total} files in view).
      </p>
      <div className="space-y-2">
        {buckets.map(([ext, count]) => {
          const pct = Math.max(4, Math.round((count / total) * 100));
          const color = EXT_COLORS[ext] ?? EXT_COLORS.other;
          return (
            <div key={ext}>
              <div className="mb-0.5 flex justify-between text-[11px] text-white/70">
                <span className="font-mono">.{ext}</span>
                <span className="text-white/45">
                  {count} ({Math.round((count / total) * 100)}%)
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
