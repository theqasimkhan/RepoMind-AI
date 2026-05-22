from dataclasses import dataclass


@dataclass
class Chunk:
    id: str
    content: str
    metadata: dict[str, str]


class VectorIndexer:
    async def index_repository(self, repository: str, chunks: list[Chunk]) -> int:
        # Vector DB adapter will be implemented for FAISS/Chroma in later iterations.
        _ = repository
        return len(chunks)
