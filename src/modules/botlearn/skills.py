from __future__ import annotations

from src.modules.botlearn.client import bl_client
from src.utils.logger import logger

_SKILL_MAP = {
    "seo_audit":           {"category": "seo",      "xp_per_run": 10},
    "competitor_analysis": {"category": "research",  "xp_per_run": 12},
    "market_research":     {"category": "research",  "xp_per_run": 12},
    "lead_generation":     {"category": "research",  "xp_per_run": 8},
    "blog_writing":        {"category": "content",   "xp_per_run": 15},
    "email_sequence":      {"category": "content",   "xp_per_run": 12},
    "social_copy":         {"category": "content",   "xp_per_run": 6},
}


async def submit_skill_proof(skill: str, run_id: str, score: float) -> dict:
    """Submit evidence of a skill execution to BotLearn for XP."""
    meta = _SKILL_MAP.get(skill, {"category": "general", "xp_per_run": 5})
    payload = {
        "skill": skill,
        "run_id": run_id,
        "score": score,
        "category": meta["category"],
        "expected_xp": meta["xp_per_run"],
    }
    try:
        result = await bl_client.post("/skills/proof", payload)
        logger.info(f"Skill proof submitted: {skill} — score={score:.2f}")
        return result
    except Exception as exc:
        logger.warning(f"Skill proof submission failed ({skill}): {exc}")
        return {}


async def get_skill_leaderboard(category: str = "seo") -> list[dict]:
    """Fetch the leaderboard for a skill category."""
    try:
        data = await bl_client.get(f"/skills/leaderboard/{category}")
        return data.get("entries", [])
    except Exception as exc:
        logger.warning(f"Leaderboard fetch failed ({category}): {exc}")
        return []
