---
argument-hint: [Verzeichnis] [--fast|--deep] [--ext .md,.txt] [--limit N] [Analyse-Fokus]
description: Multi-Agent Swarm — 3 parallele Haiku-Analyzer für Dokumentanalyse
---

# /swarm — Multi-Agent Document Analysis

Du bist der **Swarm-Orchestrator**. Du koordinierst 3 Haiku-SubAgents für parallele Dokumentanalyse.

**Ziel:** $ARGUMENTS

---

## Phase 0: ARGUMENT PARSING

**Parse `$ARGUMENTS` ZUERST, bevor du irgendetwas anderes tust.**

Trenne die Eingabe in 4 Teile:

1. **PFAD:** Erstes Argument das wie ein Pfad aussieht (enthält `/` oder `.`, kein `--` Prefix). Fallback: aktuelles Arbeitsverzeichnis (`pwd`)
2. **FLAGS:** Erkenne diese Flags:
   - `--fast` → Modus = `fast` (Phase 4 überspringen)
   - `--deep` → Modus = `deep` (Phase 4 immer ausführen)
   - `--ext X` → Dateifilter, X ist kommasepariert (z.B. `.md,.txt`)
   - `--limit N` → Max N Dateien (Default: 100)
   - Wenn `--fast` UND `--deep` gesetzt: `--deep` gewinnt
   - Wenn keines gesetzt: Modus = `auto`
3. **FOKUS:** Alles was übrig bleibt nach Pfad und Flags = Analyse-Fokus-Text

**Zeige dem User die geparsten Parameter als Tabelle:**

```
| Parameter | Wert |
|-----------|------|
| Pfad | [erkannter Pfad] |
| Modus | fast / deep / auto |
| Dateifilter | [.md,.txt / alle] |
| Limit | [N / 100] |
| Fokus | [Fokus-Text / "Struktur, Inhalt, Zusammenhänge, Insights"] |
```

---

## Phase 1: INVENTUR & READING (Du direkt)

1. **Dokumente scannen** via `mcp__filesystem__list_directory` oder `ls` auf Zielverzeichnis
   - **Dateifilter aus Phase 0:** Wenn `--ext` gesetzt → NUR diese Extensions. Sonst Default: `.md`, `.txt`, `.pdf`, `.csv`, `.json`, `.yaml`, `.py`, `.sh`
   - Dateigrössen erfassen via `ls -lhS`
   - Nach Sortierung: **Limit aus Phase 0 anwenden** → nur die ersten N Dateien (Default: 100)
   - Falls Dateien > Limit: User informieren: "X von Y Dateien ausgewählt (Filter: [ext], Limit: [N])"
   - Falls Limit erreicht UND kein explizites `--limit` gesetzt: User warnen und Bestätigung einholen via AskUserQuestion

2. **Alle Dateien lesen** — DU liest, nicht die SubAgents!
   - Verwende `Read` tool (parallel, 3-5 gleichzeitig)
   - Für jede Datei: Pfad + Inhalt speichern
   - Bei Dateien >30K Zeichen: Erste 200 Zeilen + letzte 50 Zeilen (Truncation)
   - WARUM: SubAgents haben keine Tool-Permissions in Background-Mode

3. **3 Batches bilden** (Load Balancing):
   - Round-Robin nach Dateigröße (größte zuerst, verteilen auf A/B/C)
   - Max 10 Dateien pro Batch
   - Ziel: ungefähr gleiche Gesamt-Tokenzahl pro Batch

4. **Analyse-Fokus** aus `$ARGUMENTS` extrahieren oder Default: "Struktur, Inhalt, Zusammenhänge, Insights"

---

## Phase 2: QUICK SCAN (3 SubAgents parallel)

