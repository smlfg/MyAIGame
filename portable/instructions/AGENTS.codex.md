# Codex-Specific Overrides

> These instructions supplement AGENTS.md for OpenAI Codex environments.
> Codex reads this from: ~/.codex/AGENTS.md (merge with universal AGENTS.md)

---

## Environment Differences

Codex runs in a **sandboxed container** with restrictions:
- No internet access during execution (only during setup)
- No persistent MCP server connections
- File system access is limited to the project directory
- No long-running background processes

## Delegation Architecture — Codex Mapping

| Universal Tier | Codex Equivalent |
|---------------|-----------------|
| Strategy Tier | Codex orchestrator (the main agent) |
| Execution Tier | Codex itself (single-agent, no delegation needed) |
| Research Tier | Not available in sandbox -- use pre-gathered context or ask user |
| Background Tier | Not available -- Codex is single-threaded |

**Key difference:** Codex is a single-agent system. There is no delegation to cheaper models.
All work happens in the main agent. The tier-based cost optimization does not apply.

## Web Research

Codex has **no internet access** during task execution. Adapt:
- If research is needed, surface it as a question to the user
- Use only information available in the local codebase
- Do not attempt web requests or API calls to external services

## Skills Mapping

Most skills from the universal Skilluebersicht map to direct Codex actions:

| Universal Skill | Codex Equivalent |
|----------------|-----------------|
| chef / chef-lite | Just do the code change directly |
| research | Ask user for information, or read local docs |
| test | Run test commands directly: `pytest`, `npm test`, etc. |
| check-state | `pwd && ls && git status` |
| checkpoint | `git add -A && git commit -m "checkpoint: ..."` |
| recap | Write summary to SESSION_LOG.md |
| quickwin | Scan TODOs in codebase, suggest 3 small tasks |

Skills that **cannot work** in Codex:
- chef-async, chef-subagent (no background processes)
- research-swarm, swarm (no multi-agent, no internet)
- crew (no multi-agent orchestration)
- Any skill requiring MCP servers

## Plan Mode

Codex has its own planning mechanism. The universal Plan Mode workflow adapts:
1. **Context gathering** -- Read files directly (no MCP, no hooks)
2. **Exploration** -- Browse the codebase with file reads and searches
3. **Plan** -- Write plan, present to user
4. **Execute** -- Implement directly (no delegation)

## File Paths

Codex configuration location:
- Instructions: `~/.codex/AGENTS.md`
- Project-level: `.codex/AGENTS.md` in project root
- Companion files: reference via relative paths from AGENTS.md
