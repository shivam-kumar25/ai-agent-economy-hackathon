from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_scheduler_has_error_listener():
    """Verify the APScheduler instance has the _on_job_error listener registered."""
    from src.core.scheduler import scheduler
    from apscheduler.events import EVENT_JOB_ERROR

    listeners = getattr(scheduler, "_listeners", [])
    events_covered = [mask for (_, mask) in listeners]
    assert any(mask & EVENT_JOB_ERROR for mask in events_covered), (
        "_on_job_error listener not registered for EVENT_JOB_ERROR"
    )


@pytest.mark.asyncio
async def test_run_agenthansa_tick_handles_error():
    """run_agenthansa_tick should not raise even if sub-calls fail."""
    with (
        patch("src.modules.agenthansa.scheduler_tasks.ensure_registered", new=AsyncMock(side_effect=Exception("boom"))),
    ):
        from src.modules.agenthansa.scheduler_tasks import run_agenthansa_tick
        # Should not raise
        await run_agenthansa_tick()