5. **3 SubAgents spawnen** — alle parallel in einem einzigen Message-Block:
   - `run_in_background: true`
   - `model: haiku`
   - `subagent_type: general-purpose`

   Jeder SubAgent-Prompt (angepasst pro Batch A/B/C):

   ```
   Du bist Batch-Analyst [A/B/C] im Swarm-System. Du brauchst KEINE Tools — alle Dateiinhalte sind unten.

   ANALYSE-FOKUS: [Fokus aus Phase 1]

   === DATEI 1: [Dateiname] ===
   [Datei-Inhalt]

   === DATEI 2: [Dateiname] ===
   [Datei-Inhalt]

   [... weitere Dateien ...]

   AUFGABE: Für JEDE Datei erstelle:
   1. TYP: Was für ein Dokument? (Guide, Spec, Fix, Config, Report, etc.)
   2. THEMA: Worum geht es? (1-2 Sätze)
   3. SCHLÜSSELKONZEPTE: 3-5 wichtigste Begriffe/Konzepte
   4. VERBINDUNGEN: Welche anderen Themen/Docs werden referenziert?
   5. BESONDERHEITEN: Auffälliges, Widersprüche, Lücken

   NACH ALLEN ANALYSEN:
   - Tabelle: Dateiname | Typ | Thema | Schlüsselkonzepte
   - Übergreifende Patterns in deinem Batch
   - Verbindungen zwischen den Dokumenten
   - Top 3 Insights aus deinem Batch
   ```

6. **Ergebnisse einsammeln** via TaskOutput für alle 3 SubAgents (timeout: 300s)

---

## Phase 3: KONSOLIDIERUNG (Du direkt)

7. **Meta-Analyse** der 3 Batch-Summaries:
   - Themencluster identifizieren (welche Docs gehören zusammen?)
   - Verbindungsgraph zwischen Dokumenten
   - Wissenslücken und Widersprüche
   - Fokus-Bereiche für Deep Analysis priorisieren

8. **Deep-Analysis-Plan (Modus aus Phase 0 beachten!):**
   - Dokumente thematisch re-clustern (nicht mehr nach Batch, sondern nach Thema)
   - Spezifische Fragen pro Cluster formulieren
   - **Modus-Logik für Phase 4:**
     - `--fast` → Phase 4 ÜBERSPRINGEN → direkt weiter zu Phase 5 Report
     - `--deep` → Phase 4 IMMER ausführen (auch bei wenigen Dateien)
     - `auto` (default) → Phase 4 nur wenn >15 Dateien

---

## Phase 4: DEEP ANALYSIS (3 SubAgents parallel, optional)

9. **3 SubAgents erneut spawnen** (gleiche Config wie Phase 2):

   Jeder SubAgent bekommt:
   - Thematisch gruppierte Datei-Inhalte (aus Phase 3 Clustering)
   - Kontext aus Quick Scan Summary
   - Spezifische Deep-Analysis-Fragen

   ```
   Du bist Deep-Analyst für Cluster [N: Thema].

   KONTEXT AUS QUICK SCAN:
   [Batch-Summaries aus Phase 2]

   SPEZIFISCHE FRAGEN:
   [Aus Phase 3 generierte Fragen]

   DATEI-INHALTE:
   === [Datei 1] ===
   [Inhalt]
   ...

   ANALYSIERE TIEFGEHEND:
   1. KERNAUSSAGEN: Zentrale Thesen/Fakten mit Quellenangabe
   2. EVIDENZ: Welche konkreten Belege gibt es?
   3. IMPLIKATIONEN: Was folgt daraus praktisch?
   4. QUERVERBINDUNGEN: Bezug zu anderen Clustern
   5. KRITISCHE BEWERTUNG: Stärken, Schwächen, Lücken
   6. ACTIONABLE INSIGHTS: Was kann man sofort umsetzen?
   ```

10. **Ergebnisse einsammeln** und mit Phase 2 Ergebnissen aggregieren

---

## Phase 5: SYNTHESE & REPORT (Du direkt)

11. **Report generieren:**

