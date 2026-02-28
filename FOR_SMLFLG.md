# AiSystemForVibeCoding - Das Ganze verstehen

## Was ist das hier eigentlich?

Stell dir vor, du baust dir ein Cockpit. Nicht irgendein Cockpit, sondern eines, in dem du als Pilot sitzt und eine ganze Flotte von KI-Assistenten steuerst. Jeder Assistent hat seine Spezialitat: einer kann Code schreiben, einer recherchiert im Web, einer verwaltet dein Gedachtnis, einer spricht mit GitHub, und einer kennt dein gesamtes Dateisystem.

**Das ist dieses Projekt.**

Es ist kein einzelnes Tool. Es ist ein *Orchestrierungssystem* - ein Framework, das Claude Code als strategische Zentrale nutzt und spezialisierte MCP-Server als ausfuhrende Agenten einsetzt.

## Technische Architektur

```
                    ┌─────────────────────┐
                    │    DU (der Pilot)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Claude Code       │
                    │  (Strategie-Layer)   │
                    │  - Plant             │
                    │  - Orchestriert      │
                    │  - Verifiziert       │
                    └──────────┬──────────┘
                               │ MCP Protocol (JSON-RPC)
            ┌──────────────────┼──────────────────┐
            │          │       │       │           │
     ┌──────▼──┐ ┌────▼───┐ ┌─▼──┐ ┌──▼────┐ ┌───▼────┐
     │OpenCode │ │Gemini  │ │FS  │ │Memory │ │GitHub  │
     │75 Tools │ │6 Tools │ │    │ │       │ │        │
     │Code Gen │ │Search  │ │Read│ │Store  │ │Repos   │
     │Sessions │ │Analyze │ │Write│ │Recall│ │PRs     │
     └─────────┘ └────────┘ └────┘ └───────┘ └────────┘
```

### Die Schichten

1. **Du** - Gibst die Richtung vor ("Fix den Bug", "Recherchiere MCP")
2. **Claude Code** - Versteht den Kontext, plant die Strategie, delegiert und verifiziert
3. **MCP Server** - Spezialisierte Werkzeuge, die uber ein stabiles Protokoll (JSON-RPC uber stdio) kommunizieren

### Warum MCP statt einfach Shell-Kommandos?

Gute Frage. Man konnte ja einfach `subprocess.run(["opencode", "ask", "..."])` machen. Aber:

- **Shell-Pipes sind fragil** - Ein Timeout hier, ein kaputtes Encoding dort, und alles bricht zusammen
- **MCP ist ein Protokoll** - Wie HTTP fur Webseiten, aber fur KI-Tools. Standardisiert, fehlertolerant, erweiterbar
- **Auto-Discovery** - Claude Code erkennt automatisch welche Tools verfugbar sind
- **Permissions** - Du kannst granular steuern welcher Server was darf

## Codebase-Struktur

