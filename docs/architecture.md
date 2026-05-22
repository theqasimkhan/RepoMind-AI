# RepoMind AI Architecture

## Layered Design

- Presentation Layer: Next.js frontend pages and reusable UI components
- API Layer: FastAPI routers with typed contracts
- Service Layer: Use-case orchestration (`RepositoryAnalysisService`, `RepositoryChatService`)
- AI Layer: RAG pipeline orchestration and prompt composition
- Parsing Layer: repository and dependency detection services
- Diagram Layer: Mermaid generation service
- Data Layer: vector index abstraction and future Postgres persistence

## Phase 1 Request Flow

1. User submits GitHub URL in dashboard UI
2. Frontend posts request to `/api/v1/repositories/analyze`
3. Backend service generates stack and architecture insights
4. Mermaid syntax and summary are returned to frontend
5. Frontend renders findings and diagram source

## Scale Path

- Add queue workers for long-running analysis tasks
- Cache intermediate results and embedding layers
- Persist analysis snapshots per repository and branch
- Introduce tenancy and auth boundaries
