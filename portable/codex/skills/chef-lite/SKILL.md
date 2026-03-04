---
name: chef-lite
description: "Direct delegation -- minimal overhead, no context gathering"
argument-hint: "[task description]"
category: delegation
cost-tier: minimal
dependencies:
  tools: [delegate_code]
tags: [delegation, quick, lightweight]
---

# /chef-lite -- Direct Delegation

Delegate directly to the execution engine. No context gathering, no enhancement. For quick tasks where the engine can figure it out.

**Task:** $ARGUMENTS

## Process

{{delegate_code(prompt="$ARGUMENTS", dir=project_dir)}}

Report the result in 1-2 sentences.

## Fallback

If execution engine stalls >60s, do it directly.
