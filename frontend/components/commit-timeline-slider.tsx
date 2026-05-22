"use client";

import type { CommitTimelineEntry } from "@/lib/types";

type CommitTimelineSliderProps = {
  commits: CommitTimelineEntry[];
  selectedIndex: number;
  onChange: (index: number) => void;
  className?: string;
};

function formatWhen(ts: number | null | undefined): string {
  if (ts == null) return "";
  try {
    return new Date(ts * 1000).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

export function CommitTimelineSlider({
  commits,
  selectedIndex,
  onChange,
  className,
}: CommitTimelineSliderProps) {
  if (!commits.length) {
    return (
      <div className={className}>
        <p className="text-xs text-white/50">
          No commit history in this snapshot (shallow clone may be shallow on empty repos).
        </p>
      </div>
    );
  }

  const safeIndex = Math.min(Math.max(0, selectedIndex), commits.length - 1);
  const c = commits[safeIndex];

  return (
    <div className={className}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">Time travel</p>
        <span className="text-[10px] text-white/40">
          {safeIndex + 1} / {commits.length}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={commits.length - 1}
        value={safeIndex}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-accent"
      />
      <div className="mt-2 rounded-lg border border-white/10 bg-black/20 p-3 backdrop-blur-sm">
        <p className="font-mono text-[11px] text-accent/90">{c.sha.slice(0, 12)}</p>
        <p className="mt-1 text-sm text-white/85">{c.subject}</p>
        {c.committed_at != null ? (
          <p className="mt-1 text-[11px] text-white/45">{formatWhen(c.committed_at)}</p>
        ) : null}
        <p className="mt-2 text-[10px] leading-relaxed text-white/40">
          Architecture scan reflects the tree at analysis time; the slider anchors context to recent git
          history from the clone window.
        </p>
      </div>
    </div>
  );
}
