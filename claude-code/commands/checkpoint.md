---
argument-hint: [optional: Beschreibung was gerade fertig ist]
description: Git-Snapshot + Session-Summary + sichtbarer Fortschritt
---

# /checkpoint — Fortschritt sichern und sichtbar machen

Checkpoint = Git Commit + kurze Summary + Dopamin-Hit.
Fuer ADHS-Workflow: Sichtbare Fortschritte sind Treibstoff.

**Was ist passiert:** $ARGUMENTS

---

## Was du tust:

### 1. Status pruefen
- `git status` — was hat sich geaendert?
- `git diff --stat` — wie viele Dateien, wie viele Zeilen?
- Wenn NICHTS geaendert: sag das ehrlich und schlage vor was als naechstes kommt

### 2. Git Commit erstellen
- Stage die relevanten Dateien (NICHT alles blind — `git add` nur was zusammengehoert)
- Commit-Message schreiben:
  - Kurz (1 Zeile, max 72 Zeichen)
  - Im Imperativ ("Add feature" nicht "Added feature")
  - ERKLAERE Samuel was die Message bedeutet
- **WICHTIG:** Samuel FRAGEN bevor du commitst: "Ich wuerde committen: '[message]'. Passt das?"

### 3. Fortschritt feiern
Nach erfolgreichem Commit:
```
Checkpoint gesetzt!
"[Commit-Message]"
[X] Dateien, [+Y/-Z] Zeilen
[Motivierender Kommentar basierend auf was erreicht wurde]
```

### 4. Optional: SESSION_LOG.md updaten
Wenn eine SESSION_LOG.md existiert, fuege einen kurzen Eintrag hinzu:
```
- [HH:MM] Checkpoint: [Commit-Message]
```

---

## Regeln

- IMMER Samuel fragen bevor committed wird (Regel Null: Verstehen > Ausfuehren)
- Keine sensitiven Dateien committen (.env, credentials, API keys)
- Kleine, atomare Commits — lieber 3 kleine als 1 grosser
- Motivierend aber ehrlich — nicht "Mega Sprint!" wenn nur 1 Typo gefixt wurde
- Wenn `git init` noetig: Samuel fragen, nicht einfach machen
