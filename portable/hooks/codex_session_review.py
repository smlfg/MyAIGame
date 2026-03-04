#!/usr/bin/env python3
"""Claude Code Stop Hook — Codex Session-Review bei Fehler-Haeufung.

Prueft beim Stop-Event ob die Session auffaellig viele Fehler hatte (>2).
Falls ja: ruft Codex fuer eine Gesamtanalyse auf und gibt Analyse auf stderr aus.
Nicht blockierend (exit 0), aber Claude sieht stderr als Kontext.

IRON RULE: Always exit 0. Never block the agent. Never crash.
"""

import json
import os
import subprocess
import sys

CODEX_TIMEOUT = 90
CODEX_CMD = "codex"
CWD_FALLBACK = "/home/smlflg"
ERROR_THRESHOLD = 2


def _get_state_file(session_id: str) -> str:
    """Pfad zum Error-Tracking State-File."""
    return f"/tmp/claude-codex-errors-{session_id}.json"


def _load_state(session_id: str) -> dict:
    """State-File laden."""
    path = _get_state_file(session_id)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"errors": [], "count": 0}


def _codex_available() -> bool:
    """Preflight: Codex CLI erreichbar?"""
    try:
        subprocess.run([CODEX_CMD, "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


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
        return output[:3000] if output else ""
    except subprocess.TimeoutExpired:
        return "[Codex Timeout nach 90s]"
    except FileNotFoundError:
        return "[Codex CLI nicht gefunden]"
    except Exception as e:
        return f"[Codex Fehler: {type(e).__name__}]"


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        # Prevent infinite loops: wenn Stop-Hook schon aktiv war, nicht nochmal
        if data.get("stop_hook_active"):
            sys.exit(0)

        # Session-ID: aus transcript_path oder direkt
        session_id = data.get("session_id", "")
        if not session_id:
            transcript_path = data.get("transcript_path", "")
            if transcript_path:
                session_id = os.path.basename(transcript_path).replace(".jsonl", "")

        if not session_id:
            sys.exit(0)

        cwd = data.get("cwd", os.getcwd())

        # State-File lesen
        state = _load_state(session_id)
        error_count = state.get("count", 0)

        # Unter Schwellwert → kein Review noetig
        if error_count <= ERROR_THRESHOLD:
            sys.exit(0)

        # --- Fehler-Zusammenfassung erstellen ---
        errors = state.get("errors", [])
        error_summaries = []
        for i, err in enumerate(errors[-10:], 1):  # Max letzte 10
            if isinstance(err, dict):
                tool = err.get("tool", "?")
                error = err.get("error", str(err))
                summary = f"[{tool}] {error}"
            else:
                summary = str(err)
            error_summaries.append(f"{i}. {summary}")
        error_list = "\n".join(error_summaries)

        # Codex-Gesamtanalyse
        codex_prompt = (
            f"Claude Code hatte in dieser Session {error_count} Fehler. "
            f"Analysiere das Gesamtbild (max 8 Saetze, Deutsch):\n\n"
            f"Fehler-Liste:\n{error_list}\n\n"
            f"Beantworte:\n"
            f"1. Gibt es ein wiederkehrendes Muster?\n"
            f"2. Was ist die Grundursache?\n"
            f"3. Welche Strategie-Aenderung wuerdest du empfehlen?\n"
            f"4. Sollte der aktuelle Ansatz komplett ueberdacht werden?"
        )

        codex_response = _call_codex(codex_prompt, cwd)

        # Nicht-blockierend: stderr ausgeben, Claude sieht es als Kontext
        reason = (
            f"[CODEX SESSION-REVIEW — {error_count} Fehler in dieser Session]\n\n"
            f"{codex_response}\n\n"
            f"Bitte Ansatz ueberdenken basierend auf den Empfehlungen."
        )

        print(reason, file=sys.stderr)
        sys.exit(0)  # Nicht blockierend, aber Claude sieht stderr als Kontext

    except Exception:
        pass  # Iron Rule Fallback: never crash, exit 0

    sys.exit(0)


if __name__ == "__main__":
    main()
