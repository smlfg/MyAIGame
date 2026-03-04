# Cost Dashboard & Token Monitoring — TUI Design

> Real-time cost visibility for the unified AI skill runtime.
> You should always know what you're spending. No surprises.

---

## 1. Live Cost Ticker (Always-Visible Status Bar)

The cost ticker lives in the bottom status bar of the TUI — always visible, never hidden.

```
 ╔══════════════════════════════════════════════════════════════════════════════╗
 ║  💰 Session: $2.34 │ Today: $8.12 │ Month: $47.50 │ Budget: $100          ║
 ║     [██████████░░░░░░░░░░]  47%  •  $52.50 remaining  •  12d left          ║
 ╚══════════════════════════════════════════════════════════════════════════════╝
```

**Color coding:**
- Green  (0–79% budget used): Normal operation
- Yellow (80–94%): Warning — approaching limit
- Red    (95–100%): Critical — near or at limit
- Flashing red: Hard stop triggered

**Update frequency:** After every skill invocation (not real-time polling — event-driven).

**Compact mode** (when terminal is narrow < 100 cols):
```
 💰 $2.34 | Today $8.12 | [██████░░░░] 47%
```

---

## 2. Per-Backend Breakdown (Expandable Panel)

Press `C` or `F6` to open the Cost Panel. It overlays the main TUI as a floating panel.

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  COST BREAKDOWN  (Session: 47min)                    [ESC] close │
 ├─────────────────┬──────────┬──────────┬────────────┬────────────┤
 │  Backend        │   Cost   │  Calls   │  In Tokens │ Out Tokens │
 ├─────────────────┼──────────┼──────────┼────────────┼────────────┤
 │  Claude Code    │  $1.84   │     23   │    48,200  │    12,400  │
 │  OpenCode       │  $0.41   │      8   │    18,900  │     4,100  │
 │  Gemini Flash   │  $0.07   │     12   │   210,000  │    42,000  │
 │  Codex          │  $0.02   │      3   │     5,100  │     1,200  │
 │  Local/Free     │  $0.00   │      5   │         -  │         -  │
 ├─────────────────┼──────────┼──────────┼────────────┼────────────┤
 │  TOTAL          │  $2.34   │     51   │   282,200  │    59,700  │
 └─────────────────┴──────────┴──────────┴────────────┴────────────┘

  Tip: Gemini handled 12 research calls for $0.07. Claude would cost ~$1.80 for
  the same calls. Smart routing saved you ~$1.73 this session.
```

**Navigation:** Arrow keys to scroll, `Enter` to drill into a backend for per-model detail.

**Per-model drilldown (e.g., Claude Code):**
```
 ┌─────────────────────────────────────────────────────────────────┐
 │  CLAUDE CODE — Model Detail                                      │
 ├────────────────────┬──────────┬────────────────────────────────┤
 │  Model             │  Cost    │  Calls                         │
 ├────────────────────┼──────────┼────────────────────────────────┤
 │  claude-opus-4-6   │  $1.62   │  8 calls (strategy/planning)  │
 │  claude-sonnet-4-6 │  $0.18   │  12 calls (execution)         │
 │  claude-haiku-4-5  │  $0.04   │  3 calls (subagents)          │
 └────────────────────┴──────────┴────────────────────────────────┘
```

---

## 3. Per-Skill Cost Tracking

### 3.1 Skill Cost Panel

Press `S` or `F7` to open Skill Cost view.

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  SKILL COSTS  (Today)                                [ESC] close │
 ├────────────────┬────────┬───────┬──────────┬───────────────────┤
 │  Skill         │  Tier  │ Calls │ Avg Cost │ Total Today       │
 ├────────────────┼────────┼───────┼──────────┼───────────────────┤
 │  /chef         │  low   │   12  │  $3.00   │ $36.00  ████████  │
 │  /research     │  low   │    8  │  $0.12   │  $0.96  █         │
 │  /test         │ medium │    3  │  $1.80   │  $5.40  ███       │
 │  /crew         │  high  │    1  │  $4.20   │  $4.20  ███       │
 │  /chef-lite    │minimal │    5  │  $0.18   │  $0.90  █         │
 │  /checkpoint   │  free  │    6  │  $0.00   │  $0.00            │
 ├────────────────┼────────┼───────┼──────────┼───────────────────┤
 │  TOTAL         │        │   35  │          │ $47.46            │
 └────────────────┴────────┴───────┴──────────┴───────────────────┘

  ⚠ /chef used 12x today at $36.00. Consider /chef-lite for simple
    tasks — estimated savings: $18.00 (50% reduction).
```

