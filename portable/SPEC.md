# Universal Skill Format Specification v1.0

> Intermediate representation for AI coding assistant skills that transpile to
> Claude Code, Codex CLI, and OpenCode.

---

## 1. File Layout

```
skills/
  <skill-name>/
    SKILL.md          # The universal skill definition (required)
    scripts/          # Helper scripts referenced by the skill (optional)
    references/       # Static reference docs bundled with the skill (optional)
    assets/           # Images, templates, config snippets (optional)
```

**Naming convention:** `<skill-name>` is lowercase, kebab-case. Example: `chef-async`, `research-swarm`, `debug-loop`.

**Why a directory instead of a flat file?** Claude Code uses flat `.md` files today, but Codex and OpenCode both support companion directories. The transpiler flattens for Claude Code and preserves structure for the others.

---

## 2. Frontmatter Schema

Every `SKILL.md` starts with YAML frontmatter between `---` fences.

```yaml
---
# REQUIRED
name: chef-async
description: "Delegate task to OpenCode ASYNC via MCP - continue chatting while it runs"

# OPTIONAL — enrichments for routing, cost estimation, and filtering
argument-hint: "[task description]"
category: delegation          # See Section 2.1
cost-tier: low                # See Section 2.2
dependencies:                 # See Section 2.3
  tools: [delegate_code, shell]
  scripts: ["gather-context.sh"]
  external: []                # e.g. ["crew_unified.py"]
tags: [async, non-blocking, opencode]
---
```

### 2.1 Categories

| Category        | Description                              | Examples                          |
|-----------------|------------------------------------------|-----------------------------------|
| `delegation`    | Route work to execution engines          | chef, chef-lite, delegate, auto, batch |
| `research`      | Web research and information gathering   | research, research-subagent, research-swarm |
| `testing`       | Test orchestration and validation        | test, test-crew                   |
| `multi-agent`   | Coordinate multiple agents              | crew, swarm                       |
| `workflow`      | Session management and ADHD support     | focus, bigwin, quickwin, checkpoint, recap |
| `utility`       | System checks, config, git              | check-state, review, validate-config, snapshot, setup-git |
| `meta`          | Self-improvement and learning           | selfimprove, learn                |
| `voice`         | Voice interaction modes                 | voice-smart                       |

### 2.2 Cost Tiers

| Tier       | Estimated Cost   | Typical Pattern                          |
|------------|------------------|------------------------------------------|
| `free`     | $0               | Direct response, no tool calls           |
| `minimal`  | < $0.05          | Single cheap tool call                   |
| `low`      | $0.05 - $0.30    | 1-2 MCP calls or 1 research call         |
| `medium`   | $0.30 - $1.00    | Multi-step orchestration                 |
| `high`     | $1.00 - $5.00    | Full agent crew or deep analysis         |
| `variable` | Depends on input | Scales with input size (e.g., swarm)     |

### 2.3 Dependencies

```yaml
dependencies:
  tools:                  # Abstract tool capabilities required
    - delegate_code       # Needs a code execution engine
    - research            # Needs a research/web search engine
    - spawn_subagent      # Needs sub-agent spawning
    - shell               # Needs shell command execution
    - file_read           # Needs file reading
    - file_write          # Needs file writing
    - file_search         # Needs file/content search
    - voice               # Needs voice I/O
    - git                 # Needs git operations
  scripts:                # Helper scripts from scripts/ directory
    - "gather-context.sh"
    - "gather-context-enhanced.sh"
  external:               # External dependencies not bundled
    - "crew_unified.py"   # Must exist at specific path
```

---

## 3. Body Structure

The body after frontmatter is Markdown. It follows a loose but recognizable structure:

```markdown
# /<skill-name> -- <short tagline>

<1-2 sentence description of what this skill does and the agent's role.>

**<Primary input label>:** $ARGUMENTS

---

## Process / Steps / Phases

### Phase 1: <Name>
<Instructions for this phase>

### Phase 2: <Name>
<Instructions for this phase>

---

## Rules
- <Hard constraint 1>
- <Hard constraint 2>

## Anti-Patterns
- **NEVER** <thing to avoid>
- **NEVER** <another thing>

## Fallback
1. <Primary approach>
2. <Fallback if primary fails>
3. <Last resort>

## Error Handling
- <Error condition>: <Recovery action>
```

