"""Static tips database about Claude Code internals and best practices."""

import random

TIPS: list[str] = [
    "Use /compact after ~30 min sessions — context window quality degrades silently.",
    "CLI tools cost $0 — always try shell scripts before spawning an LLM.",
    "Gemini Flash costs ~$0.10/1M tokens. Use it for research, not Opus.",
    "OpenCode MCP runs Sonnet (~$3/1M) — good for code generation, not planning.",
    "Opus (~$15/1M) is for strategy only. Never use it for lookup tasks.",
    "SKILL_TRIGGERS: after Edit/Write → /test. After Stop → /recap.",
    "git add -A is risky — always specify files explicitly to avoid leaking secrets.",
    "Hooks exit 0 = success, exit 2 = block with message. Never hard-fail silently.",
    "/recap before closing a session. /learn before opening a new one.",
    "SubAgents with Haiku (~$0.25/1M) for background tasks > 5 minutes.",
    "Wave model: 1 Opus planning → N Sonnet building. Not N Opus everything.",
    "Plan Mode before spawning agent teams. 5 agents without a plan = chaos.",
    "PostToolUse hooks can log every tool call for cost analysis.",
    "Usage JSONL format: {\"time\": \"ISO8601\", \"tool\": \"ToolName\"}",
    "Textual TUI apps render in the terminal — no browser needed, zero network deps.",
    "pathlib.Path is safer than os.path — use it everywhere for file operations.",
    "datetime.now(timezone.utc) for timestamps — never use naive datetimes.",
    "Return empty results, not errors, when data files don't exist yet.",
    "Agent teams use Shift+Down to switch between teammates.",
    "~/.claude/settings.json controls hooks, env vars, and tool permissions.",
    "JSONL (one JSON object per line) is better than JSON arrays for streaming logs.",
    "context via gather-context.sh costs $0 — always use it before delegating.",
    "Session sprawl: 10 parallel sessions with no learning = performative productivity.",
    "The cheapest tool is the one you already have. Shell > MCP > LLM.",
    "Haiku is great for classification tasks — 'which skill fits this tool call?'",
    "Backup configs before editing: cp config.json config.json.backup-$(date +%Y%m%d)",
    "Edge TTS → Piper → spd-say: always have a fallback chain for audio.",
    "Never assume GNOME settings work on Pop!_OS COSMIC (Wayland).",
    "cognitive load: 3 similar lines > premature abstraction. YAGNI applies to LLMs too.",
    "FOR_SMLFLG.md in every project — architecture, decisions, lessons learned.",
]


def get_random_tip() -> str:
    """Return a random tip from the database."""
    return random.choice(TIPS)


def get_tips_count() -> int:
    """Return the total number of tips available."""
    return len(TIPS)
