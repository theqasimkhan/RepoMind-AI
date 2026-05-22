# RepoMind AI — advancement phases

Roadmap consolidating UX, AI/ML, and platform work. Each phase lists goals, dependencies, acceptance criteria, and explicit **out of scope** items.

---

## Phase 0 — Baseline (current MVP)

**Goals:** Submit repo URL, clone/scan, stack/architecture heuristics, Mermaid diagram, async jobs in SQLite, dashboard surfaces, basic RAG chat over indexed chunks.

**Dependencies:** Git, FastAPI, Next.js, optional Redis/Celery.

**Acceptance criteria:** Analyze + job status + chat query return grounded answers with file references for typical repos.

**Out of scope:** 3D visuals, formal eval harness, embedding cache, rerankers, HyDE, production auth hardening.

**Maps to:** Foundation for all later bullets (no separate “visual” or “AI depth” split yet).

---

## Phase 1 — AI foundations (RAG quality, observability, eval)

**Goals**

- Persist or cache embeddings / FAISS-backed index per analysis job or repo fingerprint so chat does not re-encode all chunks every request.
- Citations in API responses (path + optional line range or chunk id) from retrieved chunks.
- Structured trace fields (model id, top-k, latencies, chunk counts, cache hit) in responses and logs.
- Minimal retrieval eval harness (gold Q/A or gold paths, Recall@k), runnable without paid LLM calls.

**Dependencies:** Phase 0; `sentence-transformers`, `faiss-cpu`; SQLite job/chunk storage.

**Acceptance criteria:** Second identical chat query for the same chunk set hits disk cache (when enabled); `/chat/query` returns `citations` + `trace`; eval pytest passes locally (or skips when `SKIP_FAISS_EVAL=1`).

**Out of scope:** Cross-encoder rerank, HyDE, two-stage retrieval, new chunking strategies beyond small line metadata, tool-using agent, README “experiments” narrative (see Phase 3).

**Maps to:** Embedding + FAISS cache per job/repo; citations + structured responses; trace logging; eval harness + gold set; README eval note.

---

## Phase 2 — Retrieval depth & optional query expansion

**Goals**

- Better chunking (semantic / structure-aware, overlap tuning, path-aware metadata).
- Retrieval metrics logged or exported (MRR, nDCG where labels exist).
- Two-stage retrieval (e.g. bi-encoder + **optional** cross-encoder rerank).
- **Optional** HyDE or query rewriting behind feature flags.

**Dependencies:** Phase 1 cache + trace fields; stable chunk schema and eval set growth.

**Acceptance criteria:** Rerank/HyDE off by default; turning flag on improves offline Recall@k on gold set without breaking latency SLO (define per deployment).

**Out of scope:** Full 3D “Repo Galaxy” graph, time-travel UI, Code DNA viz, glassmorphism-only redesign, architect/PR simulation (those are Phase 4+ UX).

**Maps to:** Better chunking; retrieval metrics; two-stage + rerank (optional); HyDE optional.

### Phase 2 — Implemented in this repo

| Item | Status |
|------|--------|
| **Chunking** | `RETRIEVAL_CHUNK_STRATEGY=fixed` (default, same as before) or `structure_aware` (paragraph-aware splits + size windows); `RETRIEVAL_CHUNK_SIZE`, `RETRIEVAL_CHUNK_OVERLAP`, `RETRIEVAL_MAX_CHUNKS_PER_FILE` via `config.py` / `.env`. Chunks carry optional `language` / `chunk_strategy` at index time (not persisted in SQLite beyond core columns). |
| **Path-aware embeddings** | Optional `RETRIEVAL_EMBED_PATH_PREFIX` prefixes `File: {path}` in bi-encoder input; **embedding cache stem** includes an embedding variant so vectors stay consistent. |
| **Two-stage + rerank** | `RETRIEVAL_ENABLE_RERANK` + `RETRIEVAL_FETCH_K` + `RETRIEVAL_RERANK_MODEL`; cross-encoder loaded lazily on first use (`sentence_transformers.CrossEncoder`). Trace: `rerank_enabled`, `rerank_latency_ms`, `faiss_candidate_count`, `retrieval_fetch_k`. |
| **HyDE** | `RETRIEVAL_ENABLE_HYDE` + `RETRIEVAL_HYDE_USE_LLM`; `RagPipeline.hyde_hypothetical_snippet` for live LLM expansion. Tests / CI: `HYDE_EVAL_MOCK=1` and optional `HYDE_EVAL_MOCK_TEXT` (no API keys). Trace: `hyde_applied`, `hyde_latency_ms`, `retrieval_query_preview`. |
| **Retrieval metrics (labels)** | Library `app/services/retrieval_metrics.py` (Recall@k, MRR, nDCG@k). Offline pytest asserts these on `eval/gold_set.json`. Optional API: `GET /api/v1/retrieval/metrics-export` when `RETRIEVAL_ENABLE_METRICS_ENDPOINT=true` (aggregate + per-case JSON). |
| **Deferred / not in scope here** | True learned semantic chunking (model-based segmenters), multi-vector per chunk, learned sparse retrieval, production rerank latency SLO automation, graded relevance beyond binary gold files. |

---

## Phase 3 — Agentic orchestration & documentation

**Goals**

- Bounded tool-using agent (retrieve, summarize, diagram hooks) with strict budgets and guardrails.
- Trace logging extended to spans/steps (tool calls, retrieval stages).
- README **experiments** section reproducing flags, eval commands, and baseline numbers.

