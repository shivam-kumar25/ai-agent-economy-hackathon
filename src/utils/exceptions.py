from __future__ import annotations


class GrowthMeshError(Exception):
    """Base exception for all GrowthMesh errors."""


class AgentHansaError(GrowthMeshError):
    """AgentHansa API error."""


class BotLearnError(GrowthMeshError):
    """BotLearn API error."""


class FluxAError(GrowthMeshError):
    """FluxA payment error."""


class TokenBudgetExceededError(GrowthMeshError):
    """Token budget exhausted — switch to haiku or halt expensive tasks."""


class ReviewGateError(GrowthMeshError):
    """Output failed self-review after max retries — saved locally, not submitted."""


class CrawlError(GrowthMeshError):
    """Web crawl failed for all target URLs."""


class SearchError(GrowthMeshError):
    """Web search failed after retries."""
