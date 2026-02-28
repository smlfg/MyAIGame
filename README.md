# MyAIGame — Mein AI Workflow Toolkit

> Alles was ich ueber AI-gesteuerte Entwicklung gelernt habe:
> Skills, Prompts, Agent-Orchestrierung, ADHS-Workflows.
>
> Von Samuel ([@smlfg](https://github.com/smlfg)), gebaut mit Claude Code.

---

## Ueberblick

```
┌─────────────────────────────────────────────────────┐
│                  Claude Code (Opus)                  │
│              Strategie & Orchestrierung              │
│                    ~$15 / 1M Tokens                  │
│                                                      │
│   ┌──────────┐   ┌──────────┐   ┌──────────────┐   │
│   │ OpenCode │   │  Gemini  │   │ Haiku        │   │
│   │ (Sonnet) │   │  (Flash) │   │ SubAgents    │   │
│   │  ~$3/1M  │   │ ~$0.10/1M│   │ ~$0.25/1M    │   │
│   │          │   │          │   │              │   │
│   │ Code     │   │ Research │   │ Background   │   │
│   │ schreiben│   │ Fakten   │   │ Tasks        │   │
│   └──────────┘   └──────────┘   └──────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Kernidee:** Claude Code (teuer, schlau) plant und delegiert. Die eigentliche Arbeit machen guenstigere Modelle. Recherche kostet $0.10, nicht $15.

### Kosten auf einen Blick

| Layer | Modell | Kosten/1M | Aufgabe |
|-------|--------|-----------|---------|
| Strategie | Opus | ~$15 | Planung, Entscheidungen, Orchestrierung |
| Ausfuehrung | Sonnet (OpenCode) | ~$3 | Code schreiben, Refactoring, Tests |
| Research | Flash (Gemini) | ~$0.10 | Web-Recherche, Fakten-Check |
| SubAgents | Haiku | ~$0.25 | Background-Tasks, Analyse |

---

## Skills (Slash Commands)

29 Skills in 6 Kategorien. Jeder Skill ist ein `/command` in Claude Code.

### Coding & Delegation

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/chef` | ~$3 | Standard-Delegation an OpenCode mit Context-Gathering |
| `/chef-lite` | ~$3 | Direkter OpenCode-Call ohne Context — fuer kleine Sachen |
| `/chef-async` | ~$3 | Wie /chef aber non-blocking — Claude arbeitet weiter |
| `/chef-subagent` | ~$3.25 | Haiku steuert OpenCode im Hintergrund |
| `/batch` | ~$3 | Mehrere Tasks in EINEN Call buendeln — Token-sparend |
| `/auto` | variabel | Waehlt automatisch die beste Delegation-Methode |

### Research

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/research` | ~$0.10 | Gemini Deep Web Research (Standard fuer jede Recherche) |
| `/research-subagent` | ~$0.25 | Research im Hintergrund via Haiku SubAgent |
| `/research-swarm` | ~$0.30 | 3 parallele Gemini-Agents — verschiedene Perspektiven |

### Testing

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/test` | ~$3 | Cascading Test Pipeline mit Auto-Fix-Loop |
| `/test-crew` | ~$0.27 | Guenstigere Alternative: Gemini plant, OpenCode fuehrt aus |
| `/debug-loop` | ~$3 | Bis zu 5 Iterationen: Diagnose → Fix → Test |

### ADHS Workflow

Skills die speziell fuer ADHS-Gehirne designt sind — gegen Task Paralysis, fuer Dopamin.

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/quickwin` | $0 | 3 kleine sofort-Tasks finden — gegen "wo fang ich an?" |
| `/bigwin` | $0 | Das grosse Ding anpacken das du ewig aufschiebst |
| `/focus` | $0 | EIN Ziel, EINE Session — Abschweifung bremsen |
| `/checkpoint` | $0 | Git-Snapshot + Summary + sichtbarer Fortschritt |
| `/recap` | $0 | Session zusammenfassen → SESSION_LOG.md (Kontext-Bruecke) |
| `/learn` | $0 | Nach Vibe-Coding: Verstehen was gebaut wurde |

### Multi-Agent / Orchestrierung

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/swarm` | ~$0.75 | 3 parallele Haiku-Analyzer fuer Dokumentanalyse |
| `/crew` | ~$0.60 | CrewAI mit Gemini+MiniMax Workern |
| `/research-swarm` | ~$0.30 | 3 Gemini-Agents fuer parallele Web-Research |

### Utilities

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/check-state` | $0 | pwd, ls, git status — wo stehen wir? |
| `/explore-first` | ~$0.50 | Parallele Codebase-Erkundung vor Implementierung |
| `/review` | ~$3 | Code Review der aktuellen Aenderungen |
| `/snapshot` | $0 | Projekt-Uebersicht generieren |
| `/validate-config` | $0 | Config-Datei pruefen + Backup erstellen |
| `/setup-git` | $0 | Git Branch Setup Workflow |
| `/selfimprove` | $0 | CLAUDE.md + Companion Files verbessern |
| `/ClaudeChromeExtension` | $0 | Chrome Extension Status + Troubleshooting |

### Legacy

| Skill | Kosten | Was es tut |
|-------|--------|-----------|
| `/delegate` | ~$3 | Alter Delegation-Skill — ersetzt durch /chef |

---

## Companion Files

Die CLAUDE.md ist bewusst kurz gehalten (~86 Zeilen). Details leben in Companion Files.

| Datei | Was drin steht |
|-------|---------------|
| **CLAUDE.md** | Kern-Instruktionen: Delegation Architecture, Anti-Patterns, Communication Style. Das "Betriebssystem" fuer Claude. |
| **WieArbeitestDuMitSamuel.md** | Samuels Arbeitsstil, ADHS-Praeferenzen, Plan Mode Regeln, Provider Config. Damit Claude weiss WER es gegenueber sitzt. |
| **WelcheFehlerVermeiden.md** | Top 10 Fehler aus echten Sessions. API Bug Fix Chain, Integration-Regeln. Lessons Learned die nicht verloren gehen. |
| **Skilluebersicht.md** | Alle 29 Skills mit Beschreibung, Kosten und Entscheidungsbaeumen ("Wann welchen /chef?"). Die Referenz-Tabelle. |
| **ADHD_TEMPLATE.md** | Projekt-Dashboard-Template fuer ADHS-Gehirne. Kopieren als `ADHD.md` ins Projekt-Root. Was laeuft? Was kommt? Was blockiert? |

---

## Hooks

Shell-Scripts die automatisch Context sammeln — kostet $0 in LLM-Tokens.

| Script | Was es tut |
|--------|-----------|
| **gather-context.sh** | Sammelt Projekt-Context (git status, Struktur, relevante Files) fuer Delegation. Wird von /chef automatisch aufgerufen. |
| **gather-context-enhanced.sh** | Erweiterte Version mit Keyword-Auto-Detection — findet relevante Dateien anhand der Task-Beschreibung. |
| **session-extract.sh** | Extrahiert die letzten N Nachrichten aus einer Claude Code Session (JSONL). Fuer /recap und Kontext-Bruecken. |

---

### 4. ai-Command installieren (optional)

```bash
# Repository klonen
git clone https://github.com/smlfg/MyAIGame.git
cd MyAIGame

# Commands installieren (Slash-Skills)
cp claude-code/commands/*.md ~/.claude/commands/

# CLAUDE.md installieren (Kern-Instruktionen)
cp claude-code/CLAUDE.md ~/.claude/CLAUDE.md

# Companion Files installieren
cp claude-code/companion/WieArbeitestDuMitSamuel.md ~/.claude/
cp claude-code/companion/WelcheFehlerVermeiden.md ~/.claude/
cp claude-code/companion/Skilluebersicht.md ~/.claude/
cp claude-code/companion/ADHD_TEMPLATE.md ~/.claude/

# Hooks installieren
mkdir -p ~/.claude/hooks
cp claude-code/hooks/*.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh

# settings.json — ACHTUNG: ueberschreibt bestehende Config!
# Besser: manuell die mcpServers-Section mergen
cp claude-code/settings.json ~/.claude/settings.json
```

> **Hinweis:** `settings.json` enthaelt MCP-Server-Config, Permissions und Hook-Bindings.
> Wenn du schon eine eigene `~/.claude/settings.json` hast, merge die Sections manuell statt blind zu kopieren.

### MCP Server einrichten

Das System braucht 5 MCP Server. Alle laufen ueber `npx` — kein manuelles Installieren noetig.

| Server | Paket | Funktion | Pflicht? |
|--------|-------|----------|----------|
| **opencode** | `opencode-mcp` | Code-Delegation (Sonnet) — /chef, /test, /batch | Ja |
| **gemini** | `gemini-mcp-tool` | Web-Research (Flash) — /research, /research-swarm | Ja |
| **filesystem** | `@modelcontextprotocol/server-filesystem` | Dateizugriff fuer MCP-Tools | Optional |
| **memory** | `@modelcontextprotocol/server-memory` | Persistenter Speicher zwischen Sessions | Optional |
| **github** | via `github-mcp-wrapper.sh` | GitHub API (PRs, Issues, Repos) | Optional |

**Setup:**

```bash
# Node.js muss installiert sein (npx kommt mit npm)
node --version  # >= 18 empfohlen

# OpenCode MCP braucht einen API-Key (Anthropic oder OpenRouter)
# Siehe: https://github.com/nicholasoxford/opencode-mcp

# Gemini MCP braucht einen Google AI API-Key
# Siehe: https://github.com/jmagar/gemini-mcp-tool
export GEMINI_API_KEY="dein-key"

# GitHub MCP braucht ein GitHub Token
export GITHUB_TOKEN="ghp_..."
```

Die Server starten automatisch wenn Claude Code sie braucht — kein Daemon, kein Service.

---

## bin/ Tools

Unabhaengig vom Claude Code Setup — eigenstaendige CLI-Tools.

| Tool | Was es tut |
|------|-----------|
| **ai** | Linux-Befehle erklaeren: `ai grep` → holt man-page, schickt sie an MiniMax/Ollama, zeigt Erklaerung im Terminal |
| **ai-speak** | Wie `ai`, aber mit Sprachausgabe ueber MultiKanal TTS Daemon (Edge TTS → Piper → spd-say Fallback) |

Ausfuehrliche Doku: [bin/README.md](bin/README.md)

```bash
# Installation
cp bin/ai ~/bin/ai
cp bin/ai-speak ~/bin/ai-speak
chmod +x ~/bin/ai ~/bin/ai-speak

# MiniMax API Key (schneller als lokales Ollama)
echo 'MINIMAX_API_KEY=dein-key-hier' >> ~/.env
```

---

## Repo-Struktur

```
MyAIGame/
├── README.md                              ← Du bist hier
├── bin/
│   ├── ai                                 # Linux-Befehle erklaeren
│   └── ai-speak                           # Mit Sprachausgabe
└── claude-code/
    ├── CLAUDE.md                          # Kern-Instruktionen
    ├── companion/                         # Detail-Dokumente
    │   ├── ADHD_TEMPLATE.md
    │   ├── Skilluebersicht.md
    │   ├── WelcheFehlerVermeiden.md
    │   └── WieArbeitestDuMitSamuel.md
    ├── commands/                          # 29 Slash-Skills
    │   ├── auto.md
    │   ├── batch.md
    │   ├── bigwin.md
    │   ├── ... (29 Skills total)
    │   └── validate-config.md
    ├── hooks/                             # Context-Gathering Scripts
    │   ├── gather-context.sh
    │   ├── gather-context-enhanced.sh
    │   └── session-extract.sh
    ├── scripts/
    │   └── github-mcp-wrapper.sh
    └── settings.json
```

---

## Kosten-Ranking

```
$0.00    /check-state, /validate-config, /snapshot, /setup-git
         /selfimprove, /recap, /quickwin, /checkpoint, /learn, /focus, /bigwin
$0.10    /research (Gemini Flash)
$0.25    /research-subagent (Haiku + Gemini)
$0.27    /test-crew (Gemini + OpenCode)
$0.30    /research-swarm (3x Gemini Flash)
$0.50    /explore-first (Haiku)
$0.60    /crew (CrewAI)
$0.75    /swarm (3x Haiku)
$3.00    /chef, /chef-lite, /chef-async, /test, /review, /debug-loop
$3.25    /chef-subagent (Haiku + Sonnet)
variabel /auto, /batch
```

**Faustregel:** Recherche = Gemini (~$0.10). Code = OpenCode (~$3). Strategie = Claude (~$15).

---

## Lizenz

Persoenliches Toolkit. Feel free to steal ideas.
