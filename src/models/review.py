from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReviewVerdict(BaseModel):
    score: int = Field(..., ge=0, le=100)
    passed: bool
    spec_compliance: bool
    depth: Literal["shallow", "adequate", "deep"]
    factual_issues: list[str] = Field(default_factory=list)
    format_correct: bool
    specific_feedback: str


class QuestTriage(BaseModel):
    task_type: str
    effort: Literal["low", "medium", "high"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    required_capabilities: list[str] = Field(default_factory=list)


class ScoredQuest(BaseModel):
    quest: dict
    triage: QuestTriage
    score: float
