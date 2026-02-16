# Claude System Instructions

## Core Principles

Before making changes, always check existing state first: run `pwd`, `ls`, `tree`, or `git branch` to understand the current directory structure, existing files, and branch layout before proposing or executing any changes.

## Approach Guidelines

- ALWAYS verify config formats by reading actual files/docs BEFORE making changes
- NEVER guess at config schemas — read existing configs, check documentation
- Start with the SIMPLEST possible solution, no over-engineering
- If something works, don't "improve" it unless asked

## Before Modifying Anything

1. READ the existing file completely
2. RESEARCH what options/formats are valid
3. BACKUP before editing: `cp config.json config.json.backup-$(date +%Y%m%d-%H%M%S)`
4. Test changes in isolation
5. Respect error messages — they usually tell you exactly what's wrong

## System Environment

This system runs Pop!_OS with COSMIC desktop environment (NOT GNOME). When configuring system settings, shortcuts, display, or audio, always use COSMIC-compatible tools and approaches. Never assume GNOME settings/gsettings will work. Display server is Wayland — do not use X11-only tools like xrandr.

## Languages & Gotchas

Primary languages: Python, Shell/Bash, YAML, Markdown. When writing Bash scripts, be careful with: subshell variable scoping, locale-dependent decimal separators, /dev/tty vs stdin handling, and array operations. Test edge cases before declaring done.

## Integration Work

When implementing multi-step system integrations (TTS pipelines, hooks, audio chains), make changes incrementally and test after each step. Do NOT change multiple components simultaneously — race conditions, overlapping processes, and pipe logic errors are common.

## Delegation Architecture

Claude Code is the **strategy & orchestration layer**. Use MCP servers for specialized tool access:

| Layer | Role | Tool |
|-------|------|------|
| Strategy | Planning, architecture, orchestration | Claude Code |
| Protocol | Stable communication, error handling | MCP |
| Execution | Code generation, file changes | OpenCode (via MCP) |
| Research | Web search, documentation | Gemini (via MCP) |
| Infrastructure | Files, git, memory | MCP filesystem/github/memory |

**Rules:**
- Use MCP tools for structured access (no shell subprocess hacks)
- If an MCP tool stalls >60s, fall back to doing it directly
- Always gather context BEFORE delegating — never send blind tasks
- Verify delegation results — trust but verify

## Web Research = Gemini MCP

**For ALL web research, use Gemini via MCP** (`mcp__gemini__ask-gemini`), NOT the built-in WebSearch tool.

**Why?**
- Gemini can browse and read full web pages, not just search result snippets
- Gemini synthesizes information across multiple sources
- Gemini has a massive context window for analyzing large documents
- WebSearch is only a fallback if Gemini MCP is unavailable

**Fallback chain:** Gemini MCP → WebSearch → Own knowledge (with caveat about dates)

## Commands Overview

| Command | Type | What it does |
|---------|------|-------------|
| `/chef` | Coding (MCP) | Delegate task to OpenCode with enhanced prompting |
| `/chef-async` | Coding (MCP) | Async delegation — continue chatting while OpenCode works |
| `/chef-subagent` | Coding (MCP) | SubAgent delegation — isolated context, non-blocking |
| `/crew` | Coding (External) | CrewAI orchestration with Gemini+MiniMax workers (needs crew_unified.py) |
| `/research` | Research (MCP) | Deep web research via Gemini MCP |
| `/research-subagent` | Research (MCP) | Non-blocking research via Gemini SubAgent |
| `/delegate` | Coding (MCP) | Simple OpenCode delegation (legacy, prefer /chef) |
| `/snapshot` | Utility | Generate project overview |
| `/check-state` | Utility | Check pwd, ls, git status before changes |
| `/validate-config` | Utility | Validate config files with backup |
| `/debug-loop` | Utility | Max 5 iterations: diagnose → fix → test |
| `/review` | Utility | Code review of current changes |
| `/explore-first` | Utility | Parallel codebase exploration before implementation |
| `/test` | Testing (MCP) | Cascading test pipeline via OpenCode with auto-fix and ISTQB classification |
| `/test-crew` | Testing (Multi-Agent) | Multi-agent tests: Gemini plans/analyzes, OpenCode executes/fixes |
| `/setup-git` | Utility | Git branch setup workflow |

## Cost Awareness

| Approach | Cost/1M tokens | Best for |
|----------|----------------|----------|
| Claude Code direct | ~$15 (Opus) | Strategy, orchestration, complex reasoning |
| `/chef` (OpenCode MCP) | ~$3 (Sonnet) | Code implementation, refactoring |
| `/crew` (CrewAI) | ~$0.60 (Gemini+MiniMax) | Multi-file changes, bulk work |
| `/test` (OpenCode MCP) | ~$3 (Sonnet) | Single-agent test pipeline with auto-fix |
| `/test-crew` (Multi-Agent) | ~$0.27 (Gemini+OpenCode) | Multi-agent test pipeline (cheapest) |
| `/research` (Gemini) | ~$0.10 (Flash) | Web research, doc analysis |

**Rule of thumb:** Delegate execution to cheaper models. Keep strategy at Claude Code.

## File Operations

- ALWAYS exclude from operations: `venv/`, `node_modules/`, `.git/`, `__pycache__/`, `.venv/`
- Estimate file count/size before large operations (use `du -sh`, `find | wc -l`)
- Never recursively delete without confirming scope first

## Git Workflow

When tasks involve Git operations, always confirm the branching strategy with the user first. Create branches independently from main unless explicitly told otherwise. Run `git branch -a` and `git log --oneline --graph` before any branch operations.

## Communication Style

When providing coaching, explanations, or guidance, use an inspiring and motivating tone. Avoid cold, clinical, or overly scripted responses. Explain reasoning rather than just giving commands to copy-paste.

## Anti-Patterns (Things That Waste Tokens & Time)

- **No meta-vibecoding without foundations** — don't build AI pipelines before the basic code works
- **No long-running silent processes** — always log progress, never go dark
- **One task, one session, complete it** — don't context-switch mid-task
- **Token budget awareness** — be concise, don't repeat yourself, don't explain what you're about to do AND then do it
- **No subprocess delegation via shell** — use MCP tools instead (stable protocol > fragile pipes)

## Project Documentation

For every project, write a detailed `FOR_SMLFLG.md` file that explains the whole project in plain language.

Include:
- **Technical architecture** - how the system is designed
- **Codebase structure** - how files and folders are organized and connected
- **Technologies used** - what tools, frameworks, libraries are involved
- **Technical decisions** - why we chose this approach over alternatives
- **Lessons learned**:
  - Bugs we ran into and how we fixed them
  - Potential pitfalls and how to avoid them
  - New technologies explored
  - How good engineers think and work
  - Best practices discovered
  - use tree and ls bevor doing anything
  - use cat to read documents!
  - give the user questions to answer

**Style**: Make it engaging to read - not boring technical documentation. Use analogies and anecdotes where appropriate to make concepts understandable and memorable.

**Learning**: I need you to help me get more Wisdom and more knowledge
"For every project, write a detailed FOR[yourname].md file that explains the whole project in plain language.
Explain the technical architecture, the structure of the codebase and how the various parts are connected, the technologies used, why we made these technical decisions, and lessons I can learn from it (this should include the bugs we ran into and how we fixed them, potential pitfalls and how to avoid them in the future, new technologies used, how good engineers think and work, best practices, etc).
It should be very engaging to read; don't make it sound like boring technical documentation/textbook. Where appropriate, use analogies and anecdotes to make it more understandable and memorable."
