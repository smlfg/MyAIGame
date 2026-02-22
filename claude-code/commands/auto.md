---
argument-hint: [task description]
description: Smart auto-delegation — picks the best method automatically
---

# /auto — Smart Auto-Delegation

Analysiere den Task und wähle automatisch die optimale Methode. NIE beim User fragen.

**Task:** $ARGUMENTS

## Routing-Logik (in Reihenfolge prüfen)

1. Task ist eine Frage ("?" am Ende, "was ist", "wie funktioniert", "explain", "what is") → direkt antworten, KEIN Delegate
2. Task enthält "test", "coverage", "pytest" → /test Pattern: `mcp__opencode__opencode_run` mit test-fokussiertem Prompt
3. Task enthält "research", "suche", "best practice", "what's the best", "compare" → /research Pattern: `mcp__gemini__ask-gemini`
4. Task enthält "refactor", "multi-file", "rename everywhere", "umbenennen überall", "3+ files" → /crew Pattern: Skill `crew`
5. Task ist kleiner Fix (1-2 Dateien, klar umgrenzt, kein Context nötig) → /chef-lite Pattern: `mcp__opencode__opencode_ask` direkt
6. Alles andere → /chef Pattern: `gather-context-enhanced.sh` + `mcp__opencode__opencode_run`

## Ausführung

Führe die gewählte Methode sofort aus — kein weiteres Nachfragen.

Für chef Pattern:
1. Run `bash ~/.claude/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS"` → CONTEXT
2. Call `mcp__opencode__opencode_run` mit CONTEXT + Task, `directory`: pwd, `maxDurationSeconds`: 300

Für chef-lite Pattern:
1. Call `mcp__opencode__opencode_ask` mit Task direkt, `directory`: pwd

## Report

1 Satz nach Abschluss: "Nutzte [methode] — [was gemacht, welche Datei]"
