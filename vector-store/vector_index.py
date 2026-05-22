"""
FAISS Vector Index — Phase 2E / Phase 2 retrieval.
Embeds text chunks using SentenceTransformers and indexes them in FAISS for fast semantic search.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


def _chunk_text_for_embedding(chunk: dict, *, embed_path_prefix: bool) -> str:
    body = chunk.get("content") or ""
    if not embed_path_prefix:
        return body
    fp = str(chunk.get("file_path") or "")
    return f"File: {fp}\n{body}"


class VectorIndex:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks: list[dict] = []

    def encode_chunk_texts(self, chunks: list[dict], *, embed_path_prefix: bool = False) -> np.ndarray:
        """Embed chunk bodies for indexing or cache persistence."""
        if not chunks:
            return np.zeros((0, self.dimension), dtype=np.float32)
        texts = [_chunk_text_for_embedding(c, embed_path_prefix=embed_path_prefix) for c in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return np.ascontiguousarray(embeddings, dtype=np.float32)

    def set_index_from_embeddings(self, chunks: list[dict], embeddings: np.ndarray) -> None:
        """Load a FAISS index from precomputed embeddings (disk cache path)."""
        self.chunks = chunks
        self.index.reset()
        if not chunks or embeddings.size == 0:
            return
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        if embeddings.shape[0] != len(chunks):
            raise ValueError("embeddings row count must match chunks length")
        self.index.add(embeddings)

    def build_index(self, chunks: list[dict]) -> None:
        """Embeds and indexes a list of chunk dictionaries."""
        if not chunks:
            self.chunks = []
            self.index.reset()
            return
        embeddings = self.encode_chunk_texts(chunks)
        self.set_index_from_embeddings(chunks, embeddings)

    def search(self, query: str, top_k: int = 4, *, first_stage_k: int | None = None) -> list[dict]:
        """
        Searches the FAISS index for the semantically closest chunks.

        When ``first_stage_k`` is set larger than ``top_k``, callers can retrieve more
        candidates for a second-stage reranker without changing the bi-encoder model.
        """
        if not self.chunks or self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)

        k_wanted = first_stage_k if first_stage_k is not None else top_k
        k = min(max(k_wanted, 1), len(self.chunks))
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.chunks):
                results.append(self.chunks[idx])

        if first_stage_k is None or len(results) <= top_k:
            return results[:top_k]
        return results
