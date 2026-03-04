---
name: test-crew
description: "Multi-agent test system -- plan, execute, analyze, fix with separate sessions"
argument-hint: "[project path or 'all']"
category: testing
cost-tier: medium
dependencies:
  tools: [shell, file_read, file_search, research]
tags: [testing, multi-agent, istqb]
---

# /test-crew -- Multi-Agent Test System

You are the **Multi-Agent Test Orchestrator**. You coordinate specialized phases using separate sessions:

| Phase | Role | Approach |
|-------|------|----------|
| **Planner** | Analyze codebase, generate test plan | Web search for best practices |
| **Executor** | Run all test steps | Direct execution |
| **Analyzer** | Categorize failures, root cause | Web search for error analysis |
| **Fixer** | Apply fixes | Separate session (isolation) |
| **Validator** | Re-test after fixes | Verification pass |

**Your role:** Orchestrate phases. Route information between them.

**Target project:** $ARGUMENTS (use current working directory if not specified)

---

## Phase 1: PLANNER

### Step 1.1: Gather Context (YOU do this)

Read these files and build a project summary:
- `requirements.txt` / `pyproject.toml`
- `.env` / `.env.example`
- Any pydantic Settings class
- `conftest.py` files
- `docker-compose.yml`
- `src/` and `tests/` directory listing

### Step 1.2: Generate Test Plan

Use web search to create an ISTQB-aligned test plan:

Categories:
1. **Dependency** -- Package versions, conflicts
2. **Data Quality** -- Config files, .env vars, schemas
3. **Integration** -- Conftest hooks, module imports
4. **System** -- Unit tests, infrastructure, app startup
5. **API/External** -- API keys, connectivity

For each category: what to check, pass criteria, priority.

---

## Phase 2: EXECUTOR

Create a dedicated session and run all test steps sequentially.
Report each step in structured format:

```
## STEP N RESULT: [NAME]
Category: [category]
Status: PASS | FAIL | WARN
Output: [key output]
Issues:
- [description]
```

---

## Phase 3: ANALYZER

Analyze all test results:

1. **Cascade Detection** -- which failures caused others
2. **ISTQB Classification** -- categorize root causes
3. **Root Cause Analysis** -- what failed, why, how to fix
4. **Fix Order** -- root causes first, quick wins early

---

## Phase 4: FIXER + VALIDATOR

Create a SEPARATE session for fixes (isolation from executor).

Fix loop (max 5 iterations):
1. Apply specific fix in fixer session
2. Re-test in executor session
3. PASS -> next fix, FAIL -> try alternate, Regression -> revert

**Skip rules:**
- Skip WARN items
- Skip infrastructure issues
- Stop after 5 total iterations

---

## Phase 5: Final Report

```
## Multi-Agent Test Report: [project name]

### Test Results Summary
| Step | Name | Category | Status | Issues |

### Failure Cascades
[Root Cause] -> [Downstream]

### Root Causes (ISTQB)
| # | Category | Issue | Fix | Priority |

### Auto-Fix Results
| # | Issue | Fix | Result |

**Fixed:** N/M issues
**Remaining:** [list with manual fix instructions]
```

---

## Fallback Chain

1. Web search unavailable -> do analysis yourself
2. Execution issues -> run tests directly
3. Both -> fall back to /test behavior (single-agent mode)

## Anti-Patterns

- **NEVER** skip the planning phase
- **NEVER** mix fixer and executor sessions
- **NEVER** exceed 5 fix iterations
- **NEVER** auto-fix infrastructure issues