### 3.2 Smart Suggestions Engine

Suggestions appear in the skill cost panel and as occasional status bar toasts.
They fire when thresholds are crossed — not on every invocation.

**Trigger conditions and message templates:**

| Trigger | Message |
|---------|---------|
| `/chef` > 5x/day | "You used /chef 12x today ($36). /chef-lite costs ~$0.18/call for simple tasks." |
| Research via Claude Code | "3 research calls via Claude Code ($4.50). Gemini would cost $0.04 total." |
| Skill above cost tier | "/test ran for $4.20 (expected max $1.00). Input size may be driving costs." |
| Same skill > 3x with similar args | "Repeated /debug-loop with similar input. Consider /test-crew for systematic debugging." |
| Monthly budget > 80% before mid-month | "Budget 80% used on day 12. At this rate: $187 this month vs $100 budget." |

Suggestions are non-blocking toasts — never interrupt workflow.

---

## 4. Budget Alerts System

### 4.1 Budget Configuration (in `~/.myaigame/config.yaml`)

```yaml
budget:
  daily: 15.00       # USD
  weekly: 60.00
  monthly: 100.00
  currency: USD

alerts:
  warn_at: 0.80      # 80% — yellow warning
  stop_at: 1.00      # 100% — hard stop (optional)
  hard_stop: false   # true = refuse new calls at 100%
  notify_sound: false

routing_on_low_budget:
  enabled: true
  threshold: 0.90    # trigger at 90% budget used
  prefer_tiers: [free, minimal, low]  # only allow these tiers
```

### 4.2 Alert States

```
 ┌────────────────────────────────────────────────────────────┐
 │  BUDGET WARNING                                            │
 │                                                            │
 │  Daily budget: $15.00                                      │
 │  Spent today:  $12.34  (82%)                               │
 │  Remaining:    $2.66                                       │
 │                                                            │
 │  Smart routing activated: preferring cheap backends.       │
 │  /chef → routed to /chef-lite automatically.               │
 │                                                            │
 │  [C] Configure budget   [I] Ignore   [S] See breakdown     │
 └────────────────────────────────────────────────────────────┘
```

```
 ┌────────────────────────────────────────────────────────────┐
 │  BUDGET LIMIT REACHED                                      │
 │                                                            │
 │  Monthly budget of $100.00 has been reached.               │
 │  Hard stop is OFF — you can continue but will be           │
 │  charged above your budget.                                │
 │                                                            │
 │  [C] Raise limit   [P] Pause AI calls   [X] Continue anyway│
 └────────────────────────────────────────────────────────────┘
```

### 4.3 Budget Alert Flow

```
Every skill invocation:
  POST_CALL → update_totals()
            → check_thresholds()
              ├── < 80%   → no action
              ├── 80-94%  → show yellow warning toast (once per session)
              ├── 95-99%  → show red warning (every invocation)
              └── >= 100% → show hard stop modal (if hard_stop=true: block call)
```

---

## 5. Token Economics Engine (Python)

### 5.1 Data Classes

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class CostTier(str, Enum):
    FREE = "free"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VARIABLE = "variable"


class Backend(str, Enum):
    CLAUDE_CODE = "claude-code"
    OPENCODE = "opencode"
    CODEX = "codex"
    GEMINI = "gemini"
    LOCAL = "local"