```
AiSystemForVibeCoding/
├── bin/                    # Ausfuhrbare CLI-Skripte
│   ├── ai                  # AI Command Explainer (MiniMax + Ollama)
│   └── ai-speak            # TTS-Frontend
├── config/
│   ├── audio_prompt.md     # Prompt-Template fur Audio-Narration
│   └── default.yaml        # Konfiguration
├── plugins/
│   └── claude-hook/        # Hook-Scripts fur Claude Code
│       └── hooks/          # pre_commit_tests.py, syntax_check.py, etc.
├── src/
│   └── multikanal/         # MultiKanal TTS Daemon
│       ├── adapters/       # Output-Adapter (Audio, File, etc.)
│       ├── narration/      # AI-gestutzte Narration
│       ├── tts/            # Text-to-Speech Engines
│       ├── daemon.py       # Hauptdaemon
│       └── cli.py          # CLI Interface
├── systemd/
│   └── multikanal.service  # Systemd Service Definition
├── pyproject.toml          # Python Projekt-Config
└── README.md               # Setup-Anleitung

~/.claude/                  # Claude Code Konfiguration (NICHT im Repo!)
├── settings.json           # MCP Server + Hooks + Permissions
├── CLAUDE.md               # Globale Anweisungen (MCP-Delegation, Gemini Research, Cost-Tabelle)
├── commands/               # Slash-Commands
│   ├── chef.md             # /chef — OpenCode Delegation via MCP (Manager Mode)
│   ├── chef-async.md       # /chef-async — Async OpenCode Delegation
│   ├── chef-subagent.md    # /chef-subagent — SubAgent + MCP Delegation
│   ├── crew.md             # /crew — CrewAI (Gemini+MiniMax, braucht crew_unified.py)
│   ├── research.md         # /research — Web-Research via Gemini MCP
│   ├── research-subagent.md # /research-subagent — SubAgent Research
│   ├── delegate.md         # /delegate — Simple OpenCode MCP Delegation (Legacy)
│   ├── snapshot.md         # /snapshot — Projekt-Ubersicht
│   ├── check-state.md      # /check-state — Pre-Change Verification
│   ├── validate-config.md  # /validate-config — Config Validation
│   ├── debug-loop.md       # /debug-loop — Diagnose → Fix → Test Loop
│   ├── review.md           # /review — Code Review
│   ├── explore-first.md    # /explore-first — Parallele Exploration
│   └── setup-git.md        # /setup-git — Git Branch Workflow
└── scripts/                # Hilfsskripte
    ├── snapshot.py          # Projekt-Snapshot Generator
    ├── github-mcp-wrapper.sh # GitHub Token Injection
    └── cleanup_logs.py      # Log-Bereinigung

~/.config/opencode/commands/ # OpenCode Skills (fur OpenCode intern, NICHT Claude Code!)
├── architecture/           # System Design & Architectural Patterns
│   ├── SKILL.md
│   └── PLAN.md
├── documentation/          # Docstrings, README, API Docs
│   ├── SKILL.md
│   └── PLAN.md
├── refactoring/            # Code-Refactoring & Cleanup
│   ├── SKILL.md
│   └── PLAN.md
├── testing/                # Test Generation & Coverage
│   ├── SKILL.md
│   └── PLAN.md
└── opencode-delegation/    # Multi-Step Execution (ehem. zirkulare Referenz, bereinigt)
    └── SKILL.md
```

## Die 5 MCP-Server im Detail

### 1. OpenCode (`opencode-mcp` v1.5.0)
- **Was:** Wrapped den lokalen OpenCode AI Server (75 Tools!)
- **Wozu:** Code generieren, Sessions verwalten, Dateien durchsuchen
- **Schlusseltool:** `opencode_ask` - One-Shot Fragen an die KI
- **Voraussetzung:** OpenCode muss lokal installiert sein (`~/.opencode/bin/opencode`)

### 2. Gemini (`gemini-mcp-tool` v1.1.4)
- **Was:** Zugang zu Googles Gemini API
- **Wozu:** Web-Recherche, grosse Dokumente analysieren (riesiges Context Window)
- **Schlusseltool:** `ask-gemini`
- **Voraussetzung:** `GEMINI_API_KEY` Environment Variable

### 3. Filesystem (`@modelcontextprotocol/server-filesystem` v2026.1.14)
- **Was:** Sicherer Dateizugriff mit Sandbox
- **Wozu:** Dateien lesen/schreiben innerhalb von `/home/smlflg`
- **Voraussetzung:** Keine (offizielles MCP Package)

### 4. Memory (`@modelcontextprotocol/server-memory` v2026.1.26)
- **Was:** Persistenter Key-Value Speicher
- **Wozu:** Kontext zwischen Sessions behalten, Notizen speichern
- **Voraussetzung:** Keine

### 5. GitHub (`@modelcontextprotocol/server-github` v0.6.2)
- **Was:** GitHub API Zugriff
- **Wozu:** Repos, PRs, Issues verwalten
- **Voraussetzung:** `gh auth login` muss gemacht sein (Token wird dynamisch injiziert via `github-mcp-wrapper.sh`)

## Die Custom Commands

### Delegation Commands (MCP-basiert)

