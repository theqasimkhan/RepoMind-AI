"""Index-time chunking strategies (Phase 2 retrieval depth)."""

from __future__ import annotations

from pathlib import Path


def _line_range_for_span(content: str, start: int, end: int) -> tuple[int, int]:
    start_line = content.count("\n", 0, start) + 1
    end_line = content.count("\n", 0, max(0, end - 1)) + 1 if end > start else start_line
    return start_line, max(start_line, end_line)


def _append_chunk(
    out: list[dict[str, str | int]],
    *,
    relative: str,
    chunk_index: int,
    content: str,
    full_file: str,
    span_start: int,
    span_end: int,
) -> None:
    text = content.strip()
    if not text:
        return
    sl, el = _line_range_for_span(full_file, span_start, span_end)
    ext = Path(relative).suffix.lower().lstrip(".")
    out.append(
        {
            "file_path": relative,
            "chunk_index": chunk_index,
            "content": text,
            "start_line": sl,
            "end_line": el,
            "language": ext or None,
            "chunk_strategy": None,
        }
    )


def _emit_windows(
    out: list[dict[str, str | int]],
    *,
    relative: str,
    chunk_index_ref: list[int],
    segment: str,
    full_file: str,
    seg_start: int,
    chunk_size: int,
    overlap: int,
    max_chunks: int,
) -> bool:
    """Slice `segment` with fixed windows; return True if max_chunks reached."""
    start = 0
    seg_len = len(segment)
    while start < seg_len and chunk_index_ref[0] < max_chunks:
        end = min(start + chunk_size, seg_len)
        abs_start = seg_start + start
        abs_end = seg_start + end
        window = segment[start:end]
        _append_chunk(
            out,
            relative=relative,
            chunk_index=chunk_index_ref[0],
            content=window,
            full_file=full_file,
            span_start=abs_start,
            span_end=abs_end,
        )
        chunk_index_ref[0] += 1
        if end >= seg_len:
            break
        start = max(0, end - overlap)
    return chunk_index_ref[0] >= max_chunks


def build_fixed_chunks(
    *,
    relative: str,
    content: str,
    chunk_size: int,
    overlap: int,
    max_chunks: int,
) -> list[dict[str, str | int]]:
    out: list[dict[str, str | int]] = []
    idx = [0]
    _emit_windows(
        out,
        relative=relative,
        chunk_index_ref=idx,
        segment=content,
        full_file=content,
        seg_start=0,
        chunk_size=chunk_size,
        overlap=overlap,
        max_chunks=max_chunks,
    )
    for c in out:
        c["chunk_strategy"] = "fixed"
    return out


def build_structure_aware_chunks(
    *,
    relative: str,
    content: str,
    chunk_size: int,
    overlap: int,
    max_chunks: int,
) -> list[dict[str, str | int]]:
    """
    Prefer paragraph / blank-line boundaries, then apply size windows inside large segments.
    """
    out: list[dict[str, str | int]] = []
    idx = [0]
    n = len(content)
    pos = 0
    while pos < n and idx[0] < max_chunks:
        next_break = content.find("\n\n", pos)
        if next_break == -1:
            segment = content[pos:]
            seg_end = n
        else:
            segment = content[pos:next_break]
            seg_end = next_break
        if not segment.strip():
            pos = seg_end + 2 if next_break != -1 else n
            continue
        if len(segment) <= chunk_size:
            _append_chunk(
                out,
                relative=relative,
                chunk_index=idx[0],
                content=segment,
                full_file=content,
                span_start=pos,
                span_end=seg_end,
            )
            idx[0] += 1
        else:
            if _emit_windows(
                out,
                relative=relative,
                chunk_index_ref=idx,
                segment=segment,
                full_file=content,
                seg_start=pos,
                chunk_size=chunk_size,
                overlap=overlap,
                max_chunks=max_chunks,
            ):
                break
        if idx[0] >= max_chunks:
            break
        pos = seg_end + 2 if next_break != -1 else n
    for c in out:
        c["chunk_strategy"] = "structure_aware"
    return out


def build_index_chunks_for_file(
    path: Path,
    root: Path,
    *,
    strategy: str,
    chunk_size: int,
    overlap: int,
    max_chunks_per_file: int,
) -> list[dict[str, str | int]]:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    content = raw.strip()
    if not content:
        return []
    relative = str(path.relative_to(root)).replace("\\", "/")
    if strategy == "structure_aware":
        return build_structure_aware_chunks(
            relative=relative,
            content=content,
            chunk_size=chunk_size,
            overlap=overlap,
            max_chunks=max_chunks_per_file,
        )
    return build_fixed_chunks(
        relative=relative,
        content=content,
        chunk_size=chunk_size,
        overlap=overlap,
        max_chunks=max_chunks_per_file,
    )
