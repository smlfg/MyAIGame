---
argument-hint: [meinung|code|review] [frage/aufgabe/scope]
description: Codex als Sparringspartner — Zweitmeinung, Code-Delegation oder Review
---

You are in **Sparring Mode** with Codex. Input: **$ARGUMENTS**

## Routing

Parse `$ARGUMENTS`:

- Starts with `meinung ` → **meinung**, payload = rest
- Starts with `code ` → **code**, payload = rest
- Starts with `review` → **review**, payload = rest (may be empty)
- Empty → Tell user: "Bitte Frage oder Aufgabe angeben." Show examples. STOP.
- No keyword match → **meinung** (default), payload = full `$ARGUMENTS`

## Preflight (all modes)

Run via Bash: `codex --version 2>&1`
If fails → "Codex CLI nicht gefunden." STOP.

---

## Mode: meinung

**Zweck:** Unabhaengige Zweitmeinung. Codex analysiert, Claude kommentiert. Zwei Stimmen.

1. **Duenner Context** (fuer Unabhaengigkeit):
   ```bash
   bash ~/.claude/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS" 2>/dev/null | head -60
   ```
   Capture as THIN_CONTEXT.

2. **Codex aufrufen** via Bash (timeout 120s). Prompt via stdin mit Heredoc:
   ```bash
   cat <<'PROMPT_END' | timeout 120 codex exec -s read-only -C "$(pwd)" -
   Du bist ein unabhaengiger technischer Berater. NICHT implementieren, nur ANALYSIEREN.

   PROJEKT-KONTEXT:
   {THIN_CONTEXT}

   FRAGE:
   {payload}

   Liefere:
   1. ANALYSE: Kernproblem (2-3 Saetze)
   2. DEIN ANSATZ: Konkreter Vorschlag
   3. SCHWACHSTELLEN: Min. 3 Risiken deines eigenen Vorschlags
   4. ALTERNATIVEN: Min. 2 andere Wege
   5. EMPFEHLUNG: 1 klarer Satz
   6. CONFIDENCE: hoch/mittel/niedrig + Begruendung

   Deutsch. Direkt, kein Geschwafel.
   PROMPT_END
   ```
   **Wichtig:** KEIN `--json` — ohne Flag gibt Codex die finale Antwort direkt auf stdout.
   stderr wird verworfen (Progress-Output).

3. **Output praesentieren:**

   ```
   ## Zweite Meinung von Codex

   **Frage:** {payload}

   {Codex stdout, formatiert}

   ---

   **Claudes Einordnung:** {2-3 Saetze: Zustimmung, Widerspruch, Ergaenzung. Ehrlich — wenn Codex Recht hat, sag es.}
   ```

---

## Mode: code

**Zweck:** Codex implementiert, Claude reviewed.

1. **Voller Context:**
   ```bash
   bash ~/.claude/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS" 2>/dev/null
   ```
   Capture as FULL_CONTEXT.

2. **Codex aufrufen** via Bash (timeout 300s):
   ```bash
   cat <<'PROMPT_END' | timeout 300 codex exec --full-auto -C "$(pwd)" -
   {FULL_CONTEXT}

   AUFGABE:
   {payload}

   REGELN:
   - Bestehende Code-Patterns folgen
   - Ein Task, ein Change
   - Tests wo sinnvoll
   - Keine unnoetige Komplexitaet
   PROMPT_END
   ```
   `--full-auto` = sandbox workspace-write + auto-approve (sicher, nicht yolo).

3. **Nach Abschluss** `git diff --stat` ausfuehren.

4. **Output praesentieren:**

   ```
   ## Codex Code-Ergebnis

   **Auftrag:** {payload}

   **Was Codex gemacht hat:** {2-3 Saetze aus stdout}

   **Geaenderte Dateien:**
   {git diff --stat}

   **Claudes Quick-Check:** {Auffaelligkeiten, fehlende Tests, Style-Issues — oder "Sieht gut aus."}
   ```

---

## Mode: review

**Zweck:** Codex reviewed Code, Claude ergaenzt wenn noetig.

1. **Git-Check** via Bash: `git rev-parse --is-inside-work-tree 2>&1`
   Wenn fehlschlaegt → "Kein Git-Repo. Fuer allgemeine Fragen: `/codex meinung ...`" STOP.

2. **Scope bestimmen** aus payload:
   - Leer oder `uncommitted` → `--uncommitted`
   - `vs main` / `vs master` / `base <branch>` → `--base <branch>`
   - `commit <sha>` → `--commit <sha>`
   - Sonstiges → `--uncommitted` (Default, Scope erwaehnen)

3. **Codex aufrufen** via Bash (timeout 180s):
   ```bash
   timeout 180 codex review {flags} -C "$(pwd)"
   ```
   Optional custom prompt als Argument falls payload mehr als nur den Scope enthaelt.

4. **Output praesentieren:**

   ```
   ## Codex Code Review

   **Scope:** {uncommitted / vs. main / commit abc123}

   {Codex stdout, formatiert}

   ---

   **Claudes Ergaenzung:** {Nur wenn sinnvoll. Wenn Codex alles abdeckt: "Codex hat das gut abgedeckt."}
   ```

---

## Error Handling (alle Modi)

| Situation | Reaktion |
|-----------|----------|
| `codex --version` fehlschlaegt | "Codex CLI nicht gefunden." STOP. |
| timeout (Exit 124) | "Codex Timeout nach Xs." Partial stdout zeigen falls vorhanden. |
| Exit-Code != 0 | stderr zeigen, wahrscheinliche Ursache erklaeren. |
| Leerer stdout | "Codex hat nichts zurueckgegeben." API-Key, Rate-Limit, Netzwerk als Ursachen nennen. |
| Kein Git-Repo (review) | `/codex meinung` vorschlagen. STOP. |

## Kern-Regeln

- **KEIN Fallback.** Wenn Codex versagt, NICHT selbst machen. Der Sinn ist die zweite Perspektive. Fehler melden und STOP.
- **KEIN `--json`.** Ohne Flag → stdout = finale Antwort. Einfacher, zuverlaessiger.
- **Heredoc fuer Prompts.** `cat <<'PROMPT_END' | codex exec ... -` vermeidet Shell-Quoting-Probleme.
- **Immer `-C "$(pwd)"`** damit Codex im richtigen Verzeichnis arbeitet.
- **Meinung = duenner Context** (head -60) fuer Unabhaengigkeit.
- **Code = voller Context** damit Codex tatsaechlich implementieren kann.
- **Zwei Stimmen** immer: Codex-Output + Claudes Einordnung.
