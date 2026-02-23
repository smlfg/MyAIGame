---
argument-hint: "kurze Beschreibung der gewünschten Regel/Änderung"
description: CLAUDE.md + Companion Files verbessern — neue Regel, Anti-Pattern, oder Abschnittsaenderung
---

Verbesserungsauftrag: **$ARGUMENTS**

## Prozess

1. **Ziel-Datei bestimmen** — Wo passt die Aenderung hin?
   - `~/.claude/CLAUDE.md` → Kern-Regeln, Architektur, Prinzipien
   - `~/.claude/WieArbeitestDuMitSamuel.md` → Arbeitsweise, ADHS, Kommunikation
   - `~/.claude/WelcheFehlerVermeiden.md` → Fehler, Anti-Patterns, Bug Fix Chain
   - `~/.claude/Skilluebersicht.md` → Skill-Tabellen, Kosten, Wann-welchen-Skill
   → Samuel kurz sagen welches File und warum, dann erst editieren.
2. **Datei lesen** — Ziel-Datei vollstaendig lesen
3. **Edit durchfuehren** — Edit-Tool direkt auf die Ziel-Datei
4. **Verifizieren** — `grep -n` auf das neue Schluesselwort

## Entscheidungsbaum

- Neue Verhaltensregel → CLAUDE.md (Anti-Patterns, Delegation Rules, etc.)
- Neuer Skill erstellt → Skilluebersicht.md (Tabelle + Kosten-Ranking updaten)
- Samuels Arbeitsweise/ADHS → WieArbeitestDuMitSamuel.md
- Neuer Fehler/Anti-Pattern → WelcheFehlerVermeiden.md
- Provider/Config-Info → WieArbeitestDuMitSamuel.md (Provider Config)
- Allgemeines Prinzip → CLAUDE.md (Core Principles)

## Rules

- Schreibe Regeln im bestehenden Stil (Deutsch/Englisch gemischt wie im Rest der Datei)
- KEIN neues File, kein Backup nötig — direktes Edit
- Report: eine Zeile was geändert wurde + grep-Output als Beweis
