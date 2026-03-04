# QA Review — Portable Toolkit Outputs

Reviewed by: porter-hooks agent
Date: 2026-02-26
Status: **In Progress** (Codex and OpenCode skill porting still running)

### Fixes Applied (2026-02-26, second pass)

- **FIXED [HIGH]** Issues #5/#9/#15: Replaced `~/.claude/hooks/` with `~/.opencode/hooks/` in 6 OpenCode files (chef.md, chef-async.md, auto.md, batch.md, chef-subagent.md, voice-smart/SKILL.md)
- **FIXED [HIGH]** Replaced `~/.claude/scripts/` with `~/.opencode/scripts/` in 2 OpenCode files (snapshot.md, crew/SKILL.md)
- **FIXED [HIGH]** Updated swarm/SKILL.md report path from `~/.claude/sharepoint/recaps/` to `~/.opencode/recaps/`
- **FIXED [MEDIUM]** Issue #4: AGENTS.md companion file paths now document per-tool locations (Claude: flat in ~/.claude/, Codex: ~/.codex/companion/, OpenCode: ~/.opencode/companion/)
- **NOTED** chrome-extension.md: `~/.claude/chrome/` paths are intentionally Claude-Code-specific (added explicit note)
- **FIXED** PORTING_NOTES.md: Updated path mapping table to reflect actual fixes

---

## 1. SPEC.md (Architect Output)

**Verdict: SOLID**

The universal spec is well-structured and comprehensive. Key observations:

- **Tool abstraction table** (Section 4.2) covers all 16 abstract tools with mappings to all 3 platforms. The mappings are accurate.
- **Skill classification matrix** (Section 8) lists all 30 skills with correct categories, cost tiers, and dependency analysis.
- **Frontmatter schema** (Section 2) is clear and the Codex/OpenCode porters are following it correctly.
- **`$ARGUMENTS` placeholder** is documented as universal across all targets — confirmed this is used consistently in all ported skills.

### Issues Found

1. **SPEC Section 4.2 references `codex_run()` etc.** — These are abstract Codex equivalents but Codex CLI does not actually have a `codex_run()` API. In practice, Codex skills execute tasks directly (as documented in AGENTS.codex.md). This is a cosmetic issue since the spec is for transpiler reference, not direct execution. **Severity: Low**

2. **Voice-smart tool mapping** — `{{voice_converse()}}` maps to `mcp__voicemode__converse` for Claude Code but shows "N/A" for Codex and OpenCode. The Codex and OpenCode porters both created voice-smart skill files. Need to verify these gracefully degrade when voice is unavailable. **Severity: Medium**

3. **Missing skill in SPEC** — The spec lists 30 skills but the original Claude Code commands directory also has 30 files (ClaudeChromeExtension.md included). The Codex port correctly renames it to `chrome-extension`. Naming is consistent. **Severity: None**

---

## 2. Instructions (Porter-Instructions Output)

**Verdict: GOOD — minor consistency notes**

### AGENTS.md (Universal)
- Successfully de-Claude-ified: no Claude-specific MCP calls, no tool-specific API references
- Delegation architecture uses abstract tier names (Strategy/Execution/Research/Background) instead of model names
- German Umlauts removed from English text but preserved in companion files — correct approach
- Communication style and anti-patterns preserved faithfully

### AGENTS.codex.md (Codex Overrides)
- Correctly documents sandbox limitations (no internet, no MCP, single-agent)
- Skills mapping table accurately reflects which skills can/cannot work in Codex
- Lists chef-async and chef-subagent as non-functional in Codex — matches COMPATIBILITY.md findings

### AGENTS.opencode.md (OpenCode Overrides)
- Provider configuration section includes the "Unexpected end of JSON input" known issue — useful
- `providerID`/`modelID` requirement documented — critical for OpenCode usage
- Anticipation patterns preserved for Samuel's workflow

### Companion Files
- All 4 companion files present: WieArbeitestDuMitSamuel.md, WelcheFehlerVermeiden.md, Skilluebersicht.md, ADHD_TEMPLATE.md
- Content preserved faithfully from originals
- Skilluebersicht uses abstract tier names (Research/Execution/Background) — consistent with AGENTS.md

### Issues Found

4. **AGENTS.md companion file paths** — References `companion/WieArbeitestDuMitSamuel.md` etc. This relative path works if instructions and companion/ are co-located. But deploy.sh copies them to different locations per target (Claude Code: `~/.claude/` flat, Codex: `~/.codex/companion/`, OpenCode: `~/.opencode/companion/`). For Claude Code deployment, the companion files land directly in `~/.claude/` as flat files, but AGENTS.md references `companion/` subdirectory. **Severity: Medium — path mismatch for Claude Code deployment.**

