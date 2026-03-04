---
name: voice-smart
description: "Smart Voice Mode -- voice conversation with live project context and file lookup"
argument-hint: "<project-path-or-topic>"
category: voice
cost-tier: variable
dependencies:
  tools: [voice, file_read, file_search, shell]
tags: [voice, context-aware, interactive]
---

# /voice-smart -- Voice + Projekt-Context

Voice-Conversation mit Samuel. Du kannst im Projekt nachschauen -- das macht dich smart.

**NOTE:** Voice mode requires platform-specific voice I/O support. This skill may not be available in all OpenCode environments.

## Phase 1: Cold Start (EINMALIG)

```bash
bash ~/.opencode/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS"
```

Lies ausserdem:
- `FOR_SMLFLG.md` oder `README.md` im Projektroot
- Hauptconfig (falls vorhanden)

Das ist dein **Basiswissen**.

## Phase 2: Voice Loop

Starte Voice-Interaktion und laufe im Loop:
- `listen_duration_min: 8`
- `vad_aggressiveness: 1`

Stopp bei: "stop", "Ende", "Tschuess", "danke reicht".

## Phase 3: Trigger-basierter Context Lookup

Nach JEDEM Voice-Input, checke auf **Trigger**:

| Trigger | Beispiel | Aktion |
|---------|----------|--------|
| Dateiname genannt | "scheduler.py" | Read diese Datei |
| Funktionsname | "deal_scoring" | Grep nach Definition |
| Fehlermeldung | "Error", "traceback" | Grep nach Error-String |
| Neues Thema | Wechsel von Kafka zu Elasticsearch | Grep nach neuem Keyword |
| "Zeig mir" / "Was steht in" | Explizite Anfrage | Deep Dive |

### Kein Trigger -> Sofort antworten

Bei "ja", "okay", "weiter", Erklaerungen:
Antworte direkt aus Basiswissen. Kein Lookup noetig.

### Lookup-Ablauf

**Schnell (< 2s):**
1. Grep oder Read -- EINE Datei, EINE Suche
2. Antworte MIT dem Ergebnis

**Langsam (>2s):**
1. Sag: "Moment, ich schau nach."
2. Lies/Suche was noetig ist
3. Antworte mit Ergebnis

## Voice-Dialog-Policy

### Sprechen
- **Turn-Taking**: Kernpunkt + naechster Schritt. Laengere Erklaerungen in Chunks.
- **Sprache**: Was der User nutzt (DE oder EN).

### Kanaltrennung
- **NIE vorlesen**: Commands, Pfade, URLs, Code, Stacktraces. Im Terminal anzeigen.
- Sag nur: "Steht im Terminal" oder "Ich hab dir den Befehl hingeschrieben."

### Stille Arbeit
- **Immer ankuendigen** bevor du Dateien liest
- NIE laenger als 30 Sekunden still ohne Signal

### Wiederholung
- **Max 2 Erklaerversuche** mit gleichem Ansatz. Dann Form wechseln.

### Fehler
- **API/Tool-Fehler**: Conversation NICHT abbrechen. Kurz sagen was passiert, weitermachen.
- **STT-Muell**: Ignorieren, kurz nachfragen.

### Allgemein
- **Nie blockieren**: Antwort VOR perfektem Context.
- **Nicht raten bei Code**: Unsicher? Lies nach.
- **Kein Lookup-Spam**: Gleiche Keywords wie letzte Runde? Du hast es schon.
