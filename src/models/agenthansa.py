from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CheckinResult(BaseModel):
    streak_day: int
    payout_usd: float
    xp_earned: int
    message: str = ""


class RedPacket(BaseModel):
    id: str
    challenge_type: str
    reward_usd: float


class AllianceAgent(BaseModel):
    id: str
    name: str
    alliance: str
    xp: int
    tier: str


class AgentState(BaseModel):
    agent_id: str = ""
    agent_name: str = "GrowthMesh"
    streak_days: int = 0
    xp: int = 0
    tier: str = "newcomer"
    last_checkin: str = ""
    last_agenthansa_tick: str = ""
    tasks_since_heartbeat: list[str] = Field(default_factory=list)
    total_tokens_used: int = 0
    last_task_tokens: int = 0
