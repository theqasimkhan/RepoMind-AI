import asyncio
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Set

from app.core.config import get_settings
from app.repositories.analysis_jobs_repository import AnalysisJobsRepository
from app.schemas.repository import CommitTimelineEntry, RepositoryAnalyzeResponse
from app.services.chunking import build_index_chunks_for_file
from app.utils.repo_url import github_repo_slug, normalize_github_repo_url


class RepositoryAnalysisService:
    async def analyze(self, repo_url: str) -> RepositoryAnalyzeResponse:
        result, _ = await self.analyze_with_chunks(repo_url)
        return result

    async def analyze_with_chunks(
        self, repo_url: str
    ) -> tuple[RepositoryAnalyzeResponse, list[dict[str, str | int | None]]]:
        canon = normalize_github_repo_url(repo_url)
        repo_name = github_repo_slug(canon)
        scan_data = await self._clone_and_scan(canon)
        commit_timeline = scan_data.get("commit_timeline") or []
        detected_frontend = self._detect_frontend(scan_data["files"], scan_data["dependencies"])
        detected_backend = self._detect_backend(scan_data["files"], scan_data["dependencies"])
        detected_databases = self._detect_databases(scan_data["files"], scan_data["dependencies"])
        devops_signals = self._detect_devops(scan_data["files"])
        detected_apis = self._detect_apis(scan_data["files"])
        architecture_patterns = self._detect_architecture_patterns(scan_data["files"])
        architecture_style = self._infer_architecture_style(scan_data["files"])
        folder_explanations = self._build_folder_explanations(scan_data["top_level_dirs"])
        summary = (
            f"{repo_name} contains {len(scan_data['files'])} indexed files with "
            f"{', '.join(detected_frontend or ['no clear frontend'])} and "
            f"{', '.join(detected_backend or ['no clear backend'])} signals. "
            f"Primary architecture inference: {architecture_style}."
        )
        mermaid_diagram = self._generate_mermaid(
            detected_frontend=detected_frontend,
            detected_backend=detected_backend,
            detected_databases=detected_databases,
            devops_signals=devops_signals,
            architecture_patterns=architecture_patterns,
            architecture_style=architecture_style,
            top_level_dirs=scan_data["top_level_dirs"],
        )

        return RepositoryAnalyzeResponse(
            repository=repo_name,
            repo_clone_url=canon,
            detected_frontend=detected_frontend,
            detected_backend=detected_backend,
            detected_databases=detected_databases,
            devops_signals=devops_signals,
            dependencies=scan_data["dependencies"][:30],
            detected_apis=detected_apis,
            architecture_patterns=architecture_patterns,
            folder_explanations=folder_explanations,
            file_tree=scan_data["files"][:200],
            architecture_style=architecture_style,
            summary=summary,
            mermaid_diagram=mermaid_diagram,
            commit_timeline=[CommitTimelineEntry(**c) for c in commit_timeline],
        ), scan_data["chunks"]

    async def _clone_and_scan(self, repo_url: str) -> dict:
        def _run_clone() -> dict:
            with tempfile.TemporaryDirectory(prefix="repomind-") as tmp_dir:
                clone_target = Path(tmp_dir) / "repo"
                command = [
                    "git",
                    "clone",
                    "--depth",
                    "48",
                    repo_url,
                    str(clone_target),
                ]
                result = subprocess.run(command, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    raise RuntimeError(f"git clone failed: {result.stderr.strip() or result.stdout.strip()}")
                scan = self._scan_cloned_repository(clone_target)
                scan["commit_timeline"] = self._read_commit_timeline(clone_target, limit=40)
                return scan

        return await asyncio.to_thread(_run_clone)

    def _scan_cloned_repository(self, root: Path) -> dict:
        ignored_dirs = {".git", "node_modules", ".next", ".venv", "venv", "dist", "build"}
        files: list[str] = []
        dependencies: list[str] = []
        top_level_dirs: list[str] = [child.name for child in root.iterdir() if child.is_dir()]
        chunks: list[dict[str, str | int | None]] = []

        # First pass: Discovery
        all_files: list[Path] = []
        for path in root.rglob("*"):
            if any(part in ignored_dirs for part in path.parts):
                continue
            if path.is_file():
                all_files.append(path)
                relative = str(path.relative_to(root)).replace("\\", "/")
                files.append(relative)
                if path.name == "package.json":
                    dependencies.extend(self._read_npm_dependencies(path))
                if path.name in {"requirements.txt", "pyproject.toml"}:
                    dependencies.extend(self._read_python_dependencies(path))

        # Second pass: Chunking (limited for performance/token budget)
        for path in all_files:
            if len(chunks) >= 500:
                break
            if self._is_indexable_text_file(path):
                file_chunks = self._read_file_chunks(path=path, root=root)
                chunks.extend(file_chunks)

        if len(chunks) > 500:
            chunks = chunks[:500]

        unique_dependencies = sorted(set(dependencies))
        files.sort()
        top_level_dirs.sort()
        return {
            "files": files,
            "dependencies": unique_dependencies,
            "top_level_dirs": top_level_dirs,
            "chunks": chunks,
        }

    @staticmethod
    def _read_commit_timeline(repo_root: Path, *, limit: int = 40) -> list[dict[str, str | int | None]]:
        git_dir = repo_root / ".git"
        if not git_dir.exists():
            return []
        fmt = "%H|--|%s|--|%ct"
        result = subprocess.run(
            ["git", "-C", str(repo_root), "log", f"-n{limit}", f"--pretty=format:{fmt}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=60,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        entries: list[dict[str, str | int | None]] = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|--|")
            if len(parts) < 3:
                continue
            sha, subject, ts_raw = parts[0], parts[1], parts[2]
            committed_at: int | None
            try:
                committed_at = int(ts_raw)
            except ValueError:
                committed_at = None
            entries.append({"sha": sha, "subject": subject.strip(), "committed_at": committed_at})
        return entries

    def _read_npm_dependencies(self, file_path: Path) -> list[str]:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            deps = list((data.get("dependencies") or {}).keys())
            dev_deps = list((data.get("devDependencies") or {}).keys())
            return deps + dev_deps
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to read npm dependencies from {file_path}: {e}")
            return []

    def _read_python_dependencies(self, file_path: Path) -> list[str]:
        import logging
        logger = logging.getLogger(__name__)
        if file_path.name == "requirements.txt":
            packages: list[str] = []
            try:
                for line in file_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        packages.append(stripped.split("==")[0].split(">=")[0].strip())
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read requirements.txt from {file_path}: {e}")
                return []
            return packages
        if file_path.name == "pyproject.toml":
            try:
                content = file_path.read_text(encoding="utf-8").lower()
                return [dep for dep in ["fastapi", "django", "flask", "sqlalchemy"] if dep in content]
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read pyproject.toml from {file_path}: {e}")
                return []
        return []

    def _detect_frontend(self, files: list[str], dependencies: list[str]) -> list[str]:
        signals: list[str] = []
        deps_set = {d.lower() for d in dependencies}
        files_set = {f.lower() for f in files}
        
        # Frameworks
        if any(f in files_set for f in ["next.config.js", "next.config.ts"]) or "next" in deps_set:
            signals.append("Next.js")
        if "react" in deps_set or any(".tsx" in f or ".jsx" in f for f in files_set):
            signals.append("React")
        if "vue" in deps_set or any("vue.config" in f or f.endswith(".vue") for f in files_set):
            signals.append("Vue")
        if "@angular/core" in deps_set:
            signals.append("Angular")
        if "svelte" in deps_set or any(f.endswith(".svelte") for f in files_set):
            signals.append("Svelte")
        if "nuxt" in deps_set or "nuxt.config.js" in files_set:
            signals.append("Nuxt")
            
        # Tooling
        if "vite" in deps_set or any("vite.config" in f for f in files_set):
            signals.append("Vite")
        if "tailwindcss" in deps_set or "tailwind.config.js" in files_set:
            signals.append("Tailwind CSS")
        if "streamlit" in deps_set or any("streamlit" in f for f in files_set):
            signals.append("Streamlit")
        if "gradio" in deps_set or any("gradio" in f for f in files_set):
            signals.append("Gradio")
        if any(f.endswith(".ipynb") for f in files):
            signals.append("Jupyter notebooks")
        if any(f.endswith(".html") for f in files):
            if not signals:
                signals.append("HTML (Static/Vanilla)")
            else:
                signals.append("HTML Templates")

        return sorted(set(signals))

    def _detect_backend(self, files: list[str], dependencies: list[str]) -> list[str]:
        signals: list[str] = []
        deps_set = {d.lower() for d in dependencies}
        if "fastapi" in deps_set:
            signals.append("FastAPI")
        if "django" in deps_set:
            signals.append("Django")
        if "express" in deps_set or "koa" in deps_set:
            signals.append("Express/Node.js")
        if "spring-boot" in " ".join(deps_set):
            signals.append("Spring Boot")
        if any(f.endswith(".java") for f in files):
            signals.append("Java")
        if any(f.endswith(".py") for f in files):
            signals.append("Python")
        if any(f.endswith(".go") for f in files):
            signals.append("Go")
        if any(f.endswith(".rs") for f in files):
            signals.append("Rust")
        if any(f.endswith(".ts") or f.endswith(".js") for f in files):
            signals.append("Node.js")
        return sorted(set(signals))

    def _detect_databases(self, files: list[str], dependencies: list[str]) -> list[str]:
        deps_set = {d.lower() for d in dependencies}
        mapping = {
            "postgresql": "PostgreSQL",
            "psycopg2": "PostgreSQL",
            "mongodb": "MongoDB",
            "mongoose": "MongoDB",
            "mysql": "MySQL",
            "redis": "Redis",
        }
        detected = [label for key, label in mapping.items() if key in deps_set]
        if not detected and any("docker-compose" in file_path for file_path in files):
            return ["Unknown (containerized DB likely configured)"]
        return sorted(set(detected))

    def _detect_devops(self, files: list[str]) -> list[str]:
        signals: list[str] = []
        if any("dockerfile" in file_path.lower() for file_path in files) or "docker-compose.yml" in files:
            signals.append("Docker")
        if any(file_path.startswith(".github/workflows/") for file_path in files):
            signals.append("GitHub Actions")
        if any("k8s" in file_path.lower() or "kubernetes" in file_path.lower() for file_path in files):
            signals.append("Kubernetes")
        return sorted(set(signals))

    def _detect_apis(self, files: list[str]) -> list[str]:
        api_files = [file_path for file_path in files if "api" in file_path.lower()][:15]
        return api_files

    def _detect_architecture_patterns(self, files: list[str]) -> list[str]:
        patterns: list[str] = []
        path_text = " ".join(files).lower()
        if "controller" in path_text and "service" in path_text:
            patterns.append("Layered architecture")
        if "domain" in path_text and "infrastructure" in path_text:
            patterns.append("Clean architecture")
        if "microservice" in path_text or "services/" in path_text:
            patterns.append("Service-oriented modules")
        if "repository" in path_text:
            patterns.append("Repository pattern")
        return patterns or ["Modular code organization"]

    def _infer_architecture_style(self, files: list[str]) -> str:
        service_dirs = [path for path in files if "/services/" in path.lower() or path.lower().startswith("services/")]
        app_dirs = [path for path in files if "/apps/" in path.lower() or path.lower().startswith("apps/")]
        if len(app_dirs) > 5 or len(service_dirs) > 25:
            return "Microservices-oriented repository"
        return "Modular monolith with bounded service layers"

    def _build_folder_explanations(self, folders: list[str]) -> dict[str, str]:
        descriptions: dict[str, str] = {}
        known = {
            "src": "Primary source code for core application features.",
            "app": "Application layer containing routes, pages, and orchestration logic.",
            "backend": "Backend service code and API handlers.",
            "frontend": "Frontend UI and client-side logic.",
            "docs": "Documentation and architecture guides.",
            "tests": "Automated test suites and validation assets.",
            "scripts": "Helper scripts for setup, build, or maintenance tasks.",
        }
        for folder in folders[:25]:
            descriptions[folder] = known.get(
                folder.lower(),
                "Project module containing domain-specific implementation files.",
            )
        return descriptions

    @staticmethod
    def _m_label(text: str, max_len: int = 56) -> str:
        t = (text or "").replace('"', "'").replace("\n", " ").strip()
        if len(t) > max_len:
            return t[: max_len - 1] + "…"
        return t or "—"

    def _generate_mermaid(
        self,
        detected_frontend: list[str],
        detected_backend: list[str],
        detected_databases: list[str],
        devops_signals: list[str],
        architecture_patterns: list[str],
        architecture_style: str,
        top_level_dirs: list[str],
    ) -> str:
        """Richer default diagram than a single FE/BE/DB triangle — still heuristic, not LLM-drawn."""
        style_lbl = self._m_label(architecture_style or "Inferred architecture", 52)
        fe_txt = ", ".join(detected_frontend[:6]) if detected_frontend else "Not detected (CLI / notebooks / libs only is common for ML repos)"
        be_txt = ", ".join(detected_backend[:6]) if detected_backend else "Not classified"
        db_txt = ", ".join(detected_databases[:4]) if detected_databases else "Not detected"
        lines = [
            "flowchart TB",
            f'  root["{style_lbl}"]',
            f'  fe["Frontend / UX<br/>{self._m_label(fe_txt, 72)}"]',
            f'  be["App & services<br/>{self._m_label(be_txt, 72)}"]',
            f'  db[("Data stores<br/>{self._m_label(db_txt, 56)}")]',
            "  root --> fe",
            "  root --> be",
            "  fe --> be",
            "  be --> db",
            '  be --> rag[("Vector retrieval<br/>(FAISS)")]',
            '  be --> llm["Model providers<br/>(Gemini / OpenRouter / OpenAI)"]',
        ]
        if devops_signals:
            dv = ", ".join(devops_signals[:6])
            lines.append(f'  dev["Delivery & ops<br/>{self._m_label(dv, 72)}"]')
            lines.append("  be --> dev")
        for i, pat in enumerate(architecture_patterns[:5]):
            pid = f"pat{i}"
            lines.append(f'  {pid}["{self._m_label(pat, 48)}"]')
            lines.append(f"  be --> {pid}")
        skip = {".git", ".github", "__pycache__", "node_modules", ".venv", "venv"}
        dirs = [d for d in top_level_dirs if d not in skip][:6]
        if dirs:
            dtxt = ", ".join(dirs)
            lines.append(f'  areas["Repo layout<br/>{self._m_label(dtxt, 72)}"]')
            lines.append("  root --> areas")
        return "\n".join(lines)

    def _is_indexable_text_file(self, path: Path) -> bool:
        text_extensions = {
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".java",
            ".go",
            ".rs",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".toml",
        }
        if path.suffix.lower() not in text_extensions:
            return False
        try:
            return path.stat().st_size <= 200_000
        except OSError:
            return False

    def _read_file_chunks(self, path: Path, root: Path, max_chunks: int | None = None) -> list[dict[str, str | int | None]]:
        settings = get_settings()
        max_c = max_chunks if max_chunks is not None else settings.retrieval_max_chunks_per_file
        return build_index_chunks_for_file(
            path,
            root,
            strategy=settings.retrieval_chunk_strategy,
            chunk_size=settings.retrieval_chunk_size,
            overlap=settings.retrieval_chunk_overlap,
            max_chunks_per_file=max_c,
        )


class AnalysisJobManager:
    def __init__(self) -> None:
        self._service = RepositoryAnalysisService()
        settings = get_settings()
        self._repository = AnalysisJobsRepository(settings.sqlite_db_path)
        self._running_tasks: Set[asyncio.Task] = set()

    def create_job(self, repo_url: str, user_id: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        canon = normalize_github_repo_url(repo_url)
        self._repository.create_job(job_id, canon, user_id=user_id)
        # Try Celery first; fall back to asyncio.create_task if Redis unavailable
        try:
            from app.worker.tasks import analyze_repository_task
            analyze_repository_task.delay(job_id)
        except Exception:
            task = asyncio.create_task(self._run_job(job_id))
            self._running_tasks.add(task)
            task.add_done_callback(lambda t: self._running_tasks.discard(t))
        return job_id

    def get_job(self, job_id: str) -> dict | None:
        return self._repository.get_job(job_id)

    def list_recent_jobs(self, limit: int = 20, user_id: str | None = None) -> list[dict]:
        return self._repository.list_recent_jobs(limit=limit, user_id=user_id)

    def initialize(self) -> None:
        self._repository.initialize()

    def get_retrieval_chunks(self, repo_url: str, limit: int = 200) -> list[dict]:
        canon = normalize_github_repo_url(repo_url)
        return self._repository.get_chunks_for_repo(repo_url=canon, limit=limit)

    def get_latest_completed_job_id(self, repo_url: str) -> str | None:
        canon = normalize_github_repo_url(repo_url)
        return self._repository.get_latest_completed_job_id(canon)

    def get_latest_completed_analysis(self, repo_url: str) -> RepositoryAnalyzeResponse | None:
        canon = normalize_github_repo_url(repo_url)
        raw = self._repository.get_latest_completed_result(canon)
        if not raw:
            return None
        return RepositoryAnalyzeResponse.model_validate(raw)

    async def _run_job(self, job_id: str) -> None:
        try:
            self._repository.update_job(
                job_id, status="running", progress=15, stage="Cloning and scanning repository"
            )
            await asyncio.sleep(0.1)
            repo_url = self._repository.get_repo_url(job_id)
            if not repo_url:
                raise RuntimeError("Job source repository not found")
            result, chunks = await self._service.analyze_with_chunks(repo_url)
            self._repository.update_job(
                job_id, status="running", progress=90, stage="Generating architecture insights"
            )
            await asyncio.sleep(0.1)
            self._repository.replace_chunks_for_job(job_id, chunks)
            self._repository.update_job(
                job_id,
                status="completed",
                progress=100,
                stage="Completed",
                result=result.model_dump(),
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(f"Background job {job_id} failed: {exc}", exc_info=True)
            self._repository.update_job(
                job_id, status="failed", progress=100, stage="Failed", error=str(exc)
            )


analysis_job_manager = AnalysisJobManager()
