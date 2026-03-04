---
name: swarm
description: "Multi-Agent Swarm -- 3 parallele Analyzer fuer Dokumentanalyse"
argument-hint: "[Verzeichnis] [--fast|--deep] [--ext .md,.txt] [--limit N] [Analyse-Fokus]"
category: multi-agent
cost-tier: variable
dependencies:
  tools: [spawn_subagent, file_read, file_write, shell]
tags: [multi-agent, document-analysis, parallel]
---

# /swarm -- Multi-Agent Document Analysis

Du bist der **Swarm-Orchestrator**. Du koordinierst 3 Analyzer fuer parallele Dokumentanalyse.

**Ziel:** $ARGUMENTS

---

## Phase 0: ARGUMENT PARSING

Trenne die Eingabe in 4 Teile:

1. **PFAD:** Erstes Argument das wie ein Pfad aussieht. Fallback: aktuelles Arbeitsverzeichnis
2. **FLAGS:**
   - `--fast` -> Phase 4 ueberspringen
   - `--deep` -> Phase 4 immer ausfuehren
   - `--ext X` -> Dateifilter (z.B. `.md,.txt`)
   - `--limit N` -> Max N Dateien (Default: 100)
3. **FOKUS:** Alles was uebrig bleibt = Analyse-Fokus-Text

---

## Phase 1: INVENTUR & READING (Du direkt)

1. **Dokumente scannen** -- list directory, apply filters and limits
2. **Alle Dateien lesen** -- DU liest, nicht die Analyzer!
   - Bei Dateien >30K Zeichen: Erste 200 Zeilen + letzte 50 Zeilen
   - WARUM: Sub-processes haben keine File-Permissions
3. **3 Batches bilden** (Round-Robin nach Dateigroesse)

---

## Phase 2: QUICK SCAN (3 Analyzer parallel)

Spawn 3 sub-processes, each with a batch of file contents embedded in the prompt:

{{spawn_subagent(model="lightweight", prompt="""
Du bist Batch-Analyst [A/B/C] im Swarm-System.
ANALYSE-FOKUS: [Fokus]

=== DATEI 1: [name] ===
[content]
...

AUFGABE: Fuer JEDE Datei: TYP, THEMA, SCHLUESSELKONZEPTE, VERBINDUNGEN, BESONDERHEITEN.
NACH ALLEN ANALYSEN: Tabelle + Patterns + Top 3 Insights.
""")}}

---

## Phase 3: KONSOLIDIERUNG (Du direkt)

Meta-Analyse: Themencluster, Verbindungsgraph, Wissensluecken, Deep-Analysis-Plan.

Modus-Logik fuer Phase 4:
- `--fast` -> Phase 4 UEBERSPRINGEN
- `--deep` -> Phase 4 IMMER ausfuehren
- `auto` (default) -> Phase 4 nur wenn >15 Dateien

---

## Phase 4: DEEP ANALYSIS (optional, 3 Analyzer parallel)

Re-cluster by topic, spawn 3 deep analyzers with specific questions per cluster.

---

## Phase 5: SYNTHESE & REPORT

Generate comprehensive report with Themenlandkarte, Kern-Insights, Dokumenten-Uebersicht, Cluster-Analyse, Querverbindungen, Widersprueche, Actionable Takeaways.

---

## Phase 6: REPORT SPEICHERN

Save report to standard location with date-based filename.

---

## Anti-Patterns

- **NEVER** lasse Sub-Processes Dateien lesen -- sie bekommen Permission-Denied
- **NEVER** spawne expensive model sub-processes -- immer lightweight
- **NEVER** sende Prompts ohne Datei-Inhalt -- Sub-Processes koennen nichts lesen
- **NEVER** ueberschreite 300s Timeout pro Sub-Process

## Codex Limitation
Codex does not have native sub-agent spawning like Claude Code's Task tool. Workaround options:
1. Use `codex mcp-server` to create MCP threads for parallelism
2. Run 3 sequential analysis passes instead of parallel (slower but works)
3. Use a single comprehensive analysis call (loses the multi-perspective benefit)
The document reading and orchestration pattern still works -- only the parallelism is limited.
