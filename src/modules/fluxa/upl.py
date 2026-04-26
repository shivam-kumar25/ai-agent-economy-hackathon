from __future__ import annotations

from src.modules.fluxa.wallet import fluxa_client
from src.utils.logger import logger


async def pay_agent(agent_id: str, amount_usd: float, reason: str) -> dict:
    """Pay another agent via FluxA UPL (agent-to-agent transfer)."""
    logger.info(f"UPL payment: ${amount_usd:.2f} → agent {agent_id} ({reason})")
    result = await fluxa_client.request_payout(amount_usd, destination=agent_id)
    logger.success(f"UPL payment complete: {result}")
    return result
