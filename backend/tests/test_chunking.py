"""Chunking strategies (no network, no FAISS)."""

from pathlib import Path

from app.services.chunking import (
    build_fixed_chunks,
    build_index_chunks_for_file,
    build_structure_aware_chunks,
)


def test_structure_aware_respects_paragraph_breaks():
    text = "A" * 100 + "\n\n" + "B" * 100
    chunks = build_structure_aware_chunks(
        relative="m.py",
        content=text,
        chunk_size=1200,
        overlap=50,
        max_chunks=10,
    )
    assert len(chunks) == 2
    assert "A" * 50 in chunks[0]["content"]
    assert chunks[0]["chunk_strategy"] == "structure_aware"


def test_fixed_chunking_overlap(tmp_path: Path):
    root = tmp_path
    p = root / "f.py"
    body = "\n".join([f"line {i}" for i in range(50)])
    p.write_text(body, encoding="utf-8")
    out = build_index_chunks_for_file(
        p,
        root,
        strategy="fixed",
        chunk_size=80,
        overlap=20,
        max_chunks_per_file=5,
    )
    assert out
    assert all(c.get("chunk_strategy") == "fixed" for c in out)


def test_build_fixed_chunks_metadata():
    c = build_fixed_chunks(
        relative="x.ts",
        content="hello\nworld",
        chunk_size=100,
        overlap=10,
        max_chunks=3,
    )
    assert c[0]["file_path"] == "x.ts"
    assert c[0].get("language") == "ts"
