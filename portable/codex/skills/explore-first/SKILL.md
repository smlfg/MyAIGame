---
name: explore-first
description: "Explore system state and research best approach before implementing"
category: utility
cost-tier: low
dependencies:
  tools: [spawn_subagent, shell]
tags: [exploration, pre-implementation, safety]
---

# /explore-first -- Explore Before Implementing

Before implementing anything, explore in parallel:

**Agent 1 -- System State Check:**
Check current system state and dependencies:
- What's installed (relevant packages, tools, services)
- What's running (relevant processes, daemons, ports)
- Current configuration state (config files, environment variables)
- Any potential conflicts or blockers

**Agent 2 -- Research Best Approach:**
Research the best approach for the task on this specific system:
- This is Pop!_OS with COSMIC desktop on Wayland
- Find compatible approaches
- Identify potential pitfalls specific to COSMIC/Wayland
- Compare 2-3 viable approaches with pros and cons

**After both analyses complete:**
1. Present the findings clearly to the user
2. Recommend an approach with reasoning
3. Wait for user approval before writing any code

Do NOT skip the exploration phase. Do NOT start implementing before the user approves the approach.

## Codex Limitation
Codex does not have native parallel sub-agent spawning. Workaround: Run the two exploration steps sequentially (system state check first, then research), or use shell background processes. The exploration pattern is fully portable, just not parallel.
