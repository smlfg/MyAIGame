---
argument-hint: [optional: Projektpfad oder Kontext]
description: Session zusammenfassen — Was wurde gemacht, offene Fragen, Next Steps → SESSION_LOG.md
---

# /recap — Session-Zusammenfassung

Du fasst die aktuelle Session zusammen und schreibst das Ergebnis in eine Log-Datei.
Das ist die Kontext-Bruecke zwischen Sessions -- besonders wichtig fuer ADHS-Workflow.

**Kontext:** $ARGUMENTS

---

## Was du tust:

### 0. Falls Argument "list" oder "ls" → Logs auflisten
Wenn `$ARGUMENTS` "list", "ls", "show" oder "uebersicht" enthaelt:
- Liste alle Dateien in `~/.claude/session-logs/` auf
- Zeige pro Datei: Projektname, Anzahl Sessions (zaehle `## Session` Eintraege), letztes Datum
- Zeige KEINE Inhalte, nur die Uebersicht
- Fertig — keine neue Session loggen!

### 1. Session analysieren
Schau dir die aktuelle Konversation an und identifiziere:
- **Ziel der Session:** Was wollten wir erreichen?
- **Was wurde gemacht:** Konkrete Aenderungen, erstellte Files, geloeste Probleme
- **Offene Fragen:** Was ist noch unklar oder unentschieden?
- **Blocker:** Was hat uns aufgehalten?
- **Entscheidungen:** Welche Entscheidungen wurden getroffen und warum?
- **Next Steps:** Was sollte als naechstes passieren?

### 2. SESSION_LOG.md schreiben
**IMMER** in den zentralen Ordner `~/.claude/session-logs/` schreiben!
Dateiname: `SESSION_LOG_<projektname>.md` (Projektname aus Ordnername des CWD ableiten).
Beispiel: CWD ist `/home/smlflg/DataEngeeneeringKEEPA/` → `~/.claude/session-logs/SESSION_LOG_DataEngeeneeringKEEPA.md`
Falls CWD das Home-Verzeichnis ist → `~/.claude/session-logs/SESSION_LOG_general.md`

Format (append am Ende der Datei):

```markdown
---

## Session [DATUM] — [1-Satz Zusammenfassung]

**Ziel:** [Was wollten wir?]

**Erledigt:**
- [x] Konkrete Sache 1
- [x] Konkrete Sache 2

**Offene Punkte:**
- [ ] Was noch fehlt
- [ ] Ungeloeste Frage

**Entscheidungen:**
- [Entscheidung]: weil [Begruendung]

**Blocker:**
- [Falls vorhanden]

**Next Steps:**
1. [Naechster konkreter Schritt]
2. [Danach]

**Stimmung:** [Emoji: produktiv / okay / frustrierend]
```

### 3. Kurzes Feedback
Sage Samuel:
- "Session geloggt in SESSION_LOG.md"
- 1-Satz Summary was erreicht wurde
- Feier was gut lief ("Starke Session!" / "Guter Fortschritt!")

---

## Regeln

- IMMER append, nie ueberschreiben
- Datum im ISO-Format (YYYY-MM-DD)
- Ehrlich sein -- wenn wenig passiert ist, schreib das. Kein Schoenreden.
- Kurz halten -- max 15 Zeilen pro Session-Eintrag
- NIEMALS in CWD schreiben! Immer `~/.claude/session-logs/`
- Ein Log-File pro Projekt, alle an einem Ort
