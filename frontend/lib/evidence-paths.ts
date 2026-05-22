import { SourceCitation, TraceStep } from "@/lib/types";

function normalizePath(p: string): string {
  return p.replace(/\\/g, "/").replace(/^\.\//, "").trim();
}

function maybeAddPath(raw: string, out: Set<string>): void {
  const n = normalizePath(raw);
  if (!n || n.length < 2) return;
  if (n.includes("/") || /\.[a-zA-Z0-9]{1,8}$/.test(n)) {
    out.add(n);
  }
}

function walkUnknown(val: unknown, out: Set<string>): void {
  if (val == null) return;
  if (typeof val === "string") {
    if (val.includes("/") || val.includes("\\")) {
      maybeAddPath(val, out);
    }
    return;
  }
  if (Array.isArray(val)) {
    for (const item of val) walkUnknown(item, out);
    return;
  }
  if (typeof val === "object") {
    for (const v of Object.values(val as Record<string, unknown>)) {
      walkUnknown(v, out);
    }
  }
}

/** Paths from chat citations, legacy references, and trace step payloads (best-effort). */
export function collectEvidencePaths(
  citations?: SourceCitation[],
  references?: string[],
  traceSteps?: TraceStep[],
): string[] {
  const out = new Set<string>();
  for (const c of citations ?? []) {
    if (c.file_path) maybeAddPath(c.file_path, out);
  }
  for (const r of references ?? []) {
    maybeAddPath(r, out);
  }
  for (const s of traceSteps ?? []) {
    walkUnknown(s.detail, out);
  }
  return [...out];
}
