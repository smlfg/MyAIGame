#!/usr/bin/env python3
"""Claude Code Hook — Codex-Zweitmeinung bei Fehlern.

Handles PostToolUseFailure (harte Fehler) UND PostToolUse (Soft-Error-Erkennung).
Ruft Codex CLI auf und injiziert die Analyse als additionalContext.

IRON RULE: Always exit 0. Never block the agent. Never crash.
"""

import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time

# --- Error Patterns fuer Soft-Error-Erkennung in Bash/Task Output ---
SOFT_ERROR_PATTERNS = [
    "Traceback (most recent call last)",
    "Error:",
    "FAILED",
    "SyntaxError",
    "TypeError",
    "NameError",
    "ValueError",
    "AttributeError",
    "ImportError",
    "ModuleNotFoundError",
    "KeyError",
    "IndexError",
    "RuntimeError",
    "fatal:",
    "panic:",
    "ERRNO",
    "Exception:",
    "Uncaught",
    "segfault",
    "core dumped",
]

# --- Triviale Fehler die keinen Codex-Call brauchen ---
TRIVIAL_PATTERNS = [
    "file not found",
    "no such file",
    "permission denied",
    "not unique in the file",
    "empty file",
    "command not found",
    "is a directory",
    "not a directory",
]

CODEX_TIMEOUT = 60
CODEX_CMD = "codex"
CWD_FALLBACK = "/home/smlflg"


def _codex_available() -> bool:
    """Preflight: Codex CLI erreichbar?"""
    try:
        subprocess.run([CODEX_CMD, "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _get_state_file(session_id: str) -> str:
    """Pfad zum Error-Tracking State-File."""
    return f"/tmp/claude-codex-errors-{session_id}.json"


def _load_state(session_id: str) -> dict:
    """State-File laden oder leeres Dict zurueckgeben."""
    path = _get_state_file(session_id)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"errors": [], "count": 0}


def _save_state(session_id: str, state: dict) -> None:
    """State-File atomar schreiben (temp + rename)."""
    path = _get_state_file(session_id)
    try:
        fd, tmp = tempfile.mkstemp(dir="/tmp", prefix=f"claude-codex-{session_id}-")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state, f)
            os.replace(tmp, path)  # atomar auf gleichem Filesystem
        except Exception:
            os.unlink(tmp)
    except Exception:
        pass


def _log_error(session_id: str, tool_name: str, error_text: str) -> None:
    """Fehler ins State-File loggen (mit File-Lock gegen Race Conditions)."""
    lock_path = f"/tmp/claude-codex-errors-{session_id}.lock"
    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            state = _load_state(session_id)
            state["errors"].append({
                "tool": tool_name,
                "error": error_text[:200],
                "ts": int(time.time()),
            })
            state["count"] = len(state["errors"])
            _save_state(session_id, state)
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
    except (BlockingIOError, OSError):
        # Lock nicht bekommen — kein Fehler-Tracking, aber auch kein Crash
        pass


def _is_trivial(error_text: str) -> bool:
    """Pruefen ob der Fehler trivial ist (kein Codex noetig)."""
    lower = error_text.lower()
    return any(pattern in lower for pattern in TRIVIAL_PATTERNS)


def _has_soft_error(text: str) -> bool:
    """Pruefen ob der Text Soft-Error-Patterns enthaelt."""
    return any(pattern in text for pattern in SOFT_ERROR_PATTERNS)


def _extract_response_text(tool_response) -> str:
    """Text aus tool_response extrahieren."""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        # Bash: stdout + stderr
        parts = []
        for key in ("stdout", "stderr", "output", "content", "text", "result"):
            val = tool_response.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val)
        return "\n".join(parts)
    return str(tool_response) if tool_response else ""


def _validate_cwd(cwd: str) -> str:
    """CWD validieren, Fallback auf /home/smlflg."""
    if cwd and os.path.isdir(cwd):
        return cwd
    return CWD_FALLBACK


