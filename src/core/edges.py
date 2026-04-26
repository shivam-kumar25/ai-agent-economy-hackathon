from __future__ import annotations

from src.core.graph_state import GrowthMeshState


def _decide_first_node(state: GrowthMeshState) -> str:
    """Route from 'route' node to the appropriate first data-gathering node."""
    t = state["task_type"]

    if t == "content_email":
        # If product is a URL, crawl it first to build context
        product = state["input"].get("product", "")
        if product.startswith(("http://", "https://")):
            return "crawl"
        return "write"

    if t == "content_social":
        return "write"  # topic-only — no crawl needed

    if t in ("seo_audit", "research_competitor"):
        return "crawl"

    # research_market, research_leads, content_blog — need SERP data
    return "search"


def _is_content_task(state: GrowthMeshState) -> bool:
    """After analyze, content tasks go to outline; research/SEO go straight to self_review."""
    return state["task_type"].startswith("content_")


def _review_decision(state: GrowthMeshState) -> str:
    """After self_review: pass → save, improve → improve node, force → save best attempt."""
    v = state.get("review_verdict")
    if v and v["score"] >= 75:
        return "pass"
    if state["review_iteration"] >= 2:
        return "force"  # never loop more than twice
    return "improve"
