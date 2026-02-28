# Session Browser — FOR_SMLFLG

> Dein persoenlicher Archaeologe fuer 834 Claude Code Sessions.

## Was ist das?

Ein Streamlit-Dashboard zum Durchstoebern aller Claude Code Sessions. Stell dir vor, du hast 834 Gespraeche mit einem AI-Assistenten gefuehrt — verteilt ueber 20 Projekte, manche 3 Zeilen, manche 500 Messages. Dieses Tool macht sie durchsuchbar, filterbar und previewbar.

**Anstatt:** `grep -r "keepa" ~/.claude/projects/` und dann JSONL von Hand lesen
**Jetzt:** Browser auf, filtern, klicken, lesen, resume-Command kopieren.

## Tech Stack

- **Python + Streamlit** — bekanntes Pattern aus dem MAS Dashboard
- **Pandas** — Tabellen-Handling
- **Kein Backend, keine DB** — liest direkt die JSONL-Files

## Architektur

```
SessionBrowser/
├── app.py              # Streamlit Entry Point — alles UI
├── session_parser.py   # JSONL Parser, Search Engine, Cost Calculator
├── requirements.txt    # streamlit, pandas
├── run.sh              # Starter mit venv-Management
└── FOR_SMLFLG.md       # Du liest gerade dieses File
```

Bewusst 2 Python-Dateien. Parser-Logik getrennt von UI = testbar, wiederverwendbar.

## Wie starten?

```bash
cd ~/ClaudesReich/SessionBrowser
./run.sh
# Oeffnet http://localhost:8501
```

Oder direkt: `streamlit run app.py`

Tipp: `alias claude-browser='~/ClaudesReich/SessionBrowser/run.sh'`

## Features

1. **Session-Tabelle** — Slug, Projekt, Datum, Message Count, Groesse. Sortierbar.
2. **Filter** — Projekt (Multi-Select), Zeitraum (Heute/7d/30d/Alle), Min Messages
3. **Suche** — In Slugs, Projektnamen, erster User-Message
4. **Conversation Preview** — Klick auf Session, sieht Messages mit farbigen Bubbles
5. **Resume-Command** — Copy-paste `cd ... && claude --resume ...`
6. **Kosten-Dashboard** — Input/Output Tokens, Cache, geschaetzte $ pro Session
7. **Volltextsuche** — grep-basiert in einzelnen Sessions

## Datenfluss

```
Startup → Glob alle .jsonl → Quick-Parse (nur erste 30 + letzte 10 Zeilen) → Tabelle
Klick   → Full-Parse der Session → Conversation View mit Token-Daten
Suche   → grep -l fuer Speed → Python fuer Details
```

**Quick-Parse** liest ~40 Zeilen pro File statt alles. Bei 310 Files: ~1-2s statt 30s.

## Kosten-Berechnung

Basiert auf `message.usage` in den JSONL-Daten:
- `input_tokens`, `output_tokens` direkt aus der API-Response
- `cache_read_input_tokens`, `cache_creation_input_tokens` fuer Prompt Caching
- Pricing nach Modell: Opus $15/$75, Sonnet $3/$15, Haiku $0.25/$1.25 pro 1M Tokens

## Woher kommt der Code?

- **session_parser.py** adaptiert von `~/.local/bin/claude-sessions` (CLI-Tool)
- **Pricing** aus `~/ClaudesReich/Visualisierung/data/pricing.py`
- **run.sh** Pattern aus diversen Projekten

## Entstehung

Gebaut von 7 parallelen Sonnet-Agents in einer Session. Weil: warum einen Agent nehmen wenn man sieben haben kann? Parser, App, Setup, Research, Performance-Tests, Docs — alles parallel. Die Token-Rechnung war es wert.

## Erweiterungsideen

- CSV/JSON Export Button
- Session-Vergleich (zwei Sessions nebeneinander)
- Timeline-View (wann wurde wo gearbeitet)
- grep ueber ALLE Sessions gleichzeitig (Global Search)
- Tags/Bookmarks fuer wichtige Sessions
