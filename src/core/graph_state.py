from __future__ import annotations

from typing import Any, Literal, TypedDict

TaskType = Literal[
    "seo_audit",
    "research_competitor",
    "research_market",
    "research_leads",
    "content_blog",
    "content_email",
    "content_social",
]


class _GrowthMeshStateRequired(TypedDict):
    """Must be present in the initial state dict passed to app.ainvoke()."""
    task_type: TaskType
    input: dict[str, Any]
    run_id: str
    started_at: str   # datetime.utcnow().isoformat()
    review_iteration: int  # start at 0
    tokens_used: int       # start at 0


class GrowthMeshState(_GrowthMeshStateRequired, total=False):
    """Populated by graph nodes during execution. Absent until the node that sets them runs."""
    # Web data
    crawl_results: list[dict]
    search_results: list[dict]
    # LLM work
    outline: dict | None
    draft: str | None
    structured_output: dict | None
    # Review loop
    review_verdict: dict | None   # ReviewVerdict.model_dump()
    # Output
    final_output: str
    output_path: str
    # Side-effect flags
    memory_saved: bool
    botlearn_reported: bool
    agenthansa_submitted: bool