@dataclass
class ProviderPricing:
    """Pricing per 1M tokens in USD. Update when providers change rates."""
    provider_id: str
    model_id: str
    input_per_million: float    # USD per 1M input tokens
    output_per_million: float   # USD per 1M output tokens
    has_cache: bool = False
    cache_write_per_million: float = 0.0
    cache_read_per_million: float = 0.0

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> float:
        cost = (
            (input_tokens / 1_000_000) * self.input_per_million
            + (output_tokens / 1_000_000) * self.output_per_million
        )
        if self.has_cache:
            cost += (cache_write_tokens / 1_000_000) * self.cache_write_per_million
            cost += (cache_read_tokens / 1_000_000) * self.cache_read_per_million
        return cost


# Pricing table — update these as providers change rates
PRICING_TABLE: dict[tuple[str, str], ProviderPricing] = {
    ("anthropic", "claude-opus-4-6"): ProviderPricing(
        provider_id="anthropic",
        model_id="claude-opus-4-6",
        input_per_million=15.00,
        output_per_million=75.00,
        has_cache=True,
        cache_write_per_million=18.75,
        cache_read_per_million=1.50,
    ),
    ("anthropic", "claude-sonnet-4-6"): ProviderPricing(
        provider_id="anthropic",
        model_id="claude-sonnet-4-6",
        input_per_million=3.00,
        output_per_million=15.00,
        has_cache=True,
        cache_write_per_million=3.75,
        cache_read_per_million=0.30,
    ),
    ("anthropic", "claude-haiku-4-5"): ProviderPricing(
        provider_id="anthropic",
        model_id="claude-haiku-4-5",
        input_per_million=0.80,
        output_per_million=4.00,
    ),
    ("google", "gemini-2.0-flash"): ProviderPricing(
        provider_id="google",
        model_id="gemini-2.0-flash",
        input_per_million=0.10,
        output_per_million=0.40,
    ),
    ("openai", "gpt-4o"): ProviderPricing(
        provider_id="openai",
        model_id="gpt-4o",
        input_per_million=2.50,
        output_per_million=10.00,
    ),
    ("local", "ollama"): ProviderPricing(
        provider_id="local",
        model_id="ollama",
        input_per_million=0.0,
        output_per_million=0.0,
    ),
}


@dataclass
class CostEvent:
    """A single AI call with full cost accounting."""
    event_id: str
    timestamp: datetime
    skill_name: str             # e.g. "chef", "research", "test"
    backend: Backend
    provider_id: str            # e.g. "anthropic"
    model_id: str               # e.g. "claude-opus-4-6"
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    cost_tier: CostTier = CostTier.FREE
    session_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.cost_usd == 0.0:
            key = (self.provider_id, self.model_id)
            if key in PRICING_TABLE:
                pricing = PRICING_TABLE[key]
                self.cost_usd = pricing.calculate_cost(
                    self.input_tokens,
                    self.output_tokens,
                    self.cache_write_tokens,
                    self.cache_read_tokens,
                )


@dataclass
class SessionBudget:
    """Tracks budget consumption across time windows."""
    daily_limit: float = 15.00
    weekly_limit: float = 60.00
    monthly_limit: float = 100.00
    currency: str = "USD"

    # Runtime state — populated by CostTracker
    session_spent: float = 0.0
    today_spent: float = 0.0
    week_spent: float = 0.0
    month_spent: float = 0.0

    @property
    def daily_pct(self) -> float:
        return self.today_spent / self.daily_limit if self.daily_limit else 0.0

    @property
    def monthly_pct(self) -> float:
        return self.month_spent / self.monthly_limit if self.monthly_limit else 0.0

    @property
    def daily_remaining(self) -> float:
        return max(0.0, self.daily_limit - self.today_spent)

    @property
    def monthly_remaining(self) -> float:
        return max(0.0, self.monthly_limit - self.month_spent)

    def alert_level(self, window: str = "daily") -> str:
        """Returns 'ok', 'warn', 'critical', or 'over'."""
        pct = self.daily_pct if window == "daily" else self.monthly_pct
        if pct >= 1.0:
            return "over"
        if pct >= 0.95:
            return "critical"
        if pct >= 0.80:
            return "warn"
        return "ok"
