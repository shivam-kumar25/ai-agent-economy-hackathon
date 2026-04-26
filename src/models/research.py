from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PricingTier(BaseModel):
    name: str
    price: str
    key_features: list[str]


class CompetitorTeardown(BaseModel):
    company: str
    positioning: str
    pricing_tiers: list[PricingTier]
    key_strengths: list[str]
    weaknesses: list[str]
    growth_signals: list[str]
    differentiation_opportunity: str


class MarketTrend(BaseModel):
    trend: str
    signal_strength: Literal["weak", "moderate", "strong"]
    implication: str


class MarketReport(BaseModel):
    market_size_signal: str
    top_trends: list[MarketTrend]
    buyer_triggers: list[str]
    icp_pain_points: list[str]
    underserved_niches: list[str]
    recommended_positioning: str


class LeadRecord(BaseModel):
    name: str
    title: str
    company: str
    linkedin_url: str | None = None
    funding_stage: str | None = None
    hiring_signals: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    confidence: int = Field(..., ge=0, le=100)


class LeadList(BaseModel):
    icp_summary: str
    leads: list[LeadRecord]
    total_found: int
