from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # TokenRouter / LLM
    tokenrouter_api_key: str = Field(..., description="Required — app fails here if missing")
    llm_model_quality: str = Field("claude-sonnet-4-6")
    llm_model_fast: str = Field("claude-haiku-4-5-20251001")

    # AgentHansa
    agenthansa_api_key: str = Field("", description="Set after registration")
    agenthansa_base_url: str = Field("https://www.agenthansa.com/api")
    agenthansa_alliance: str = Field("heavenly")

    # BotLearn
    botlearn_api_key: str = Field("", description="Set after BotLearn setup")
    botlearn_base_url: str = Field("https://www.botlearn.ai")

    # FluxA
    fluxa_agent_id: str = Field("")
    fluxa_jwt: str = Field("")
    fluxa_wallet_api: str = Field("https://walletapi.fluxapay.xyz")

    # LangSmith
    langchain_tracing_v2: bool = Field(True)
    langsmith_api_key: str = Field("", alias="LANGSMITH_API_KEY")
    langchain_project: str = Field("growthagent-hackathon")

    # Token budget
    token_budget_total: int = Field(5_000_000)
    token_warn_threshold: int = Field(500_000)

    # Scheduler
    scheduler_enabled: bool = Field(True)
    agenthansa_tick_hours: int = Field(3)
    botlearn_heartbeat_hours: int = Field(12)

    # Paths
    memory_dir: str = Field("./memory")
    outputs_dir: str = Field("./outputs")
    skills_dir: str = Field("./skills")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazy singleton — never called at module import time.
    If .env is missing the required TOKENROUTER_API_KEY, this raises a clear
    ValidationError on first call rather than a cryptic error mid-execution."""
    return Settings()
