from __future__ import annotations

from src.modules.seo.crawler import crawl_urls
from src.utils.logger import logger


async def crawl_competitor(url: str) -> list[dict]:
    """Crawl key competitor pages: homepage, pricing, features, about."""
    base = url.rstrip("/")
    urls = [base, f"{base}/pricing", f"{base}/features", f"{base}/about"]
    results = await crawl_urls(urls)
    logger.debug(f"Crawled {len(results)} pages for {base}")
    return results
