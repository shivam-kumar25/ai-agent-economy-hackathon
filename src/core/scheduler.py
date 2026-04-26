from __future__ import annotations

from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config.settings import get_settings
from src.utils.logger import logger


def _on_job_error(event: JobExecutionEvent) -> None:
    """Log all scheduler job exceptions.
    APScheduler swallows exceptions in jobs silently by default — this makes them visible."""
    logger.error(
        f"Scheduler job '{event.job_id}' raised an exception: {event.exception}\n"
        f"Traceback: {event.traceback}"
    )


def build_scheduler() -> AsyncIOScheduler:
    s = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)

    scheduler.add_job(
        _agenthansa_tick_wrapper,
        IntervalTrigger(hours=s.agenthansa_tick_hours),
        id="agenthansa_tick",
        max_instances=1,   # never overlap — quest execution can take minutes
        coalesce=True,     # missed ticks (e.g. during sleep) merge into one
    )
    scheduler.add_job(
        _botlearn_heartbeat_wrapper,
        IntervalTrigger(hours=s.botlearn_heartbeat_hours),
        id="botlearn_heartbeat",
        max_instances=1,
        coalesce=True,
    )
    return scheduler


async def _agenthansa_tick_wrapper() -> None:
    """Wrapper so the import is deferred until the job actually runs."""
    from src.modules.agenthansa.scheduler_tasks import run_agenthansa_tick
    await run_agenthansa_tick()


async def _botlearn_heartbeat_wrapper() -> None:
    from src.modules.botlearn.heartbeat import run_botlearn_heartbeat
    await run_botlearn_heartbeat()


async def _expert_services_refresh_wrapper() -> None:
    """Re-declare services daily so they stay fresh on the marketplace."""
    from src.modules.agenthansa.expert import declare_services
    await declare_services()


# Module-level scheduler singleton — call scheduler.start() in startup.py
scheduler = build_scheduler()
