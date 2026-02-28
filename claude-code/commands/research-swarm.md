---
argument-hint: [Research-Thema / Fragestellung]
description: 3 parallele Gemini-Agents fuer crazy deep web research aus verschiedenen Perspektiven
---

# /research-swarm — Gemini Multi-Agent Web Research

Du bist der **Research-Swarm-Orchestrator**. Du koordinierst 3 parallele Gemini-Recherchen zum gleichen Thema -- jede aus einem anderen Blickwinkel.

**Thema:** $ARGUMENTS

---

## Phase 1: PERSPEKTIVEN DEFINIEREN (Du direkt)

Zerteile das Thema in 3 unterschiedliche Recherche-Winkel:

| Agent | Perspektive | Beispiel fuer "React State Management" |
|-------|------------|----------------------------------------|
| **Agent A: Fakten & Docs** | Offizielle Dokumentation, aktuelle Version, API-Referenz | "React docs, official recommendations 2026" |
| **Agent B: Praxis & Community** | Blog-Posts, Tutorials, StackOverflow, GitHub Issues, Erfahrungsberichte | "Real-world experience, common pitfalls, community opinions" |
| **Agent C: Vergleich & Alternativen** | Konkurrenz-Analyse, Benchmarks, Vor/Nachteile, Trends | "Alternatives comparison, benchmarks, future trends" |

Passe die 3 Perspektiven an das konkrete Thema an. Nicht jedes Thema braucht "Alternativen" -- manchmal ist "Geschichte & Kontext" oder "Security-Aspekte" oder "Kosten-Analyse" besser.

Erklaere Samuel kurz: "Ich recherchiere das aus 3 Winkeln: [A], [B], [C]. Damit kriegen wir ein Gesamtbild."

---

## Phase 2: 3 GEMINI-CALLS DIREKT (Du selbst)

**WICHTIG:** SubAgents haben KEINEN Zugriff auf MCP Tools (Gemini, WebSearch etc.). Deshalb machst DU (der Orchestrator) die 3 Gemini-Calls direkt.

Rufe 3x `mcp__gemini__ask-gemini` parallel auf (in einem einzigen Message-Block) mit den folgenden Prompts:

### Agent A: Fakten & Docs
```
Recherchiere gruendlich zum Thema: [THEMA]
Fokus: OFFIZIELLE QUELLEN & DOKUMENTATION

Liefere:
- Offizielle Dokumentation (mit URLs)
- Aktuelle Version / Stand der Technik (2025-2026)
- API-Referenz oder Kern-Konzepte
- Best Practices laut offiziellen Quellen
- Bekannte Limitierungen oder Caveats

Sprache: Deutsch. Quellen-URLs angeben.
```

### Agent B: Praxis & Community
```
Recherchiere gruendlich zum Thema: [THEMA]
Fokus: PRAXIS-ERFAHRUNGEN & COMMUNITY

Liefere:
- Haeufigste Probleme und Loesungen (StackOverflow, GitHub Issues)
- Blog-Posts und Tutorials (2025-2026, mit URLs)
- Community-Meinungen und Kontroversen
- Typische Anfaenger-Fehler
- Real-World Erfahrungsberichte

Sprache: Deutsch. Quellen-URLs angeben.
```

### Agent C: Vergleich & Alternativen
```
Recherchiere gruendlich zum Thema: [THEMA]
Fokus: VERGLEICHE, ALTERNATIVEN & TRENDS

Liefere:
- Vergleich mit Alternativen (Tabelle: Feature | Option A | Option B | ...)
- Benchmarks oder Performance-Vergleiche (wenn vorhanden)
- Vor- und Nachteile
- Wohin geht der Trend? (2026+)
- Empfehlung: Wann welche Option?

Sprache: Deutsch. Quellen-URLs angeben.
```

---

## Phase 3: SYNTHESE (Du direkt)

Ergebnisse einsammeln (TaskOutput, timeout: 120s pro Agent).

Dann konsolidieren:

```markdown
## Research-Swarm Report: [Thema]

### Orchestrierung
| Metrik | Wert |
|--------|------|
| Gemini-Agents | 3 parallel |
| Perspektiven | [A], [B], [C] |
| Geschaetzte Kosten | ~$0.30 (3x Flash) |

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

- **SubAgent-Limitation:** MCP Tools (Gemini, WebSearch) sind NICHT in SubAgents verfuegbar. Immer direkt im Orchestrator ausfuehren.
- **Gemini-Timeout (120s):** Verarbeite verfuegbare Ergebnisse, logge fehlende Agents
- **Gemini nicht erreichbar:** Fallback auf 3x WebSearch (teurer, aber funktioniert)
- **Thema zu breit:** AskUserQuestion → "Das Thema ist riesig. Welcher Aspekt interessiert dich am meisten?"
- **Thema zu schmal:** Nur 1 Gemini-Call statt 3 (→ normales /research reicht)

## Anti-Patterns

- **NEVER** Opus/Sonnet SubAgents fuer die Recherche -- immer Haiku + Gemini
- **NEVER** alle 3 Agents die gleiche Frage stellen -- Perspektiven muessen unterschiedlich sein
- **NEVER** ohne Synthese abliefern -- die Zusammenfuehrung ist der eigentliche Wert

---

**Jetzt starten: Perspektiven definieren → 3 Gemini-Calls parallel → Synthese + Report.**
