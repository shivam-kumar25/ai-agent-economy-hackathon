from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.core.memory import memory
from src.modules.agenthansa.client import ah_client
from src.utils.logger import logger

_AGENT_NAME = "GrowthMesh"
_AGENT_DESC = (
    "Full-stack B2B growth agent. SEO audits, competitor teardowns, market intelligence, "
    "lead generation, blog writing, email sequences, and social copy — every output "
    "self-reviewed and scored before delivery. LangGraph-orchestrated. LangSmith-traced."
)
_CAPABILITIES = ["seo_audit", "research", "content_writing", "lead_generation", "quality_review"]


async def register_agent() -> dict:
    """Call /api/agents/register without auth (first-time only).
    Returns the full response including api_key (tabb_...) and id."""
    s = get_settings()
    async with httpx.AsyncClient(base_url=s.agenthansa_base_url, timeout=30) as client:
        r = await client.post("/agents/register", json={
            "name":         _AGENT_NAME,
            "description":  _AGENT_DESC,
        })
        r.raise_for_status()
        return r.json()


async def ensure_registered() -> str:
    """Register on AgentHansa if not already. Idempotent. Returns agent_id."""
    state = memory.get_state()
    if state.agent_id:
        logger.debug(f"Already registered: {state.agent_id}")
        return state.agent_id

    s = get_settings()
    if s.agenthansa_api_key:
        # Key already set — just fetch profile to confirm registration
        try:
            profile = await ah_client.get("/agents/me")
            agent_id = profile.get("id", profile.get("agent_id", ""))
            memory.update_state(agent_id=agent_id, agent_name=profile.get("name", _AGENT_NAME))
            logger.success(f"AgentHansa confirmed — agent_id: {agent_id}")
            return agent_id
        except Exception:
            pass

    result = await register_agent()
    agent_id = result.get("id", result.get("agent_id", ""))
    api_key = result.get("api_key", "")
    memory.update_state(agent_id=agent_id, agent_name=result.get("name", _AGENT_NAME))

    if api_key:
        logger.success(
            f"[bold green]Registered on AgentHansa![/bold green]\n"
            f"  agent_id : {agent_id}\n"
            f"  api_key  : {api_key}\n\n"
            f"  → Add to .env:  AGENTHANSA_API_KEY={api_key}"
        )
    return agent_id


async def wire_fluxa_wallet() -> dict:
    """Link the FluxA wallet to this AgentHansa agent so it can receive payouts."""
    s = get_settings()
    if not s.fluxa_agent_id:
        logger.warning("FLUXA_AGENT_ID not set — skipping wallet link")
        return {}
    return await ah_client.put("/agents/fluxa-wallet", {"fluxa_agent_id": s.fluxa_agent_id})


async def get_profile() -> dict:
    return await ah_client.get("/agents/me")


async def get_earnings() -> dict:
    return await ah_client.get("/agents/earnings")


async def do_checkin() -> dict:
    result = await ah_client.post("/agents/checkin", {})
    memory.update_state(
        streak_days=result.get("streak_day", 0),
        last_checkin=__import__("datetime").datetime.utcnow().isoformat(),
    )
    return result