```

### 5.2 CostTracker — Storage and Query Engine

```python
import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime, date, timedelta
from uuid import uuid4


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cost_events (
    event_id    TEXT PRIMARY KEY,
    timestamp   TEXT NOT NULL,
    skill_name  TEXT NOT NULL,
    backend     TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    model_id    TEXT NOT NULL,
    input_tokens  INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_write_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens  INTEGER NOT NULL DEFAULT 0,
    cost_usd    REAL NOT NULL DEFAULT 0.0,
    cost_tier   TEXT,
    session_id  TEXT,
    tags        TEXT,   -- JSON array
    metadata    TEXT    -- JSON object
);
CREATE INDEX IF NOT EXISTS idx_timestamp  ON cost_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_skill_name ON cost_events(skill_name);
CREATE INDEX IF NOT EXISTS idx_backend    ON cost_events(backend);
"""


class CostTracker:
    def __init__(self, db_path: Path = Path("~/.myaigame/costs.db")):
        self.db_path = db_path.expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def record(self, event: CostEvent) -> None:
        self._conn.execute(
            """INSERT INTO cost_events VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event.event_id,
                event.timestamp.isoformat(),
                event.skill_name,
                event.backend.value,
                event.provider_id,
                event.model_id,
                event.input_tokens,
                event.output_tokens,
                event.cache_write_tokens,
                event.cache_read_tokens,
                event.cost_usd,
                event.cost_tier.value,
                event.session_id,
                json.dumps(event.tags),
                json.dumps(event.metadata),
            ),
        )
        self._conn.commit()

    def total_today(self) -> float:
        today = date.today().isoformat()
        row = self._conn.execute(
            "SELECT COALESCE(SUM(cost_usd),0) FROM cost_events WHERE timestamp >= ?",
            (today,),
        ).fetchone()
        return row[0]

    def total_month(self) -> float:
        month_start = date.today().replace(day=1).isoformat()
        row = self._conn.execute(
            "SELECT COALESCE(SUM(cost_usd),0) FROM cost_events WHERE timestamp >= ?",
            (month_start,),
        ).fetchone()
        return row[0]

    def by_skill(self, since: Optional[date] = None) -> list[dict]:
        since_str = (since or date.today()).isoformat()
        rows = self._conn.execute(
            """SELECT skill_name,
                      COUNT(*) as calls,
                      ROUND(AVG(cost_usd),4) as avg_cost,
                      ROUND(SUM(cost_usd),4) as total_cost
               FROM cost_events
               WHERE timestamp >= ?
               GROUP BY skill_name
               ORDER BY total_cost DESC""",
            (since_str,),
        ).fetchall()
        return [
            {"skill": r[0], "calls": r[1], "avg_cost": r[2], "total_cost": r[3]}
            for r in rows
        ]

    def by_backend(self, since: Optional[date] = None) -> list[dict]:
        since_str = (since or date.today()).isoformat()
        rows = self._conn.execute(
            """SELECT backend,
                      COUNT(*) as calls,
                      SUM(input_tokens) as in_tokens,
                      SUM(output_tokens) as out_tokens,
                      ROUND(SUM(cost_usd),4) as total_cost
               FROM cost_events
               WHERE timestamp >= ?
               GROUP BY backend
               ORDER BY total_cost DESC""",
            (since_str,),
        ).fetchall()
        return [
            {
                "backend": r[0], "calls": r[1],
                "input_tokens": r[2], "output_tokens": r[3],
                "total_cost": r[4],
            }
            for r in rows
        ]

    def export_csv(self, output_path: Path, since: Optional[date] = None) -> Path:
        since_str = (since or date(2020, 1, 1)).isoformat()
        rows = self._conn.execute(
            "SELECT * FROM cost_events WHERE timestamp >= ? ORDER BY timestamp",
            (since_str,),
        ).fetchall()
        cols = [
            "event_id","timestamp","skill_name","backend","provider_id","model_id",
            "input_tokens","output_tokens","cache_write_tokens","cache_read_tokens",
            "cost_usd","cost_tier","session_id","tags","metadata",
        ]
        with open(output_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        return output_path

    def export_markdown(self, since: Optional[date] = None) -> str:
        today = date.today()
        since = since or today.replace(day=1)
        lines = [
            f"# AI Cost Report — {since} to {today}",
            "",
            f"**Total: ${self.total_month():.2f}**",
            "",
            "## By Skill",
            "| Skill | Calls | Avg Cost | Total |",
            "|-------|-------|----------|-------|",
        ]
        for row in self.by_skill(since):
            lines.append(
                f"| {row['skill']} | {row['calls']} | ${row['avg_cost']:.4f} | ${row['total_cost']:.2f} |"
            )
        lines += ["", "## By Backend", "| Backend | Calls | In Tokens | Out Tokens | Total |",
                  "|---------|-------|-----------|------------|-------|"]
        for row in self.by_backend(since):
            lines.append(
                f"| {row['backend']} | {row['calls']} | {row['input_tokens']:,} | "
                f"{row['output_tokens']:,} | ${row['total_cost']:.2f} |"
            )
        return "\n".join(lines)
```

---

## 6. Cost-Aware Routing Integration

### 6.1 Architecture

```
  Skill invocation
        │
        ▼
  SmartRouter.route(skill, args, context)
        │
        ├── query CostTracker.budget_status()
        │
        ├── [budget OK]     → normal tier selection
        │
        ├── [budget WARN]   → prefer cheaper alternatives
        │   ├── /chef       → /chef-lite (if task simple enough)
        │   ├── /research   → gemini (already cheap, keep)
        │   └── /test       → /test with cheaper model
        │
        └── [budget CRITICAL] → free/minimal only
            ├── reject high/medium tier skills
            └── notify user with options
```

### 6.2 Routing Decisions (Python)

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingDecision:
    original_skill: str
    routed_skill: str
    original_backend: Backend
    routed_backend: Backend
    reason: str
    estimated_savings: float


class BudgetAwareRouter:
    """Wraps the smart router with budget awareness."""

    CHEAPER_ALTERNATIVES: dict[str, str] = {
        "chef": "chef-lite",
        "research-swarm": "research",
        "test-crew": "test",
        "crew": "chef",
        "swarm": "chef-async",
    }

    TIER_WEIGHTS: dict[str, int] = {
        "free": 0, "minimal": 1, "low": 2,
        "medium": 3, "high": 4, "variable": 2,
    }

    def route(
        self,
        skill_name: str,
        budget: SessionBudget,
        skill_tier: CostTier,
    ) -> RoutingDecision:
        alert = budget.alert_level("daily")

        if alert == "ok":
            return RoutingDecision(
                skill_name, skill_name,
                Backend.CLAUDE_CODE, Backend.CLAUDE_CODE,
                "budget healthy", 0.0,
            )

        if alert == "warn" and skill_tier in (CostTier.HIGH, CostTier.VARIABLE):
            alt = self.CHEAPER_ALTERNATIVES.get(skill_name, skill_name)
            return RoutingDecision(
                skill_name, alt,
                Backend.CLAUDE_CODE, Backend.OPENCODE,
                f"budget at {budget.daily_pct:.0%} — routing to cheaper alternative",
                estimated_savings=0.5,  # rough estimate
            )

        if alert in ("critical", "over"):
            tier_val = self.TIER_WEIGHTS.get(skill_tier.value, 99)
            if tier_val >= 3:  # medium or higher
                return RoutingDecision(
                    skill_name, skill_name,
                    Backend.CLAUDE_CODE, Backend.CLAUDE_CODE,
                    "BLOCKED: budget critical, only free/minimal/low tiers allowed",
                    0.0,
                )

        return RoutingDecision(
            skill_name, skill_name,
            Backend.CLAUDE_CODE, Backend.CLAUDE_CODE,
            "within tier limits", 0.0,
        )
```

### 6.3 Pinning Skills to Cheap Backends

The router learns from history. After N calls, if a skill always succeeds on
a cheaper backend, it gets pinned there:

```yaml
# ~/.myaigame/routing-pins.yaml  (auto-generated, user-editable)
pins:
  research: gemini          # 100% success rate, 97% cheaper than claude
  chef-lite: opencode       # 94% success rate, 80% cheaper
  checkpoint: local         # free, no AI needed
```

---

## 7. Full ASCII Dashboard Mockup

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  MyAIGame — Cost Dashboard                                        F6 close  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  LIVE TOTALS                                                                 ║
║  ┌──────────────┬──────────────┬──────────────┬─────────────────────────┐   ║
║  │ Session      │ Today        │ This Month   │ Monthly Budget          │   ║
║  │   $2.34      │   $8.12      │  $47.50      │ [██████████░░░░░░░░░░]  │   ║
║  │  51 calls    │  142 calls   │  891 calls   │  47%  •  $52.50 left    │   ║
║  └──────────────┴──────────────┴──────────────┴─────────────────────────┘   ║
║                                                                              ║
║  TOP SKILLS TODAY                    BACKEND BREAKDOWN (session)            ║
║  ┌──────────────────────────────┐    ┌──────────────────────────────────┐   ║
║  │ /chef        12x  $36.00 ████│    │ Claude Code  $1.84   23 calls    │   ║
║  │ /test         3x   $5.40 ███ │    │ OpenCode     $0.41    8 calls    │   ║
║  │ /crew         1x   $4.20 ███ │    │ Gemini Flash $0.07   12 calls    │   ║
║  │ /research     8x   $0.96 █   │    │ Codex        $0.02    3 calls    │   ║
║  │ /chef-lite    5x   $0.90 █   │    │ Local/Free   $0.00    5 calls    │   ║
║  │ /checkpoint   6x   $0.00     │    └──────────────────────────────────┘   ║
║  └──────────────────────────────┘                                            ║
║                                                                              ║
║  SAVINGS OPPORTUNITIES                                                       ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │ ⚡ /chef used 12x today ($36.00). /chef-lite = ~$18 savings.         │   ║
║  │ ✓  Gemini handled 12 research calls for $0.07 (vs ~$1.80 on Claude)  │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  [R] Report  [E] Export CSV  [B] Budget Config  [H] History  [ESC] Close    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Integration Points

### 8.1 Where CostTracker hooks into the runtime

```
Skill lifecycle:
  PRE_CALL  → SmartRouter queries budget, may reroute
  CALL      → AI backend executes
  POST_CALL → CostTracker.record(CostEvent(...))
            → SessionBudget.update()
            → StatusBar.refresh()
            → SuggestionsEngine.check()
```

### 8.2 Files

```
~/.myaigame/
  costs.db              # SQLite — all CostEvents
  config.yaml           # budget limits, alert thresholds
  routing-pins.yaml     # auto-learned backend preferences
  reports/
    2026-02-cost.csv    # auto-exported at month end
    2026-02-cost.md     # markdown summary
```

### 8.3 Config integration (SPEC.md cost-tier field)

The `cost-tier` frontmatter field from SPEC.md section 2.2 maps directly to
`CostTier` enum values. The router reads this at invocation time to decide
whether to allow, warn, or reroute the call based on current budget state.

| SPEC cost-tier | CostTier enum  | Budget WARN action          | Budget CRITICAL action |
|----------------|----------------|-----------------------------|------------------------|
| `free`         | FREE           | allow                       | allow                  |
| `minimal`      | MINIMAL        | allow                       | allow                  |
| `low`          | LOW            | allow                       | allow                  |
| `medium`       | MEDIUM         | warn + suggest cheaper alt  | block (optional)       |
| `high`         | HIGH           | route to cheaper alt        | block                  |
| `variable`     | VARIABLE       | warn                        | warn + cap tokens      |

---

## 9. Implementation Notes

- **SQLite over JSON** for history: supports queries, aggregation, and large history without parsing full files.
- **Event-driven updates**: StatusBar refreshes only after POST_CALL, not on a timer — avoids unnecessary redraws.
- **Suggestions are stateful**: the SuggestionsEngine tracks which suggestions have been shown per session to avoid repeating them.
- **Pricing table is a constant dict** in Python source, not config — so it can be updated via git diff, not silent config edits.
- **Export on session end**: auto-export to CSV when monthly budget crosses 80% or at month end.

---

*Last updated: 2026-02-26*
