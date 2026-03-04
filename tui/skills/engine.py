"""Skill engine — discover, index, and retrieve skills from SKILL.md files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .parser import SkillParser, SkillParseError

# Default skill directories to search (relative to project root or absolute)
DEFAULT_SKILL_DIRS = [
    Path.home() / "Projekte" / "MyAIGame" / "portable" / "skills",
]


class SkillEngine:
    """Discovers and indexes skills from SKILL.md files.

    Usage::
        engine = SkillEngine()
        engine.discover_skills()          # scan default dirs
        skill = engine.get_skill("chef")  # lookup by name
        results = engine.search("code")   # fuzzy name search
    """

    def __init__(self, extra_dirs: Optional[list[Path]] = None):
        self._skills: dict[str, dict] = {}
        self._dirs: list[Path] = list(DEFAULT_SKILL_DIRS)
        if extra_dirs:
            self._dirs.extend(extra_dirs)

    def discover_skills(self, skill_dirs: Optional[list[Path]] = None) -> int:
        """Scan directories for SKILL.md files and populate the registry.

        Returns the count of successfully loaded skills.
        """
        dirs = skill_dirs if skill_dirs is not None else self._dirs
        loaded = 0
        for base_dir in dirs:
            if not base_dir.exists():
                continue
            for skill_md in base_dir.rglob("SKILL.md"):
                try:
                    skill = SkillParser.parse(skill_md)
                    self._skills[skill["name"]] = skill
                    loaded += 1
                except (SkillParseError, OSError):
                    pass  # Skip malformed files silently
        return loaded

    def get_skill(self, name: str) -> Optional[dict]:
        """Return skill dict by exact name, or None."""
        return self._skills.get(name)

    def list_skills(self) -> dict[str, dict]:
        """Return all loaded skills keyed by name."""
        return dict(self._skills)

    def search(self, query: str) -> list[dict]:
        """Fuzzy-ish search: return skills whose name or tags contain query."""
        q = query.lower()
        results = []
        for skill in self._skills.values():
            name_match = q in skill["name"].lower()
            tag_match = any(q in t.lower() for t in skill.get("tags", []))
            desc_match = q in skill.get("description", "").lower()
            if name_match or tag_match or desc_match:
                results.append(skill)
        return results

    def register(self, skill: dict) -> None:
        """Manually register a skill dict (for testing / dynamic loading)."""
        if "name" not in skill:
            raise ValueError("skill dict must have a 'name' key")
        self._skills[skill["name"]] = skill

    def clear(self) -> None:
        """Remove all registered skills."""
        self._skills.clear()
