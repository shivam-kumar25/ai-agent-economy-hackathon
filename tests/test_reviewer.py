from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_reviewer_skips_already_reviewed():
    with (
        patch("src.modules.agenthansa.reviewer.memory") as mock_mem,
        patch("src.modules.agenthansa.reviewer.ah_client") as mock_ah,
    ):
        mock_mem.already_reviewed = AsyncMock(return_value=True)
        mock_ah.get = AsyncMock(side_effect=[
            {"quests": [{"id": "q1", "title": "Test quest", "spec": {}}]},
            {"submissions": [{"agent_id": "a1", "agent_name": "bot", "content": "output"}]},
        ])

        from src.modules.agenthansa.reviewer import run_alliance_reviewer_pass
        await run_alliance_reviewer_pass()

        mock_mem.already_reviewed.assert_awaited_once_with("q1", "a1")


@pytest.mark.asyncio
async def test_reviewer_runs_for_new_quest():
    mock_verdict = MagicMock()
    mock_verdict.score = 85
    mock_verdict.passed = True
    mock_verdict.specific_feedback = "Great work"
    mock_verdict.spec_compliance = "full"
    mock_verdict.depth = "deep"

    with (
        patch("src.modules.agenthansa.reviewer.memory") as mock_mem,
        patch("src.modules.agenthansa.reviewer.ah_client") as mock_client,
        patch("src.modules.agenthansa.reviewer.review_chain") as mock_chain,
        patch("src.modules.agenthansa.reviewer.AsyncSessionLocal") as mock_db,
    ):
        mock_mem.already_reviewed = AsyncMock(return_value=False)
        mock_chain.ainvoke = AsyncMock(return_value=mock_verdict)
        mock_client.get = AsyncMock(side_effect=[
            {"quests": [{"id": "q2", "title": "Test", "spec": {"brief": "do X"}}]},
            {"submissions": [{"agent_id": "a2", "agent_name": "bot2", "content": "great work"}]},
        ])
        mock_client.post = AsyncMock(return_value={"accepted": True})

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_db.return_value = mock_session

        from src.modules.agenthansa.reviewer import run_alliance_reviewer_pass
        await run_alliance_reviewer_pass()

        mock_chain.ainvoke.assert_awaited_once()
        mock_client.post.assert_awaited()
