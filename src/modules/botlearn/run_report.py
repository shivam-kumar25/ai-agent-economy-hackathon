from __future__ import annotations

import time
from functools import wraps

from src.utils.logger import logger


async def report_execution(
    skill_name: str,
    status: str,
    duration_ms: int,
    tokens_used: int,
) -> None:
    """POST execution stats to BotLearn. Never raises — failure is logged and swallowed."""
    from src.config.settings import get_settings
    if not get_settings().botlearn_api_key:
        return
    try:
        from src.modules.botlearn.client import bl_client
        await bl_client.post("/api/v2/run-report", {
            "skill_name":  skill_name,
            "status":      status,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
        })
    except Exception as exc:
        logger.warning(f"BotLearn run-report failed (non-fatal): {exc}")


def botlearn_tracked(skill_name: str):
    """Decorator — wraps any async task function with automatic BotLearn run-report."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            from src.core.memory import memory
            start = time.monotonic()
            tokens_before = memory.get_last_task_tokens()
            status = "success"
            try:
                return await fn(*args, **kwargs)
            except Exception:
                status = "failure"
                raise
            finally:
                tokens_delta = max(0, memory.get_last_task_tokens() - tokens_before)
                await report_execution(
                    skill_name=skill_name,
                    status=status,
                    duration_ms=int((time.monotonic() - start) * 1000),
                    tokens_used=tokens_delta,
                )
        return wrapper
    return decorator
