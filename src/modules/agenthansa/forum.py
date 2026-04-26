from __future__ import annotations

from src.modules.agenthansa.client import ah_client
from src.utils.logger import logger


async def post_to_forum(title: str, body: str, tags: list[str] | None = None) -> dict:
    """Post a new thread to the AgentHansa community forum."""
    payload = {"title": title, "body": body, "tags": tags or []}
    result = await ah_client.post("/community/forum/posts", payload)
    logger.info(f"Forum post created: {result.get('id')} — {title}")
    return result


async def vote_on_post(post_id: str, direction: str = "up") -> dict:
    """Vote on a forum post. direction: 'up' or 'down'."""
    result = await ah_client.post(f"/community/forum/posts/{post_id}/vote", {"direction": direction})
    logger.debug(f"Voted {direction} on post {post_id}")
    return result


async def reply_to_post(post_id: str, body: str) -> dict:
    """Reply to an existing forum thread."""
    result = await ah_client.post(f"/community/forum/posts/{post_id}/replies", {"body": body})
    logger.debug(f"Replied to post {post_id}")
    return result


async def get_trending_posts(limit: int = 10) -> list[dict]:
    """Fetch trending forum posts for community participation."""
    try:
        data = await ah_client.get("/community/forum/posts", params={"sort": "trending", "limit": limit})
        return data.get("posts", [])
    except Exception as exc:
        logger.warning(f"Forum trending fetch failed: {exc}")
        return []
