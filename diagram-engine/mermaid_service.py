"""Standalone Mermaid diagram service for the diagram-engine module.

Mirrors the heuristic diagram logic in
``backend/app/services/repository_service.py::_generate_mermaid`` so that
both entry-points produce equivalent flowchart output.
"""
from __future__ import annotations


class MermaidDiagramService:
    """Generate a rich ``flowchart TB`` diagram from detected stack signals."""

    _MAX_LABEL = 72

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_service_architecture(
        self,
        frontend: str,
        backend: str,
        data_store: str,
        vector_store: str,
        *,
        devops: str | None = None,
        architecture_style: str | None = None,
        architecture_patterns: list[str] | None = None,
        top_level_dirs: list[str] | None = None,
    ) -> str:
        """Generate a Mermaid ``flowchart TB`` diagram.

        Parameters
        ----------
        frontend:
            Comma-separated frontend technologies (or descriptive string).
        backend:
            Comma-separated backend technologies.
        data_store:
            Primary database / data store label.
        vector_store:
            Vector store label (e.g. ``"FAISS"``).
        devops:
            Optional comma-separated devops signals.
        architecture_style:
            One-line architecture style label.
        architecture_patterns:
            Optional list of architecture pattern labels.
        top_level_dirs:
            Optional list of top-level repository directory names.
        """
        style_lbl = self._m_label(
            architecture_style or "Inferred architecture", 52
        )
        fe_txt = frontend or "Not detected (CLI / notebooks / libs only)"
        be_txt = backend or "Not classified"
        db_txt = data_store or "Not detected"
        vs_txt = vector_store or "FAISS"

        lines: list[str] = [
            "flowchart TB",
            f'  root["{style_lbl}"]',
            f'  fe["Frontend / UX<br/>{self._m_label(fe_txt)}"]',
            f'  be["App & services<br/>{self._m_label(be_txt)}"]',
            f'  db[("Data stores<br/>{self._m_label(db_txt, 56)}")]',
            "  root --> fe",
            "  root --> be",
            "  fe --> be",
            "  be --> db",
            f'  be --> rag[("Vector retrieval<br/>({self._m_label(vs_txt, 40)})")]',
            '  be --> llm["Model providers<br/>(Gemini / OpenRouter / OpenAI)"]',
        ]

        if devops:
            lines.append(
                f'  dev["Delivery & ops<br/>{self._m_label(devops)}"]'
            )
            lines.append("  be --> dev")

        for i, pat in enumerate((architecture_patterns or [])[:5]):
            pid = f"pat{i}"
            lines.append(f'  {pid}["{self._m_label(pat, 48)}"]')
            lines.append(f"  be --> {pid}")

        _skip = {".git", ".github", "__pycache__", "node_modules", ".venv", "venv"}
        dirs = [d for d in (top_level_dirs or []) if d not in _skip][:6]
        if dirs:
            dtxt = ", ".join(dirs)
            lines.append(
                f'  areas["Repo layout<br/>{self._m_label(dtxt)}"]'
            )
            lines.append("  root --> areas")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Convenience: build from StackSignals dataclass (repo-parser output)
    # ------------------------------------------------------------------

    def generate_from_stack_signals(self, signals) -> str:  # type: ignore[override]
        """Accept a ``StackSignals`` instance and produce a diagram.

        ``signals`` is expected to have ``.frontend``, ``.backend``,
        ``.databases``, and ``.devops`` list attributes.
        """
        fe = ", ".join(signals.frontend) if signals.frontend else ""
        be = ", ".join(signals.backend) if signals.backend else ""
        db = ", ".join(signals.databases) if signals.databases else ""
        dv = ", ".join(signals.devops) if signals.devops else None
        return self.generate_service_architecture(
            frontend=fe,
            backend=be,
            data_store=db,
            vector_store="FAISS",
            devops=dv,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _m_label(text: str, max_len: int = 72) -> str:
        """Sanitise and truncate a label for Mermaid node text."""
        t = (text or "").replace('"', "'").replace("\n", " ").strip()
        if len(t) > max_len:
            return t[: max_len - 1] + "…"
        return t or "—"
