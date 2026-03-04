---
name: selfimprove
description: "Improve system instructions -- neue Regel, Anti-Pattern, oder Aenderung"
argument-hint: "[kurze Beschreibung der gewuenschten Regel/Aenderung]"
---

# /selfimprove -- System Instructions verbessern

Verbesserungsauftrag: **$ARGUMENTS**

## Prozess

1. **Ziel-Datei bestimmen** -- Wo passt die Aenderung hin?
   - `AGENTS.md` (OpenCode equivalent of CLAUDE.md) -> Kern-Regeln, Architektur, Prinzipien
   - Companion files if they exist -> Arbeitsweise, Fehler, Skill-Referenz
   - Tell user which file and why, then edit.

2. **Datei lesen** -- Ziel-Datei vollstaendig lesen

3. **Edit durchfuehren** -- Edit directly

4. **Verifizieren** -- `grep -n` auf das neue Schluesselwort

## Entscheidungsbaum

- Neue Verhaltensregel -> AGENTS.md (Anti-Patterns, Rules, etc.)
- Neuer Skill erstellt -> Skill-Referenz updaten
- Arbeitsweise/ADHS -> Companion file
- Neuer Fehler/Anti-Pattern -> Error patterns file
- Allgemeines Prinzip -> AGENTS.md (Core Principles)

## Rules

- Schreibe Regeln im bestehenden Stil (Deutsch/Englisch gemischt wie im Rest der Datei)
- KEIN neues File, kein Backup noetig -- direktes Edit
- Report: eine Zeile was geaendert wurde + grep-Output als Beweis
