from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.agenthansa.client import AgentHansaClient


@pytest.mark.asyncio
async def test_get_returns_json():
    client = AgentHansaClient()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"ok": True}

    with patch.object(client._client, "get", new=AsyncMock(return_value=mock_response)):
        result = await client.get("/test")

    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_post_sends_json():
    client = AgentHansaClient()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"id": "abc"}

    with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)) as mock_post:
        result = await client.post("/tasks", {"title": "test"})

    assert result == {"id": "abc"}


@pytest.mark.asyncio
async def test_context_manager():
    client = AgentHansaClient()
    async with client as c:
        assert c is client


@pytest.mark.asyncio
async def test_retry_on_connect_error():
    client = AgentHansaClient()
    call_count = 0

    async def failing_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.ConnectError("connection refused")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"recovered": True}
        return mock_response

    with patch.object(client._client, "get", new=failing_get):
        result = await client.get("/retry-test")

    assert result == {"recovered": True}
    assert call_count == 2