### 3.1 Body Elements

| Element            | Required | Description                                    |
|--------------------|----------|------------------------------------------------|
| Title + tagline    | YES      | `# /<name> -- <tagline>`                       |
| Role statement     | YES      | What the agent becomes when this skill activates |
| `$ARGUMENTS`       | YES      | Placeholder for user input                     |
| Process/Steps      | YES      | The main instruction sequence                  |
| Rules              | RECOMMENDED | Hard constraints                            |
| Anti-Patterns      | RECOMMENDED | Explicit "never do this" list               |
| Fallback chain     | OPTIONAL | Graceful degradation when tools fail           |
| Error Handling     | OPTIONAL | Recovery from specific error conditions        |
| Output format      | OPTIONAL | Template for the skill's output                |
| Cost table         | OPTIONAL | Breakdown of expected costs                    |

### 3.2 The `$ARGUMENTS` Placeholder

In the body, `$ARGUMENTS` is replaced with the user's input when the skill is invoked. This is universal across all three targets:

| Target       | Syntax in source   | Runtime replacement              |
|--------------|--------------------|---------------------------------|
| Claude Code  | `$ARGUMENTS`       | Injected by Claude Code runtime  |
| Codex CLI    | `$ARGUMENTS`       | Injected by Codex skill loader   |
| OpenCode     | `$ARGUMENTS`       | Injected by OpenCode command system |

---

## 4. Tool Abstractions

The core innovation: skills reference **abstract capabilities** instead of tool-specific APIs. The transpiler maps these to the correct tool call for each target.

### 4.1 Abstract Tool Syntax

In the skill body, tool calls are written as:

```
{{tool_name(param1, param2, ...)}}
```

### 4.2 Tool Mapping Table

| Abstract Tool                          | Claude Code                                 | Codex CLI                        | OpenCode                                |
|---------------------------------------|---------------------------------------------|----------------------------------|-----------------------------------------|
| `{{delegate_code(prompt, dir)}}`      | `mcp__opencode__opencode_ask(prompt, directory)` | `codex_run(prompt, dir)` or inline execution | `opencode_ask(prompt, directory)` |
| `{{delegate_code_async(prompt, dir)}}` | `opencode_session_create` + `opencode_message_send_async` | `codex_run_async(prompt, dir)` | `opencode_session_create` + `opencode_message_send_async` |
| `{{delegate_code_session(title, dir)}}` | `opencode_session_create(title)` | `codex_session_create(title)` | `opencode_session_create(title)` |
| `{{delegate_code_run(prompt, dir, timeout)}}` | `mcp__opencode__opencode_run(prompt, dir, maxDurationSeconds)` | `codex_run(prompt, dir, timeout)` | `opencode_run(prompt, dir, maxDurationSeconds)` |
| `{{research(query)}}`                | `mcp__gemini__ask-gemini(query)`            | `web_search(query)` or MCP research | `web_search(query)` or MCP research |
| `{{spawn_subagent(model, prompt)}}`   | `Task(model, prompt, run_in_background)` | `codex_spawn(model, prompt)` | `opencode_session_create` + `opencode_message_send` |
| `{{shell(command)}}`                  | `Bash(command)`                             | `shell_exec(command)` | `shell_exec(command)` |
| `{{read_file(path)}}`                | `Read(path)`                                | `file_read(path)` | `file_read(path)` |
| `{{write_file(path, content)}}`      | `Write(path, content)`                      | `file_write(path, content)` | `file_write(path, content)` |
| `{{edit_file(path, old, new)}}`      | `Edit(path, old, new)`                      | `file_edit(path, old, new)` | `file_edit(path, old, new)` |
| `{{search_files(pattern, path)}}`    | `Grep(pattern, path)`                       | `file_search(pattern, path)` | `file_search(pattern, path)` |
| `{{glob_files(pattern, path)}}`      | `Glob(pattern, path)`                       | `file_glob(pattern, path)` | `file_glob(pattern, path)` |
| `{{gather_context(dir, task)}}`      | `Bash("~/.claude/hooks/gather-context.sh dir task")` | `scripts/gather-context.sh dir task` | `scripts/gather-context.sh dir task` |
| `{{ask_user(question)}}`            | `AskUserQuestion(question)` | `user_prompt(question)` | `user_prompt(question)` |
| `{{voice_converse(text, opts)}}`     | `mcp__voicemode__converse(text, opts)` | N/A (not supported) | N/A (not supported) |
| `{{check_session(sessionId)}}`       | `mcp__opencode__opencode_check(sessionId)` | `codex_check(sessionId)` | `opencode_check(sessionId)` |
| `{{review_changes(sessionId)}}`      | `mcp__opencode__opencode_review_changes(sessionId)` | `codex_review(sessionId)` | `opencode_review_changes(sessionId)` |
| `{{revert_session(sessionId)}}`      | `mcp__opencode__opencode_session_revert(sessionId)` | `codex_revert(sessionId)` | `opencode_session_revert(sessionId)` |