5. **AGENTS.opencode.md references `~/.claude/hooks/gather-context.sh`** — This path is Claude-Code-specific. Should reference the portable hooks location or use a relative path. The same issue appears in OpenCode commands (chef.md, batch.md, etc. all reference `~/.claude/hooks/`). **Severity: HIGH — OpenCode skills will fail if Claude Code is not installed.**

---

## 3. Codex Skills (Porter-Codex Output)

**Verdict: GOOD — 30/30 skills ported, uses SPEC format correctly**

### Coverage
All 30 original Claude Code commands are present as Codex skill directories with SKILL.md files:
- auto, batch, bigwin, checkpoint, check-state, chef, chef-async, chef-lite, chef-subagent, chrome-extension, crew, debug-loop, delegate, explore-first, focus, learn, quickwin, recap, research, research-subagent, research-swarm, review, selfimprove, setup-git, snapshot, swarm, test, test-crew, validate-config, voice-smart

### Frontmatter Compliance
- All skills have YAML frontmatter with `name`, `description`
- Most have `argument-hint`, `category`, `cost-tier`, `dependencies`, `tags`
- Dependencies correctly reference abstract tool names from SPEC Section 4.2

### Tool Abstractions
- Skills use `{{gather_context()}}`, `{{delegate_code_run()}}`, `{{research()}}` etc. — matches SPEC
- Fallback chains present where expected (chef, chef-async, delegate)
- `$ARGUMENTS` placeholder used consistently

### Issues Found

6. **chef-async has Codex limitation note** — Good practice. It notes Codex cannot do async natively and suggests workarounds. Same approach should be used for other limited skills (crew, swarm, research-swarm). **Severity: Low — informational**

7. **No scripts/ subdirectories** — SPEC Section 1 defines optional `scripts/` directories for helper scripts. The Codex skills reference `gather-context.sh` in dependencies but don't bundle the script. The deploy.sh script handles this by copying hooks separately. This works but is fragile — if someone copies just the skills/ directory without hooks/, the dependencies break. **Severity: Low**

---

## 4. OpenCode Skills (Porter-OpenCode Output)

**Verdict: IN PROGRESS — 13/30 skills ported, complex skills incomplete**

### Coverage
- **Commands (simple skills):** 7 ported — auto, batch, chef, chef-async, chef-lite, chef-subagent, delegate
- **Skills (complex, directory-based):** 6 directories created (crew, research-swarm, swarm, test, test-crew, voice-smart) but **EMPTY** — only `scripts/` subdirs exist, no SKILL.md files
- **Missing entirely:** bigwin, checkpoint, check-state, debug-loop, explore-first, focus, learn, quickwin, recap, research, research-subagent, review, selfimprove, setup-git, snapshot, validate-config, chrome-extension

### Issues Found