| Command | MCP Server | Was macht es? |
|---------|-----------|---------------|
| `/chef` | OpenCode | Manager Mode: Kontext sammeln → Prompt enhancen → an OpenCode MCP delegieren → verifizieren |
| `/chef-async` | OpenCode | Wie /chef, aber async — du kannst weiter chatten wahrend OpenCode arbeitet |
| `/chef-subagent` | OpenCode | SubAgent-Delegation: isolierter Kontext, non-blocking, Token-effizient |
| `/crew` | Extern | CrewAI mit Gemini+MiniMax Workern (80% gunstiger, braucht crew_unified.py) |
| `/research` | Gemini | Deep Web-Research via Gemini MCP (NICHT WebSearch!) |
| `/research-subagent` | Gemini | Non-blocking Research via SubAgent + Gemini MCP |
| `/delegate` | OpenCode | Simple OpenCode-Delegation (Legacy, bevorzuge /chef) |

### Utility Commands (keine MCP-Abhaengigkeit)

| Command | Was macht es? |
|---------|---------------|
| `/snapshot` | Generiert Projekt-Ubersicht (Dateien, Git, Sprachen) |
| `/check-state` | Pruft pwd, ls, git status vor Anderungen |
| `/validate-config` | Validiert JSON/YAML/TOML Configs mit Backup |
| `/debug-loop` | Max 5 Iterationen: Diagnose → Fix → Test |
| `/review` | Code Review der aktuellen Anderungen |
| `/explore-first` | Parallele Codebase-Exploration vor Implementierung |
| `/setup-git` | Git Branch Setup Workflow |

### Die Chef-Hierarchie (Wann welchen Command?)

```
Einfacher Task (<30s)     → /chef        (synchron, direkt)
Langer Task (>60s)        → /chef-async  (async, weiter chatten)
Isolierter Kontext nötig  → /chef-subagent (SubAgent, Token-effizient)
Multi-File, bulk work     → /crew        (CrewAI, 80% günstiger)
Web-Research              → /research    (Gemini MCP)
Research im Hintergrund   → /research-subagent (SubAgent + Gemini)
```

## Technische Entscheidungen - und warum

### Warum `npx -y` statt globaler Installation?
- **Immer die neueste Version** - kein manuelles `npm update`
- **Keine globale Verschmutzung** - Packages werden gecached, nicht global installiert
- **Portabilitat** - Auf jedem System mit Node.js sofort lauffähig

### Warum ein Wrapper-Script fur GitHub?
```bash
#!/bin/bash
export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"
exec npx -y @modelcontextprotocol/server-github "$@"
```
Der GitHub MCP Server braucht einen Token. Statt den Token hardcoded in die Config zu schreiben (Sicherheitsrisiko!), wird er dynamisch aus `gh auth token` geholt. Clever und sicher.

### Warum Commands als Markdown-Dateien?
Claude Code liest `.md` Dateien aus `~/.claude/commands/` und macht sie als `/command` verfugbar. Das ist elegant weil:
- **Versionierbar** - Du kannst die Commands in Git tracken
- **Lesbar** - Jeder kann den Command lesen und verstehen
- **Erweiterbar** - Neuer Command = neue Markdown-Datei

## Bugs und Fixes - Die Lessons Learned

### Bug 1: `opencode-mcp-tool` existiert nicht (404)
- **Problem:** Die settings.json referenzierte `opencode-mcp-tool` - ein npm Package das nicht existiert
- **Fix:** Geandert zu `opencode-mcp` (das echte Package, v1.5.0)
- **Lesson:** **IMMER `npm view <package> version` prufen bevor man ein Package in die Config schreibt.** npm gibt keine Warnung bei der Konfiguration - der Fehler tritt erst beim Starten auf.

### Bug 2: Falscher Tool-Name in `/delegate`
- **Problem:** Die `/delegate` Command referenzierte `ask-opencode` als MCP Tool
- **Fix:** Geandert zu `opencode_ask` (der tatsachliche Tool-Name des Servers)
- **Lesson:** **Tool-Namen sind package-spezifisch.** Man muss `tools/list` gegen den Server ausfuhren, um die echten Namen zu erfahren. Nie raten!