### 4.3 Inline vs. Descriptive Tool References

Skills can reference tools in two ways:

**Inline** (for simple, single-step calls):
```markdown
Call {{research("best practices for React state management 2026")}} and present findings.
```

**Descriptive** (for complex orchestration — the skill describes intent, the agent maps to tools):
```markdown
Send the test plan to the execution engine:
{{delegate_code(prompt="""
Run each test step and report results.
## Test Plan
[Paste Planner's output here]
""", dir=project_path)}}
```

**Raw passthrough** (when the skill needs target-specific syntax):
```markdown
<!-- target:claude-code -->
Call `mcp__opencode__opencode_session_create(title="Test Pipeline")`
<!-- target:codex -->
Call `codex_session_create(title="Test Pipeline")`
<!-- target:opencode -->
Call `opencode_session_create(title="Test Pipeline")`
<!-- /target -->
```

Use raw passthrough sparingly. The abstract tools should cover 90%+ of cases.

---

## 5. Agent Abstractions

Skills that orchestrate multiple agents use abstract agent patterns:

### 5.1 Agent Roles

```yaml
agents:
  - role: planner
    engine: research        # Maps to: Gemini Flash / web search
    description: "Analyze codebase, generate test plan"
  - role: executor
    engine: code            # Maps to: OpenCode / Codex
    description: "Run all test steps"
  - role: analyzer
    engine: research        # Maps to: Gemini Flash / web search
    description: "Categorize failures, root cause analysis"
```

### 5.2 Agent Mapping

| Abstract Engine  | Claude Code                        | Codex CLI              | OpenCode                   |
|------------------|------------------------------------|------------------------|-----------------------------|
| `research`       | `mcp__gemini__ask-gemini`          | Built-in web search    | Built-in web search or MCP  |
| `code`           | OpenCode MCP session               | Codex execution        | OpenCode session            |
| `subagent`       | Task tool (Haiku model)            | Codex sub-process      | Separate OpenCode session   |
| `orchestrator`   | Claude Code main thread (Opus)     | Codex main thread      | OpenCode main thread        |

---

## 6. Fallback Chain Pattern

A recurring pattern across skills. Standardized:

```markdown
## Fallback

1. **Primary:** {{research(query)}} — cheapest, fastest
2. **Secondary:** {{shell("web_search_cli query")}} — if primary stalls >60s
3. **Tertiary:** Use own knowledge — note: may be outdated, caveat to user

Tell the user which fallback was triggered.
```

The transpiler maps the abstract fallback to target-specific tool chains:

| Fallback Level | Claude Code               | Codex CLI            | OpenCode              |
|----------------|---------------------------|----------------------|-----------------------|
| Primary        | Gemini MCP                | Built-in search      | Built-in search / MCP |
| Secondary      | WebSearch tool             | `curl` + parse       | WebSearch tool         |
| Tertiary       | Own knowledge + caveat    | Own knowledge        | Own knowledge          |

