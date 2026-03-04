"""Data models for TUI state persistence."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Session:
    id: str
    goal: str
    started_at: datetime
    ended_at: Optional[datetime]
    provider: str
    total_cost: float
    status: str  # 'active', 'completed', 'abandoned'


@dataclass
class Message:
    id: str
    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    tokens_in: int
    tokens_out: int
    cost: float


@dataclass
class SkillInvocation:
    id: str
    session_id: str
    skill_name: str
    provider: str
    cost: float
    duration_ms: int
    success: bool


@dataclass
class FocusSession:
    id: str
    session_id: str
    goal: str
    started_at: datetime
    duration_planned: int  # minutes
    duration_actual: Optional[int]  # minutes, None if not completed
    completed: bool


@dataclass
class ParkedDistraction:
    id: str
    session_id: str
    text: str
    created_at: datetime
    promoted_to_task: bool


@dataclass
class Checkpoint:
    id: str
    session_id: str
    git_hash: str
    summary: str
    files_changed: int
    tests_passed: Optional[bool]


@dataclass
class CostEvent:
    id: str
    session_id: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost: float
    timestamp: datetime
    context: str  # 'message', 'skill', 'tool'
