# Codex CLI Porting Notes

> Documenting what ported cleanly, what has limitations, and what doesn't work at all.

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Ported cleanly (100% functional) | 17 | Full port |
| Ported with limitations | 11 | Partial port, documented workarounds |
| Not portable | 2 | Cannot work in Codex |
| **Total** | **30** | |

---

## 1. Ported Cleanly (17 skills)

These skills are pure conversational, use only basic tools (shell, file read/write, search), or map 1:1 to Codex capabilities.

| # | Skill | Category | Notes |
|---|-------|----------|-------|
| 1 | quickwin | workflow | Pure conversational + git/search. 100% portable. |
| 2 | focus | workflow | Pure conversational. 100% portable. |
| 3 | checkpoint | workflow | Git operations + file write. 100% portable. |
| 4 | recap | workflow | File write + conversation analysis. 100% portable. |
| 5 | bigwin | workflow | Pure conversational + file read/write. 100% portable. |
| 6 | learn | meta | Git + file read/write. 100% portable. |
| 7 | selfimprove | meta | File read/edit. 100% portable. |
| 8 | review | utility | Git + file read + search. 100% portable. |
| 9 | check-state | utility | Shell + file read. 100% portable. |
| 10 | validate-config | utility | Shell + file read + research. 100% portable. |
| 11 | setup-git | utility | Git operations only. 100% portable. |
| 12 | debug-loop | utility | File read + shell. 100% portable. |
| 13 | chef-lite | delegation | Direct one-shot delegation. Maps to Codex native execution. |
| 14 | chef | delegation | Context script + delegation. Script is bash, fully portable. |
| 15 | batch | delegation | Batched delegation. Same pattern works in Codex. |
| 16 | research | research | Maps to Codex `web_search` tool or MCP. |
| 17 | auto | delegation | Routing logic is pure decision-making. Delegates to other skills. |

---

## 2. Ported with Limitations (11 skills)

These skills use features that Codex handles differently or lacks native support for.

### 2.1 Async/Session Skills (limited async support)

| Skill | Limitation | Workaround |
|-------|-----------|------------|
| **chef-async** | Codex has no native async session management. No equivalent of `opencode_session_create` + `opencode_message_send_async`. | Run `codex --quiet` in background via shell. Or fall back to synchronous execution. |
| **delegate** | Session workflow (create/send/review/revert) maps partially. Codex lacks session persistence across calls. | Use one-shot execution for simple tasks. For complex tasks, use sequential shell calls. |

### 2.2 Sub-Agent Skills (no native spawning)

| Skill | Limitation | Workaround |
|-------|-----------|------------|
| **chef-subagent** | Codex has no `Task` tool equivalent for spawning background sub-agents. | Use `codex mcp-server` to create MCP threads, or run a separate `codex` process in background shell. Non-blocking behavior is limited. |
| **research-subagent** | Same as chef-subagent -- no background sub-agent spawning. | Use /research (synchronous) as simpler fallback. Or use MCP server threads. |
| **explore-first** | Parallel sub-agents for system check + research. | Run sequentially instead of parallel. Same results, just slower. |

### 2.3 Multi-Agent Orchestration Skills (significant limitations)

| Skill | Limitation | Workaround |
|-------|-----------|------------|
| **swarm** | Requires 3 parallel sub-agents for document analysis. Codex cannot spawn parallel lightweight agents. | Options: (1) MCP server threads, (2) sequential analysis passes, (3) single comprehensive analysis. Loses parallelism benefit but analysis quality is preserved. |
| **crew** | External `crew_unified.py` dependency works fine via shell. CrewAI script is independent of Codex. | No limitation on the script itself -- it manages its own LLM providers. Main concern: user must have crew_unified.py installed. |
| **research-swarm** | 3 parallel research calls in single turn. Codex cannot parallelize tool calls. | Execute 3 web_search calls sequentially. Same quality, ~3x slower. |
| **test** | Complex session-based test pipeline with fix loop. Session management is partial. | Create the test pipeline as a single extended prompt rather than session-based multi-step. Revert capability is limited -- use git stash instead. |
| **test-crew** | Multi-agent orchestration (planner/executor/analyzer/fixer). Separate research and code engines. | In Codex, all agents run in same context. Planner/analyzer use web_search, executor/fixer use native Codex execution. The orchestration pattern works but agents aren't truly isolated. |

### 2.4 Snapshot (external dependency)

| Skill | Limitation | Workaround |
|-------|-----------|------------|
| **snapshot** | Requires `snapshot.py` script at specific path. | Include fallback: manual inspection via `tree -L 2`, `git status`, config file checks. |

---

## 3. Not Portable (2 skills)

| Skill | Why | Alternative |
|-------|-----|-------------|
| **voice-smart** | Codex CLI has NO voice I/O capabilities. Voice mode requires microphone input, speech-to-text, text-to-speech. Terminal-only tool. | Use Claude Code or a voice-enabled AI interface. No Codex equivalent exists. |
| **chrome-extension** | Specific to Claude Code's Chrome Native Messaging integration. Codex has no browser extension. | Not applicable -- this is a Claude Code-only diagnostic tool. |