For code execution fallbacks:

| Fallback Level | Claude Code                 | Codex CLI           | OpenCode              |
|----------------|-----------------------------|--------------------|------------------------|
| Primary        | OpenCode MCP                | Codex native        | OpenCode native        |
| Secondary      | Direct Bash execution       | Direct shell        | Direct shell           |

---

## 7. Target-Specific Transpilation

### 7.1 Claude Code Output

```
.claude/commands/<skill-name>.md
```

- Flat file, no directory structure
- Frontmatter: only `description` and `argument-hint` (other fields stripped)
- Abstract tools expanded to full `mcp__*` calls
- Scripts referenced by absolute path (`~/.claude/hooks/...`)
- `$ARGUMENTS` preserved as-is

### 7.2 Codex CLI Output

```
.codex/skills/<skill-name>/
  SKILL.md
  scripts/       (if any)
  references/    (if any)
```

- Full directory structure preserved
- Frontmatter: `name`, `description` (other fields in metadata comment)
- Abstract tools mapped to Codex equivalents
- Scripts copied to `scripts/` subdirectory
- `$ARGUMENTS` preserved as-is

### 7.3 OpenCode Output

Skills become either **skills** or **commands** depending on complexity:

**Simple skills (no orchestration):**
```
.opencode/commands/<skill-name>.md
```

**Complex skills (multi-agent, sessions):**
```
.opencode/skills/<skill-name>/
  SKILL.md
  scripts/       (if any)
```

- Frontmatter: `name`, `description`
- Abstract tools mapped to OpenCode equivalents
- `$ARGUMENTS` preserved as-is
- Complex orchestration may additionally generate `.opencode/tools/<skill-name>.ts` for native tool integration

---

## 8. Skill Classification Matrix

Analysis of all 30 source skills classified by their universal properties:

| # | Skill               | Category     | Cost  | Tools Used                       | Has Fallback | Has Anti-Patterns | Complexity |
|---|---------------------|-------------|-------|----------------------------------|-------------|-------------------|------------|
| 1 | auto                | delegation  | variable | delegate_code, research, shell | No          | No                | routing    |
| 2 | batch               | delegation  | low    | delegate_code_run, shell        | No          | No                | simple     |
| 3 | bigwin              | workflow    | free   | file_read, file_write           | No          | No                | simple     |
| 4 | check-state         | utility     | free   | shell, file_read                | No          | No                | simple     |
| 5 | checkpoint          | workflow    | free   | shell (git)                     | No          | No                | simple     |
| 6 | chef                | delegation  | low    | delegate_code_run, shell        | Yes (60s)   | Yes               | medium     |
| 7 | chef-async          | delegation  | low    | delegate_code_async, shell      | Yes (60s)   | No                | medium     |
| 8 | chef-lite           | delegation  | minimal| delegate_code                   | Yes (60s)   | No                | simple     |
| 9 | chef-subagent       | delegation  | low    | spawn_subagent, delegate_code   | No          | No                | medium     |
| 10| ChromeExtension     | utility     | free   | shell                           | No          | No                | simple     |
| 11| crew                | multi-agent | high   | shell (external script)         | No          | No                | complex    |
| 12| debug-loop          | utility     | variable| file_read, shell               | No          | No                | iterative  |
| 13| delegate            | delegation  | low    | delegate_code, file_read        | Yes (60s)   | Yes               | medium     |
| 14| explore-first       | utility     | low    | spawn_subagent                  | No          | No                | simple     |
| 15| focus               | workflow    | free   | file_write                      | No          | No                | simple     |
| 16| learn               | meta        | free   | shell (git), file_read, file_write | No       | No                | simple     |
| 17| quickwin            | workflow    | free   | shell (git), search_files       | No          | No                | simple     |
| 18| recap               | workflow    | free   | file_write                      | No          | No                | simple     |
| 19| research            | research    | low    | research                        | Yes (60s)   | No                | simple     |
| 20| research-subagent   | research    | low    | spawn_subagent, research        | No          | No                | medium     |
| 21| research-swarm      | research    | medium | research (x3 parallel)          | Yes         | Yes               | complex    |
| 22| review              | utility     | free   | shell, file_read, search_files  | No          | No                | simple     |
| 23| selfimprove         | meta        | free   | file_read, edit_file            | No          | No                | simple     |
| 24| setup-git           | utility     | free   | shell (git)                     | No          | No                | simple     |
| 25| snapshot            | utility     | free   | shell (script)                  | No          | No                | simple     |
| 26| swarm               | multi-agent | variable| spawn_subagent (x3+), file_read| Yes         | Yes               | complex    |
| 27| test                | testing     | medium | delegate_code, research         | Yes (60s)   | Yes               | complex    |
| 28| test-crew           | testing     | medium | delegate_code, research         | Yes (60s)   | Yes               | complex    |
| 29| validate-config     | utility     | free   | file_read, shell, research      | No          | No                | simple     |
| 30| voice-smart         | voice       | variable| voice, file_read, search_files, shell | Yes  | No                | complex    |

