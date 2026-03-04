# FOR_SMLFLG.md -- The Portable AI Toolkit, Explained

> Wie man 30 AI-Skills fuer 3 verschiedene Tools baut, ohne den Verstand zu verlieren.

---

## Was ist das hier?

Stell dir vor, du hast eine Musiksammlung auf Vinyl. Klingt super, aber du willst die gleiche Musik auch im Auto (CD), beim Joggen (MP3) und in der Kueche (Streaming). Du brauchst einen Weg, deine Songs einmal zu pflegen und auf alle Formate zu verteilen.

Das ist genau was `portable/` macht -- nur mit AI-Coding-Skills statt Musik.

**Die Plattenspieler:**
- **Claude Code** -- Dein Hauptsystem. Opus orchestriert, Sonnet codet. 30 Skills, Hooks, Companion Files. Das Original-Vinyl.
- **Codex CLI** -- OpenAI's Terminal-Agent. Andere Syntax, andere Config, aber aehnliche Ideen. Die CD.
- **OpenCode** -- Open-source Agent mit Plugin-System und MCP-Support. Flexibler, aber weniger ausgereift. Der MP3-Player.

**Das Ziel:** Schreib einen Skill einmal, deploy ihn ueberall.

---

## Architektur

```
MyAIGame/
├── claude-code/              # Das Original (Vinyl)
│   ├── CLAUDE.md             # Kern-Instruktionen
│   ├── commands/             # 30 Slash-Skills
│   ├── companion/            # Detail-Dokumente
│   ├── hooks/                # Context-Gathering + Automation
│   └── settings.json         # Config + MCP + Hook-Bindings
│
└── portable/                 # Die Jukebox (spielt alles)
    ├── SPEC.md               # Universelles Format -- die Bauanleitung
    ├── FOR_SMLFLG.md         # Du bist hier
    ├── deploy.sh             # Installer -- kopiert aufs richtige Regal
    │
    ├── instructions/         # System-Instruktionen (plattformunabhaengig)
    │   ├── AGENTS.md         # Universelle Version von CLAUDE.md
    │   └── companion/        # Alle Companion Files
    │       ├── WieArbeitestDuMitSamuel.md
    │       ├── WelcheFehlerVermeiden.md
    │       ├── Skilluebersicht.md
    │       └── ADHD_TEMPLATE.md
    │
    ├── hooks/                # Portable Hooks
    │   ├── gather-context.sh          # Projekt-Context sammeln ($0 LLM-Kosten)
    │   ├── gather-context-enhanced.sh # Mit Keyword-Detection
    │   ├── session-extract.sh         # Session-Nachrichten extrahieren
    │   ├── hooks.json                 # Claude Code Hook-Bindings
    │   ├── pre_commit_tests.py        # Pre-commit via git hooks (portabel)
    │   ├── syntax_check.py            # Syntax-Pruefung nach Edits
    │   ├── post_tool_use.py           # Narration nach Tool-Calls
    │   ├── stop.py                    # Session-Ende Narration
    │   ├── codex_advisor.py           # Codex-spezifischer Advisor
    │   └── codex_session_review.py    # Codex Session-Review
    │
    ├── codex/                # Codex-spezifische Config
    │   ├── config.toml       # Codex CLI Konfiguration
    │   └── skills/           # [wird von Task #3 befuellt]
    │
    └── opencode/             # OpenCode-spezifische Config
        ├── opencode.json     # OpenCode Konfiguration + MCP
        ├── plugins/          # Hook-Aequivalente als TypeScript-Plugins
        │   ├── context-injection.ts   # System-Prompt-Erweiterung
        │   ├── post-response.ts       # Nach jeder Antwort
        │   └── on-error.ts            # Fehler-Handling
        ├── commands/         # [wird von Task #4 befuellt]
        └── skills/           # [wird von Task #4 befuellt]
```

---

## Die drei Schichten

### Schicht 1: Was ALLE teilen (95% des Werts)

**System-Instruktionen** (`AGENTS.md`) -- Die Seele des Setups. Core Principles, Delegation Architecture, Anti-Patterns, Communication Style. Das ist plattformunabhaengig, weil es VERHALTEN beschreibt, nicht TOOLS.

