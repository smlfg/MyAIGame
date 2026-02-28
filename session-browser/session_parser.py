"""
session_parser.py — Parse Claude Code session JSONL files for SessionBrowser.

Handles 310+ session files efficiently with quick metadata extraction
and full conversation parsing on demand.
"""

import ast
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CLAUDE_DIR = Path.home() / ".claude" / "projects"

PRICING = {
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-opus-4-5": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
}

# Fallback pricing for partial model name matches
PRICING_FALLBACK = {
    "opus": {"input": 15.00, "output": 75.00},
    "sonnet": {"input": 3.00, "output": 15.00},
    "haiku": {"input": 0.25, "output": 1.25},
}


def format_size(bytes_: int) -> str:
    """Human-readable file size."""
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    if bytes_ < 1024 ** 3:
        return f"{bytes_ / 1024 ** 2:.1f} MB"
    return f"{bytes_ / 1024 ** 3:.1f} GB"


def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 timestamp string to datetime (UTC-aware)."""
    if not ts_str:
        return None
    try:
        # Handle both Z suffix and +00:00
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _project_label(project_dir_name: str) -> str:
    """Convert raw project directory name to human-readable label."""
    label = project_dir_name
    # Replace home prefix
    label = label.replace("-home-smlflg-", "~/")
    label = label.replace("-home-smlflg", "~")
    # Strip leading dash if still present
    if label.startswith("-"):
        label = label.lstrip("-")
    # Convert remaining dashes to slashes if no slash yet
    if "/" not in label and label != "~":
        label = label.replace("-", "/")
    return label


def _get_model_pricing(model: str) -> dict:
    """Look up pricing for a model name, falling back to partial match."""
    if not model:
        return {"input": 0.0, "output": 0.0}
    # Exact match first
    if model in PRICING:
        return PRICING[model]
    # Partial match
    model_lower = model.lower()
    for key, pricing in PRICING.items():
        if key in model_lower or model_lower in key:
            return pricing
    # Fallback by family name
    for family, pricing in PRICING_FALLBACK.items():
        if family in model_lower:
            return pricing
    return {"input": 0.0, "output": 0.0}


def extract_content(message: object) -> str:
    """Extract plain text from a message object (handles string and block list)."""
    if isinstance(message, dict):
        content = message.get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict):
                    btype = block.get("type", "")
                    if btype == "text":
                        texts.append(block.get("text", ""))
                    elif btype == "tool_use":
                        name = block.get("name", "")
                        if name:
                            texts.append(f"[tool: {name}]")
            return " ".join(texts).strip()
    if isinstance(message, str):
        try:
            parsed = ast.literal_eval(message)
            return extract_content(parsed)
        except (ValueError, SyntaxError):
            return message.strip()
    return ""


def _all_session_files() -> list[Path]:
    """Return all session JSONL files, excluding subagents/ directories."""
    files = []
    for path in CLAUDE_DIR.glob("*/*.jsonl"):
        # Exclude subagents directory
        if "subagents" in path.parts:
            continue
        files.append(path)
    return files


def quick_parse_all() -> list[dict]:
    """
    Fast metadata extraction for all sessions.

    Reads only the first ~30 lines and last ~10 lines of each file
    to stay well under 3 seconds for 310+ files.

    Returns list of session dicts sorted by last_timestamp descending.
    """
    results = []

    for filepath in _all_session_files():
        try:
            stat = filepath.stat()
            file_size = stat.st_size

            session_id = filepath.stem
            project_dir = filepath.parent.name
            project = _project_label(project_dir)

            # Read first 30 + last 10 lines efficiently
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                head_lines = []
                for _ in range(30):
                    line = f.readline()
                    if not line:
                        break
                    head_lines.append(line)

            # For last lines, read from end (small files: just re-read)
            if file_size < 1024 * 512:  # under 512 KB — read all
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    all_lines = f.readlines()
                tail_lines = all_lines[-10:] if len(all_lines) > 30 else []
            else:
                # Use subprocess tail for large files
                try:
                    result = subprocess.run(
                        ["tail", "-n", "10", str(filepath)],
                        capture_output=True, text=True, timeout=2
                    )
                    tail_lines = result.stdout.splitlines(keepends=True)
                except Exception:
                    tail_lines = []

            all_sample = head_lines + tail_lines

            slug = ""
            cwd = ""
            first_timestamp = None
            last_timestamp = None
            user_msg_count = 0
            assistant_msg_count = 0
            first_user_message = ""
            last_user_message = ""

            for line in all_sample:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Extract metadata from first available record
                if not slug and obj.get("slug"):
                    slug = obj["slug"]
                if not cwd and obj.get("cwd"):
                    cwd = obj["cwd"]

                ts = parse_timestamp(obj.get("timestamp"))

                msg_type = obj.get("type", "")

                if msg_type == "user":
                    user_msg_count += 1
                    if ts and (first_timestamp is None or ts < first_timestamp):
                        first_timestamp = ts
                    content = extract_content(obj.get("message", obj))
                    if content and not content.startswith("[tool"):
                        if not first_user_message:
                            first_user_message = content[:200]
                        # Always overwrite — last one wins from tail lines
                        last_user_message = content[:200]

                elif msg_type == "assistant":
                    assistant_msg_count += 1

                if ts and (last_timestamp is None or ts > last_timestamp):
                    last_timestamp = ts

            results.append({
                "session_id": session_id,
                "slug": slug,
                "project": project,
                "cwd": cwd,
                "first_timestamp": first_timestamp,
                "last_timestamp": last_timestamp,
                "user_msg_count": user_msg_count,
                "assistant_msg_count": assistant_msg_count,
                "file_size": file_size,
                "file_size_human": format_size(file_size),
                "filepath": str(filepath),
                "first_user_message": first_user_message,
                "last_user_message": last_user_message,
            })

        except (OSError, PermissionError):
            continue

    # Sort by last_timestamp descending (None goes to end)
    results.sort(
        key=lambda s: s["last_timestamp"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )
    return results


def full_parse_session(filepath: str) -> dict:
    """
    Parse a complete session JSONL file.

    Returns a dict with full conversation tree and token/cost totals.
    """
    path = Path(filepath)
    session_id = path.stem
    project_dir = path.parent.name
    project = _project_label(project_dir)

    messages = []
    slug = ""
    cwd = ""
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read = 0
    total_cache_creation = 0
    cost_by_model: dict[str, dict] = {}

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if not slug and obj.get("slug"):
                    slug = obj["slug"]
                if not cwd and obj.get("cwd"):
                    cwd = obj["cwd"]

                msg_type = obj.get("type", "")
                if msg_type not in ("user", "assistant"):
                    continue

                raw_msg = obj.get("message", {})
                timestamp = parse_timestamp(obj.get("timestamp"))

                # Extract content blocks
                content_blocks = []
                raw_content = raw_msg.get("content", "") if isinstance(raw_msg, dict) else ""

                if isinstance(raw_content, str):
                    if raw_content.strip():
                        content_blocks.append({"type": "text", "text": raw_content.strip()})
                elif isinstance(raw_content, list):
                    for block in raw_content:
                        if not isinstance(block, dict):
                            continue
                        btype = block.get("type", "")
                        if btype == "text":
                            content_blocks.append({
                                "type": "text",
                                "text": block.get("text", ""),
                            })
                        elif btype == "tool_use":
                            content_blocks.append({
                                "type": "tool_use",
                                "name": block.get("name", ""),
                                "id": block.get("id", ""),
                                "input_summary": str(block.get("input", ""))[:200],
                            })
                        elif btype == "tool_result":
                            content_blocks.append({
                                "type": "tool_result",
                                "tool_use_id": block.get("tool_use_id", ""),
                                "content": str(block.get("content", ""))[:200],
                            })
                        elif btype == "thinking":
                            content_blocks.append({
                                "type": "thinking",
                                "text": block.get("thinking", "")[:200],
                            })

                # Token usage (assistant messages only)
                model = ""
                token_usage = {}
                if msg_type == "assistant" and isinstance(raw_msg, dict):
                    model = raw_msg.get("model", "")
                    usage = raw_msg.get("usage", {}) or {}
                    inp = usage.get("input_tokens", 0) or 0
                    out = usage.get("output_tokens", 0) or 0
                    cache_read = usage.get("cache_read_input_tokens", 0) or 0
                    cache_create = usage.get("cache_creation_input_tokens", 0) or 0

                    token_usage = {
                        "input_tokens": inp,
                        "output_tokens": out,
                        "cache_read_input_tokens": cache_read,
                        "cache_creation_input_tokens": cache_create,
                    }

                    total_input_tokens += inp
                    total_output_tokens += out
                    total_cache_read += cache_read
                    total_cache_creation += cache_create

                    # Track cost by model
                    if model:
                        if model not in cost_by_model:
                            cost_by_model[model] = {
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "cache_read": 0,
                                "cache_creation": 0,
                                "cost": 0.0,
                            }
                        p = _get_model_pricing(model)
                        msg_cost = (inp * p["input"] + out * p["output"]) / 1_000_000
                        cost_by_model[model]["input_tokens"] += inp
                        cost_by_model[model]["output_tokens"] += out
                        cost_by_model[model]["cache_read"] += cache_read
                        cost_by_model[model]["cache_creation"] += cache_create
                        cost_by_model[model]["cost"] += msg_cost

                # Tool calls list for convenience
                tool_calls = [b for b in content_blocks if b["type"] == "tool_use"]

                messages.append({
                    "role": msg_type,
                    "content": content_blocks,
                    "text": extract_content(raw_msg),
                    "timestamp": timestamp,
                    "timestamp_str": timestamp.isoformat() if timestamp else "",
                    "model": model,
                    "token_usage": token_usage,
                    "tool_calls": tool_calls,
                    "uuid": obj.get("uuid", ""),
                    "parent_uuid": obj.get("parentUuid", ""),
                })

    except (OSError, PermissionError) as e:
        return {"error": str(e), "session_id": session_id}

    # Total cost
    total_cost = sum(m["cost"] for m in cost_by_model.values())

    return {
        "session_id": session_id,
        "slug": slug,
        "project": project,
        "cwd": cwd,
        "filepath": str(path),
        "messages": messages,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cache_read": total_cache_read,
        "total_cache_creation": total_cache_creation,
        "total_cost": total_cost,
        "cost_breakdown_by_model": cost_by_model,
    }


def search_sessions(keyword: str, session_files: Optional[list[str]] = None) -> list[dict]:
    """
    Fast keyword search across session files using grep.

    Returns list of dicts with filepath, session_id, slug, and match context.
    """
    if session_files is None:
        session_files = [str(p) for p in _all_session_files()]

    if not keyword or not session_files:
        return []

    # Fast file filtering with grep -l
    try:
        result = subprocess.run(
            ["grep", "-l", "-i", "--", keyword] + session_files,
            capture_output=True, text=True, timeout=10
        )
        matching_files = [f for f in result.stdout.splitlines() if f.strip()]
    except subprocess.TimeoutExpired:
        matching_files = session_files  # fallback: search all
    except Exception:
        matching_files = []

    results = []
    for filepath in matching_files:
        path = Path(filepath)
        session_id = path.stem
        project = _project_label(path.parent.name)
        slug = ""
        matches = []

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if keyword.lower() not in line.lower():
                    continue

                # Try to extract readable content from JSON
                try:
                    obj = json.loads(line)
                    if not slug and obj.get("slug"):
                        slug = obj["slug"]
                    text = extract_content(obj.get("message", obj))
                except (json.JSONDecodeError, Exception):
                    text = line.strip()

                # Gather context lines (previous + next)
                context_before = []
                for j in range(max(0, i - 2), i):
                    try:
                        ctx_obj = json.loads(lines[j])
                        ctx_text = extract_content(ctx_obj.get("message", ctx_obj))
                        if ctx_text:
                            context_before.append(ctx_text[:100])
                    except Exception:
                        pass

                context_after = []
                for j in range(i + 1, min(len(lines), i + 3)):
                    try:
                        ctx_obj = json.loads(lines[j])
                        ctx_text = extract_content(ctx_obj.get("message", ctx_obj))
                        if ctx_text:
                            context_after.append(ctx_text[:100])
                    except Exception:
                        pass

                matches.append({
                    "line_number": i + 1,
                    "content": text[:300],
                    "context": {
                        "before": context_before,
                        "after": context_after,
                    },
                })

                if len(matches) >= 20:  # Cap matches per file
                    break

        except (OSError, PermissionError):
            continue

        results.append({
            "filepath": filepath,
            "session_id": session_id,
            "slug": slug,
            "project": project,
            "matches": matches,
            "match_count": len(matches),
        })

    return results


def calc_session_cost(messages: list[dict]) -> dict:
    """
    Calculate token totals and cost from a list of parsed messages.

    Expects messages in the format returned by full_parse_session().
    """
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_creation = 0
    cost_by_model: dict[str, dict] = {}

    for msg in messages:
        usage = msg.get("token_usage", {})
        if not usage:
            continue

        model = msg.get("model", "unknown")
        inp = usage.get("input_tokens", 0) or 0
        out = usage.get("output_tokens", 0) or 0
        cache_read = usage.get("cache_read_input_tokens", 0) or 0
        cache_create = usage.get("cache_creation_input_tokens", 0) or 0

        total_input += inp
        total_output += out
        total_cache_read += cache_read
        total_cache_creation += cache_create

        if model not in cost_by_model:
            cost_by_model[model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read": 0,
                "cache_creation": 0,
                "cost": 0.0,
            }

        p = _get_model_pricing(model)
        msg_cost = (inp * p["input"] + out * p["output"]) / 1_000_000
        cost_by_model[model]["input_tokens"] += inp
        cost_by_model[model]["output_tokens"] += out
        cost_by_model[model]["cache_read"] += cache_read
        cost_by_model[model]["cache_creation"] += cache_create
        cost_by_model[model]["cost"] += msg_cost

    total_cost = sum(m["cost"] for m in cost_by_model.values())

    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cache_read": total_cache_read,
        "total_cache_creation": total_cache_creation,
        "total_cost": total_cost,
        "cost_breakdown_by_model": cost_by_model,
    }


def get_all_projects() -> list[str]:
    """Return sorted unique project labels from all session files."""
    projects = set()
    for path in _all_session_files():
        projects.add(_project_label(path.parent.name))
    return sorted(projects)
