---
argument-hint: [task 1] | [task 2] | [task 3] ...
description: Batch multiple tasks into ONE opencode_run call — ~80% token savings
---

# /batch — Multi-Task Batching

Fasst mehrere Tasks in EINEN `opencode_run` Call zusammen. ~80% Token-Ersparnis vs. einzelne Calls.

**Tasks:** $ARGUMENTS

## Schritte

1. **Parse Tasks** aus `$ARGUMENTS`:
   - Trennzeichen: `|` oder nummerierte Liste (1. 2. 3.) oder Bullet-Liste (- item)
   - Max 10 Tasks pro Batch

2. **Context einmal holen** (nicht pro Task!):
   Run `bash ~/.claude/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS"` → CONTEXT

3. **Kombinierten Prompt bauen:**
   ```
   PROJECT CONTEXT:
   <CONTEXT output>

   TASKS (alle in einem Pass erledigen):
   1. <task 1>
   2. <task 2>
   N. <task N>

   Erledige alle Tasks sequentiell in einem einzigen Durchgang.
   Report pro Task: was gemacht, welche Dateien geändert.
   Bei Abhängigkeiten (Task B braucht Ergebnis von A): erst A, dann B.
   ```

4. **Einen einzigen `mcp__opencode__opencode_run` Call:**
   - `prompt`: kombinierter Prompt aus Schritt 3
   - `directory`: pwd
   - `providerID`: "anthropic"
   - `modelID`: "claude-sonnet-4-5"
   - `maxDurationSeconds`: 600

5. **Report:**
   - Welche Tasks erledigt
   - Welche Dateien geändert
   - Blocker oder offene Punkte

## Regeln

- Unabhängige Tasks → ein kombinierter Prompt
- Abhängige Tasks (B braucht A) → trotzdem gebatcht, sequentielle Ausführung im Prompt beschreiben
- Context wird EINMAL geholt, nicht pro Task
- Immer `providerID` + `modelID` angeben
- Max 10 Tasks pro Batch — bei mehr aufteilen

## Beispiel-Aufruf

```
/batch fix the login bug | add unit test for auth module | update README with new env vars
```
