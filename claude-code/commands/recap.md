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

### 1. Session analysieren
Schau dir die aktuelle Konversation an und identifiziere:
- **Ziel der Session:** Was wollten wir erreichen?
- **Was wurde gemacht:** Konkrete Aenderungen, erstellte Files, geloeste Probleme
- **Offene Fragen:** Was ist noch unklar oder unentschieden?
- **Blocker:** Was hat uns aufgehalten?
- **Entscheidungen:** Welche Entscheidungen wurden getroffen und warum?
- **Next Steps:** Was sollte als naechstes passieren?

### 2. SESSION_LOG.md schreiben
Finde oder erstelle die Datei `SESSION_LOG.md` im aktuellen Projektverzeichnis.

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
- Wenn kein Projektverzeichnis erkennbar: in CWD schreiben
