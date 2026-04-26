from __future__ import annotations

import asyncio

import httpx
import newspaper  # package: newspaper3k

from src.utils.logger import logger

_HEADERS = {"User-Agent": "GrowthMesh/1.0 (B2B growth agent; research@growthagent.ai)"}


async def fetch_and_extract(url: str, client: httpx.AsyncClient) -> tuple[str, str]:
    """Fetch a URL and extract clean article text.
    Returns (title, text). Never raises — returns empty strings on failure."""
    try:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()
        article = newspaper.Article(url)
        article.set_html(resp.text)
        # newspaper3k .parse() is synchronous and CPU-bound — offload to thread
        await asyncio.to_thread(article.parse)
        return article.title or "", article.text or ""
    except Exception as exc:
        logger.debug(f"fetch_and_extract failed for {url}: {exc}")
        return "", ""


def make_client(timeout: float = 15.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout, connect=5.0),
        headers=_HEADERS,
        follow_redirects=True,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    )
