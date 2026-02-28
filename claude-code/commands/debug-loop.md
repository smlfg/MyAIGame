Run an autonomous debug loop to diagnose and fix an issue. Maximum 5 iterations.

## Problem: $ARGUMENTS

## Debug Loop Protocol:

For each iteration (max 5):

### 1. DIAGNOSE
- Read error messages carefully — they usually tell you exactly what's wrong
- Check logs, stack traces, and recent changes
- Identify the root cause (not just the symptom)

### 2. HYPOTHESIZE
- State your hypothesis: "I think the issue is X because Y"
- Identify what evidence would confirm or deny this hypothesis

### 3. FIX
- Make the minimal change needed to fix the issue
- Do NOT refactor, clean up, or "improve" other code while fixing
- One fix per iteration

### 4. TEST
- Run the relevant test or reproduce the error
- Check if the fix actually resolved the issue
- Check for regressions (did the fix break something else?)

### 5. EVALUATE
- If FIXED: Report what was wrong and what fixed it. EXIT LOOP.
- If NOT FIXED: Update diagnosis with new information. Go to next iteration.
- If ITERATION 5 and still not fixed: STOP and report findings to user.

## Rules:
- NEVER make more than one change per iteration
- ALWAYS test after each change
- ALWAYS explain your reasoning before making changes
- If you're stuck after 3 iterations, consider asking the user for more context
- Log each iteration clearly so the user can follow your thinking

## Output format per iteration:
```
## Iteration N/5

**Diagnosis:** What I think is wrong
**Evidence:** What I observed
**Fix:** What I'm changing and why
**Test:** How I'm verifying
**Result:** Fixed ✓ / Not fixed → continuing
```
