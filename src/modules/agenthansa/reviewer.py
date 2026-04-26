from __future__ import annotations

import json
from datetime import datetime

from src.core.chains import review_chain
from src.core.memory import memory
from src.db.engine import AsyncSessionLocal
from src.db.tables import ReviewRecord
from src.models.review import ReviewVerdict
from src.modules.agenthansa.client import ah_client
from src.utils.logger import logger


async def run_alliance_reviewer_pass() -> None:
    """Grade all unreviewed alliance submissions. Verify passing ones, post feedback on failing."""
    data = await ah_client.get("/alliance-war/quests")
    quests = data.get("quests", [])

    for quest in quests:
        try:
            subs_data = await ah_client.get(f"/alliance-war/quests/{quest['id']}/submissions")
        except Exception as exc:
            logger.warning(f"Submissions fetch failed for quest {quest['id']}: {exc}")
            continue

        for sub in subs_data.get("submissions", []):
            agent_id = sub.get("agent_id", "")
            quest_id = quest["id"]

            if await memory.already_reviewed(quest_id, agent_id):
                continue

            try:
                verdict: ReviewVerdict = await review_chain.ainvoke({
                    "spec":    json.dumps(quest.get("spec", {})),
                    "content": sub.get("content", ""),
                })
            except Exception as exc:
                logger.warning(f"Review chain failed for {quest_id}/{agent_id}: {exc}")
                continue

            # Persist review record
            async with AsyncSessionLocal() as session:
                session.add(ReviewRecord(
                    quest_id=quest_id,
                    agent_id=agent_id,
                    agent_name=sub.get("agent_name", "unknown"),
                    score=verdict.score,
                    verdict="pass" if verdict.passed else "fail",
                    feedback=verdict.specific_feedback,
                    created_at=datetime.utcnow(),
                ))
                await session.commit()

            if verdict.passed and verdict.score >= 75:
                try:
                    await ah_client.post(f"/alliance-war/quests/{quest_id}/verify", {})
                    logger.success(
                        f"Verified {sub.get('agent_name')} on quest {quest_id} — score {verdict.score}"
                    )
                except Exception as exc:
                    logger.warning(f"Verify badge failed: {exc}")
            else:
                try:
                    await ah_client.post("/forum", {
                        "alliance_only": True,
                        "title":    f"Quality feedback: {quest_id} — {sub.get('agent_name', 'agent')}",
                        "body":     (
                            f"Score: {verdict.score}/100\n\n"
                            f"Issues:\n{verdict.specific_feedback}\n\n"
                            f"Spec compliance: {verdict.spec_compliance}\n"
                            f"Depth: {verdict.depth}"
                        ),
                        "category": "feedback",
                    })
                except Exception as exc:
                    logger.warning(f"Forum feedback post failed: {exc}")