**Companion Files** -- Wie Samuel arbeitet, welche Fehler zu vermeiden sind, ADHD-Templates. Rein menschlich, null Tool-Abhaengigkeit.

**Context-Gathering Scripts** -- `gather-context.sh` und Freunde. Pure Bash, laufen ueberall. Sammeln Projekt-Info fuer $0.

**Die Erkenntnis:** ~95% des Werts steckt in den Instruktionen und Workflows. Die Tool-Aufrufe sind nur die letzte Meile.

### Schicht 2: Was sich unterscheidet (die 5% Reibung)

| Aspekt | Claude Code | Codex CLI | OpenCode |
|--------|-------------|-----------|----------|
| **Skill-Pfad** | `~/.claude/commands/foo.md` | `~/.codex/skills/foo/SKILL.md` | `~/.opencode/commands/foo.md` oder `~/.opencode/skills/foo/SKILL.md` |
| **Instructions** | `~/.claude/CLAUDE.md` | `~/.codex/instructions.md` | `~/.opencode/AGENTS.md` |
| **Config** | `settings.json` (JSON) | `config.toml` (TOML) | `opencode.json` (JSON) |
| **Hooks** | Native Hook-System (pre/post tool use) | Keine nativen Hooks | Plugin-System (TypeScript) |
| **MCP** | Voll unterstuetzt (5 Server) | Nicht unterstuetzt | Nativ unterstuetzt |
| **Permissions** | Allow-Liste pro Tool | `approval_policy` (suggest/auto-edit/full-auto) | `permission` (ask/auto-edit/allow) |
| **Sub-Agents** | Task tool (Haiku model) | Kein Equivalent | Separate Sessions |

### Schicht 3: Was NICHT portierbar ist

- **Voice-Integration** (`voice-smart.md`) -- Braucht VoiceMode MCP, nur in Claude Code
- **Multi-Kanal Narration** (`post_tool_use.py`, `stop.py`) -- Spricht mit localhost:7742 Daemon, Claude-Code-spezifisch
- **Codex Advisor** (`codex_advisor.py`) -- Per Definition Codex-spezifisch
- **Chrome Extension** -- Claude Code only

---

## Entscheidungslog

### Warum AGENTS.md statt CLAUDE.md als universeller Name?

CLAUDE.md ist Claude-branding. Codex liest `instructions.md`. OpenCode kann alles lesen. `AGENTS.md` ist neutral und beschreibt was es ist: Instruktionen fuer AI-Agents, egal welches Modell.

### Warum {{delegate_code()}} statt direkter MCP-Calls?

Das war die Kern-Entscheidung. Die Skills sollen INTENT beschreiben ("delegiere Code-Ausfuehrung"), nicht MECHANIK ("rufe mcp__opencode__opencode_ask auf"). Der Transpiler macht die Uebersetzung. Vorteile:

1. **Ein Skill, drei Formate** -- Schreib einmal, transpile dreimal
2. **Tool-Updates brechen nichts** -- Wenn OpenCode sein API aendert, update den Transpiler, nicht 30 Skills
3. **Lesbarkeit** -- `{{research(query)}}` ist klarer als `mcp__gemini__ask-gemini`

### Warum Flat Files fuer Claude Code, Directories fuer Codex/OpenCode?

Claude Code erwartet `~/.claude/commands/foo.md`. Punkt. Keine Subdirectories, keine SKILL.md. Codex und OpenCode erlauben Directories mit `scripts/` und `references/`. Also: der Transpiler flattened fuer Claude Code und preserviert Structure fuer den Rest.

### Warum deploy.sh statt einem Python-Installer?

- Bash ist ueberall (Linux/macOS)
- Keine Abhaengigkeiten ausser coreutils
- Samuel kann es lesen und verstehen
- `--dry-run` fuer Sicherheit, Backups automatisch

### Warum kein Transpiler in v1?