---

## 9. Observed Patterns Across Skills

### 9.1 The Delegation Hierarchy

The skills form a clear delegation tree, from simplest to most complex:

```
chef-lite          Direct one-shot delegation (no context gathering)
  |
chef               Context-enhanced delegation (gather-context.sh + opencode_run)
  |
chef-async         Non-blocking delegation (session + async message)
  |
chef-subagent      Isolated delegation (via sub-agent, background)
  |
delegate           Full delegation with complexity assessment (simple vs. session)
  |
batch              Multi-task batching into one delegation call
  |
auto               Smart routing — picks the right delegation method
```

### 9.2 The Research Hierarchy

```
research           Single Gemini call, structured output
  |
research-subagent  Non-blocking research via Haiku sub-agent
  |
research-swarm     3 parallel Gemini calls from different perspectives + synthesis
```

### 9.3 The 60-Second Fallback Pattern

Found in: chef, chef-async, chef-lite, delegate, research, test, test-crew.

```
IF primary_tool stalls > 60 seconds:
  1. Tell user: "X not responding -- handling directly"
  2. Execute via fallback tool
  3. Note in output which path was taken
```

### 9.4 The Orchestrator Pattern

Found in: test, test-crew, swarm, research-swarm.

```
Phase 1: GATHER (orchestrator reads files, builds context)
Phase 2: PLAN (research engine analyzes, creates plan)
Phase 3: EXECUTE (code engine runs the plan)
Phase 4: ANALYZE (research engine evaluates results)
Phase 5: FIX (code engine applies fixes, max N iterations)
Phase 6: REPORT (orchestrator synthesizes final report)
```

### 9.5 The ADHD Support Pattern

Found in: focus, bigwin, quickwin, checkpoint, recap.

```
1. Low barrier to entry (absurdly simple first step)
2. Time-boxed chunks (15 min, 5 min steps)
3. Visible progress (git commits, session logs)
4. Celebration after completion
5. No judgment, no pressure
```

---

## 10. Transpiler Contract

A conforming transpiler MUST:

1. **Parse frontmatter** — extract all fields, pass unknown fields through as comments
2. **Preserve `$ARGUMENTS`** — never rename or transform
3. **Map abstract tools** — replace `{{tool(...)}}` with target-specific syntax
4. **Map agent references** — replace abstract engine names with target tools
5. **Handle target blocks** — include only the matching `<!-- target:X -->` block
6. **Strip irrelevant metadata** — e.g., Claude Code only keeps `description` + `argument-hint`
7. **Copy companion files** — scripts/, references/, assets/ to the right location
8. **Generate a manifest** — list of all skills with their metadata for the target

A conforming transpiler SHOULD:

1. **Validate dependencies** — warn if a required tool is not available on the target
2. **Estimate cost** — compute expected cost per skill invocation
3. **Generate index** — create a skill index/registry for the target platform

---

## 11. Version History

| Version | Date       | Changes                                  |
|---------|------------|------------------------------------------|
| 1.0     | 2026-02-26 | Initial spec from analysis of 30 Claude Code skills |
