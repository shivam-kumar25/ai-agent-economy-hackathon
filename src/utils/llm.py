from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from src.config.settings import get_settings


def _make_llm(model: str, max_tokens: int) -> ChatAnthropic:
    s = get_settings()
    return ChatAnthropic(
        model=model,
        anthropic_api_key=s.tokenrouter_api_key,
        anthropic_api_url="https://api.tokenrouter.com",
        max_tokens=max_tokens,
    )


# Module-level singletons — _make_llm calls get_settings() lazily so this
# only executes when src.utils.llm is first imported (not at package import).
llm = _make_llm("claude-sonnet-4-6", max_tokens=4096)
llm_fast = _make_llm("claude-haiku-4-5-20251001", max_tokens=1024)


def cached_system(prompt: str) -> SystemMessage:
    """Wrap a large system prompt with cache_control.
    Saves 80-90% tokens on repeat calls with identical prompts."""
    return SystemMessage(
        content=prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}},
    )