### Bug 3: MCP Server in settings.json werden NICHT geladen!
- **Problem:** Server waren in `~/.claude/settings.json` unter `mcpServers` konfiguriert, wurden aber von Claude Code **komplett ignoriert**. `claude mcp list` zeigte "No MCP servers configured."
- **Root Cause:** Claude Code liest MCP Server **nur** aus `~/.claude.json` (via `claude mcp add -s user`), NICHT aus `~/.claude/settings.json`. Das `mcpServers`-Feld in settings.json wird fur andere Zwecke genutzt oder gar nicht.
- **Fix:** Alle 5 Server mit `claude mcp add -s user` neu registriert. Danach: alle connected.
- **Lesson:** **`claude mcp add -s user` ist der EINZIGE zuverlässige Weg MCP Server hinzuzufugen.** Die settings.json ist fur permissions, hooks, und andere Einstellungen — NICHT fur MCP Server.

## Wie gute Engineers denken

### 1. "Trust but Verify"
Wir haben nicht einfach die Config geschrieben und gehofft. Wir haben:
- Jedes npm Package einzeln gepruft (`npm view`)
- Jeden MCP Server manuell gestartet und das Initialize-Handshake getestet
- Die Tool-Listen abgefragt um die echten Tool-Namen zu verifizieren

### 2. "One thing at a time"
Statt alles auf einmal zu andern, haben wir systematisch getestet:
1. Erst: Existieren die Packages?
2. Dann: Starten die Server?
3. Dann: Stimmen die Tool-Namen?
4. Dann: Funktionieren die Commands?

### 3. "Backup before modify"
Vor jeder Config-Anderung: `cp file file.backup-$(date)`. Klingt trivial, rettet Leben.

### 4. "Fehler sind Daten"
Der 404-Fehler war kein Problem - er war Information. Er hat uns zum richtigen Package gefuhrt.

## Best Practices fur die Zukunft

1. **Neuen MCP Server hinzufugen?** → Erst `npm view <package>`, dann `claude mcp add -s user <name> -- npx -y <package>`, dann neue Session starten
2. **Command referenziert MCP Tool?** → Tool-Name uber `tools/list` verifizieren, nicht raten
3. **MCP Server antwortet nicht?** → Fallback einbauen (wie `/research` es mit WebSearch macht)
4. **Neue Session nötig** → MCP Server werden beim Session-Start geladen. Config-Anderungen brauchen einen Neustart
5. **Secrets nie hardcoden** → Wrapper-Scripts oder Environment Variables nutzen (wie `github-mcp-wrapper.sh`)

## Potenzielle Fallstricke

- **OpenCode muss laufen** - Der `opencode-mcp` Server wraps die OpenCode Headless API. Wenn OpenCode nicht installiert oder nicht gestartet ist, funktioniert `/chef` nicht
- **npx Cache** - Bei erstem Start lädt npx die Packages herunter. Das kann 30-60 Sekunden dauern und sieht aus wie ein Timeout
- **Token-Ablauf** - Der GitHub Token aus `gh auth` kann ablaufen. Dann muss `gh auth refresh` gemacht werden
- **Gemini Rate Limits** - Viele Anfragen in kurzer Zeit? Gemini hat Rate Limits. Der Fallback auf WebSearch ist dein Freund

## Die grosse Migration: Shell → MCP (Februar 2026)

### Was passiert ist

Wir hatten auf dem T450s (altes System) ausgereifte Commands, die alle uber `opencode run` via Bash-Shell delegierten. Das funktionierte, war aber fragil — Shell-Pipes, Encoding-Probleme, Timeouts.

Beim Umzug auf das neue System haben wir ALLES auf MCP umgestellt:

| Vorher (T450s) | Nachher (neues System) |
|----------------|----------------------|
| `opencode run --format json "..."` via Bash | `mcp__opencode__opencode_ask(prompt="...")` |
| `nohup opencode run ... &` via Bash | `opencode_message_send_async` + `opencode_wait` |
| `gemini "PROMPT"` via Bash | `mcp__gemini__ask-gemini(prompt="...")` |
| Mehrere `opencode run ... &` parallel via Bash | Task tool mit `opencode_ask` parallel |

