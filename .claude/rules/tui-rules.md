---
paths: ["tui/**", "tui-design/**"]
---

# TUI Conventions

- Terminal UI uses COSMIC Desktop (Wayland) — no X11 assumptions
- cosmic-term has NO `-e` flag — use alternatives
- Test with kitty or tmux when cosmic-term not available
- Keep UI responsive — async operations for heavy tasks
- Consistent keybinding patterns across all TUI components
