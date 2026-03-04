# OpenCode Port -- Porting Notes

> All 30 Claude Code skills ported to OpenCode format.
> Date: 2026-02-26

---

## Overview

| Metric | Count |
|--------|-------|
| Total skills ported | 30 |
| Simple commands (.md) | 24 |
| Complex skills (SKILL.md dir) | 6 |
| Collapsed (delegation layer removed) | 7 |
| Ported 1:1 | 17 |
| Custom plugins needed | 0 (existing plugins suffice) |

---

## 1. What Collapsed (Delegation -> Native)

The KEY INSIGHT: In Claude Code, `/chef` delegates TO OpenCode. In OpenCode itself, that delegation layer disappears -- the skill IS the instruction to the engine that was previously being delegated to.

| Skill | Claude Code | OpenCode | Notes |
|-------|-------------|----------|-------|
| **chef** | gather-context + `mcp__opencode__opencode_ask` | gather-context + execute directly | Delegation layer collapses |
| **chef-lite** | `mcp__opencode__opencode_ask` one-shot | Execute directly | Simplest collapse |
| **chef-async** | `opencode_session_create` + `opencode_message_send_async` | Create session + async send (native) | Session API stays, MCP wrapper removed |
| **chef-subagent** | Task tool (Haiku) -> MCP opencode | Create separate session | Sub-agent becomes session isolation |
| **delegate** | Complexity assessment + MCP delegation | Complexity assessment + direct execution | Routing logic preserved, delegation removed |
| **batch** | Combine tasks + `opencode_run` | Combine tasks + execute all | Same batching logic, no MCP hop |
| **auto** | Route to right delegation method | Route to right execution method | Routing preserved, delegation removed |

**What this means:** These 7 skills still exist as commands but their instructions are simplified. Instead of "call `mcp__opencode__opencode_ask` with prompt X", they say "execute task X directly". The orchestration logic (context gathering, routing, batching) is preserved.

---

## 2. What Ported Cleanly (1:1)

These skills contain no delegation -- they're pure instructions/workflows that work identically across platforms.

### Workflow / ADHS Skills
| Skill | Format | Notes |
|-------|--------|-------|
| **bigwin** | command | 1:1 port, pure ADHS coaching workflow |
| **focus** | command | 1:1 port, session focus tracking |
| **quickwin** | command | 1:1 port, task scanning + presentation |
| **recap** | command | 1:1 port, session logging |
| **checkpoint** | command | 1:1 port, git commit + celebration |
| **learn** | command | 1:1 port, post-session knowledge extraction |

### Utility Skills
| Skill | Format | Notes |
|-------|--------|-------|
| **check-state** | command | 1:1 port, system state checks |
| **review** | command | 1:1 port, code review checklist |
| **debug-loop** | command | 1:1 port, iterative debug cycle |
| **explore-first** | command | 1:1 port, explore-before-implement |
| **setup-git** | command | 1:1 port, git branch workflow |
| **snapshot** | command | 1:1 port, calls snapshot.py script |
| **validate-config** | command | 1:1 port, config validation workflow |
| **chrome-extension** | command | 1:1 port (renamed from ClaudeChromeExtension) |
| **selfimprove** | command | Adapted: references AGENTS.md instead of CLAUDE.md |

### Research Skills
| Skill | Format | Notes |
|-------|--------|-------|
| **research** | command | Adapted: uses built-in web search instead of Gemini MCP |
| **research-subagent** | command | Adapted: uses session instead of Task tool sub-agent |

---

## 3. What Uses Skills (Complex, Directory-Based)

These skills have multi-phase orchestration that benefits from the SKILL.md directory structure.

| Skill | Why complex | Key adaptations |
|-------|-------------|-----------------|
| **test** | 7-step pipeline + auto-fix loop | Executes directly instead of via MCP delegation |
| **test-crew** | 5-phase multi-agent orchestration | Sessions replace MCP sessions; web search replaces Gemini |
| **crew** | External CrewAI dependency | Minimal change -- still calls crew_unified.py |
| **swarm** | Parallel document analysis, 6 phases | Sessions replace Task sub-agents; orchestrator reads files |
| **research-swarm** | 3 parallel research perspectives | Direct web search instead of Gemini MCP |
| **voice-smart** | Voice I/O + dynamic context lookup | Marked as platform-dependent; voice API may not be available |

---

## 4. What Uses Existing Plugins

