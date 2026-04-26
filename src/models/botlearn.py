from __future__ import annotations

from pydantic import BaseModel, Field


class SkillRecord(BaseModel):
    id: str
    name: str
    install_id: str = ""


class BenchmarkDimensions(BaseModel):
    perceive: float = 0.0
    reason: float = 0.0
    act: float = 0.0
    memory: float = 0.0
    guard: float = 0.0
    autonomy: float = 0.0


class BenchmarkResult(BaseModel):
    session_id: str
    overall_score: float
    dimensions: BenchmarkDimensions


class BotLearnState(BaseModel):
    registered: bool = False
    benchmark_run: bool = False
    benchmark_score: float | None = None
    dimension_scores: dict = Field(default_factory=dict)
    last_benchmark_date: str = ""
    last_heartbeat: str = ""
    installed_skills: list[SkillRecord] = Field(default_factory=list)
    karma: int = 0