---

## 4. Codex-Specific Technical Notes

### 4.1 No Hook System
Codex has NO hook system (unlike Claude Code's PreToolUse/PostToolUse hooks). Skills that depend on hooks need:
- Inline logic in the skill body
- OR notes documenting the missing behavior

**Affected skills:** chef, chef-async, batch (these use gather-context hooks). Workaround: Call scripts directly via shell instead of hooks.

### 4.2 Config Format
Codex uses TOML config (not JSON like Claude Code). Provider/model configuration is different:
- Claude Code: `settings.json` with `mcpServers`, `permissions`
- Codex: `codex.toml` or environment variables

### 4.3 Sub-Agent Architecture
| Feature | Claude Code | Codex |
|---------|------------|-------|
| Background tasks | `Task(run_in_background=true, model="haiku")` | Not natively supported |
| Sub-agent spawning | `Task(subagent_type, model, prompt)` | `codex mcp-server` threads |
| Parallel execution | Multiple Task calls in one turn | Sequential only (or MCP threads) |
| Model selection | Per-agent model choice (haiku/sonnet/opus) | Single model per session |

### 4.4 Session Management
| Feature | Claude Code + OpenCode | Codex |
|---------|----------------------|-------|
| Create session | `opencode_session_create` | No persistent sessions |
| Async messages | `opencode_message_send_async` | Not supported |
| Session revert | `opencode_session_revert` | Use `git stash`/`git checkout` |
| Review changes | `opencode_review_changes` | Use `git diff` |

### 4.5 Tool Mapping Applied

| Abstract Tool | Codex Equivalent |
|--------------|-----------------|
| `{{delegate_code(prompt, dir)}}` | Codex native inline execution |
| `{{delegate_code_run(prompt, dir, timeout)}}` | `codex_run(prompt, dir)` or inline |
| `{{research(query)}}` | `web_search(query)` |
| `{{spawn_subagent(model, prompt)}}` | MCP server threads (limited) |
| `{{shell(command)}}` | `shell_exec(command)` |
| `{{read_file(path)}}` | `file_read(path)` |
| `{{write_file(path, content)}}` | `file_write(path, content)` |
| `{{edit_file(path, old, new)}}` | `file_edit(path, old, new)` |
| `{{search_files(pattern, path)}}` | `file_search(pattern, path)` |
| `{{gather_context(dir, task)}}` | `shell_exec("scripts/gather-context.sh dir task")` |
| `{{ask_user(question)}}` | `user_prompt(question)` |
| `{{voice_converse(text, opts)}}` | N/A (not supported) |
| `{{check_session(sessionId)}}` | N/A (no sessions) |
| `{{review_changes(sessionId)}}` | `shell_exec("git diff")` |
| `{{revert_session(sessionId)}}` | `shell_exec("git stash")` or `git checkout` |

---

## 5. Recommendations

### For Users
1. **Start with the 17 fully-portable skills** -- they work identically in Codex
2. **ADHS/workflow skills are 100% portable** -- use them immediately
3. **Delegation skills work well** -- chef, chef-lite, batch, auto all port cleanly
4. **Multi-agent skills need adaptation** -- expect sequential instead of parallel execution
5. **Voice and Chrome skills won't work** -- use Claude Code for those

### For Developers
1. **MCP server threads** are the best workaround for sub-agent limitations
2. **Git operations** replace session management (stash/diff instead of session revert/review)
3. **Sequential execution** replaces parallel sub-agents with minimal quality loss
4. **External scripts** (gather-context.sh, crew_unified.py, snapshot.py) work unchanged

---

## 6. File Inventory

```
codex/
  PORTING_NOTES.md          # This file
  scripts/
    gather-context.sh        # Context gathering (from hooks)
    gather-context-enhanced.sh  # Enhanced context with keyword detection
  skills/
    auto/SKILL.md
    batch/SKILL.md
    bigwin/SKILL.md
    check-state/SKILL.md
    checkpoint/SKILL.md
    chef/SKILL.md
    chef-async/SKILL.md
    chef-lite/SKILL.md
    chef-subagent/SKILL.md
    chrome-extension/SKILL.md
    crew/SKILL.md
    debug-loop/SKILL.md
    delegate/SKILL.md
    explore-first/SKILL.md
    focus/SKILL.md
    learn/SKILL.md
    quickwin/SKILL.md
    recap/SKILL.md
    research/SKILL.md
    research-subagent/SKILL.md
    research-swarm/SKILL.md
    review/SKILL.md
    selfimprove/SKILL.md
    setup-git/SKILL.md
    snapshot/SKILL.md
    swarm/SKILL.md
    test/SKILL.md
    test-crew/SKILL.md
    validate-config/SKILL.md
    voice-smart/SKILL.md
```
