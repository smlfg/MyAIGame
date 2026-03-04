---
name: auto
description: "Smart auto-delegation -- picks the best method automatically"
argument-hint: "[task description]"
category: delegation
cost-tier: variable
dependencies:
  tools: [delegate_code, delegate_code_run, research, shell]
  scripts: ["gather-context-enhanced.sh"]
tags: [routing, smart, auto-select]
---

# /auto -- Smart Auto-Delegation

Analysiere den Task und waehle automatisch die optimale Methode. NIE beim User fragen.

**Task:** $ARGUMENTS

## Routing-Logik (in Reihenfolge pruefen)

1. Task ist eine Frage ("?" am Ende, "was ist", "wie funktioniert", "explain", "what is") -> direkt antworten, KEIN Delegate
2. Task enthaelt "test", "coverage", "pytest" -> /test Pattern: delegate with test-focused prompt
3. Task enthaelt "research", "suche", "best practice", "what's the best", "compare" -> /research Pattern: {{research(query)}}
4. Task enthaelt "refactor", "multi-file", "rename everywhere", "3+ files" -> /crew Pattern
5. Task ist kleiner Fix (1-2 Dateien, klar umgrenzt, kein Context noetig) -> /chef-lite Pattern: {{delegate_code(prompt, dir)}}
6. Alles andere -> /chef Pattern: gather-context + {{delegate_code_run(prompt, dir, timeout=300)}}

## Ausfuehrung

Fuehre die gewaehlte Methode sofort aus -- kein weiteres Nachfragen.

Fuer chef Pattern:
1. {{gather_context(dir=project_dir, task="$ARGUMENTS")}}
2. {{delegate_code_run(prompt=CONTEXT + task, dir=project_dir, timeout=300)}}

Fuer chef-lite Pattern:
1. {{delegate_code(prompt="$ARGUMENTS", dir=project_dir)}}

## Report

1 Satz nach Abschluss: "Nutzte [methode] -- [was gemacht, welche Datei]"