The `plugins/` directory (created by Task #5) already provides:

| Plugin | Replaces | Skills that benefit |
|--------|----------|-------------------|
| `context-injection.ts` | Claude Code's `gather-context.sh` auto-injection | chef, batch, auto |
| `post-response.ts` | Claude Code's post-response hooks | recap, checkpoint |
| `on-error.ts` | Claude Code's error handling hooks | all skills with fallback |
| `pre-commit.ts` | Claude Code's pre-commit hooks | checkpoint |

No additional custom tools (`.opencode/tools/*.ts`) were needed -- the existing plugin layer covers all hook-equivalent behavior.

---

## 5. Tool Mapping Applied

| Claude Code Tool | OpenCode Equivalent | Where Used |
|-----------------|---------------------|------------|
| `mcp__opencode__opencode_ask` | Direct execution (native) | chef, chef-lite, delegate |
| `mcp__opencode__opencode_run` | Direct execution (native) | batch, auto |
| `mcp__opencode__opencode_session_create` | `opencode_session_create` (native) | chef-async, test, test-crew |
| `mcp__opencode__opencode_message_send_async` | `opencode_message_send_async` (native) | chef-async |
| `mcp__opencode__opencode_check` | `opencode_check` (native) | chef-async |
| `mcp__opencode__opencode_review_changes` | `opencode_review_changes` (native) | chef-async, test |
| `mcp__gemini__ask-gemini` | Built-in web search | research, research-swarm, test-crew |
| `Task(model="haiku")` | Separate session or direct execution | swarm, research-subagent, chef-subagent |
| `Bash(command)` | `shell_exec(command)` | all skills with shell commands |
| `Read(path)` | `file_read(path)` | all skills with file reading |
| `Grep(pattern)` | `file_search(pattern)` | quickwin, review, voice-smart |
| `AskUserQuestion` | `user_prompt` | focus, bigwin, explore-first |

---

## 6. Path Adaptations

Scripts that reference `~/.claude/hooks/` have been updated to `~/.opencode/hooks/` by the linter/hooks porter. Key paths:

| Claude Code Path | OpenCode Path |
|-----------------|---------------|
| `~/.claude/hooks/gather-context.sh` | `~/.opencode/hooks/gather-context.sh` |
| `~/.claude/hooks/gather-context-enhanced.sh` | `~/.opencode/hooks/gather-context-enhanced.sh` |
| `~/.claude/scripts/snapshot.py` | `~/.opencode/scripts/snapshot.py` |
| `~/.claude/scripts/crew_unified.py` | `~/.opencode/scripts/crew_unified.py` |

---

## 7. File Inventory

```
opencode/
  opencode.json              # Platform config (from Task #5)
  PORTING_NOTES.md           # This file
  plugins/
    context-injection.ts     # System prompt transform (from Task #5)
    post-response.ts         # Post-response hooks (from Task #5)
    on-error.ts              # Error handling (from Task #5)
    pre-commit.ts            # Pre-commit hooks (from Task #5)
  commands/
    auto.md                  # Smart auto-routing (collapsed)
    batch.md                 # Multi-task batching (collapsed)
    bigwin.md                # ADHS anti-procrastination
    check-state.md           # Project state check
    checkpoint.md            # Git snapshot + celebration
    chef.md                  # Context-enhanced execution (collapsed)
    chef-async.md            # Background execution (collapsed)
    chef-lite.md             # Direct execution (collapsed)
    chef-subagent.md         # Isolated execution (collapsed)
    chrome-extension.md      # Chrome extension status
    debug-loop.md            # Iterative debug cycle
    delegate.md              # Smart delegation (collapsed)
    explore-first.md         # Explore before implementing
    focus.md                 # Session focus mode
    learn.md                 # Post-session learning
    quickwin.md              # Find 3 quick wins
    recap.md                 # Session summary
    research.md              # Web research
    research-subagent.md     # Background research
    review.md                # Code review
    selfimprove.md           # System instructions improvement
    setup-git.md             # Git branch setup
    snapshot.md              # Project snapshot
    validate-config.md       # Config validation
  skills/
    crew/
      SKILL.md               # CrewAI multi-agent
    research-swarm/
      SKILL.md               # 3-perspective research
    swarm/
      SKILL.md               # Document analysis swarm
    test/
      SKILL.md               # Cascading test pipeline
    test-crew/
      SKILL.md               # Multi-agent test system
    voice-smart/
      SKILL.md               # Voice + context mode
```

Total: 24 commands + 6 skills = 30 ported skills.