Die Skills werden manuell portiert (Tasks #3 und #4). Ein Transpiler waere over-engineering fuer 30 Files. Wenn das Toolkit auf 100+ Skills waechst oder die Community es nutzt, lohnt sich ein Transpiler. Bis dahin: SPEC.md ist die Bauanleitung, Menschen sind der Transpiler.

---

## Was portierbar ist und was nicht

### Portabilitaets-Matrix

| Feature | Claude Code | Codex CLI | OpenCode | Portabel? |
|---------|:-----------:|:---------:|:--------:|:---------:|
| System-Instruktionen | ja | ja | ja | VOLL |
| Companion Files | ja | ja | ja | VOLL |
| Delegation Skills | ja | ja | ja | VOLL (mit Tool-Mapping) |
| Research Skills | ja | teilweise | teilweise | HOCH (Fallback: WebSearch) |
| ADHD Workflow Skills | ja | ja | ja | VOLL |
| Testing Skills | ja | ja | ja | HOCH (mit Tool-Mapping) |
| Context-Gathering | ja | ja | ja | VOLL (pure Bash) |
| Pre-commit Hooks | ja | via git hooks | via plugins | HOCH |
| MCP Server Config | ja | nein | ja | TEILWEISE |
| Voice Integration | ja | nein | nein | NICHT PORTABEL |
| Hook System (native) | ja | nein | plugins | TEILWEISE |
| Narration/TTS | ja | nein | nein | NICHT PORTABEL |

### Kosten-Vergleich

| Operation | Claude Code | Codex CLI | OpenCode |
|-----------|-------------|-----------|----------|
| Research-Call | ~$0.10 (Gemini Flash) | ~$0.10 (built-in search) | ~$0.10 (web search) |
| Code-Delegation | ~$3 (Sonnet via OpenCode MCP) | ~$0.15 (o4-mini native) | ~$3 (Sonnet native) |
| Strategy/Orchestration | ~$15 (Opus) | ~$3 (o4-mini) | ~$15 (Opus) or ~$3 (Sonnet) |
| Sub-Agent Task | ~$0.25 (Haiku) | N/A | ~$3 (separate session) |

**Einsicht:** Codex ist fuer Code-Ausfuehrung drastisch guenstiger (~$0.15 vs ~$3), hat aber kein Hook-System und keine MCP-Integration. OpenCode ist am flexibelsten (Plugins + MCP), braucht aber mehr Setup.

---

## Lessons Learned

### 1. Instruktionen sind wertvoller als Tools

Die 30 Skills funktionieren, weil die CLAUDE.md/AGENTS.md dem Modell beibringt WIE es denken soll. Die Tool-Calls sind austauschbar. Die Denkweise nicht.

**Analogie:** Ein Koch mit guten Rezepten kocht gut in jeder Kueche. Die Kueche (Claude/Codex/OpenCode) ist austauschbar, die Rezepte (Instruktionen) nicht.

### 2. Hook-Systeme sind der groesste Unterschied

Claude Code hat ein ausgereiftes Hook-System (PreToolUse, PostToolUse, Stop). Codex hat nichts. OpenCode hat Plugins. Das ist die groesste Portabilitaets-Luecke.

**Workaround:** Git hooks decken Pre-commit ab. Alles andere (Narration, Session-Review) ist Claude-Code-spezifisch und lebt nur dort.

### 3. MCP ist die Zukunft, aber noch nicht ueberall

Claude Code und OpenCode sprechen MCP. Codex (noch) nicht. Langfristig wird MCP der Standard. Kurzfristig: Codex-Skills muessen ohne MCP auskommen.

### 4. ADHD-Skills sind 100% portabel

`/focus`, `/bigwin`, `/quickwin`, `/checkpoint`, `/recap` -- alles pure Markdown-Instruktionen. Kein einziger Tool-Call der plattformspezifisch ist. Das sind die universellsten Skills im ganzen Toolkit.

### 5. Der 60-Sekunden-Fallback ist ein Pattern, kein Feature

Fast jeder Delegation-Skill hat: "Wenn MCP 60s nicht antwortet, mach es direkt." Das ist kein Claude-Code-Feature, das ist ein universelles Resilience-Pattern. Funktioniert ueberall.

---

## Naechste Schritte

1. Tasks #3 und #4 abwarten (Codex/OpenCode Skill-Portierung)
2. README.md updaten mit Portable-Section
3. deploy.sh end-to-end testen auf sauberem System
4. Spaeter: Transpiler bauen wenn >50 Skills
5. Spaeter: Community-Feedback einarbeiten

---

*Gebaut mit Claude Code Agent Teams, Februar 2026.*
*Architektur: 1 Spec, 3 Targets, 30 Skills, 0 Vendor Lock-in.*
