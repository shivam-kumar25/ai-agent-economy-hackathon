from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from src.utils.logger import logger


def api_retry():
    """Retry decorator for all external API calls (AgentHansa, BotLearn, FluxA).
    Retries on HTTP errors and connection errors with exponential backoff."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )


def scrape_retry():
    """Retry decorator for web scraping — DuckDuckGo can rate-limit aggressively."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )
