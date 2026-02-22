from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AgentEvent:
    timestamp: datetime
    session_id: str
    agent: str  # "opus", "sonnet", "flash", "haiku", "minimax"
    event_type: (
        str  # "user_msg", "assistant_msg", "tool_call", "tool_result", "delegation"
    )
    tokens_in: int
    tokens_out: int
    cost_usd: float
    duration_ms: Optional[int] = None
    tool_name: Optional[str] = None
    parent_event_id: Optional[str] = None
    content_preview: str = ""
    metadata: dict = field(default_factory=dict)
    source: str = ""  # "claude" or "opencode"
