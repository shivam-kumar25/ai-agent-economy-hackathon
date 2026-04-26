from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_graph_compiles():
    """Smoke test: the LangGraph graph compiles without error."""
    with (
        patch("src.core.chains.llm"),
        patch("src.core.chains.llm_fast"),
        patch("src.config.settings.get_settings") as mock_settings,
    ):
        mock_settings.return_value = MagicMock(
            tokenrouter_api_key="test",
            agenthansa_api_key="test",
            botlearn_api_key="test",
            fluxa_api_key="test",
            langchain_tracing_v2=False,
            langchain_api_key=None,
            db_url="sqlite+aiosqlite:///./memory/test.db",
            outputs_dir="outputs",
            memory_dir="memory",
        )
        from src.core.orchestrator import build_graph
        graph = build_graph()
        assert graph is not None


@pytest.mark.asyncio
async def test_seo_audit_task_type_routes_to_crawl():
    from src.core.edges import _decide_first_node
    from src.core.graph_state import GrowthMeshState

    state: GrowthMeshState = {
        "task_type": "seo_audit",
        "input": {"url": "https://example.com"},
        "run_id": "test-run",
        "started_at": "2026-04-25T00:00:00",
        "review_iteration": 0,
        "tokens_used": 0,
    }
    assert _decide_first_node(state) == "crawl"


@pytest.mark.asyncio
async def test_content_blog_routes_to_search():
    from src.core.edges import _decide_first_node
    from src.core.graph_state import GrowthMeshState

    state: GrowthMeshState = {
        "task_type": "content_blog",
        "input": {"topic": "AI marketing"},
        "run_id": "test-run",
        "started_at": "2026-04-25T00:00:00",
        "review_iteration": 0,
        "tokens_used": 0,
    }
    assert _decide_first_node(state) == "search"


@pytest.mark.asyncio
async def test_content_email_with_url_routes_to_crawl():
    from src.core.edges import _decide_first_node
    from src.core.graph_state import GrowthMeshState

    state: GrowthMeshState = {
        "task_type": "content_email",
        "input": {"product": "https://myproduct.com", "audience": "SMBs"},
        "run_id": "test-run",
        "started_at": "2026-04-25T00:00:00",
        "review_iteration": 0,
        "tokens_used": 0,
    }
    assert _decide_first_node(state) == "crawl"


@pytest.mark.asyncio
async def test_content_email_without_url_routes_to_write():
    from src.core.edges import _decide_first_node
    from src.core.graph_state import GrowthMeshState

    state: GrowthMeshState = {
        "task_type": "content_email",
        "input": {"product": "My SaaS Tool", "audience": "SMBs"},
        "run_id": "test-run",
        "started_at": "2026-04-25T00:00:00",
        "review_iteration": 0,
        "tokens_used": 0,
    }
    assert _decide_first_node(state) == "write"
