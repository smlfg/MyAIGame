---
argument-hint: <project-path-or-topic>
description: Smart Voice Mode — voice conversation with live project context and file lookup
---

# Smart Voice Mode — Voice + Projekt-Context

Voice-Conversation mit Samuel. Du kannst im Projekt nachschauen — das macht dich smart.

## Phase 1: Cold Start (EINMALIG, vor erstem converse)

```bash
bash ~/.claude/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS"
```

Lies ausserdem:
- `FOR_SMLFLG.md` oder `README.md` im Projektroot
- Hauptconfig (falls vorhanden: `docker-compose*`, `*.yaml`, `*.toml`)

Das ist dein **Basiswissen**. Reicht fuer die meisten Fragen.

## Phase 2: Voice Loop

Starte converse und laufe im Loop:
- `wait_for_response: true`
- `metrics_level: "minimal"`
- `listen_duration_min: 8`
- `vad_aggressiveness: 1`

Nach jeder Runde: IMMER wieder converse mit wait_for_response=true.
Stopp bei: "stop", "Ende", "Tschuess", "danke reicht".

## Phase 3: Trigger-basierter Context Lookup

Nach JEDEM converse-Ergebnis, checke Samuels Aussage auf **Trigger**:

### Trigger erkannt → Lookup starten

| Trigger | Beispiel | Aktion |
|---------|----------|--------|
| Dateiname genannt | "scheduler.py", "docker-compose" | `Read` diese Datei |
| Funktionsname | "deal_scoring", "fetch_prices" | `Grep` nach Definition |
| Fehlermeldung | "Error", "traceback", "failed" | `Grep` nach Error-String |
| Neues Thema | Wechsel von Kafka zu Elasticsearch | `Grep` nach neuem Keyword |
| "Zeig mir" / "Was steht in" | Explizite Anfrage | Deep Dive (Phase 4) |

### Kein Trigger → Sofort antworten

Bei "ja", "okay", "weiter", Erklaerungen, Meinungsfragen:
Antworte direkt aus deinem Basiswissen. Kein Lookup noetig.

### Lookup-Ablauf (wenn Trigger)

**Schnell (< 2s, kein Voice-Delay):**
1. `Grep` oder `Read` direkt — EINE Datei, EINE Suche
2. Antworte per converse MIT dem Ergebnis (wait_for_response=true)

**Langsam (braucht mehr als 2s):**
1. Sag per converse (wait_for_response=false): "Moment, ich schau nach."
2. Lies/Suche was noetig ist
3. Antworte per converse mit Ergebnis (wait_for_response=true)

**Background (optional, nur bei komplexen Fragen):**
1. Starte `Task(run_in_background=true, model="haiku")` fuer tiefere Suche
2. Antworte SOFORT per converse mit dem was du weisst
3. Naechste Runde: Wenn Task-Ergebnis da → einbauen. Wenn nicht → ignorieren.

## Phase 4: Deep Dive (nur auf explizite Anfrage)

Wenn Samuel sagt "zeig mir den Code", "lies die Datei", "was steht in X":
1. converse(wait_for_response=false): "Moment, ich schau nach."
2. Read die Datei ausfuehrlich
3. converse mit Zusammenfassung (wait_for_response=true)

## Regeln

- **KURZ**: Max 3 Saetze pro converse. ADHS-freundlich.
- **Sprache**: Was Samuel nutzt, nutzt du auch (DE oder EN).
- **Nie blockieren**: Antwort VOR perfektem Context. Schnell > perfekt.
- **Nicht raten bei Code**: Unsicher? Lies nach. Das ist dein Vorteil.
- **Max 1 Background-Task**: Nie mehrere parallel. Neuer ersetzt alten.
- **Kein Lookup-Spam**: Gleiche Keywords wie letzte Runde? Du hast es schon.
