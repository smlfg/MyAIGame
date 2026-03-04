# Skilluebersicht

Alle verfuegbaren Workflows/Skills. Abstrakt beschrieben -- die genaue Invocation haengt vom Tool ab.

> **Kosten-Tiers:**
> - **Free** = lokale Shell-Befehle, kein API-Call
> - **Research** = guenstigstes Modell (z.B. Flash, Mini)
> - **Execution** = mittleres Modell (z.B. Sonnet, MiniMax)
> - **Strategy** = teuerstes Modell (z.B. Opus, GPT-4)

---

## Coding & Delegation

| Skill | Was es tut | Kosten-Tier | Wann benutzen |
|-------|-----------|-------------|---------------|
| chef | Delegation an Execution-Tier mit Context-Gathering | Execution | **Standard fuer jede Code-Aufgabe.** Refactoring, neue Features, Bug-Fixes |
| chef-lite | Direkter Execution-Call ohne Context-Gathering | Execution | Kleine Aenderungen wo Context klar ist (<50 Zeilen) |
| chef-async | Wie chef aber non-blocking | Execution | Laengere Tasks wo du nicht warten willst |
| chef-subagent | Background-Agent der Execution-Tier steuert | Background + Execution | Background-Tasks die >5min dauern |
| batch | Mehrere Tasks in EINEN Execution-Call buendeln | Execution | Viele kleine Aenderungen auf einmal |
| auto | Smart auto-delegation -- waehlt beste Methode automatisch | variabel | Wenn du nicht weisst welchen chef du willst |

### Wann welchen chef?

```
Kleine Aenderung, Context klar     -> chef-lite
Normale Aufgabe                    -> chef
Dauert laenger, will weiterarbeiten -> chef-async
Riesen-Task im Hintergrund         -> chef-subagent
Viele kleine Tasks auf einmal       -> batch
Keine Ahnung                       -> auto
```

---

## Research & Analyse

| Skill | Was es tut | Kosten-Tier | Wann benutzen |
|-------|-----------|-------------|---------------|
| research | Deep Web Research (1 Agent) | Research | **Standard fuer jede Recherche.** Docs lesen, Fakten pruefen, APIs verstehen |
| research-subagent | Research als Background-Agent (non-blocking) | Background | Recherche im Hintergrund waehrend du weiter arbeitest |
| research-swarm | 3 parallele Research-Agents fuer Mega-Research | 3x Research | Grosse Themen die mehrere Perspektiven brauchen |
| swarm | 3 parallele Analyzer fuer Dokumentanalyse. Flags: `--fast`, `--deep`, `--ext`, `--limit` | 3x Background | Lokale Dokumente analysieren, Patterns finden |

### Wann welche Research?

```
Schnelle Fakten-Frage              -> research
Recherche neben anderer Arbeit      -> research-subagent
Grosses Thema, mehrere Perspektiven -> research-swarm
Lokale Dateien analysieren          -> swarm
Schneller Ueberblick ohne Deep      -> swarm --fast
Nur bestimmte Dateitypen            -> swarm --ext .md,.txt
Tiefenanalyse erzwingen             -> swarm --deep
```

---

## Testing

| Skill | Was es tut | Kosten-Tier | Wann benutzen |
|-------|-----------|-------------|---------------|
| test | Cascading Test Pipeline mit Auto-Fix-Loop | Execution | **Standard nach jedem Feature.** Findet + fixt Fehler automatisch |
| test-crew | Multi-Agent: Research plant Tests, Execution fuehrt aus + fixt | Research + Execution | Guenstigere Alternative zu test |

---

## Utilities

| Skill | Was es tut | Kosten-Tier | Wann benutzen |
|-------|-----------|-------------|---------------|
| check-state | Zeigt pwd, ls, git status -- wo stehen wir? | Free | **VOR jeder Aenderung.** Orientierung schaffen |
| validate-config | Config-Datei pruefen + Backup erstellen | Free | Bevor Config-Dateien geaendert werden |
| snapshot | Projekt-Uebersicht generieren (Struktur, Dateien) | Free | Wenn du einen Ueberblick ueber ein Projekt brauchst |
| setup-git | Git Branch Setup Workflow | Free | Neues Feature starten, Branch anlegen |
| review | Code Review der aktuellen Aenderungen | Execution | Vor einem Commit -- Qualitaets-Check |
| debug-loop | Max 5 Iterationen: Diagnose -> Fix -> Test | Execution | Hartnaeckige Bugs die mehrere Versuche brauchen |
| explore-first | Parallele Codebase-Erkundung vor Implementierung | Background | Grosses unbekanntes Projekt verstehen |
| selfimprove | Agent-Instructions verbessern | Free | Neue Regel oder Anti-Pattern eintragen |
| recap | Session zusammenfassen -> SESSION_LOG.md | Free | **Am Ende jeder Session.** Kontext-Bruecke fuer ADHS |
| quickwin | 3 kleine sofort-Tasks finden -- Anti-Task-Paralysis | Free | Wenn du nicht weisst wo anfangen |
| checkpoint | Git-Snapshot + Summary + Dopamin-Feedback | Free | Regelmaessig Fortschritt sichern und feiern |
| learn | Nach Coding: Kernfunktionen erklaeren + Wissen sichern | Free | **Nach jeder Coding-Session.** Verstehen was gebaut wurde |
| focus | Session-Discipline: EIN Ziel, Abschweifung bremsen, Parken | Free | ADHS-Anker -- wenn du dranbleiben willst |

---

## Multi-Agent / Orchestrierung

| Skill | Was es tut | Kosten-Tier | Wann benutzen |
|-------|-----------|-------------|---------------|
| crew | Multi-Agent mit Research+Execution Workern | Research + Execution | Multi-File Changes, grosse Refactorings |
| swarm | 3 Background-Agents fuer Dokumentanalyse | 3x Background | Viele Dokumente parallel analysieren |
| research-swarm | 3 Research-Agents fuer parallele Web-Research | 3x Research | Deep Research aus 3 Perspektiven |

---

## Kosten-Ranking (guenstigste zuerst)

```
Free        check-state, validate-config, snapshot, setup-git, selfimprove, recap, quickwin, checkpoint, learn, focus
Research    research
Background  research-subagent
Research x3 research-swarm
Background  explore-first
Mixed       crew, test-crew
Background x3 swarm
Execution   chef, chef-lite, chef-async, test, review, debug-loop
Exec+BG     chef-subagent
variabel    auto, batch
```

**Faustregel:** Recherche mit Research-Tier, Code mit Execution-Tier, Strategie mit Strategy-Tier.
