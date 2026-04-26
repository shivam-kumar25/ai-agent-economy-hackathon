from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

# Remove default handler
logger.remove()

# Console — human-readable with Rich-style colors
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# File — JSON structured, rotating
Path("logs").mkdir(exist_ok=True)
logger.add(
    "logs/growthagent.jsonl",
    format="{time} {level} {name} {message}",
    serialize=True,       # JSON output
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    enqueue=True,         # thread-safe async-friendly
)

__all__ = ["logger"]
