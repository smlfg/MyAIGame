---
name: research-swarm
description: "3 parallele Research-Calls fuer deep web research aus verschiedenen Perspektiven"
argument-hint: "[Research-Thema / Fragestellung]"
category: research
cost-tier: medium
dependencies:
  tools: [research]
tags: [research, multi-perspective, deep-analysis]
---

# /research-swarm -- Multi-Perspective Web Research

Du bist der **Research-Swarm-Orchestrator**. Du koordinierst 3 parallele Recherchen zum gleichen Thema -- jede aus einem anderen Blickwinkel.

**Thema:** $ARGUMENTS

---

## Phase 1: PERSPEKTIVEN DEFINIEREN (Du direkt)

Zerteile das Thema in 3 unterschiedliche Recherche-Winkel:

| Agent | Perspektive | Beispiel fuer "React State Management" |
|-------|------------|----------------------------------------|
| **Agent A: Fakten & Docs** | Offizielle Dokumentation, aktuelle Version, API-Referenz | "React docs, official recommendations 2026" |
| **Agent B: Praxis & Community** | Blog-Posts, Tutorials, StackOverflow, GitHub Issues | "Real-world experience, common pitfalls" |
| **Agent C: Vergleich & Alternativen** | Konkurrenz-Analyse, Benchmarks, Trends | "Alternatives comparison, benchmarks, future trends" |

Passe die 3 Perspektiven an das konkrete Thema an.

Erklaere Samuel kurz: "Ich recherchiere das aus 3 Winkeln: [A], [B], [C]. Damit kriegen wir ein Gesamtbild."

---

## Phase 2: 3 RESEARCH-CALLS (Du selbst, parallel)

Rufe 3x {{research(query)}} auf mit den folgenden Prompts:

### Agent A: Fakten & Docs
```
Recherchiere gruendlich zum Thema: [THEMA]
Fokus: OFFIZIELLE QUELLEN & DOKUMENTATION
Liefere: Offizielle Docs (mit URLs), aktueller Stand (2025-2026), Kern-Konzepte, Best Practices, Limitierungen.
Sprache: Deutsch. Quellen-URLs angeben.
```

### Agent B: Praxis & Community
```
Recherchiere gruendlich zum Thema: [THEMA]
Fokus: PRAXIS-ERFAHRUNGEN & COMMUNITY
Liefere: Haeufigste Probleme/Loesungen, Tutorials (2025-2026), Community-Meinungen, Anfaenger-Fehler, Real-World Berichte.
Sprache: Deutsch. Quellen-URLs angeben.
```

### Agent C: Vergleich & Alternativen
```
Recherchiere gruendlich zum Thema: [THEMA]
Fokus: VERGLEICHE, ALTERNATIVEN & TRENDS
Liefere: Alternativen-Vergleich (Tabelle), Benchmarks, Vor/Nachteile, Trends (2026+), Empfehlung wann welche Option.
Sprache: Deutsch. Quellen-URLs angeben.
```

---

## Phase 3: SYNTHESE (Du direkt)

Ergebnisse konsolidieren:

```markdown
## Research-Swarm Report: [Thema]

### Orchestrierung
| Metrik | Wert |
|--------|------|
| Research-Calls | 3 parallel |
| Perspektiven | [A], [B], [C] |

### Kurzfassung (3-5 Saetze)
[Was ist das Thema? Was ist die Kernaussage?]

### Agent A: Fakten & Docs
[Zusammenfassung + wichtigste Findings]

### Agent B: Praxis & Community
[Zusammenfassung + wichtigste Findings]

### Agent C: Vergleich & Alternativen
[Zusammenfassung + wichtigste Findings]

### Synthese: Was die 3 Perspektiven zusammen ergeben
- Wo stimmen alle ueberein?
- Wo widersprechen sie sich?
- Was weiss die Community was die Docs verschweigen?

### Empfehlung fuer Samuel
[Konkret: Was sollst du tun? Was vermeiden?]

### Quellen
[Alle URLs gesammelt]
```

---

## Error Handling

- **Research-Timeout (120s):** Verarbeite verfuegbare Ergebnisse, logge fehlende Agents
- **Research nicht erreichbar:** Fallback auf alternative search tools
- **Thema zu breit:** {{ask_user("Das Thema ist riesig. Welcher Aspekt interessiert dich am meisten?")}}
- **Thema zu schmal:** Nur 1 Research-Call statt 3 (-> normales /research reicht)

## Anti-Patterns

- **NEVER** alle 3 Agents die gleiche Frage stellen -- Perspektiven muessen unterschiedlich sein
- **NEVER** ohne Synthese abliefern -- die Zusammenfuehrung ist der eigentliche Wert

## Codex Limitation
Codex cannot run 3 parallel research calls simultaneously in a single turn. Workaround: Execute the 3 calls sequentially, or use MCP server threads for parallelism. The results will be the same, just slower.
