"""Lightweight heuristic stack detector for the repo-parser module.

Mirrors the richer detection logic used by
``backend/app/services/repository_service.py`` so that both paths
report consistent technology signals from a file-list scan.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StackSignals:
    frontend: list[str] = field(default_factory=list)
    backend: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    devops: list[str] = field(default_factory=list)


class StackDetector:
    """Detect tech-stack signals from a list of relative file paths.

    Accepts the same ``files`` format used throughout the project
    (forward-slash-separated, relative to the repo root).
    """

    def detect_from_file_list(
        self,
        files: list[str],
        dependencies: list[str] | None = None,
    ) -> StackSignals:
        lowered = [f.lower() for f in files]
        deps_set = {d.lower() for d in (dependencies or [])}
        return StackSignals(
            frontend=self._detect_frontend(lowered, deps_set),
            backend=self._detect_backend(lowered, deps_set),
            databases=self._detect_databases(lowered, deps_set),
            devops=self._detect_devops(lowered),
        )

    # ------------------------------------------------------------------
    # Frontend
    # ------------------------------------------------------------------

    def _detect_frontend(self, files: list[str], deps: set[str]) -> list[str]:
        signals: list[str] = []

        # Frameworks / meta-frameworks
        if any("next.config" in f for f in files) or "next" in deps:
            signals.append("Next.js")
        if "react" in deps or any(".tsx" in f or ".jsx" in f for f in files):
            signals.append("React")
        if "vue" in deps or any("vue.config" in f or f.endswith(".vue") for f in files):
            signals.append("Vue")
        if "@angular/core" in deps:
            signals.append("Angular")
        if "svelte" in deps or any(f.endswith(".svelte") for f in files):
            signals.append("Svelte")
        if "nuxt" in deps or any("nuxt.config" in f for f in files):
            signals.append("Nuxt")

        # Build tooling
        if "vite" in deps or any("vite.config" in f for f in files):
            signals.append("Vite")
        if "tailwindcss" in deps or any("tailwind.config" in f for f in files):
            signals.append("Tailwind CSS")

        # ML / data-science UIs (critical for ML repos that skip traditional FE)
        if "streamlit" in deps or any("streamlit" in f for f in files):
            signals.append("Streamlit")
        if "gradio" in deps or any("gradio" in f for f in files):
            signals.append("Gradio")
        if any(f.endswith(".ipynb") for f in files):
            signals.append("Jupyter notebooks")
        if "panel" in deps or any("panel" in f for f in files):
            signals.append("Panel")
        if "dash" in deps or any("/dash" in f for f in files):
            signals.append("Plotly Dash")
        if any(f.endswith(".html") for f in files):
            if not signals:
                signals.append("HTML (Static/Vanilla)")
            else:
                signals.append("HTML Templates")

        return sorted(set(signals))

    # ------------------------------------------------------------------
    # Backend
    # ------------------------------------------------------------------

    def _detect_backend(self, files: list[str], deps: set[str]) -> list[str]:
        signals: list[str] = []

        if "fastapi" in deps:
            signals.append("FastAPI")
        if "flask" in deps:
            signals.append("Flask")
        if "django" in deps:
            signals.append("Django")
        if "express" in deps or "koa" in deps:
            signals.append("Express/Node.js")
        if "spring-boot" in " ".join(deps):
            signals.append("Spring Boot")

        # Language signals from file extensions
        if any(f.endswith(".py") for f in files):
            signals.append("Python")
        if any(f.endswith(".java") for f in files):
            signals.append("Java")
        if any(f.endswith(".go") for f in files):
            signals.append("Go")
        if any(f.endswith(".rs") for f in files):
            signals.append("Rust")
        if any(f.endswith(".ts") or f.endswith(".js") for f in files):
            signals.append("Node.js")

        return sorted(set(signals))

    # ------------------------------------------------------------------
    # Databases
    # ------------------------------------------------------------------

    def _detect_databases(self, files: list[str], deps: set[str]) -> list[str]:
        _mapping = {
            "postgresql": "PostgreSQL",
            "psycopg2": "PostgreSQL",
            "asyncpg": "PostgreSQL",
            "mongodb": "MongoDB",
            "motor": "MongoDB",
            "mongoose": "MongoDB",
            "mysql": "MySQL",
            "redis": "Redis",
            "aioredis": "Redis",
            "sqlite": "SQLite",
            "sqlalchemy": "SQLAlchemy (ORM)",
            "prisma": "Prisma (ORM)",
        }
        detected = [label for key, label in _mapping.items() if key in deps]
        if not detected and any("docker-compose" in f for f in files):
            return ["Unknown (containerised DB likely in Compose)"]
        return sorted(set(detected))

    # ------------------------------------------------------------------
    # DevOps / delivery
    # ------------------------------------------------------------------

    def _detect_devops(self, files: list[str]) -> list[str]:
        signals: list[str] = []

        if any("dockerfile" in f for f in files) or any(
            "docker-compose" in f for f in files
        ):
            signals.append("Docker")
        if any(".github/workflows" in f for f in files):
            signals.append("GitHub Actions")
        if any("k8s" in f or "kubernetes" in f for f in files):
            signals.append("Kubernetes")
        if any("terraform" in f or ".tf" == f[-3:] for f in files):
            signals.append("Terraform")
        if any("makefile" == f.split("/")[-1] for f in files):
            signals.append("Make")

        return sorted(set(signals))
