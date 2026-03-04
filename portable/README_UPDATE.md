# Portable Setup

> One source, three targets. Write your AI workflow once, deploy to Claude Code, Codex CLI, and OpenCode.

---

## What Is This?

The `portable/` directory contains a **tool-agnostic version** of the entire MyAIGame toolkit. Instead of being locked to Claude Code, all instructions, skills, hooks, and configs are written in a universal format and deployed to whichever AI coding tool you use.

```
portable/                          # The universal source of truth
├── SPEC.md                        # Universal skill format specification
├── COMPATIBILITY.md               # What works where (detailed matrix)
├── deploy.sh                      # Interactive installer
├── instructions/                  # System instructions (AGENTS.md)
│   ├── AGENTS.md                  # Universal agent instructions
│   ├── AGENTS.codex.md            # Codex-specific overrides
│   ├── AGENTS.opencode.md         # OpenCode-specific overrides
│   └── companion/                 # Companion documents (all portable)
│       ├── ADHD_TEMPLATE.md
│       ├── Skilluebersicht.md
│       ├── WelcheFehlerVermeiden.md
│       └── WieArbeitestDuMitSamuel.md
├── hooks/                         # Shared scripts (bash + python)
├── codex/                         # Codex-specific config + skills
│   ├── config.toml
│   └── skills/
└── opencode/                      # OpenCode-specific config + plugins
    ├── opencode.json
    └── plugins/
```

## Supported Tools

| Tool | Version | Instruction File | Skills Location | Hooks |
|------|---------|-----------------|----------------|-------|
| **Claude Code** | Any | `~/.claude/CLAUDE.md` | `~/.claude/commands/*.md` | Native hooks in `settings.json` |
| **Codex CLI** | >= 0.1 | `~/.codex/instructions.md` | `~/.codex/skills/<name>/SKILL.md` | Git hooks only (no native hook system) |
| **OpenCode** | >= 0.1 | `~/.opencode/AGENTS.md` | `~/.opencode/commands/*.md` + `skills/` | Experimental plugins (`.ts`) |

## Quick Install

### Option A: Interactive Installer (Recommended)

```bash
cd portable/
./deploy.sh              # Detects installed tools, asks what to deploy
./deploy.sh --dry-run    # Preview what would happen, change nothing
```

### Option B: Deploy to a Specific Tool

```bash
./deploy.sh --target claude    # Deploy to Claude Code only
./deploy.sh --target codex     # Deploy to Codex CLI only
./deploy.sh --target opencode  # Deploy to OpenCode only
./deploy.sh --target all       # Deploy to all three
```

### Option C: Manual Install

**Claude Code:**
```bash
cp portable/instructions/AGENTS.md ~/.claude/CLAUDE.md
cp portable/instructions/companion/*.md ~/.claude/
cp portable/hooks/*.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/*.sh
```

**Codex CLI:**
```bash
cp portable/instructions/AGENTS.md ~/.codex/instructions.md
cp portable/codex/config.toml ~/.codex/config.toml
cp -r portable/codex/skills/ ~/.codex/skills/
```

**OpenCode:**
```bash
cp portable/instructions/AGENTS.md ~/.opencode/AGENTS.md
cp portable/opencode/opencode.json ~/.opencode/opencode.json
cp -r portable/opencode/plugins/ ~/.opencode/plugins/
```

The installer backs up existing files automatically (timestamped `.backup-YYYYMMDD-HHMMSS` suffix).

## Compatibility Overview

### Fully Portable (works identically everywhere)

- **System instructions** -- AGENTS.md core principles, anti-patterns, error avoidance
- **ADHS workflows** -- focus, quickwin, checkpoint, recap, bigwin, learn
- **Companion files** -- WieArbeitestDuMitSamuel.md, WelcheFehlerVermeiden.md, ADHD_TEMPLATE.md
- **Context-gathering hooks** -- gather-context.sh, gather-context-enhanced.sh
- **Git workflows** -- setup-git, review, commit patterns

### Partially Portable (works with limitations)

