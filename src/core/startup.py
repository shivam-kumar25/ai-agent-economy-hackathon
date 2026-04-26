from __future__ import annotations

from pathlib import Path

from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

from src.config.settings import get_settings
from src.db.base import Base
from src.db.engine import engine
from src.utils.logger import logger


async def initialize() -> None:
    """Run once at process startup. Idempotent — safe to call multiple times."""
    s = get_settings()

    # Create output and memory directories
    for d in [
        s.memory_dir,
        s.outputs_dir,
        "outputs/audits",
        "outputs/research",
        "outputs/content",
        "logs",
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)

    # LLM response cache — must be set before any LLM call
    cache_path = f"{s.memory_dir}/llm_cache.db"
    set_llm_cache(SQLiteCache(database_path=cache_path))
    logger.debug(f"LLM cache: {cache_path}")

    # Create all SQLAlchemy tables (Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.debug("Database tables ready")

    # Credential sanity checks (warn, don't crash — keys may be set after startup)
    if not s.agenthansa_api_key:
        logger.warning("AGENTHANSA_API_KEY not set — register with: growthagent agent setup")
    if not s.botlearn_api_key:
        logger.warning("BOTLEARN_API_KEY not set — register with: growthagent botlearn setup")
    if not s.langsmith_api_key:
        logger.warning("LANGSMITH_API_KEY not set — LangSmith tracing disabled")

    logger.success("GrowthMesh initialized")
