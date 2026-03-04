"""SKILL.md parser — extracts YAML frontmatter and body."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


class SkillParseError(ValueError):
    """Raised when a SKILL.md cannot be parsed."""


class SkillParser:
    """Parse SKILL.md files into skill metadata dicts."""

    @staticmethod
    def parse(path: Path) -> dict:
        """Parse a SKILL.md file and return the skill metadata dict.

        Returns a dict with at minimum:
            name (str), description (str), cost_tier (str),
            category (str), delegate (str), body (str)
        """
        text = path.read_text(encoding="utf-8")
        return SkillParser.parse_text(text, source=str(path))

    @staticmethod
    def parse_text(text: str, source: str = "<string>") -> dict:
        """Parse raw SKILL.md text."""
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise SkillParseError(
                f"{source}: missing YAML frontmatter (expected --- ... ---)"
            )

        frontmatter_raw, body = match.group(1), match.group(2)

        if _YAML_AVAILABLE:
            try:
                meta = yaml.safe_load(frontmatter_raw) or {}
            except yaml.YAMLError as e:
                raise SkillParseError(f"{source}: invalid YAML frontmatter: {e}") from e
        else:
            # Minimal fallback: parse simple key: value lines
            meta = {}
            for line in frontmatter_raw.splitlines():
                if ":" in line and not line.startswith(" "):
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()

        if "name" not in meta:
            raise SkillParseError(f"{source}: frontmatter missing required 'name' field")

        meta["body"] = body.strip()
        meta.setdefault("description", "")
        meta.setdefault("cost_tier", "medium")
        meta.setdefault("category", "general")
        meta.setdefault("delegate", "opencode")
        meta.setdefault("dependencies", [])
        meta.setdefault("tags", [])

        return meta

    @staticmethod
    def resolve_template(skill: dict, arguments: str) -> str:
        """Substitute $ARGUMENTS placeholder in the skill body."""
        body = skill.get("body", "")
        return body.replace("$ARGUMENTS", arguments)
