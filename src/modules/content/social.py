from __future__ import annotations

import re

PLATFORM_LIMITS = {
    "twitter": 280,
    "linkedin": 3000,
    "instagram": 2200,
}


def enforce_limit(text: str, platform: str) -> str:
    limit = PLATFORM_LIMITS.get(platform.lower(), 3000)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#\w+", text)


def add_hashtags(text: str, tags: list[str]) -> str:
    existing = set(extract_hashtags(text))
    new_tags = [t if t.startswith("#") else f"#{t}" for t in tags if f"#{t}" not in existing]
    if not new_tags:
        return text
    return f"{text.rstrip()}\n\n{' '.join(new_tags)}"
