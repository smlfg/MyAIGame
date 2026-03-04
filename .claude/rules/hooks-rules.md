---
paths: ["plugins/**/*.py"]
---

# Hook Conventions

- Hooks MUST exit 0 (success) or 2 (block with message)
- JSON on stdout = additionalContext injection
- stderr = logging only (not shown to user)
- Always timeout-safe — graceful degradation over hard failure
- Never block the main process — async where possible
