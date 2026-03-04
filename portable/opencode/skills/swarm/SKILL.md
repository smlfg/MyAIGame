---
name: swarm
description: "Multi-Agent Swarm -- parallel document analysis with session-based workers"
argument-hint: "[Verzeichnis] [--fast|--deep] [--ext .md,.txt] [--limit N] [Analyse-Fokus]"
category: multi-agent
cost-tier: variable
dependencies:
  tools: [file_read, spawn_subagent]
tags: [swarm, document-analysis, parallel]
---

# /swarm -- Multi-Agent Document Analysis

Du bist der **Swarm-Orchestrator**. Du koordinierst parallele Dokumentanalyse via separate sessions.

**Ziel:** $ARGUMENTS

---

## Phase 0: ARGUMENT PARSING

**Parse `$ARGUMENTS` ZUERST:**

1. **PFAD:** Erstes Argument das wie ein Pfad aussieht. Fallback: aktuelles Arbeitsverzeichnis (`pwd`)
2. **FLAGS:**
   - `--fast` -> Modus = `fast` (Phase 4 ueberspringen)
   - `--deep` -> Modus = `deep` (Phase 4 immer ausfuehren)
   - `--ext X` -> Dateifilter, X ist kommasepariert (z.B. `.md,.txt`)
   - `--limit N` -> Max N Dateien (Default: 100)
   - Wenn `--fast` UND `--deep`: `--deep` gewinnt
   - Wenn keines: Modus = `auto`
3. **FOKUS:** Alles was uebrig bleibt = Analyse-Fokus-Text

**Zeige geparste Parameter als Tabelle.**

---

## Phase 1: INVENTUR & READING (Du direkt)

1. **Dokumente scannen** im Zielverzeichnis
   - Dateifilter anwenden
   - Limit anwenden
   - Falls Dateien > Limit: User informieren

2. **Alle Dateien lesen** -- DU liest, nicht die Worker-Sessions!
   - Bei Dateien >30K Zeichen: Erste 200 + letzte 50 Zeilen
   - WARUM: Separate sessions may not have file access

3. **3 Batches bilden** (Load Balancing):
   - Round-Robin nach Dateigroesse
   - Max 10 Dateien pro Batch

---

## Phase 2: QUICK SCAN (3 Sessions parallel)

Erstelle 3 separate sessions, jede mit einem Batch:

Jeder Session-Prompt:
```
Du bist Batch-Analyst [A/B/C]. Alle Dateiinhalte sind unten.

ANALYSE-FOKUS: [Fokus]

=== DATEI 1: [Dateiname] ===
[Datei-Inhalt]

AUFGABE: Fuer JEDE Datei erstelle:
1. TYP: Was fuer ein Dokument?
2. THEMA: Worum geht es? (1-2 Saetze)
3. SCHLUESSELKONZEPTE: 3-5 wichtigste Begriffe
4. VERBINDUNGEN: Referenzen zu anderen Docs
5. BESONDERHEITEN: Auffaelliges, Widersprueche, Luecken

NACH ALLEN ANALYSEN:
- Tabelle: Dateiname | Typ | Thema | Schluesselkonzepte
- Uebergreifende Patterns
- Top 3 Insights aus deinem Batch
```

---

## Phase 3: KONSOLIDIERUNG (Du direkt)

Meta-Analyse der 3 Batch-Summaries:
- Themencluster identifizieren
- Verbindungsgraph zwischen Dokumenten
- Wissensluecken und Widersprueche
- Modus-Logik fuer Phase 4:
  - `--fast` -> Phase 4 UEBERSPRINGEN
  - `--deep` -> Phase 4 IMMER
  - `auto` -> Phase 4 nur wenn >15 Dateien

---

## Phase 4: DEEP ANALYSIS (optional, 3 Sessions)

Thematisch re-clusterte Sessions mit spezifischen Deep-Analysis-Fragen.

---

## Phase 5: SYNTHESE & REPORT

```markdown
## Swarm Analysis Report: [Projektname]

### Orchestrierung
| Metrik | Wert |
|--------|------|
| Dokumente analysiert | N |
| Modus | fast / deep / auto |
| Sessions | 3 (Quick) + 3 (Deep, optional) |

### Themenlandkarte
[ASCII-Diagramm der Cluster]

### Kern-Insights (Top 10)
1. [Insight + Quellenangabe]

### Dokumenten-Uebersicht
| # | Dokument | Typ | Thema | Cluster |

### Querverbindungen & Patterns
### Widersprueche & Wissensluecken
### Actionable Takeaways
```

---

## Phase 6: REPORT SPEICHERN

Speichere Report unter: `~/.opencode/recaps/swarm_[YYYY-MM-DD]_[slug].md`

---

## Anti-Patterns

- **NEVER** lasse Worker-Sessions Dateien lesen -- gib den Inhalt im Prompt mit
- **NEVER** ueberschreite 300s Timeout pro Session
- **NEVER** sende Prompts ohne Datei-Inhalt
