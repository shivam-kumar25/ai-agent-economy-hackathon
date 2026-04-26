from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.utils.retry import api_retry


class BotLearnClient:
    """Async HTTP client for the BotLearn API. Same contract as AgentHansaClient."""

    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            base_url=s.botlearn_base_url,
            headers={"Authorization": f"Bearer {s.botlearn_api_key}"},
            timeout=httpx.Timeout(20.0, connect=10.0),
        )

    async def __aenter__(self) -> "BotLearnClient":
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

    async def aclose(self) -> None:
        await self._client.aclose()


bl_client = BotLearnClient()
