from __future__ import annotations

import asyncio

import extruct
import httpx
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader

from src.utils.logger import logger


def _alt_coverage(soup: BeautifulSoup) -> float:
    images = soup.find_all("img")
    if not images:
        return 1.0
    return sum(1 for i in images if i.get("alt", "").strip()) / len(images)


def _count_internal_links(soup: BeautifulSoup, base_url: str) -> int:
    from urllib.parse import urlparse
    domain = urlparse(base_url).netloc
    return sum(
        1 for a in soup.find_all("a", href=True)
        if domain in a["href"] or a["href"].startswith("/")
    )


def _get_meta(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": f"og:{name}"})
    return (tag or {}).get("content", "") if tag else ""


async def crawl_urls(urls: list[str]) -> list[dict]:
    """Crawl a list of URLs and extract SEO signals.
    WebBaseLoader.load() is synchronous — run in a thread to not block the event loop."""
    if not urls:
        return []

    loader = WebBaseLoader(
        web_paths=urls,
        requests_per_second=2,
        continue_on_failure=True,
    )
    try:
        docs = await asyncio.to_thread(loader.load)
    except Exception as exc:
        logger.warning(f"WebBaseLoader failed: {exc}")
        return []

    results = []
    for doc in docs:
        html = doc.page_content
        src = doc.metadata.get("source", "")
        soup = BeautifulSoup(html, "lxml")

        try:
            structured = extruct.extract(
                html,
                base_url=src,
                syntaxes=["json-ld", "opengraph", "microdata"],
            )
        except Exception:
            structured = {}

        results.append({
            "url":            src,
            "title":          soup.find("title").text.strip() if soup.find("title") else "",
            "meta_desc":      _get_meta(soup, "description"),
            "h_tags":         [(t.name, t.text.strip()) for t in soup.find_all(["h1", "h2", "h3"])],
            "image_alt_pct":  _alt_coverage(soup),
            "internal_links": _count_internal_links(soup, src),
            "schema_types":   [i.get("@type") for i in structured.get("json-ld", [])],
            "og_title":       (structured.get("opengraph") or [{}])[0].get("og:title", ""),
            "word_count":     len(html.split()),
            "load_headers":   {k: v for k, v in doc.metadata.items() if k != "source"},
        })

    return results