def _call_codex(prompt: str, cwd: str) -> str:
    """Codex CLI aufrufen via stdin-Prompt und Antwort zurueckgeben."""
    if not _codex_available():
        return ""
    cwd = _validate_cwd(cwd)
    try:
        result = subprocess.run(
            [CODEX_CMD, "exec", "-s", "read-only", "--ephemeral",
             "--skip-git-repo-check", "-C", cwd, "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CODEX_TIMEOUT,
        )
        output = (result.stdout or "").strip()
        if not output:
            output = (result.stderr or "").strip()
        return output[:2000] if output else ""
    except subprocess.TimeoutExpired:
        return "[Codex Timeout nach 60s]"
    except FileNotFoundError:
        return "[Codex CLI nicht gefunden]"
    except Exception as e:
        return f"[Codex Fehler: {type(e).__name__}]"


def _output_context(hook_event: str, context: str) -> None:
    """additionalContext als hookSpecificOutput auf stdout ausgeben."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "additionalContext": context,
        }
    }
    print(json.dumps(output))


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        session_id = data.get("session_id", "")
        if not session_id:
            # Fallback: aus transcript_path extrahieren
            tp = data.get("transcript_path", "")
            if tp:
                session_id = os.path.basename(tp).replace(".jsonl", "")
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})
        cwd = data.get("cwd", os.getcwd())
        hook_event = data.get("hook_event_name", "PostToolUse")

        # --- Input-Zusammenfassung fuer Codex (max 500 Zeichen) ---
        input_summary = ""
        if isinstance(tool_input, dict):
            cmd = tool_input.get("command", "")
            desc = tool_input.get("description", "")
            file_path = tool_input.get("file_path", "")
            prompt = tool_input.get("prompt", "")
            if desc:
                input_summary = desc
            elif cmd:
                input_summary = f"Command: {cmd}"
            elif file_path:
                input_summary = f"File: {file_path}"
            elif prompt:
                input_summary = f"Prompt: {prompt}"
        input_summary = input_summary[:500]

        # ======================================
        # SCHICHT 1: HARTER FEHLER (PostToolUseFailure)
        # ======================================
        error = data.get("error", "")
        if error:
            # Trivial-Filter
            if _is_trivial(error):
                sys.exit(0)

            # Error loggen (nur mit session_id)
            if session_id:
                _log_error(session_id, tool_name, error)

            # Codex-Prompt
            codex_prompt = (
                f"Claude Code hat einen Fehler gemacht. Analysiere kurz (max 5 Saetze, Deutsch):\n\n"
                f"Tool: {tool_name}\n"
                f"Input: {input_summary}\n"
                f"Fehler: {error[:500]}\n\n"
                f"Beantworte:\n"
                f"1. Was ist schiefgelaufen?\n"
                f"2. Was sollte stattdessen gemacht werden?\n"
                f"3. Liegt ein grundsaetzliches Missverstaendnis vor?"
            )

            codex_response = _call_codex(codex_prompt, cwd)
            if codex_response:
                _output_context(hook_event, (
                    f"[CODEX ZWEITMEINUNG — Fehler bei {tool_name}]\n"
                    f"{codex_response}\n"
                    f"[Beruecksichtige diese Analyse bevor du weitermachst.]"
                ))

            sys.exit(0)

        # ======================================
        # SCHICHT 2: SOFT-ERROR CHECK (PostToolUse)
        # ======================================
        tool_response = data.get("tool_response")
        if not tool_response:
            sys.exit(0)

        # Nur Bash und Task pruefen
        if tool_name not in ("Bash", "Task"):
            sys.exit(0)

        response_text = _extract_response_text(tool_response)
        if not response_text:
            sys.exit(0)

        # Self-Detection-Filter: eigene Codex-Ausgaben ignorieren
        if "[CODEX ZWEITMEINUNG" in response_text or "[CODEX SESSION-REVIEW" in response_text:
            sys.exit(0)

        # Schneller String-Scan — sofort raus wenn nichts gefunden
        if not _has_soft_error(response_text):
            sys.exit(0)

        # Soft-Error gefunden — loggen
        # Finde welches Pattern gematcht hat fuer bessere Logs
        matched = [p for p in SOFT_ERROR_PATTERNS if p in response_text]
        if session_id:
            _log_error(session_id, tool_name, f"soft-error: {', '.join(matched[:3])}")

        # Codex aufrufen
        codex_prompt = (
            f"Claude Code hat ein Tool benutzt das zwar nicht crashed ist, "
            f"aber der Output enthaelt Fehler-Indikatoren. Analysiere kurz (max 5 Saetze, Deutsch):\n\n"
            f"Tool: {tool_name}\n"
            f"Input: {input_summary}\n"
            f"Output (gekuerzt):\n{response_text[:500]}\n\n"
            f"Erkannte Patterns: {', '.join(matched[:5])}\n\n"
            f"Beantworte:\n"
            f"1. Was ist schiefgelaufen?\n"
            f"2. Was sollte stattdessen gemacht werden?\n"
            f"3. Liegt ein grundsaetzliches Missverstaendnis vor?"
        )

        codex_response = _call_codex(codex_prompt, cwd)
        if codex_response:
            _output_context(hook_event, (
                f"[CODEX ZWEITMEINUNG — Soft-Error in {tool_name} Output]\n"
                f"{codex_response}\n"
                f"[Beruecksichtige diese Analyse bevor du weitermachst.]"
            ))

    except Exception:
        pass  # Iron Rule: never crash

    sys.exit(0)


if __name__ == "__main__":
    main()
