Before implementing anything, use sub-agents to explore in parallel:

**Agent 1 — System State Check:**
Use a Task agent to check the current system state and dependencies:
- What's installed (relevant packages, tools, services)
- What's running (relevant processes, daemons, ports)
- Current configuration state (config files, environment variables)
- Any potential conflicts or blockers

**Agent 2 — Research Best Approach:**
Use a Task agent to research the best approach for the task on this specific system:
- This is Pop!_OS with COSMIC desktop on Wayland
- Find approaches that are compatible with this environment
- Identify potential pitfalls specific to COSMIC/Wayland
- Compare 2-3 viable approaches with pros and cons

**After both agents report back:**
1. Present the findings clearly to the user
2. Recommend an approach with reasoning
3. Wait for user approval before writing any code or making any changes

Do NOT skip the exploration phase. Do NOT start implementing before the user approves the approach.
