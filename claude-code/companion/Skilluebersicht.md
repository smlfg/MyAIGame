# Skilluebersicht

Alle verfuegbaren Slash-Commands fuer Claude Code. Stand: 22.02.2026.

---

## Coding & Delegation

| Skill | Was es tut | Kosten | Wann benutzen |
|-------|-----------|--------|---------------|
| `/chef` | Delegation an OpenCode MCP mit Context-Gathering via gather-context.sh | ~$3 (Sonnet) | **Standard fuer jede Code-Aufgabe.** Refactoring, neue Features, Bug-Fixes |
| `/chef-lite` | Direkter OpenCode-Call ohne Context-Gathering | ~$3 (Sonnet) | Kleine Aenderungen wo Context klar ist (<50 Zeilen) |
| `/chef-async` | Wie /chef aber non-blocking -- Claude arbeitet weiter | ~$3 (Sonnet) | Laengere Tasks wo du nicht warten willst |
| `/chef-subagent` | Haiku-SubAgent der OpenCode steuert (isolierter Kontext) | ~$0.25 (Haiku) + $3 | Background-Tasks die >5min dauern |
| `/batch` | Mehrere Tasks in EINEN opencode_run Call buendeln | ~$3 (Sonnet) | Viele kleine Aenderungen auf einmal |
| `/auto` | Smart auto-delegation -- waehlt beste Methode automatisch | variabel | Wenn du nicht weisst welchen /chef du willst |

### Wann welchen /chef?

```
Kleine Aenderung, Context klar     → /chef-lite
Normale Aufgabe                    → /chef
Dauert laenger, will weiterarbeiten → /chef-async
Riesen-Task im Hintergrund         → /chef-subagent
Viele kleine Tasks auf einmal       → /batch
Keine Ahnung                       → /auto
```

---

## Research & Analyse

| Skill | Was es tut | Kosten | Wann benutzen |
|-------|-----------|--------|---------------|
| `/research` | Gemini MCP Deep Web Research (1 Agent) | ~$0.10 (Flash) | **Standard fuer jede Recherche.** Docs lesen, Fakten pruefen, APIs verstehen |
| `/research-subagent` | Gemini-Research als Haiku-SubAgent (non-blocking) | ~$0.25 (Haiku) | Recherche im Hintergrund waehrend du weiter arbeitest |
| `/research-swarm` | **NEU!** 3 parallele Gemini-Agents fuer Mega-Research | ~$0.30 (3x Flash) | Grosse Themen die mehrere Perspektiven brauchen |
| `/swarm` | 3 parallele Haiku-Analyzer fuer Dokumentanalyse. Flags: `--fast` (kein Deep), `--deep` (force Deep), `--ext .md,.txt` (Dateifilter), `--limit N` (max Dateien) | ~$0.75 (3x Haiku) | Lokale Dokumente analysieren, Patterns finden |

### Wann welche Research?

```
Schnelle Fakten-Frage              → /research
Recherche neben anderer Arbeit      → /research-subagent
Grosses Thema, mehrere Perspektiven → /research-swarm  ← NEU
Lokale Dateien analysieren          → /swarm
Schneller Ueberblick ohne Deep      → /swarm --fast
Nur bestimmte Dateitypen            → /swarm --ext .md,.txt
Tiefenanalyse erzwingen             → /swarm --deep
```

---

## Testing

| Skill | Was es tut | Kosten | Wann benutzen |
|-------|-----------|--------|---------------|
| `/test` | Cascading Test Pipeline via OpenCode mit Auto-Fix-Loop | ~$3 (Sonnet) | **Standard nach jedem Feature.** Findet + fixt Fehler automatisch |
| `/test-crew` | Multi-Agent: Gemini plant Tests, OpenCode fuehrt aus + fixt | ~$0.27 (Gemini+OC) | Guenstigere Alternative zu /test |

---

## Utilities