| Feature | Limitation |
|---------|-----------|
| **Delegation skills** (chef, chef-async, etc.) | Codex is single-agent -- delegation becomes direct execution |
| **Research skills** | Codex has no internet in sandbox -- user provides research context |
| **Pre-commit hooks** | Codex uses git hooks (not native); OpenCode plugins are experimental |
| **Multi-agent orchestration** (crew, swarm) | Codex cannot spawn sub-agents; OpenCode uses separate sessions |

### Not Portable

| Feature | Why |
|---------|-----|
| **MCP servers** (Gemini, OpenCode, filesystem, memory) | Codex has no MCP support |
| **Voice/narration hooks** (post_tool_use.py, stop.py) | Requires MultiKanalAgent daemon |
| **Session-end hooks** (stop.py) | OpenCode has no session-end event |
| **Codex second-opinion** (codex_advisor.py) | This IS the cross-tool integration -- runs FROM Claude Code |

For the full compatibility matrix, see [COMPATIBILITY.md](portable/COMPATIBILITY.md).

## Cost Comparison Across Providers

The toolkit uses a **tier-based cost model** that abstracts away specific model names. Map your preferred provider to each tier:

| Tier | Role | Claude/Anthropic | OpenAI | Open Source |
|------|------|-----------------|--------|-------------|
| **Strategy** | Planning, orchestration | Opus (~$15/1M) | o1/GPT-4o (~$15/1M) | Llama 405B (self-hosted) |
| **Execution** | Code generation, refactoring | Sonnet (~$3/1M) | GPT-4o-mini (~$0.60/1M) | Qwen 2.5 Coder, DeepSeek |
| **Research** | Web research, fact-checking | -- | -- | Gemini Flash (~$0.10/1M) |
| **Background** | Parallel sub-tasks | Haiku (~$0.25/1M) | GPT-4o-mini (~$0.60/1M) | Any fast local model |

**Key insight:** The strategy tier is 150x more expensive than research. Never use strategy-tier models for fact-checking or web research. The skill system enforces this by routing research tasks to the cheapest available model.

### Per-Skill Cost Tiers

```
Free         check-state, validate-config, snapshot, setup-git, selfimprove,
             recap, quickwin, checkpoint, learn, focus, bigwin
Research     research (~$0.10)
Background   research-subagent, explore-first (~$0.25-0.50)
Mixed        crew, test-crew, research-swarm (~$0.27-0.60)
Execution    chef, chef-lite, chef-async, test, review, debug-loop (~$3)
```

## Architecture: How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    portable/ (Universal Source)               │
│                                                              │
│  AGENTS.md ─────────┬──────────────┬────────────────────┐   │
│  companion/          │              │                    │   │
│  hooks/              │              │                    │   │
│  SPEC.md             │              │                    │   │
│                      ▼              ▼                    ▼   │
│              ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│              │  Claude  │   │  Codex   │   │  OpenCode    │ │
│              │  Code    │   │  CLI     │   │              │ │
│              │          │   │          │   │              │ │
│              │ CLAUDE.md│   │instruct. │   │ AGENTS.md    │ │
│              │ commands/│   │  .md     │   │ commands/    │ │
│              │ hooks/   │   │ skills/  │   │ plugins/     │ │
│              │ settings │   │ config   │   │ opencode     │ │
│              │  .json   │   │  .toml   │   │  .json       │ │
│              └──────────┘   └──────────┘   └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

The `deploy.sh` script handles the mapping:
- **AGENTS.md** becomes `CLAUDE.md` (Claude Code), `instructions.md` (Codex), or stays `AGENTS.md` (OpenCode)
- **Skills** become flat `.md` commands (Claude Code), directory-based skills (Codex), or commands/skills (OpenCode)
- **Hooks** become native hooks (Claude Code), git hooks (Codex), or TypeScript plugins (OpenCode)
- **Config** becomes `settings.json` (Claude Code), `config.toml` (Codex), or `opencode.json` (OpenCode)

For the full universal skill format specification, see [SPEC.md](portable/SPEC.md).