8. **17 skills not yet ported to OpenCode.** This is expected since porter-opencode is still working (Task #4 in_progress). The 7 commands that ARE done are well-written and correctly adapted for OpenCode's execution model. **Severity: Expected — not a bug.**

9. **OpenCode commands hardcode `~/.claude/hooks/` path** — As noted in Issue #5, chef.md line 16 says `bash ~/.claude/hooks/gather-context-enhanced.sh`, chef-async.md references `~/.claude/hooks/gather-context.sh`, auto.md and batch.md do the same. These should reference the OpenCode-local hooks path (e.g., `~/.opencode/hooks/` or a relative path). **Severity: HIGH — blocks OpenCode standalone use.**

10. **OpenCode chef.md uses "Execution Mode" framing** — "This is a native OpenCode command -- no delegation needed because YOU are the execution engine." This is correct and well-adapted to OpenCode's paradigm where it IS the code agent, not the orchestrator.

11. **Complex OpenCode skills are empty shells** — The 6 skill directories (crew, test, test-crew, swarm, research-swarm, voice-smart) have been created with `scripts/` subdirs but no SKILL.md content yet. These are the hardest to port since they involve multi-agent orchestration. **Severity: Expected — in progress.**

---

## 5. Hooks & Config (Porter-Hooks Output — My Own Work)

**Self-review for completeness:**

### Hooks
- All 10 scripts copied to `portable/hooks/`
- Shell scripts have +x permission
- No modifications to universal scripts (correct — they work as-is)

### Config
- `codex/config.toml` — Documents limitations accurately, comments explain what can't be ported
- `opencode/opencode.json` — Valid JSON, MCP servers defined, plugin paths referenced
- OpenCode plugins (4 .ts files) — Best-effort ports of hook behavior

### Issues Found (Self-Review)

12. **opencode.json `permission` field** — Set to `"auto-edit"`. The OpenCode docs may use different permission values. Need to verify against actual OpenCode config schema. **Severity: Low — may need adjustment.**

13. **opencode.json plugin paths** — References `plugins/context-injection.ts` etc. as relative paths. These need to be relative to the opencode.json location, which varies by deployment. Deploy.sh places them in `~/.opencode/plugins/` which should work if opencode.json is at `~/.opencode/opencode.json`. **Severity: Low**

---

## 6. Deploy Script (Architect Output)

**Verdict: GOOD — well-structured, safe defaults**

- Backup-before-overwrite logic is correct (uses `diff -q` to skip identical files)
- Interactive mode with tool detection
- Dry-run mode available
- Validation step after each deployment

### Issues Found

14. **Claude Code deployment path for settings.json** — The deploy script says it won't overwrite existing settings.json (warns user to merge manually). This is the right approach since settings.json contains user-specific MCP server paths. **Severity: None — correct behavior.**

15. **deploy.sh does NOT address the `~/.claude/hooks/` path issue** in OpenCode commands. It copies hooks to `~/.opencode/hooks/` but the OpenCode skill files still reference `~/.claude/hooks/`. **Severity: HIGH — same as Issue #5/#9.**

---

## 7. Cross-Cutting Issues

### Issue #5/#9/#15 — Path References (CRITICAL)

The most significant issue across the entire toolkit: **OpenCode commands/skills hardcode `~/.claude/hooks/` paths**.

Files affected:
- `portable/opencode/commands/chef.md` (line 16)
- `portable/opencode/commands/chef-async.md` (line 16)
- `portable/opencode/commands/auto.md` (line 27)
- `portable/opencode/commands/batch.md` (line 22)

These should reference `~/.opencode/hooks/` or use a variable/relative path.

**Recommended fix:** Replace `~/.claude/hooks/` with `~/.opencode/hooks/` in all OpenCode skill files, since deploy.sh copies hooks there.

### Issue #4 — Companion File Path Mismatch (MEDIUM)

AGENTS.md references `companion/WieArbeitestDuMitSamuel.md` but Claude Code deployment places these as flat files in `~/.claude/`. Either:
- a) Deploy.sh should create `~/.claude/companion/` and put them there, OR
- b) The Claude Code deployment should patch the paths in AGENTS.md

### SPEC vs. Actual Consistency

The SPEC's tool abstraction table (Section 4.2) is consistent with what the Codex porter used. The Codex skills correctly use `{{delegate_code_run()}}`, `{{research()}}`, `{{gather_context()}}` etc.

The OpenCode porter chose NOT to use abstract tool syntax (no `{{}}` notation) and instead wrote native OpenCode API calls. This is a valid approach — the SPEC says "the transpiler maps these to the correct tool call for each target" — so the OpenCode output IS the transpiled result. Not an issue, just an observation.

### COMPATIBILITY.md Consistency

My COMPATIBILITY.md findings align with:
- AGENTS.codex.md (confirms Codex limitations — no MCP, no async, no multi-agent)
- AGENTS.opencode.md (confirms OpenCode capabilities)
- SPEC Section 4.2 "N/A" entries for voice in Codex/OpenCode
- Codex skills that note their own limitations (e.g., chef-async's Codex limitation note)

No contradictions found between COMPATIBILITY.md and other outputs.

---

## Summary

| Area | Status | Issues |
|------|--------|--------|
| SPEC.md | Done, solid | 2 low, 1 medium |
| Instructions (AGENTS.md + overrides) | Done, good | 1 medium, 1 HIGH |
| Companion files | Done, faithful | None |
| Codex skills (30/30) | Done, good | 2 low |
| OpenCode skills (13/30) | In progress | 1 HIGH (paths), 17 skills pending |
| Hooks & config | Done | 2 low |
| Deploy script | Done, well-built | 1 HIGH (path propagation) |
| COMPATIBILITY.md | Done, consistent | None |

### Critical Action Items

1. **[HIGH] Fix `~/.claude/hooks/` paths in OpenCode commands** — Replace with `~/.opencode/hooks/` in all 4 affected files (chef.md, chef-async.md, auto.md, batch.md) and any future OpenCode skills that reference hooks.

2. **[HIGH] Ensure deploy.sh propagates correct paths** — After OpenCode skill porting completes, verify no `~/.claude/` references remain in OpenCode output.

3. **[MEDIUM] Resolve companion file path mismatch** — Either change AGENTS.md references or change deploy.sh for Claude Code target.

4. **[WAIT] OpenCode complex skills** — 6 skill directories are empty shells. Wait for porter-opencode to complete, then re-review.
