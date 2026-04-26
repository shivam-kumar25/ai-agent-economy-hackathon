from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("TOKENROUTER_API_KEY", "test-key")
os.environ.setdefault("AGENTHANSA_API_KEY", "test-ah-key")
os.environ.setdefault("BOTLEARN_API_KEY", "test-bl-key")
os.environ.setdefault("FLUXA_API_KEY", "test-fluxa-key")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm():
    with patch("src.utils.llm.llm") as m:
        m.ainvoke = AsyncMock(return_value=MagicMock(content='{"result": "ok"}'))
        yield m


@pytest.fixture
def mock_llm_fast():
    with patch("src.utils.llm.llm_fast") as m:
        m.ainvoke = AsyncMock(return_value=MagicMock(content="yes"))
        yield m


@pytest.fixture
def mock_ah_client():
    with patch("src.modules.agenthansa.client.ah_client") as m:
        m.get = AsyncMock(return_value={})
        m.post = AsyncMock(return_value={"id": "test-id"})
        m.patch = AsyncMock(return_value={})
        yield m


@pytest.fixture
def mock_memory():
    with patch("src.core.memory.memory") as m:
        m.get_latest_audit = AsyncMock(return_value=None)
        m.save_audit = AsyncMock()
        m.save_quest = AsyncMock()
        m.update_state = MagicMock()
        m.get_state = MagicMock(return_value={})
        m.already_reviewed = AsyncMock(return_value=False)
        m.get_last_task_tokens = MagicMock(return_value=0)
        yield m
