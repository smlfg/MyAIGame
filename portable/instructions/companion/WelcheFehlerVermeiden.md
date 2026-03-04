# Welche Fehler vermeiden?

Fehler die Samuel und AI-Agents gemeinsam gemacht haben -- und wie man sie vermeidet.
Aus Analyse-Sessions + laufende Erkenntnisse.

---

## REGEL NULL: Samuel muss VERSTEHEN was passiert

**Das ist die wichtigste Regel in diesem ganzen System.**

Der Agent darf NICHT einfach weitermachen ohne dass Samuel versteht was passiert.
Samuel kann z.B. kein Git -- weil Agents immer alles fuer ihn machen. Das ist kein Feature, das ist ein Bug.

### Was der Agent tun MUSS:

**Bei jedem nicht-trivialen Schritt:**
1. **Erklaeren BEVOR ausfuehren** -- "Ich wuerde jetzt X machen, weil Y. Kurz erklaert: ..."
2. **Verstaendnis-Fragen stellen** -- "Weisst du was ein rebase ist? Soll ich kurz erklaeren?"
3. **Nicht einfach durchrattern** -- Lieber eine Frage zu viel als Samuel im Dunkeln lassen

**Besonders bei Git:**
- Vor jedem `git commit`: "Wir speichern jetzt diese Aenderungen: [Liste]. Commit-Message waere: '...'. OK?"
- Vor jedem `git push`: "Das schickt deinen Code ins Internet (GitHub). Sicher?"
- Vor jedem `git branch`: "Wir erstellen einen Seitenzweig -- wie ein Paralleluniversum deines Codes. Warum: ..."
- Bei Merge/Rebase: IMMER erst erklaeren was das ist, Analogie nutzen, dann fragen ob klar

**Generell:**
- Wenn Samuel etwas zum ersten Mal sieht -> erklaeren, nicht ueberspringen
- Wenn der Agent 3+ Befehle am Stueck ausfuehrt -> kurze Zusammenfassung was gerade passiert ist
- Wenn ein Fehler auftritt -> erklaeren was schiefging, nicht einfach fixen und weitermachen
- **Ziel: Samuel soll es SELBST koennen, nicht vom Agent abhaengig sein**

### Lern-Momente aktiv schaffen:
- "Das war uebrigens ein typischer [Konzept]-Fall. Merke dir: ..."
- "Fun fact: Der Befehl heisst so weil ..."
- "Tipp: Das kannst du auch ohne mich machen mit: `git status`"

---

## Top 10 Fehler (sortiert nach Impact)

### KRITISCH

#### #1: Task Incompletion Loop
- **Was:** Dutzende Sessions angefangen, weniger als ein Drittel fertig
- **Warum:** ADHS-bedingtes Multi-Tasking + kein Focus-Mechanismus
- **Kosten:** Massive Token-Verschwendung fuer unvollstaendige Arbeit
- **Vermeiden:**
  - Pro Session: EIN Ziel, klar definiert
  - Max 2-3 parallele Sessions
  - Agent fragt am Anfang: "Was ist das EINE Ziel dieser Session?"
  - Agent fragt bei Abschweifung: "Sollen wir das parken und erst [aktueller Task] fertig machen?"

#### #2: Zombie-Prozesse
- **Was:** Background-Tasks gestartet, nie bereinigt
- **Warum:** Fire-and-forget ohne Cleanup-Habit
- **Kosten:** API-Waste, Disk-Bloat, Ueberblick verloren
- **Vermeiden:**
  - Nach jedem Background-Task: Timer setzen, Status nach 5min pruefen
  - Woechentlich 30min Session-Autopsy (was laeuft noch? was kann weg?)
  - Agent erinnert: "Du hast noch N offene Sessions. Aufraeumen?"

#### #3: Specs ohne Execution
- **Was:** Specs/Plaene geschrieben, nie implementiert
- **Warum:** Planen fuehlt sich produktiv an (ist es aber nicht ohne Umsetzung)
- **Vermeiden:**
  - Regel: Code First, Docs Second
  - Vor neuem Feature: Werden die bestehenden ueberhaupt genutzt?
  - Deadline: Spec -> 48h implementieren oder loeschen

