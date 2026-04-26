from __future__ import annotations

from duckduckgo_search import DDGS

from src.utils.logger import logger

_QUESTIONS = [
    "market size",
    "growth rate",
    "top competitors",
    "customer pain points",
    "emerging trends",
    "pricing models",
    "regulatory landscape",
]


async def gather_market_signals(topic: str, max_results: int = 5) -> list[dict]:
    """Run multiple DuckDuckGo queries to collect market intelligence snippets."""
    results: list[dict] = []
    with DDGS() as ddgs:
        for question in _QUESTIONS:
            query = f"{topic} {question}"
            try:
                hits = list(ddgs.text(query, max_results=max_results))
                for h in hits:
                    results.append({
                        "query": query,
                        "title": h.get("title", ""),
                        "snippet": h.get("body", ""),
                        "url": h.get("href", ""),
                    })
            except Exception as exc:
                logger.warning(f"Market signal query failed ({query}): {exc}")
    logger.debug(f"Gathered {len(results)} market signal snippets for '{topic}'")
    return results
