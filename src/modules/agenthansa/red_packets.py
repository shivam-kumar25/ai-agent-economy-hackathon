from __future__ import annotations

from src.modules.agenthansa.client import ah_client
from src.utils.llm import llm_fast
from src.utils.logger import logger


async def handle_red_packets() -> None:
    """Check for active red packets and attempt to join each one."""
    try:
        packets = await ah_client.get("/red-packets")
    except Exception as exc:
        logger.warning(f"Red packets fetch failed: {exc}")
        return

    for p in packets.get("active", []):
        try:
            challenge = await ah_client.get(f"/red-packets/{p['id']}/challenge")
            answer = (await llm_fast.ainvoke(
                f"Answer in one word or number only. Question: {challenge.get('question', '')}"
            )).content.strip()
            await ah_client.post(f"/red-packets/{p['id']}/join", {"answer": answer})
            logger.success(f"Joined red packet {p['id']}")
        except Exception as exc:
            logger.warning(f"Red packet {p.get('id')} failed: {exc}")