### Warum das wichtig ist

**Shell-basierte Delegation:**
```bash
# Fragil: Encoding, Timeouts, Zombie-Prozesse
cd ~/project && opencode run --format json "do something" 2>&1
```

**MCP-basierte Delegation:**
```
# Stabil: Typisiert, Fehlerbehandlung, Auto-Discovery
mcp__opencode__opencode_ask(prompt="do something", directory="/path")
```

Der Unterschied ist wie zwischen "jemanden anrufen und hoffen dass er rangeht" vs "eine typisierte API mit Retry-Logic aufrufen". MCP ist das Protokoll, Shell war der Hack.

### Die Erkenntnis: Skills ≠ Commands

Ein wichtiges Learning: **OpenCode Skills** (`~/.config/opencode/commands/`) und **Claude Code Commands** (`~/.claude/commands/`) sind VERSCHIEDENE Dinge:

- **Claude Code Commands** = Anweisungen fur Claude Code (den Orchestrator)
- **OpenCode Skills** = Anweisungen fur OpenCode (den Ausfuhrer)

Die Skills (architecture, documentation, refactoring, testing) laufen *innerhalb* von OpenCode und nutzen OpenCodes eigene Tools (read_file, write_file, bash). Die brauchen KEIN MCP, weil sie nicht in Claude Code laufen!

Der `opencode-delegation` Skill hatte eine zirkulare Referenz — OpenCode sollte sich selbst aufrufen via `opencode run`. Das wurde zu einem generischen `multi-step-execution` Skill umgebaut.

### Kostenvergleich: Warum Delegation sich lohnt

| Approach | Kosten/1M Tokens | Wofur |
|----------|-----------------|-------|
| Claude Code direkt (Opus) | ~$15 | Strategie, Orchestrierung, komplexes Reasoning |
| `/chef` (OpenCode/Sonnet) | ~$3 | Code-Implementierung, Refactoring |
| `/crew` (CrewAI/Gemini+MiniMax) | ~$0.60 | Multi-File, Bulk-Arbeit |
| `/research` (Gemini Flash) | ~$0.10 | Web-Research, Dokumentanalyse |

**Faustregel:** Opus denkt, Sonnet implementiert, Flash recherchiert, MiniMax macht die Drecksarbeit.

### OpenCode via MCP delegieren — ein Praxisbeispiel

Bei der Migration haben wir OpenCode uber MCP genutzt um den `opencode-delegation` Skill umzuschreiben — Meta-Delegation! Claude Code hat via `mcp__opencode__opencode_ask` den Auftrag gegeben, und OpenCode (mit MiniMax, viel gunstiger als Opus) hat die Datei umgeschrieben.

Das ist genau der Workflow, den das System ermoglicht:
1. Du sagst Claude Code was du willst
2. Claude Code plant und formuliert einen prazisen Prompt
3. OpenCode fuhrt aus (mit gunstigerem Model)
4. Claude Code verifiziert das Ergebnis

## Fragen zum Nachdenken

1. **Wann lohnt sich Delegation?** Ab welcher Aufgabenkomplexitat sparst du mehr Geld durch Delegation an gunstigere Modelle, als du durch den Overhead der Orchestrierung verlierst?

2. **MCP vs Shell:** Warum ist ein typisiertes Protokoll besser als Shell-Pipes? Was passiert wenn dein JSON Output ein unescaped Quote enthalt?

3. **Skills vs Commands:** Wenn du ein neues Feature zu deinem Workflow hinzufugen willst — wie entscheidest du ob es ein Claude Code Command oder ein OpenCode Skill werden soll?

4. **Fallback-Strategien:** Was passiert wenn Gemini nicht antwortet? Was wenn OpenCode einen Timeout hat? Hast du fur jeden kritischen Pfad einen Plan B?

5. **Token-Budgets:** Wenn du 100$ pro Monat fur KI hast — wie verteilst du das optimal zwischen Opus (teuer, schlau), Sonnet (mittel), und Flash/MiniMax (billig)?