**Dependencies:** Phase 1–2; stable API contracts for tools.

**Acceptance criteria:** Agent cannot loop unbounded; failures degrade to single-shot RAG; experiments section matches runnable commands.

**Out of scope:** Replacing core analyze pipeline with fully autonomous coding agents.

**Maps to:** Bounded tool-using agent; trace logging (deep); README experiments section.

### Phase 3 — Implemented in this repo

| Item | Status |
|------|--------|
| **Bounded tool agent** | `CHAT_AGENT_ENABLED` (default off). Planner JSON loop with tools `retrieve`, `summarize` (LLM via `RagPipeline.summarize_snippets`), `diagram` (deterministic Mermaid from retrieved paths), `answer`. Hard caps: `CHAT_AGENT_MAX_TOOL_ROUNDS`, `CHAT_AGENT_MAX_RETRIEVE_REFINES`, `CHAT_AGENT_MAX_LLM_CALLS`. On planner/parse failure or agent exception → initial retrieval only, then single final `answer` (degraded). |
| **Trace spans / steps** | `ChatQueryTrace.trace_steps`: `TraceStep` list (`kind` = `span` \| `tool`) for HyDE, embedding cache, FAISS retrieval, each agent plan/tool, and final LLM. Server JSON log unchanged shape (`trace` includes nested steps). |
| **API / UI** | `POST /api/v1/chat/query` returns optional `diagram_mermaid` when the diagram tool ran. Chat UI shows collapsible **Agent steps** from `trace.trace_steps` and renders optional Mermaid. |
| **Tests / mocks** | `tests/test_chat_agent.py` (no paid LLM). Env: `CHAT_AGENT_MOCK=1`, optional `CHAT_AGENT_MOCK_STEPS` JSON array for deterministic planner. |
| **README experiments** | `README.md` — **Reproducible experiments (Phase 1–3)** table with pytest commands and flags. |
| **Deferred** | Autonomous multi-session coding agents; replacing the analyze pipeline with a fully LLM-driven clone; OpenTelemetry export of spans (structured trace only in API/logs). |

---

## Phase 4+ — Product & visualization layers

**Goals**

- **Visual:** Repo Galaxy 3D force graph + chat highlights; time-travel architecture slider; Code DNA visualization; glassmorphism / Linear-style dashboard polish; architect / PR simulation mode.
- API contracts and performance budgets for large graphs.

**Dependencies:** Phase 1 traces + citations (for linking chat to graph nodes); optional Phase 2 for richer retrieval context in UI.

**Acceptance criteria:** Documented UX specs and API stubs or feature flags; heavy visualization shipped incrementally (not blocking Phase 1–3).

**Out of scope in Phase 4 planning doc:** Implementing full 3D engine, full simulation backend, or redesign in the same release as Phase 1 AI work.

**Maps to:** All remaining visual / dashboard / simulation bullets from prior discussions.

### Phase 4+ — Implemented in this repo

| Item | Status |
|------|--------|
| **Repo Galaxy 3D** | `react-force-graph-3d` + `three`: folder-tree nodes (dirs + files), light edges between sampled `detected_apis` paths; embedded on **Dashboard** analysis and **Chat** (when latest analysis exists). Citations / references / trace `detail` strings drive **pulse/highlight** on matching file and ancestor directory nodes (`frontend/lib/evidence-paths.ts`, `frontend/components/repo-galaxy-3d.tsx`). |
| **Glass / Linear-style polish** | Global `.card` / `.glass-panel`, body gradient, chat header/footer blur (`frontend/app/globals.css`, `chat-interface.tsx`). |
| **Code DNA** | Extension histogram from `file_tree` (`frontend/components/code-dna-viz.tsx`) on dashboard analysis + chat side panel. |
| **Time-travel (commits)** | Shallow clone depth increased to 48; `git log` → `commit_timeline` on `RepositoryAnalyzeResponse`; **Commit timeline slider** in analysis (metadata + UX anchor; diagram/tree stay scan-time, documented in UI). |
| **Architect / PR simulation** | **Deferred:** full PR simulation backend. **Shipped thin slice:** `/architect` page + nav links — structured staff-engineer prompt over existing `POST /api/v1/chat/query` (no new LLM route). |
| **Latest analysis for UI** | `GET /api/v1/repositories/analysis/latest?repo_url=` returns last completed job snapshot (404 if none) for Galaxy on chat without oversized URLs. |

**Deferred (still Phase 4+ scope):** per-commit file-tree replay (would require checkout/re-scan per slider); OpenTelemetry export; full 3D engine customization beyond force layout; dedicated architect API with tool traces.

---

## Traceability matrix

| Advancement (from discussions)                         | Primary phase |
| ------------------------------------------------------- | ------------- |
| Repo Galaxy 3D + chat highlights                       | 4+            |
| Time-travel architecture slider                       | 4+            |
| Code DNA visualization                                 | 4+            |
| Glassmorphism / Linear-style dashboard                 | 4+            |
| Architect / PR simulation mode                         | 4+            |
| Eval harness + gold Q/A                                | 1             |
| Retrieval metrics                                      | 2 (expand in 3) |
| Better chunking                                        | 2             |
| Two-stage retrieval + cross-encoder rerank (optional)  | 2             |
| HyDE optional                                          | 2             |
| Embedding + FAISS cache per job/repo                   | 1             |
| Citations + structured responses                       | 1             |
| Trace logging                                          | 1 (deepen in 3) |
| Bounded tool-using agent                               | 3             |
| README experiments section                             | 3             |
