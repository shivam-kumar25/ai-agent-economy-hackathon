from __future__ import annotations

import asyncio

_keybert_instance = None
_keybert_available: bool | None = None


def _get_keybert():
    """Lazy singleton — loads ~500 MB sentence-transformers model on first call.
    Returns None if keybert / torch is not installed (soft dependency)."""
    global _keybert_instance, _keybert_available
    if _keybert_available is False:
        return None
    if _keybert_instance is not None:
        return _keybert_instance
    try:
        from keybert import KeyBERT
        _keybert_instance = KeyBERT()
        _keybert_available = True
        return _keybert_instance
    except Exception:
        _keybert_available = False
        return None


def _sync_extract(text: str, top_n: int) -> list[tuple[str, float]]:
    kb = _get_keybert()
    if kb is None:
        # Fallback: simple word-frequency extraction (no ML, no deps)
        import re
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        stopwords = {"this", "that", "with", "from", "have", "will", "they", "their",
                     "been", "also", "more", "into", "your", "about", "which", "when"}
        ranked = sorted(
            [(w, c / max(freq.values())) for w, c in freq.items() if w not in stopwords],
            key=lambda x: x[1], reverse=True,
        )
        return ranked[:top_n]
    return kb.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
        use_mmr=True,
        diversity=0.7,
    )


async def extract_keywords(text: str, top_n: int = 15) -> list[tuple[str, float]]:
    """Run keyword extraction in a thread pool — never blocks the event loop."""
    if not text.strip():
        return []
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_extract, text, top_n)
