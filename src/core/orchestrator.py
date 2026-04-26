from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.core.edges import _decide_first_node, _is_content_task, _review_decision
from src.core.graph_state import GrowthMeshState
from src.core.nodes import (
    crawl_web_sources,
    create_outline,
    improve_output,
    prompt_agenthansa_submit,
    report_to_botlearn,
    route_by_task_type,
    run_llm_analysis,
    run_self_review,
    save_outputs,
    search_web,
    write_content,
)


def build_graph() -> StateGraph:
    g = StateGraph(GrowthMeshState)

    g.add_node("route",         route_by_task_type)
    g.add_node("crawl",         crawl_web_sources)
    g.add_node("search",        search_web)
    g.add_node("analyze",       run_llm_analysis)
    g.add_node("outline",       create_outline)
    g.add_node("write",         write_content)
    g.add_node("self_review",   run_self_review)
    g.add_node("improve",       improve_output)
    g.add_node("save",          save_outputs)
    g.add_node("report",        report_to_botlearn)
    g.add_node("submit_prompt", prompt_agenthansa_submit)

    g.set_entry_point("route")

    g.add_conditional_edges("route", _decide_first_node, {
        "crawl":  "crawl",
        "search": "search",
        "write":  "write",
    })

    g.add_edge("crawl",  "analyze")
    g.add_edge("search", "analyze")

    g.add_conditional_edges("analyze", _is_content_task, {
        True:  "outline",
        False: "self_review",
    })

    g.add_edge("outline", "write")
    g.add_edge("write",   "self_review")

    g.add_conditional_edges("self_review", _review_decision, {
        "pass":    "save",
        "improve": "improve",
        "force":   "save",
    })
    g.add_edge("improve",       "self_review")
    g.add_edge("save",          "report")
    g.add_edge("report",        "submit_prompt")
    g.add_edge("submit_prompt", END)

    return g


# Compiled singleton — import this everywhere
app = build_graph().compile()