#### #4: Secrets Exposed (Security)
- **Was:** API-Keys in Config-Dateien, potenziell in Cloud-Sync
- **Vermeiden:**
  - Secrets NIEMALS in Config-Dateien -> stattdessen ~/.env.local oder env vars
  - .gitignore pruefen: *.env.local, *.secrets, settings.json
  - API-Keys quarterly rotieren
  - Pre-commit Hook: grep nach api_key/jwt/token

### HOCH

#### #5: Delegation ohne Context = Garbage-In
- **Was:** Tasks delegiert ohne Projekt-Kontext mitzugeben
- **Symptom:** Generische Outputs die nicht zum Projekt passen
- **Vermeiden:**
  - Vor JEDER Delegation: Context sammeln (Projektstruktur, relevante Dateien)
  - Keine Vermutungen in Delegation-Prompts (Fakten only)

#### #6: Instruction Bloat
- **Was:** Alles in eine Datei gestopft (Rules, Commands, Config, Debug-Tipps)
- **Kosten:** Token-Overhead pro Session, Cognitive Load
- **Vermieden durch:** Auslagerung in Companion Files

#### #7: Kosten-Wissen ohne Kosten-Disziplin
- **Was:** Weiss dass guenstige Modelle existieren, nutzt trotzdem teure fuer simple Tasks
- **Vermeiden:**
  - Research-Tier IMMER zuerst fuer Recherche
  - Web Search NIE als erste Wahl
  - Monatlich: kurzer Cost-Check

#### #8: TODO-Chaos
- **Was:** Viele TODO-Dateien ohne Review, nie konsolidiert
- **Vermeiden:**
  - EINE TODO_CURRENT.md statt viele verstreute Dateien
  - Woechentlich: 30min Review
  - Erledigt -> Archiv, nicht loeschen

#### #9: Dokumentation statt Execution
- **Was:** Guides und Plaene schreiben statt Code
- **Vermeiden:**
  - FOR_SMLFLG.md erst NACH Projekt-Abschluss schreiben
  - Faustregel: 80% Coding, 20% Dokumentation

#### #10: Keine Baseline vor Aenderungen
- **Was:** Sessions starten ohne "Wo stehen wir?" Snapshot
- **Vermeiden:**
  - Session-Start: State checken (pwd, ls, git status)
  - Session-Ende: git diff gegen Start vergleichen
  - "Hat sich etwas verbessert?" muss beantwortbar sein

---

## External API & Bug Fix Chain

**PFLICHT bei jedem externen API-Fehler oder unbekannten Endpoint:**

```
1. Fehlermeldung lesen -- was sagt sie GENAU?
2. Research-Tier fragen: "What is the correct [API] endpoint for [feature]?"
3. Ergebnis: exakter Endpoint, HTTP-Method, Parameter aus Docs
4. Dann erst Execution-Tier: "Research confirmed: endpoint X, method Y, params Z. Fix."
```

**Verbotene Woerter in Delegation-Prompts:**
"try", "maybe", "might", "possibly", "I think", "should be", "probably"
-> Wenn du so denkst: STOP. Erst Research-Tier fragen. Dann Fakten delegieren.

**Beispiel FALSCH:**
> "Try changing 'deals' to 'deal' in the request"

**Beispiel RICHTIG:**
> "Research confirmed: endpoint is GET /deals, param deal_parms (not selection). Fix both."

---

## Integration Work

Bei Multi-Step System-Integrationen (Pipelines, Hooks, Chains):
- Aenderungen INKREMENTELL machen
- Nach JEDEM Schritt testen
- NICHT mehrere Komponenten gleichzeitig aendern
- Race Conditions, Pipe-Fehler und Overlapping Processes sind die ueblichen Verdaechtigen

---

## Anti-Pattern Checkliste (Schnell-Referenz)

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Tool-Schreib-Spirale | Baut 5 Workflows statt 1 zu nutzen | Bestehende Workflows erst nutzen |
| Planning Paralysis | Guides schreiben die nie gelesen werden | Code First, Docs Second |
| Delegate Without Verify | Task delegieren, Output ignorieren | Ergebnis immer pruefen |
| Session Hoarder | Dutzende Sessions, keine DONE | Max 2-3 parallel, woechentlich aufraeumen |
| Cost-Awareness ohne Discipline | Kennt Preise, nutzt trotzdem teuer | Research-Tier Default, Rest Fallback |
| Sub-Agent Limitations | Sub-Agent soll externe Tools nutzen | Sub-Agents haben oft KEINEN externen Tool-Zugriff. Direkt im Orchestrator machen |
