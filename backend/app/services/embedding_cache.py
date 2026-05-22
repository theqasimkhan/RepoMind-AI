"""Disk cache for chunk embeddings to avoid re-encoding on every chat request."""

from __future__ import annotations

import hashlib
import threading
import time
from pathlib import Path

import numpy as np

_io_lock = threading.Lock()


def compute_chunk_set_fingerprint(chunks: list[dict]) -> str:
    """Stable fingerprint for the ordered chunk list (content lengths + paths + indices)."""
    parts = [
        f"{c.get('file_path', '')}:{c.get('chunk_index', 0)}:{len(c.get('content') or '')}"
        for c in chunks
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8", errors="replace")).hexdigest()


def compute_cache_stem(
    repo_url: str,
    job_id: str,
    fingerprint: str,
    model_name: str,
    *,
    embedding_variant: str = "",
) -> str:
    """``embedding_variant`` distinguishes cache keys when embedding inputs change (e.g. path prefix)."""
    raw = f"{repo_url}|{job_id}|{fingerprint}|{model_name}|{embedding_variant}".encode(
        "utf-8", errors="replace"
    )
    return hashlib.sha256(raw).hexdigest()


def _npz_path(cache_dir: Path, stem: str) -> Path:
    return cache_dir / f"{stem}.npz"


def try_load_cached_embeddings(
    cache_dir: Path, stem: str, *, ttl_seconds: int
) -> np.ndarray | None:
    path = _npz_path(cache_dir, stem)
    if not path.is_file():
        return None
    if ttl_seconds > 0 and (time.time() - path.stat().st_mtime) > ttl_seconds:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    loaded = np.load(path)
    emb = loaded["embeddings"]
    return np.ascontiguousarray(emb, dtype=np.float32)


def save_embeddings_to_cache(
    cache_dir: Path, stem: str, embeddings: np.ndarray, *, max_total_bytes: int
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _npz_path(cache_dir, stem)
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, embeddings=np.ascontiguousarray(embeddings, dtype=np.float32))
    tmp.replace(path)
    if max_total_bytes > 0:
        prune_oldest(cache_dir, max_total_bytes)


def prune_oldest(cache_dir: Path, max_total_bytes: int) -> None:
    files = [p for p in cache_dir.glob("*.npz") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    if total <= max_total_bytes:
        return
    for path in sorted(files, key=lambda p: p.stat().st_mtime):
        if total <= max_total_bytes:
            break
        try:
            sz = path.stat().st_size
            path.unlink(missing_ok=True)
            total -= sz
        except OSError:
            continue


def resolve_cache_dir(configured: str, backend_root: Path) -> Path:
    p = Path(configured)
    if not p.is_absolute():
        return (backend_root / p).resolve()
    return p.resolve()


def load_or_build_embeddings(
    *,
    vector_index: object,
    chunks: list[dict],
    cache_dir: Path,
    stem: str,
    ttl_seconds: int,
    max_total_bytes: int,
    embed_path_prefix: bool = False,
) -> tuple[np.ndarray, bool]:
    """
    Returns (embeddings, cache_hit). Caller applies embeddings via set_index_from_embeddings.
    Thread-safe with double-checked locking to prevent race conditions.
    """
    if not chunks:
        return vector_index.encode_chunk_texts([], embed_path_prefix=embed_path_prefix), False

    # First check without lock
    cached = try_load_cached_embeddings(cache_dir, stem, ttl_seconds=ttl_seconds)
    if cached is not None:
        return cached, True

    # Acquire lock and double-check to prevent race condition
    with _io_lock:
        cached = try_load_cached_embeddings(cache_dir, stem, ttl_seconds=ttl_seconds)
        if cached is not None:
            return cached, True

        # Build embeddings
        embeddings = vector_index.encode_chunk_texts(chunks, embed_path_prefix=embed_path_prefix)
        save_embeddings_to_cache(cache_dir, stem, embeddings, max_total_bytes=max_total_bytes)
        return embeddings, False
