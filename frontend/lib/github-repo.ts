/** Match backend `normalize_github_repo_url` for client-side links (chat, etc.). */

export function canonicalGithubRepoUrl(raw: string): string {
  const s = raw.trim();
  if (!s) return s;
  if (s.startsWith("http://") || s.startsWith("https://")) return s;
  if (s.toLowerCase().startsWith("github.com/")) return `https://${s}`;
  if (/^[\w.-]+\/[\w.-]+$/.test(s)) return `https://github.com/${s}`;
  return s;
}