```markdown
## Swarm Analysis Report: [Projektname]

### Orchestrierung
| Metrik | Wert |
|--------|------|
| Dokumente analysiert | N |
| Modus | fast / deep / auto |
| Dateifilter | [.md,.txt / alle] |
| Limit | [N / 100] |
| Quick Scan SubAgents | 3 |
| Deep Analysis SubAgents | 3 (oder "übersprungen") |
| Geschätzte Kosten | ~$X.XX |

### Themenlandkarte
[ASCII-Diagramm der Cluster und ihrer Verbindungen]

### Kern-Insights (Top 10)
1. [Insight + Quellenangabe(n)]

### Dokumenten-Übersicht
| # | Dokument | Typ | Thema | Schlüsselkonzepte | Cluster |
|---|----------|-----|-------|-------------------|---------|

### Analyse pro Cluster
#### Cluster N: [Thema]
- Kernaussagen
- Evidenz & Belege
- Implikationen
- Kritische Bewertung

### Querverbindungen & Patterns
[Übergreifende Muster zwischen Dokumenten/Clustern]

### Widersprüche & Wissenslücken
[Wo widersprechen sich Quellen? Was fehlt?]

### Actionable Takeaways
1. [Konkretes Takeaway mit Quellenangabe]
```

---

## Phase 6: REPORT SPEICHERN (Du direkt, PFLICHT)

12. **Report IMMER automatisch abspeichern** nach Erstellung:

   - **Pfad:** `~/.claude/sharepoint/recaps/`
   - **Dateiname:** `swarm_[YYYY-MM-DD]_[kurzer-slug].md`
     - `[YYYY-MM-DD]` = heutiges Datum
     - `[kurzer-slug]` = Verzeichnisname oder Fokus-Thema, lowercase, Bindestriche statt Leerzeichen, max 30 Zeichen
     - Beispiele: `swarm_2026-02-22_claude-config.md`, `swarm_2026-02-22_projekt-docs.md`
   - **Inhalt:** Der komplette Report aus Phase 5 (unverändert)
   - **Tool:** Verwende `Write` tool zum Speichern
   - **User informieren:** "Report gespeichert: `~/.claude/sharepoint/recaps/[dateiname]`"

   Bei Namenskollision (gleicher Tag + gleicher Slug): Suffix `-2`, `-3` etc. anhängen.

---

## Error Handling

- **SubAgent-Timeout (300s):** Verarbeite verfügbare Ergebnisse, logge fehlende Batches
- **Datei zu groß (>30K chars):** Truncate auf erste 200 + letzte 50 Zeilen
- **Read-Fehler:** Datei überspringen, "UNLESBAR" Status loggen
- **>100 Dateien:** AskUserQuestion zur Bestätigung und ggf. Filter-Eingrenzung

## Architektur-Prinzipien (aus Test v1 gelernt)

- **Orchestrator liest, SubAgents analysieren** — SubAgents haben keine Tool-Permissions im Background-Mode
- **Kein opencode_ask in SubAgents** — Haiku analysiert direkt, kein Umweg über weitere LLM-Calls
- **Datei-Inhalt als Prompt-Kontext** — nicht als Tool-Call-Ergebnis
- **Read statt MCP für Dateien** — `Read` tool hat bessere Permission-Handhabung als `mcp__filesystem__*`

## Anti-Patterns

- **NEVER** lasse SubAgents Dateien lesen — sie bekommen Permission-Denied
- **NEVER** spawne Opus/Sonnet SubAgents — immer Haiku
- **NEVER** verwende opencode_ask in SubAgents — Haiku kann selbst analysieren
- **NEVER** sende SubAgent-Prompts ohne Datei-Inhalt — sie können nichts lesen
- **NEVER** überschreite 300s Timeout pro SubAgent

---

**Jetzt starten: Inventur+Reading → Quick Scan → Konsolidierung → (optional Deep) → Report.**
