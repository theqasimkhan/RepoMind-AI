export type AnalysisRequest = {
  repo_url: string;
};

export type CommitTimelineEntry = {
  sha: string;
  subject: string;
  committed_at?: number | null;
};

export type AnalysisResponse = {
  repository: string;
  repo_clone_url?: string | null;
  detected_frontend: string[];
  detected_backend: string[];
  detected_databases: string[];
  devops_signals: string[];
  dependencies: string[];
  detected_apis: string[];
  architecture_patterns: string[];
  folder_explanations: Record<string, string>;
  file_tree: string[];
  architecture_style: string;
  summary: string;
  mermaid_diagram: string;
  commit_timeline?: CommitTimelineEntry[];
};

export type AnalysisJobStartResponse = {
  job_id: string;
  status: string;
};

export type AnalysisJobStatusResponse = {
  job_id: string;
  repo_url: string | null;
  user_id?: string | null;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  stage: string;
  created_at: string | null;
  updated_at: string | null;
  error: string | null;
  result: AnalysisResponse | null;
};

export type ChatQueryRequest = {
  repo_url: string;
  question: string;
};

export type SourceCitation = {
  file_path: string;
  chunk_id?: string | null;
  start_line?: number | null;
  end_line?: number | null;
};

export type TraceStep = {
  name: string;
  kind: "span" | "tool";
  latency_ms?: number;
  detail?: Record<string, unknown>;
};

export type ChatQueryTrace = {
  model_id: string;
  top_k: number;
  latency_ms: number;
  retrieval_latency_ms: number;
  llm_latency_ms: number;
  num_chunks_in_index: number;
  num_chunks_retrieved: number;
  embedding_cache_hit?: boolean;
  embedding_model?: string | null;
  chunk_strategy?: string | null;
  retrieval_embed_path_prefix?: boolean;
  retrieval_fetch_k?: number | null;
  faiss_candidate_count?: number | null;
  rerank_enabled?: boolean;
  rerank_latency_ms?: number | null;
  hyde_applied?: boolean;
  hyde_latency_ms?: number | null;
  retrieval_query_preview?: string | null;
  trace_steps?: TraceStep[];
  agent_enabled?: boolean;
  agent_degraded?: boolean;
  agent_tool_rounds_used?: number;
};

export type ChatQueryResponse = {
  answer: string;
  references: string[];
  citations?: SourceCitation[];
  trace?: ChatQueryTrace | null;
  diagram_mermaid?: string | null;
};
