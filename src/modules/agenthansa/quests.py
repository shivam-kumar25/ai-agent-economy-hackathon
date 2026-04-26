from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.core.chains import triage_chain
from src.core.memory import memory
from src.db.engine import AsyncSessionLocal
from src.db.tables import QuestRecord
from src.models.review import QuestTriage, ScoredQuest
from src.modules.agenthansa.client import ah_client
from src.utils.logger import logger


def _map_quest_to_task_type(quest: dict) -> str:
    """Map AgentHansa quest category to GrowthMesh task_type."""
    category = quest.get("category", quest.get("type", "")).lower()
    if "seo" in category:
        return "seo_audit"
    if "blog" in category or "article" in category or "post" in category:
        return "content_blog"
    if "email" in category or "outreach" in category:
        return "content_email"
    if "social" in category or "linkedin" in category or "twitter" in category:
        return "content_social"
    if "competitor" in category or "competitive" in category:
        return "research_competitor"
    if "market" in category or "industry" in category:
        return "research_market"
    if "lead" in category:
        return "research_leads"
    return "content_blog"  # safe default


async def triage_quests() -> list[ScoredQuest]:
    """Fetch open quests, classify with haiku, return scored+filtered list."""
    data = await ah_client.get("/alliance-war/quests")
    quests = data.get("quests", [])
    if not quests:
        return []

    # Classify all quests concurrently — haiku is cheap
    triaged: list[QuestTriage] = await asyncio.gather(*[
        triage_chain.ainvoke({"quest_json": json.dumps(q)})
        for q in quests
    ], return_exceptions=True)

    effort_divisor = {"low": 1, "medium": 2, "high": 4}
    scored = []
    for quest, t in zip(quests, triaged):
        if isinstance(t, Exception):
            logger.warning(f"Triage failed for quest {quest.get('id')}: {t}")
            continue
        if t.confidence < 0.7 or t.effort == "high":
            continue
        scored.append(ScoredQuest(
            quest=quest,
            triage=t,
            score=quest.get("budget", 0) / effort_divisor.get(t.effort, 4),
        ))

    return sorted(scored, key=lambda x: x.score, reverse=True)


async def execute_quest(quest: dict) -> None:
    """Claim → run graph → self-review gate → submit."""
    from src.core.orchestrator import app as graph

    quest_id = quest["id"]
    task_type = _map_quest_to_task_type(quest)

    # Claim the quest
    try:
        await ah_client.post(f"/alliance-war/quests/{quest_id}/claim", {})
    except Exception as exc:
        logger.warning(f"Quest {quest_id} claim failed: {exc}")
        return

    result = await graph.ainvoke({
        "task_type":        task_type,
        "input":            {**quest.get("spec", {}), "quest_id": quest_id},
        "run_id":           str(uuid4()),
        "started_at":       datetime.utcnow().isoformat(),
        "review_iteration": 0,
        "tokens_used":      0,
    })

    verdict = result.get("review_verdict")
    score   = verdict["score"] if verdict else 0

    if score < 75:
        logger.warning(f"Quest {quest_id} failed self-review (score={score}). Not submitting.")
        return

    # Submit
    output_path = result.get("output_path", "")
    proof_url = Path(output_path).resolve().as_uri() if output_path else ""

    try:
        await ah_client.post(f"/alliance-war/quests/{quest_id}/submit", {
            "content":   result.get("final_output", ""),
            "proof_url": proof_url,
        })
        await ah_client.post(f"/alliance-war/quests/{quest_id}/verify", {})
        logger.success(f"Quest {quest_id} submitted (score={score}) + Human Verified badge requested")
    except Exception as exc:
        logger.error(f"Quest {quest_id} submit failed: {exc}")
        return

    # Record in SQLAlchemy
    async with AsyncSessionLocal() as session:
        session.add(QuestRecord(
            id=quest_id,
            task_type=task_type,
            title=quest.get("title", ""),
            reward_usd=quest.get("budget", 0),
            self_review_score=score,
            human_verified=True,
            tokens_used=result.get("tokens_used", 0),
            created_at=datetime.utcnow(),
        ))
        await session.commit()
