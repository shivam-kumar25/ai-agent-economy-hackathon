from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import httpx

from src.core.memory import memory
from src.modules.botlearn.client import bl_client
from src.utils.llm import llm, llm_fast
from src.utils.logger import logger


async def run_botlearn_heartbeat() -> None:
    """12-hour BotLearn heartbeat: SDK check → browse → engage → skill post → DM."""
    logger.info("BotLearn heartbeat — start")

    # 1 — SDK version check (async HTTP, not sync httpx.get)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://www.botlearn.ai/sdk/skill.json")
            remote = resp.json()
        skill_path = Path("skills/botlearn/skill.json")
        if skill_path.exists():
            local = json.loads(skill_path.read_text())
            if remote.get("version") != local.get("version"):
                logger.info(f"BotLearn SDK update available: {local.get('version')} → {remote.get('version')}")
    except Exception as exc:
        logger.debug(f"SDK version check failed (non-fatal): {exc}")

    # 2 — Browse and score community feed
    try:
        posts = (await bl_client.get("/api/community/posts?limit=15")).get("posts", [])
        scored = []
        for post in posts:
            try:
                raw = (await llm_fast.ainvoke(
                    f"Rate this AI agent community post quality 1-5 (number only):\n{post.get('body', '')[:200]}"
                )).content.strip()
                scored.append((post, int(raw)))
            except (ValueError, Exception):
                scored.append((post, 3))

        scored.sort(key=lambda x: x[1], reverse=True)

        # 3 — Upvote top 3
        for post, _ in scored[:3]:
            try:
                await bl_client.post(f"/api/community/posts/{post['id']}/vote", {})
            except Exception:
                pass

        # Comment on the top post
        if scored:
            top_post = scored[0][0]
            comment = (await llm.ainvoke(
                f"Write a 1-2 sentence insightful comment for an AI agent community post. "
                f"Post:\n{top_post.get('body', '')[:500]}"
            )).content
            try:
                await bl_client.post(f"/api/community/posts/{top_post['id']}/comments", {"body": comment})
            except Exception:
                pass
    except Exception as exc:
        logger.warning(f"Feed browse failed: {exc}")

    # 4 — Skill experience post (only if tasks ran since last heartbeat)
    try:
        tasks_done = memory.flush_tasks_since_heartbeat()
        if tasks_done:
            exp_post = (await llm.ainvoke(
                f"Write a 100-word skill experience post for an AI agent community. "
                f"Tasks completed: {', '.join(set(tasks_done))}. Be specific about results."
            )).content
            await bl_client.post("/api/community/posts", {
                "title":    f"GrowthMesh execution report — {', '.join(set(tasks_done))}",
                "body":     exp_post,
                "category": "skill-experience",
            })
    except Exception as exc:
        logger.warning(f"Skill experience post failed: {exc}")

    # 5 — DM check and reply
    try:
        dms = (await bl_client.get("/api/community/dm/inbox")).get("messages", [])
        for dm in dms[:3]:
            try:
                reply = (await llm.ainvoke(
                    f"Reply helpfully in 2-3 sentences to this AI agent community DM:\n{dm.get('body', '')}"
                )).content
                await bl_client.post(f"/api/community/dm/{dm['thread_id']}/reply", {"body": reply})
            except Exception:
                pass
    except Exception as exc:
        logger.warning(f"DM check failed: {exc}")

    memory.update_botlearn_state(last_heartbeat=datetime.utcnow().isoformat())
    logger.success("BotLearn heartbeat — done")
