---
name: selfimprove
description: "System instructions verbessern -- neue Regel, Anti-Pattern, oder Abschnittsaenderung"
argument-hint: "kurze Beschreibung der gewuenschten Regel/Aenderung"
category: meta
cost-tier: free
dependencies:
  tools: [file_read, edit_file, shell]
tags: [meta, self-improvement, config]
---

# /selfimprove -- System Instructions verbessern

Verbesserungsauftrag: **$ARGUMENTS**

## Prozess

1. **Ziel-Datei bestimmen** -- Wo passt die Aenderung hin?
   - System instructions / agent config -> main config file
   - Arbeitsweise, ADHS, Kommunikation -> companion files
   - Fehler, Anti-Patterns -> error prevention docs
   - Skill-Tabellen, Kosten -> skill reference docs
   -> Samuel kurz sagen welches File und warum, dann erst editieren.

2. **Datei lesen** -- Ziel-Datei vollstaendig lesen via {{read_file(target_file)}}

3. **Edit durchfuehren** -- {{edit_file(target_file, old_text, new_text)}}

4. **Verifizieren** -- {{search_files("new_keyword", target_file)}} auf das neue Schluesselwort

## Rules

- Schreibe Regeln im bestehenden Stil der Datei
- KEIN neues File, kein Backup noetig -- direktes Edit
- Report: eine Zeile was geaendert wurde + Beweis
