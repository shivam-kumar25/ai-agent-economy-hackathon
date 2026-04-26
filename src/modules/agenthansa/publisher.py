from __future__ import annotations

from src.modules.agenthansa.client import ah_client
from src.utils.logger import logger


async def publish_task(
    title: str,
    description: str,
    budget_usd: float,
    capabilities_required: list[str],
) -> dict:
    """Publish a task to the AgentHansa A2A mesh for another agent to execute."""
    result = await ah_client.post("/community/tasks", {
        "title":                  title,
        "description":            description,
        "budget":                 budget_usd,
        "capabilities_required":  capabilities_required,
        "alliance":               "open",
    })
    logger.info(f"Published A2A task: {result.get('id')} — {title}")
    return result
