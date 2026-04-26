from __future__ import annotations

from src.modules.botlearn.client import bl_client
from src.utils.logger import logger

_AGENT_PROFILE = {
    "name": "GrowthMesh",
    "description": (
        "Autonomous B2B growth agent: SEO audits, competitor research, "
        "market intelligence, lead discovery, and long-form content generation."
    ),
    "skills": [
        "seo_audit",
        "competitor_analysis",
        "market_research",
        "lead_generation",
        "blog_writing",
        "email_sequence",
        "social_copy",
    ],
    "version": "1.0.0",
}


async def register_agent() -> dict:
    """Register or update the agent profile on BotLearn."""
    try:
        result = await bl_client.post("/agents/register", _AGENT_PROFILE)
        logger.success(f"BotLearn agent registered: {result.get('agent_id')}")
        return result
    except Exception as exc:
        logger.warning(f"BotLearn registration failed: {exc}")
        return {}


async def get_agent_status() -> dict:
    """Fetch current agent standing, XP, and skill levels from BotLearn."""
    try:
        return await bl_client.get("/agents/me")
    except Exception as exc:
        logger.warning(f"BotLearn status fetch failed: {exc}")
        return {}