| Skill | Was es tut | Kosten | Wann benutzen |
|-------|-----------|--------|---------------|
| `/check-state` | Zeigt pwd, ls, git status -- wo stehen wir? | $0 (lokal) | **VOR jeder Aenderung.** Orientierung schaffen |
| `/validate-config` | Config-Datei pruefen + Backup erstellen | $0 (lokal) | Bevor Config-Dateien geaendert werden |
| `/snapshot` | Projekt-Uebersicht generieren (Struktur, Dateien) | $0 (lokal) | Wenn du einen Ueberblick ueber ein Projekt brauchst |
| `/setup-git` | Git Branch Setup Workflow | $0 (lokal) | Neues Feature starten, Branch anlegen |
| `/review` | Code Review der aktuellen Aenderungen | ~$3 (Sonnet) | Vor einem Commit -- Qualitaets-Check |
| `/debug-loop` | Max 5 Iterationen: Diagnose → Fix → Test | ~$3 (Sonnet) | Hartnäckige Bugs die mehrere Versuche brauchen |
| `/explore-first` | Parallele Codebase-Erkundung vor Implementierung | ~$0.50 (Haiku) | Grosses unbekanntes Projekt verstehen |
| `/selfimprove` | CLAUDE.md + Companion Files verbessern | ~$0 | Neue Regel oder Anti-Pattern eintragen |
| `/recap` | Session zusammenfassen → SESSION_LOG.md | $0 (lokal) | **Am Ende jeder Session.** Kontext-Bruecke fuer ADHS |
| `/quickwin` | 3 kleine sofort-Tasks finden — Anti-Task-Paralysis | $0 (lokal) | Wenn du nicht weisst wo anfangen |
| `/checkpoint` | Git-Snapshot + Summary + Dopamin-Feedback | $0 (lokal) | Regelmaessig Fortschritt sichern und feiern |
| `/learn` | Nach Vibe-Coding: Kernfunktionen erklaeren + Wissen sichern | $0 (lokal) | **Nach jeder Coding-Session.** Verstehen was gebaut wurde |
| `/focus` | Session-Discipline: EIN Ziel, Abschweifung bremsen, Parken | $0 (lokal) | ADHS-Anker — wenn du dranbleiben willst |

---

## Multi-Agent / Orchestrierung

| Skill | Was es tut | Kosten | Wann benutzen |
|-------|-----------|--------|---------------|
| `/crew` | CrewAI mit Gemini+MiniMax Workern | ~$0.60 | Multi-File Changes, grosse Refactorings |
| `/swarm` | 3 Haiku-Agents fuer Dokumentanalyse. Flags: `--fast`, `--deep`, `--ext`, `--limit` | ~$0.75 | Viele Dokumente parallel analysieren |
| `/research-swarm` | **NEU!** 3 Gemini-Agents fuer parallele Web-Research | ~$0.30 | Crazy deep research aus 3 Perspektiven |

---

## Spezial

| Skill | Was es tut | Kosten | Wann benutzen |
|-------|-----------|--------|---------------|
| `/ClaudeChromeExtension` | Chrome Extension Status + Troubleshooting | $0 | Chrome Extension Probleme |

---

## Kosten-Ranking (guenstigste zuerst)

```
$0.00   /check-state, /validate-config, /snapshot, /setup-git, /selfimprove, /recap, /quickwin, /checkpoint, /learn, /focus
$0.10   /research (Gemini Flash)
$0.25   /research-subagent (Haiku + Gemini)
$0.27   /test-crew (Gemini + OpenCode)
$0.30   /research-swarm (3x Gemini Flash)  ← NEU
$0.50   /explore-first (Haiku)
$0.60   /crew (CrewAI)
$0.75   /swarm (3x Haiku)
$3.00   /chef, /chef-lite, /chef-async, /test, /review, /debug-loop
$3.25   /chef-subagent (Haiku + Sonnet)
variabel /auto, /batch
```

**Faustregel:** Recherche mit Gemini (~$0.10), Code mit OpenCode (~$3), Strategie mit Claude (~$15).

---

## Vorgeschlagene neue Skills (aus der Analyse)

| Skill | Zweck | Warum fehlt er | Priority |
|-------|-------|---------------|----------|
| `/focus` | Session-Discipline: EIN Ziel, Abschweifung bremsen | DONE — implementiert als eigenstaendiger Skill | DONE |
| `/baseline` | State-Snapshot: "Wo stehen wir?" vor jeder Aenderung | Teilweise via /checkpoint abgedeckt | MEDIUM |
| `/commit` | Git Commit mit Erklaerung was passiert | Samuel lernt Git nicht wenn Claude alles still macht | HIGH |
| `/measure` | Token-Kosten, Completion-Rate, Session-Stats tracken | Kostenoptimierung braucht Daten | MEDIUM |
| `/learn` | Nach Vibe-Coding: Kernfunktionen erklaeren + Wissen sichern | DONE — implementiert als eigenstaendiger Skill | DONE |
| `/research-swarm` | 3 parallele Gemini-Agents fuer Mega-Research | Grosse Themen brauchen mehrere Blickwinkel | DONE (siehe unten) |
