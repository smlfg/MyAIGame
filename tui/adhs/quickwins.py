"""Quick Win Generator — static analysis, $0 cost, no LLM needed."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class QuickWin:
    title: str
    description: str
    estimated_minutes: int
    skill_to_run: Optional[str]  # e.g. "/fix", "/lint", None for manual


class QuickWinGenerator:
    """
    Heuristic quick-win finder using only static analysis:
      - TODO/FIXME comments in source files
      - Failing tests (via pytest --collect-only)
      - Lint warnings (via ruff/flake8 if available)
      - Uncommitted files (git status)

    All analysis is local and instantaneous — no LLM, no network, $0 cost.
    """

    MAX_WINS = 5
    _SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".rs", ".go", ".sh"}

    def generate(self, project_path: Path, count: int = 3) -> list[QuickWin]:
        wins: list[QuickWin] = []
        wins += self._find_todos(project_path)
        wins += self._find_uncommitted(project_path)
        wins += self._find_lint_warnings(project_path)
        wins += self._find_failing_tests(project_path)
        # Deduplicate by title, keep top N
        seen: set[str] = set()
        unique: list[QuickWin] = []
        for w in wins:
            if w.title not in seen:
                seen.add(w.title)
                unique.append(w)
        return unique[:count]

    # ------------------------------------------------------------------
    # Finders
    # ------------------------------------------------------------------

    def _find_todos(self, project_path: Path) -> list[QuickWin]:
        results: list[QuickWin] = []
        todo_re = re.compile(r"#\s*(TODO|FIXME|HACK|XXX)[:\s]+(.*)", re.IGNORECASE)

        for src_file in self._iter_source_files(project_path):
            try:
                text = src_file.read_text(errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                m = todo_re.search(line)
                if m:
                    kind = m.group(1).upper()
                    comment = m.group(2).strip()[:80]
                    rel = src_file.relative_to(project_path)
                    results.append(QuickWin(
                        title=f"{kind}: {comment[:50]}",
                        description=f"{rel}:{lineno} — {comment}",
                        estimated_minutes=5,
                        skill_to_run="/fix",
                    ))
                if len(results) >= self.MAX_WINS:
                    return results
        return results

    def _find_uncommitted(self, project_path: Path) -> list[QuickWin]:
        results: list[QuickWin] = []
        try:
            out = subprocess.check_output(
                ["git", "status", "--short"],
                cwd=project_path,
                stderr=subprocess.DEVNULL,
                timeout=5,
                text=True,
            )
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return results

        modified = []
        untracked = []
        for line in out.splitlines():
            status = line[:2].strip()
            filename = line[3:].strip()
            if status in ("M", "MM", "AM"):
                modified.append(filename)
            elif status == "??":
                untracked.append(filename)

        if modified:
            results.append(QuickWin(
                title=f"Commit {len(modified)} modified file(s)",
                description=", ".join(modified[:3]) + (" ..." if len(modified) > 3 else ""),
                estimated_minutes=3,
                skill_to_run="/checkpoint",
            ))
        if untracked:
            results.append(QuickWin(
                title=f"Review {len(untracked)} untracked file(s)",
                description=", ".join(untracked[:3]) + (" ..." if len(untracked) > 3 else ""),
                estimated_minutes=5,
                skill_to_run=None,
            ))
        return results

    def _find_lint_warnings(self, project_path: Path) -> list[QuickWin]:
        """Try ruff, fall back to flake8, skip silently if neither present."""
        for tool, args in [
            ("ruff", ["ruff", "check", "--quiet", "--no-cache", str(project_path)]),
            ("flake8", ["flake8", "--max-line-length=120", "--statistics", str(project_path)]),
        ]:
            try:
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=project_path,
                )
                lines = [l for l in result.stdout.splitlines() if l.strip()]
                if lines:
                    count = len(lines)
                    return [QuickWin(
                        title=f"Fix {min(count, 99)}+ lint warning(s) ({tool})",
                        description=lines[0][:100],
                        estimated_minutes=10,
                        skill_to_run="/lint",
                    )]
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                continue
        return []

    def _find_failing_tests(self, project_path: Path) -> list[QuickWin]:
        """Run pytest --tb=no -q and surface failures."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=no", "-q", "--no-header"],
                capture_output=True,
                text=True,
                timeout=20,
                cwd=project_path,
            )
            # pytest exits 1 on failure
            if result.returncode not in (0, 5):  # 5 = no tests collected
                summary_line = ""
                for line in reversed(result.stdout.splitlines()):
                    if "failed" in line or "error" in line:
                        summary_line = line.strip()
                        break
                if summary_line:
                    return [QuickWin(
                        title=f"Fix failing tests: {summary_line[:60]}",
                        description="Run pytest to see details",
                        estimated_minutes=15,
                        skill_to_run="/test",
                    )]
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _iter_source_files(self, root: Path):
        skip_dirs = {"venv", ".venv", "node_modules", ".git", "__pycache__", "dist", "build"}
        for path in root.rglob("*"):
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.is_file() and path.suffix in self._SOURCE_EXTENSIONS:
                yield path
