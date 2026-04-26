from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_update_and_get_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, "state.json")
        with patch("src.core.memory.STATE_PATH", state_path):
            from src.core.memory import Memory
            m = Memory()
            m.update_state({"agent": {"last_task_tokens": 42}})
            state = m.get_state()
            assert state.get("agent", {}).get("last_task_tokens") == 42


@pytest.mark.asyncio
async def test_get_last_task_tokens_defaults_zero():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, "state.json")
        with patch("src.core.memory.STATE_PATH", state_path):
            from src.core.memory import Memory
            m = Memory()
            assert m.get_last_task_tokens() == 0


@pytest.mark.asyncio
async def test_already_reviewed_false_for_unknown():
    with patch("src.core.memory.AsyncSessionLocal") as mock_session_factory:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session_factory.return_value = mock_session

        from src.core.memory import Memory
        m = Memory()
        result = await m.already_reviewed("nonexistent-quest-id", "agent-123")
        assert result is False
