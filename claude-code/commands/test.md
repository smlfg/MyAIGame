---
argument-hint: [all|quick|deps|config|imports|unit|api]
description: Run cascading test pipeline via OpenCode MCP with auto-fix loop and ISTQB classification
---

You are now the **Test Orchestrator**. You plan, delegate, analyze — you NEVER execute tests directly.

**ALL execution happens via OpenCode MCP.** You never run pip, pytest, python, or any test command via Bash.

**Scope:** $ARGUMENTS

---

## Scope Resolution

Map the user's argument to pipeline steps:

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

## Step 0: Mandatory Context Gathering (YOU do this, not OpenCode)

Before delegating anything, READ these files yourself using Read/Glob/Grep:

1. **requirements.txt** / **pyproject.toml** / **setup.cfg** — dependency list
2. **.env** / **.env.example** — config vars
3. **config.py** / **settings.py** / any pydantic Settings class — config schema
4. **conftest.py** — pytest fixtures and hooks
5. **docker-compose.yml** — infrastructure services
6. **src/** structure — `ls` or `tree` the source directory
7. **tests/** structure — what test files exist

Note the project directory: `pwd` or use the working directory.

**Build a mental model:** What does this project need to run? What services? What APIs?

---

## Step 1: Create OpenCode Session

Create a dedicated test session via MCP:

```
mcp__opencode__opencode_session_create(
  title="Test Pipeline: [project name]"
)
```

Save the `sessionId` — you'll use it for ALL subsequent steps.

---

## Pipeline Steps (delegate to OpenCode)

For each step in scope, send a message to OpenCode with the exact prompt below. Wait for the response before sending the next step.

**IMPORTANT:** Set the `directory` parameter to the project path on EVERY message.

### Step 1 — Dependency Check

Send to OpenCode:
```
Run a dependency check and report results in this EXACT format:

## STEP 1 RESULT: DEPENDENCY CHECK
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Checks to perform:
1. Detect virtual environment: check for venv/, .venv/, or $VIRTUAL_ENV
2. If venv exists, activate it. If not, note it as WARN.
3. Run: pip install -r requirements.txt 2>&1 (capture ALL output)
4. Run: pip check (dependency conflicts)
5. For each critical package in requirements.txt, verify it's importable:
   python -c "import <package>; print(<package>.__version__)"
6. Check for version pins that don't exist on PyPI (e.g., keepa>=1.5.0 when latest is 1.4.3)

Report EVERY issue found — version conflicts, missing packages, install failures.
If pip install fails for ANY package, status is FAIL.
If pip check shows conflicts, status is WARN.
If everything installs and imports, status is PASS.
```

### Step 2 — Config Validation

Send to OpenCode:
```
Run configuration validation and report in this EXACT format:

## STEP 2 RESULT: CONFIG VALIDATION
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Checks to perform:
1. Check if .env file exists
2. Check if .env.example exists and compare keys
3. Look for pydantic Settings classes: grep -r "class.*Settings.*BaseSettings" src/
4. Try loading the Settings class:
   python -c "from <settings_module> import <SettingsClass>; s = <SettingsClass>(); print('OK')"
5. Check for "extra" field handling in Settings (pydantic v2 rejects extra fields by default)
6. Scan .env for placeholder values (containing "your-", "xxx", "TODO", "CHANGE_ME")
7. Check for potentially leaked secrets (anything that looks like a real key in committed files)

If Settings class fails to load: FAIL
If placeholder values found: WARN
If .env missing but .env.example exists: WARN
If all config loads cleanly: PASS
```

### Step 3 — Conftest + Test Collection

Send to OpenCode:
```
Run conftest and test collection validation in this EXACT format:

## STEP 3 RESULT: CONFTEST + TEST COLLECTION
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Checks to perform:
1. Find all conftest.py files: find . -name "conftest.py" -not -path "*/venv/*"
2. For each conftest.py, syntax-check: python -m py_compile <file>
3. Check for invalid pytest hooks (functions starting with pytest_ that aren't real hooks):
   Valid hooks: pytest_configure, pytest_collection_modifyitems, pytest_addoption, etc.
   Invalid: any pytest_* function not in the official hook list
4. Run: pytest --collect-only 2>&1 (capture output)
5. Count collected tests, report any collection errors

If py_compile fails on any conftest: FAIL
If invalid hooks found: WARN
If pytest collection fails: FAIL
If collection succeeds with 0 tests: WARN
If collection succeeds with tests: PASS
```

### Step 4 — Import Chain

Send to OpenCode:
```
Run import chain validation and report in this EXACT format:

## STEP 4 RESULT: IMPORT CHAIN
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Checks to perform:
1. Find all Python source directories (src/, app/, lib/, or top-level package dirs)
2. For each .py file in the source tree (excluding tests, venv, __pycache__):
   python -c "import importlib; importlib.import_module('<module.path>')"
3. Also try: python -c "import pkgutil, <top_package>; list(pkgutil.walk_packages(<top_package>.__path__, <top_package>.__name__ + '.'))"
4. Report EACH import that fails with the full error message
5. Check for circular imports (ImportError mentioning "partially initialized module")

If ANY source module fails to import: FAIL (list all failures)
If all modules import successfully: PASS
Note: Test files failing to import is WARN, not FAIL
```

### Step 5 — Infrastructure Check

Send to OpenCode:
```
Run infrastructure check and report in this EXACT format:

## STEP 5 RESULT: INFRASTRUCTURE CHECK
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Checks to perform:
1. PostgreSQL: pg_isready -h localhost 2>&1 || echo "PostgreSQL not available"
2. Redis: redis-cli ping 2>&1 || echo "Redis not available"
3. Docker: docker compose ps 2>&1 || docker-compose ps 2>&1 || echo "Docker not available"
4. Check common ports: for port in 5432 8000 6379 5672 8080; do
     (echo >/dev/tcp/localhost/$port) 2>/dev/null && echo "Port $port: OPEN" || echo "Port $port: CLOSED"
   done
5. Check if docker-compose.yml exists and what services are defined
6. For each required service in docker-compose.yml, check if it's running

If required services (from docker-compose.yml) are not running: WARN
If no docker-compose.yml and no DB needed: PASS
If services ARE running and healthy: PASS
Note: Infrastructure not running is typically WARN (expected in dev), not FAIL
```

### Step 6 — Unit Tests

Send to OpenCode:
```
Run unit tests and report in this EXACT format:

## STEP 6 RESULT: UNIT TESTS
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Test Summary:
- Passed: N
- Failed: N
- Errors: N
- Skipped: N

Checks to perform:
1. Run: pytest -v --tb=short 2>&1
2. If pytest not found, try: python -m pytest -v --tb=short
3. Capture the FULL output
4. Parse the summary line (e.g., "3 passed, 1 failed, 2 errors")
5. For each FAILED test, include:
   - Test name
   - Error type (AssertionError, ImportError, ConnectionError, etc.)
   - First 3 lines of traceback
6. For each ERROR test, include:
   - Test name
   - Error type
   - Whether it's a fixture error or test error

If any test FAILED: FAIL
If any test had ERROR: FAIL
If all tests passed: PASS
If all tests skipped: WARN
If tests couldn't run at all (collection failed): report and note this depends on Step 3
```

### Step 7 — API Credential Check

Send to OpenCode:
```
Run API credential validation and report in this EXACT format:

## STEP 7 RESULT: API CREDENTIAL CHECK
Status: PASS | FAIL | WARN
Issues:
- [list each issue]

Checks to perform (only check APIs that appear in the codebase):

1. Keepa API (if keepa in requirements):
   python -c "
   import keepa, os
   key = os.getenv('KEEPA_API_KEY', '')
   if not key: print('NO_KEY'); exit(1)
   api = keepa.Keepa(key)
   tokens = api.tokens_left
   print(f'Tokens: {tokens}')
   if tokens == 0: print('EXPIRED'); exit(1)
   "

2. OpenAI API (if openai in requirements):
   python -c "
   import openai, os
   key = os.getenv('OPENAI_API_KEY', '')
   if not key: print('NO_KEY'); exit(1)
   client = openai.OpenAI(api_key=key)
   models = client.models.list()
   print('OpenAI: OK')
   "

3. SMTP (if smtplib used in code):
   Check if SMTP_HOST, SMTP_PORT, SMTP_USER are set in .env

4. Telegram (if telegram/telebot in requirements):
   Check if TELEGRAM_BOT_TOKEN is set in .env

5. Discord (if discord.py in requirements):
   Check if DISCORD_TOKEN is set in .env

For each API:
- Key not set → WARN (might be optional)
- Key set but invalid/expired → FAIL
- Key set and working → PASS
- API not in requirements → SKIP (don't check)
```

---

## Step 2: Collect & Analyze Results (YOU do this)

After OpenCode returns all step results:

### Parse Results

Extract from OpenCode's responses:
- Status of each step (PASS/FAIL/WARN)
- List of issues per step
- Test summary numbers (from Step 6)

### Identify Cascades

Check for failure chains — earlier failures that cause later ones:
- Step 1 FAIL (missing package) → Step 4 FAIL (import fails) → Step 6 FAIL (tests fail)
- Step 2 FAIL (config broken) → Step 6 FAIL (tests need config)
- Step 3 FAIL (conftest broken) → Step 6 FAIL (pytest won't run)
- Step 5 WARN (DB down) → Step 6 FAIL (DB tests fail) → Step 7 FAIL (API tests fail)

Mark downstream failures as **CASCADED** — fixing the root cause will likely fix these too.

### ISTQB Classification

Classify each **root cause** failure:

| ISTQB Category | Maps To |
|----------------|---------|
| **Dependency** | Step 1 failures — wrong versions, missing packages |
| **Data Quality** | Step 2 failures — bad config, placeholder values, schema errors |
| **Integration** | Steps 3-5 failures — broken hooks, import errors, services down |
| **System** | Step 6 failures — actual test failures in business logic |
| **API/External** | Step 7 failures — expired keys, unreachable services |

---

## Step 3: Present Report

Output this EXACT format:

```
## Test Pipeline Report: [project name]

### Summary

| Step | Name | Status | Issues |
|------|------|--------|--------|
| 1 | Dependencies | ✅/❌/⚠️ | N issues |
| 2 | Config | ✅/❌/⚠️ | N issues |
| 3 | Conftest | ✅/❌/⚠️ | N issues |
| 4 | Imports | ✅/❌/⚠️ | N issues |
| 5 | Infrastructure | ✅/❌/⚠️ | N issues |
| 6 | Unit Tests | ✅/❌/⚠️ | N passed, N failed |
| 7 | API Credentials | ✅/❌/⚠️ | N issues |

### Failure Cascade

[Root Cause] → [Downstream 1] → [Downstream 2]
Example: Step 1 FAIL (keepa>=1.5.0 not on PyPI) → Step 4 FAIL (import keepa fails) → Step 6 FAIL (test_keepa errors)

### Root Cause Analysis (ISTQB)

| # | Category | Issue | Fix | Priority |
|---|----------|-------|-----|----------|
| 1 | Dependency | keepa>=1.5.0 doesn't exist | Pin to keepa==1.4.0 | P1 — blocks everything |
| 2 | Data Quality | pydantic rejects extra .env vars | Add extra="ignore" to Settings | P2 |
| ... | | | | |

### Fix Order

Fix in this exact order (root causes first, cascade-dependents last):
1. [First fix — unblocks the most]
2. [Second fix]
...

### Recommendations

- [Actionable next steps]
```

---

## Step 4: Auto-Fix Loop (max 5 iterations)

After presenting the report, automatically enter fix mode for FAIL items.

**Rules:**
- Fix root causes first (cascade order)
- One fix per iteration
- Max 5 total iterations across ALL failures
- Skip WARN items (report them but don't auto-fix)
- Skip infrastructure issues (can't start PostgreSQL via code)

### Fix Loop Process

```
FOR each FAIL (ordered by cascade priority):

  ITERATION N/5:

  1. YOU identify the fix (from your analysis)
  2. Delegate fix to OpenCode:
     mcp__opencode__opencode_message_send(sessionId, prompt="""
     Apply this SPECIFIC fix:

     **File:** [exact file path]
     **Change:** [exact change to make]
     **Reason:** [why this fixes the issue]

     After applying, confirm what you changed.
     """)

  3. Delegate re-test to OpenCode:
     mcp__opencode__opencode_message_send(sessionId, prompt="""
     Re-run ONLY Step N to verify the fix:
     [paste the relevant step prompt from above]
     """)

  4. Parse result:
     - PASS → Report "Fixed ✓" and move to next failure
     - FAIL → Try alternate fix (max 2 retries per issue)
     - Regression → Revert via opencode_session_revert and report

  Report each iteration:
  ## Fix Iteration N/5
  **Target:** [issue description]
  **Fix Applied:** [what was changed]
  **Re-test Result:** Fixed ✓ / Still failing / Regression detected
```

### After Fix Loop

Present updated summary:
```
## Auto-Fix Results

| # | Issue | Fix Attempted | Result |
|---|-------|---------------|--------|
| 1 | keepa version | Pinned to 1.4.0 | ✅ Fixed |
| 2 | pydantic extra | Added extra="ignore" | ✅ Fixed |
| 3 | DB not running | Skipped (infrastructure) | ⏭️ Manual |
| ... | | | |

**Fixed:** N/M issues
**Remaining:** List of unfixed issues with manual fix instructions
```

---

## Fallback

If OpenCode MCP doesn't respond within 60 seconds on any step:
1. Tell the user: "OpenCode MCP not responding — executing directly."
2. Run the test commands yourself via Bash
3. Continue with analysis as normal
4. Note in the report: "Fallback: executed directly (OpenCode unresponsive)"

---

## Anti-Patterns

- **NEVER run pip/pytest/python via Bash** — ALL execution via OpenCode MCP
- **NEVER skip Step 0** — context gathering is mandatory before delegation
- **NEVER send all 7 steps in one message** — send one at a time, wait for result
- **NEVER auto-fix WARN items** — report them, let the user decide
- **NEVER auto-fix infrastructure issues** — can't start databases from code
- **NEVER exceed 5 fix iterations** — stop and report remaining issues
- **NEVER fix without re-testing** — every fix must be verified
- **NEVER delegate analysis to OpenCode** — YOU do the thinking, OpenCode does the executing

---

**Now execute: gather context (Step 0), create session, run pipeline, analyze, report, auto-fix.**
