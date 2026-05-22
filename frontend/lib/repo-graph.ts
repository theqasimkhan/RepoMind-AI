export type RepoGraphNode = {
  id: string;
  name: string;
  nodeType: "file" | "dir";
  val: number;
};

export type RepoGraphLink = { source: string; target: string };

const DIR_PREFIX = "dir:";

function dirId(path: string): string {
  return `${DIR_PREFIX}${path}`;
}

/**
 * Folder-tree nodes + light cross-links between sampled API paths (heuristic "module" edges).
 */
export function buildRepoGraphData(
  fileTree: string[],
  options?: { maxFiles?: number; apiPaths?: string[] },
): { nodes: RepoGraphNode[]; links: RepoGraphLink[] } {
  const maxFiles = options?.maxFiles ?? 100;
  const files = fileTree.slice(0, maxFiles).map((f) => f.replace(/\\/g, "/"));
  const apiPaths = (options?.apiPaths ?? [])
    .map((p) => p.replace(/\\/g, "/"))
    .filter((p) => files.includes(p))
    .slice(0, 20);

  const dirPaths = new Set<string>();
  for (const f of files) {
    const parts = f.split("/");
    for (let i = 0; i < parts.length - 1; i++) {
      dirPaths.add(parts.slice(0, i + 1).join("/"));
    }
  }

  const nodes: RepoGraphNode[] = [];
  const links: RepoGraphLink[] = [];
  const rootId = dirId("__root__");
  nodes.push({ id: rootId, name: "repo", nodeType: "dir", val: 10 });

  const sortedDirs = [...dirPaths].sort();
  for (const d of sortedDirs) {
    nodes.push({ id: dirId(d), name: d.split("/").pop() ?? d, nodeType: "dir", val: 7 });
  }

  for (const d of sortedDirs) {
    const parts = d.split("/");
    if (parts.length <= 1) {
      links.push({ source: rootId, target: dirId(d) });
    } else {
      const parent = parts.slice(0, -1).join("/");
      links.push({ source: dirId(parent), target: dirId(d) });
    }
  }

  for (const f of files) {
    nodes.push({ id: f, name: f.split("/").pop() ?? f, nodeType: "file", val: 3 });
    const parts = f.split("/");
    const parentId = parts.length === 1 ? rootId : dirId(parts.slice(0, -1).join("/"));
    links.push({ source: parentId, target: f });
  }

  for (let i = 0; i < apiPaths.length - 1; i++) {
    links.push({ source: apiPaths[i], target: apiPaths[i + 1] });
  }

  return { nodes, links };
}

export function fileMatchesEvidence(fileId: string, evidence: Set<string>): boolean {
  if (evidence.has(fileId)) return true;
  const base = fileId.split("/").pop() ?? "";
  for (const e of evidence) {
    if (e === fileId) return true;
    if (e.endsWith(fileId) || fileId.endsWith(e)) return true;
    if (!e.includes("/") && base === e) return true;
  }
  return false;
}

export function dirTouchesEvidence(dirPath: string, evidence: Set<string>): boolean {
  const id = dirPath.startsWith(DIR_PREFIX) ? dirPath.slice(DIR_PREFIX.length) : dirPath;
  if (id === "__root__") return false;
  for (const e of evidence) {
    if (e === id || e.startsWith(`${id}/`)) return true;
  }
  return false;
}
