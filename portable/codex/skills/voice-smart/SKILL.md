---
name: voice-smart
description: "Smart Voice Mode -- voice conversation with live project context and file lookup"
argument-hint: "<project-path-or-topic>"
category: voice
cost-tier: variable
dependencies:
  tools: [voice, file_read, search_files, shell]
  scripts: ["gather-context.sh"]
tags: [voice, interactive, context-aware]
---

# /voice-smart -- Voice + Projekt-Context

Voice-Conversation mit Samuel. Du kannst im Projekt nachschauen -- das macht dich smart.

## Phase 1: Cold Start (EINMALIG)

{{gather_context(dir=project_dir, task="$ARGUMENTS")}}

Lies ausserdem:
- FOR_SMLFLG.md oder README.md im Projektroot
- Hauptconfig (falls vorhanden)

Das ist dein **Basiswissen**.

## Phase 2: Voice Loop

Start voice conversation and loop:
- wait_for_response: true
- listen_duration_min: 8
- Stopp bei: "stop", "Ende", "Tschuess", "danke reicht"

## Phase 3: Trigger-basierter Context Lookup

Nach JEDEM Voice-Ergebnis, checke auf Trigger:

| Trigger | Aktion |
|---------|--------|
| Dateiname genannt | {{read_file(filename)}} |
| Funktionsname | {{search_files(function_name, ".")}} |
| Fehlermeldung | {{search_files(error_string, ".")}} |
| Neues Thema | {{search_files(keyword, ".")}} |
| "Zeig mir" | Deep Dive (Phase 4) |
| Kein Trigger | Sofort aus Basiswissen antworten |

## Voice-Dialog-Policy

- **Turn-Taking**: Kernpunkt + naechster Schritt, 5-12 Sekunden pro Chunk
- **Kanaltrennung**: NIE Commands/Code/URLs vorlesen -- im Terminal anzeigen
- **Stille Arbeit**: Immer ankuendigen bevor Dateien gelesen werden
- **Fehler**: Conversation NIE abbrechen. Kurz sagen was passiert, Fallback nutzen

## Codex Limitation
**Voice mode is NOT supported in Codex CLI.** Codex is a terminal-based tool without voice I/O capabilities. This skill cannot be ported to Codex. Users should use Claude Code or a voice-enabled interface instead.
