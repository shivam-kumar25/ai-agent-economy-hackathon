from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.utils.logger import logger
from src.utils.retry import api_retry


class FluxAClient:
    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            base_url=s.fluxa_wallet_api,
            headers={
                "Authorization": f"Bearer {s.fluxa_jwt}",
                "X-Agent-ID": s.fluxa_agent_id,
            },
            timeout=30.0,
        )

    @api_retry()
    async def get_balance(self) -> dict:
        r = await self._client.get("/wallet/balance")
        r.raise_for_status()
        return r.json()

    @api_retry()
    async def request_payout(self, amount_usd: float, destination: str) -> dict:
        r = await self._client.post("/wallet/payout", json={
            "amount_usd":  amount_usd,
            "destination": destination,
        })
        r.raise_for_status()
        return r.json()


fluxa_client = FluxAClient()
