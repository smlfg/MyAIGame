---
name: test
description: "Cascading test pipeline with auto-fix loop and ISTQB classification"
argument-hint: "[all|quick|deps|config|imports|unit|api]"
category: testing
cost-tier: medium
dependencies:
  tools: [shell, file_read, file_search]
tags: [testing, pipeline, istqb, auto-fix]
---

# /test -- Cascading Test Pipeline

You are the **Test Orchestrator**. You plan, execute, analyze, and auto-fix.

In OpenCode you ARE the execution engine -- run tests directly.

**Scope:** $ARGUMENTS

---

## Scope Resolution

| Argument | Steps | Description |
|----------|-------|-------------|
| `all` (default) | 1-7 | Full project validation |
| `quick` | 1-3 | Fast smoke test (~30s) |
| `deps` | 1 | Dependency audit only |
| `config` | 2-3 | .env + pydantic settings + conftest |
| `imports` | 1-4 | Through import chain |
| `unit` | 1-6 | Through unit tests |
| `api` | 7 | API credential check only |

If no argument or empty: default to `all`.

---

## Step 0: Mandatory Context Gathering

Before running tests, READ these files:

1. **requirements.txt** / **pyproject.toml** / **setup.cfg** -- dependency list
2. **.env** / **.env.example** -- config vars
3. **config.py** / **settings.py** / any pydantic Settings class
4. **conftest.py** -- pytest fixtures and hooks
5. **docker-compose.yml** -- infrastructure services
6. **src/** structure
7. **tests/** structure

**Build a mental model:** What does this project need to run?

---

## Pipeline Steps

### Step 1 -- Dependency Check
1. Detect virtual environment (venv/, .venv/, $VIRTUAL_ENV)
2. `pip install -r requirements.txt 2>&1`
3. `pip check` (dependency conflicts)
4. For each critical package, verify importable
5. Check for version pins that don't exist on PyPI

### Step 2 -- Config Validation
1. Check .env exists, compare with .env.example
2. Look for pydantic Settings classes
3. Try loading Settings class
4. Scan .env for placeholder values
5. Check for leaked secrets in committed files

### Step 3 -- Conftest + Test Collection
1. Find all conftest.py files
2. Syntax-check each one
3. Check for invalid pytest hooks
4. `pytest --collect-only 2>&1`

### Step 4 -- Import Chain
1. Find all Python source directories
2. Try importing each module
3. Report import failures with full error
4. Check for circular imports

### Step 5 -- Infrastructure Check
1. PostgreSQL: `pg_isready -h localhost`
2. Redis: `redis-cli ping`
3. Docker: `docker compose ps`
4. Check common ports (5432, 8000, 6379, 5672, 8080)

### Step 6 -- Unit Tests
1. `pytest -v --tb=short 2>&1`
2. Parse summary (passed, failed, errors, skipped)
3. For each failure: test name, error type, traceback

### Step 7 -- API Credential Check
Check only APIs that appear in the codebase (Keepa, OpenAI, SMTP, Telegram, Discord).

---

## Result Analysis

### Parse Results
Extract status per step (PASS/FAIL/WARN).

### Identify Cascades
Step 1 FAIL -> Step 4 FAIL -> Step 6 FAIL (root cause propagation).

### ISTQB Classification
| Category | Maps To |
|----------|---------|
| **Dependency** | Step 1 failures |
| **Data Quality** | Step 2 failures |
| **Integration** | Steps 3-5 failures |
| **System** | Step 6 failures |
| **API/External** | Step 7 failures |

---

## Report Format

```
## Test Pipeline Report: [project name]

### Summary
| Step | Name | Status | Issues |
|------|------|--------|--------|

### Failure Cascade
[Root Cause] -> [Downstream 1] -> [Downstream 2]

### Root Cause Analysis (ISTQB)
| # | Category | Issue | Fix | Priority |

### Fix Order
1. [First fix -- unblocks the most]
```

---

## Auto-Fix Loop (max 5 iterations)

For each FAIL (ordered by cascade priority):
1. Identify the fix
2. Apply the minimal change
3. Re-run the relevant test step
4. Parse: PASS -> next fix, FAIL -> try alternate (max 2 retries)

**Skip rules:**
- Skip WARN items (report only)
- Skip infrastructure issues
- Stop after 5 total iterations

---

## Anti-Patterns

- **NEVER** skip Step 0 -- context gathering is mandatory
- **NEVER** auto-fix WARN items
- **NEVER** auto-fix infrastructure issues
- **NEVER** exceed 5 fix iterations
- **NEVER** fix without re-testing
