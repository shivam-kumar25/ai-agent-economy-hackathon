from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SEOIssue(BaseModel):
    issue: str
    impact: Literal["high", "medium", "low"]
    fix: str
    effort: Literal["low", "medium", "high"]


class KeywordGap(BaseModel):
    topic: str
    competitor_ranking: str
    difficulty: Literal["low", "medium", "high"]
    search_intent: Literal["informational", "commercial", "transactional"]


class ContentOpportunity(BaseModel):
    title: str
    target_keyword: str
    search_intent: str
    estimated_traffic_potential: Literal["low", "medium", "high"]


class AuditResult(BaseModel):
    score: int = Field(..., ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "F"]
    summary: str
    critical_issues: list[SEOIssue]
    quick_wins: list[SEOIssue]
    keyword_gaps: list[KeywordGap]
    content_map: list[ContentOpportunity]
    delta: dict | None = None
