from __future__ import annotations

from src.modules.botlearn.client import bl_client
from src.utils.llm import llm_fast
from src.utils.logger import logger


async def browse_community_feed(limit: int = 20) -> list[dict]:
    """Fetch recent posts from the BotLearn community feed."""
    try:
        data = await bl_client.get("/community/feed", params={"limit": limit})
        return data.get("posts", [])
    except Exception as exc:
        logger.warning(f"Community feed fetch failed: {exc}")
        return []


async def engage_with_posts(posts: list[dict]) -> int:
    """Like and optionally reply to community posts. Returns engagement count."""
    engaged = 0
    for post in posts[:10]:
        post_id = post.get("id")
        if not post_id:
            continue
        try:
            await bl_client.post(f"/community/posts/{post_id}/like", {})
            engaged += 1

            if post.get("question") and engaged <= 3:
                question = post.get("content", "")[:500]
                reply = (await llm_fast.ainvoke(
                    f"Give a helpful, concise reply (1-2 sentences) to this community question: {question}"
                )).content.strip()
                await bl_client.post(f"/community/posts/{post_id}/reply", {"content": reply})
        except Exception as exc:
            logger.warning(f"Community engage failed (post {post_id}): {exc}")
    logger.info(f"Community engagement: {engaged} interactions")
    return engaged


async def reply_to_dms(limit: int = 5) -> int:
    """Fetch and reply to unread DMs on BotLearn. Returns reply count."""
    try:
        data = await bl_client.get("/community/dms/unread", params={"limit": limit})
        dms = data.get("messages", [])
    except Exception as exc:
        logger.warning(f"DM fetch failed: {exc}")
        return 0

    replied = 0
    for dm in dms:
        dm_id = dm.get("id")
        if not dm_id:
            continue
        try:
            content = dm.get("content", "")[:400]
            reply = (await llm_fast.ainvoke(
                f"Reply helpfully and briefly (1-2 sentences) to this message: {content}"
            )).content.strip()
            await bl_client.post(f"/community/dms/{dm_id}/reply", {"content": reply})
            replied += 1
        except Exception as exc:
            logger.warning(f"DM reply failed ({dm_id}): {exc}")
    return replied
