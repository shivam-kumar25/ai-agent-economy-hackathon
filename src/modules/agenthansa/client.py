from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.utils.logger import logger
from src.utils.retry import api_retry


class AgentHansaClient:
    """Async HTTP client for the AgentHansa REST API.

    Use as a module-level singleton (ah_client) — the underlying httpx.AsyncClient
    is created once and kept open for the process lifetime.
    Supports async context manager for tests that need explicit lifecycle control."""

    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            base_url=s.agenthansa_base_url,
            headers={"Authorization": f"Bearer {s.agenthansa_api_key}"},
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def __aenter__(self) -> "AgentHansaClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.aclose()

    @api_retry()
    async def get(self, path: str, **kwargs) -> dict:
        r = await self._client.get(path, **kwargs)
        r.raise_for_status()
        return r.json()

    @api_retry()
    async def post(self, path: str, json: dict | None = None, **kwargs) -> dict:
        r = await self._client.post(path, json=json, **kwargs)
        r.raise_for_status()
        return r.json()

    @api_retry()
    async def patch(self, path: str, json: dict | None = None) -> dict:
        r = await self._client.patch(path, json=json)
        r.raise_for_status()
        return r.json()

    @api_retry()
    async def put(self, path: str, json: dict | None = None) -> dict:
        r = await self._client.put(path, json=json)
        r.raise_for_status()
        return r.json()

    async def aclose(self) -> None:
        await self._client.aclose()


ah_client = AgentHansaClient()
