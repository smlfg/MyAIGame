---
name: batch
description: "Batch multiple tasks into ONE execution call -- ~80% token savings"
argument-hint: "[task 1] | [task 2] | [task 3] ..."
category: delegation
cost-tier: low
dependencies:
  tools: [delegate_code_run, shell]
  scripts: ["gather-context-enhanced.sh"]
tags: [batch, efficiency, multi-task]
---

# /batch -- Multi-Task Batching

Fasst mehrere Tasks in EINEN Execution-Call zusammen. ~80% Token-Ersparnis vs. einzelne Calls.

**Tasks:** $ARGUMENTS

## Schritte

1. **Parse Tasks** aus `$ARGUMENTS`:
   - Trennzeichen: `|` oder nummerierte Liste (1. 2. 3.) oder Bullet-Liste (- item)
   - Max 10 Tasks pro Batch

2. **Context einmal holen** (nicht pro Task!):
   {{gather_context(dir=project_dir, task="$ARGUMENTS")}}
   Capture as CONTEXT.

3. **Kombinierten Prompt bauen:**
   ```
   PROJECT CONTEXT:
   <CONTEXT output>

   TASKS (alle in einem Pass erledigen):
   1. <task 1>
   2. <task 2>
   N. <task N>

   Erledige alle Tasks sequentiell in einem einzigen Durchgang.
   Report pro Task: was gemacht, welche Dateien geaendert.
   Bei Abhaengigkeiten (Task B braucht Ergebnis von A): erst A, dann B.
   ```

4. **Einen einzigen Execution-Call:**
   {{delegate_code_run(prompt=combined_prompt, dir=project_dir, timeout=600)}}

5. **Report:**
   - Welche Tasks erledigt
   - Welche Dateien geaendert
   - Blocker oder offene Punkte

## Regeln

- Unabhaengige Tasks -> ein kombinierter Prompt
- Abhaengige Tasks (B braucht A) -> trotzdem gebatcht, sequentielle Ausfuehrung im Prompt beschreiben
- Context wird EINMAL geholt, nicht pro Task
- Max 10 Tasks pro Batch -- bei mehr aufteilen
