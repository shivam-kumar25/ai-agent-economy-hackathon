from __future__ import annotations

import re


def word_count(text: str) -> int:
    return len(text.split())


def extract_headings(text: str) -> list[str]:
    return re.findall(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)


def inject_cta(text: str, cta: str) -> str:
    """Append a call-to-action block if one isn't already present."""
    if cta.lower()[:20] in text.lower():
        return text
    return f"{text.rstrip()}\n\n---\n\n{cta}\n"


def strip_markdown(text: str) -> str:
    """Return plain text suitable for readability scoring."""
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()
