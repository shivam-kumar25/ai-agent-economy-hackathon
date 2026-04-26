from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, date
from pathlib import Path
from uuid import uuid4

import aiofiles
import httpx
import textstat
from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.documents import Document
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.chains import (
    ANALYSIS_CHAINS,
    WRITE_CHAINS,
    improve_chain,
    outline_chain,
    review_chain,
)
from src.core.graph_state import GrowthMeshState
from src.core.memory import memory
from src.models.review import ReviewVerdict
from src.modules.seo.crawler import crawl_urls
from src.utils.logger import logger
from src.utils.scraper import fetch_and_extract, make_client

# ── Jinja2 environment (module-level, stateless) ──────────────────────
_jinja = Environment(
    loader=FileSystemLoader("src/templates/"),
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
)

# ── DuckDuckGo search (lazy singleton — validates on first use, not import) ──
_duckduckgo = None

def _get_ddg():
    global _duckduckgo
    if _duckduckgo is None:
        from langchain_community.tools import DuckDuckGoSearchResults
        _duckduckgo = DuckDuckGoSearchResults(output_format="list", num_results=8)
    return _duckduckgo


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), reraise=True)
async def _ddg_search(query: str) -> list[dict]:
    return await _get_ddg().arun(query)


# ── Helper functions ──────────────────────────────────────────────────

def _get_urls_to_crawl(state: GrowthMeshState) -> list[str]:
    inp = state["input"]
    t = state["task_type"]
    if t == "seo_audit":
        return [inp["url"]] + inp.get("competitors", [])[:3]
    if t == "research_competitor":
        base = inp.get("url") or inp.get("target", "")
        base = base.rstrip("/")
        return [base, f"{base}/pricing", f"{base}/features", f"{base}/about"]
    if t == "content_email":
        return [inp["product"]]
    return [inp.get("url", "")]


def _build_search_query(state: GrowthMeshState) -> str:
    t, inp = state["task_type"], state["input"]
    if t == "research_market":
        return f"{inp.get('industry', '')} {inp.get('icp', '')} market trends 2025 2026"
    if t == "research_leads":
        return f"{inp.get('icp', '')} companies hiring funding B2B"
    if t == "content_blog":
        kw = inp.get("keyword", "")
        return f"{kw} guide best practices site:reddit.com OR site:quora.com OR site:g2.com"
    return inp.get("query", inp.get("keyword", ""))


def _extract_gaps(results: list[dict]) -> str:
    return "\n\n".join(r.get("full_text", r.get("body", ""))[:500] for r in results[:3])


def _build_spec_summary(state: GrowthMeshState) -> str:
    t, inp = state["task_type"], state["input"]
    if t == "seo_audit":
        return f"SEO audit for {inp.get('domain', inp.get('url', ''))}. Score /100. Find critical issues and keyword gaps."
    if t == "content_blog":
        return f"Blog post targeting '{inp.get('keyword')}'. ~{inp.get('words', 1500)} words. Tone: {inp.get('tone', 'professional')}."
    if t == "content_email":
        return f"5-email cold outreach drip for product '{inp.get('product')}' to ICP: {inp.get('icp')}."
    if t == "content_social":
        return f"Social copy ({inp.get('platform')}) about '{inp.get('topic')}'. 3 ranked variations."
    if t == "research_competitor":
        return f"Competitor teardown for {inp.get('target', inp.get('url', ''))}."
    if t == "research_market":
        return f"Market intelligence for: {inp.get('icp', inp.get('industry', ''))}."
    if t == "research_leads":
        return f"Lead list for ICP: {inp.get('icp', '')}. Min 5 leads, confidence-scored."
    return f"Task: {t}. Input: {inp}"


def _slug(inp: dict) -> str:
    raw = (
        inp.get("keyword") or inp.get("topic") or inp.get("domain")
        or inp.get("product") or inp.get("icp") or inp.get("target") or "output"
    )
    return re.sub(r"[^a-z0-9]+", "-", raw.lower())[:40].strip("-")


def _output_path(task: str, inp: dict) -> str:
    d = date.today().isoformat()
    slug = _slug(inp)
    if task == "seo_audit":
        return f"outputs/audits/{inp.get('domain', slug)}-{d}.md"
    if task == "research_competitor":
        return f"outputs/research/competitor-{slug}-{d}.md"
    if task == "research_market":
        return f"outputs/research/market-{slug}-{d}.md"
    if task == "research_leads":
        return f"outputs/research/leads-{slug}-{d}.md"
    if task == "content_blog":
        return f"outputs/content/blog-{slug}-{d}.md"
    if task == "content_email":
        return f"outputs/content/email-seq-{slug}-{d}.md"
    return f"outputs/content/social-{slug}-{d}.md"


def _build_doc_metadata(state: GrowthMeshState) -> dict:
    inp = state["input"]
    return {
        "task_type": state["task_type"],
        "domain":    inp.get("domain", inp.get("url", "")),
        "keyword":   inp.get("keyword", inp.get("topic", "")),
        "run_id":    state.get("run_id", ""),
    }


def _estimate_tokens(obj) -> int:
    try:
        return len(json.dumps(obj.model_dump() if hasattr(obj, "model_dump") else obj)) // 4
    except Exception:
        return 0


def _print_summary(task: str, state: GrowthMeshState, path: str) -> None:
    from rich.console import Console
    from rich.panel import Panel
    c = Console(highlight=False)
    verdict = state.get("review_verdict") or {}
    score = verdict.get("score", "N/A")
    try:
        c.print(Panel(
            f"[bold green]OK {task.replace('_', ' ').title()}[/bold green]\n"
            f"Review score: {score}/100  |  Tokens: {state['tokens_used']:,}\n"
            f"Saved: {path}",
            expand=False,
        ))
    except UnicodeEncodeError:
        print(f"[OK] {task} | score={score} | tokens={state['tokens_used']} | {path}")


# ── Graph Nodes ───────────────────────────────────────────────────────

async def route_by_task_type(state: GrowthMeshState) -> dict:
    """Pass-through — routing is handled by the _decide_first_node edge function."""
    return {}


async def crawl_web_sources(state: GrowthMeshState) -> dict:
    urls = _get_urls_to_crawl(state)
    results = await crawl_urls(urls)
    return {"crawl_results": results}


async def search_web(state: GrowthMeshState) -> dict:
    query = _build_search_query(state)
    try:
        raw: list[dict] = await _ddg_search(query)
    except Exception as exc:
        logger.warning(f"DuckDuckGo search failed: {exc}")
        raw = []

    enriched = []
    async with make_client() as client:
        for r in raw[:3]:
            href = r.get("href", r.get("link", ""))
            if href:
                title, text = await fetch_and_extract(href, client)
                enriched.append({**r, "full_text": text[:4000], "title": title or r.get("title", "")})
            else:
                enriched.append({**r, "full_text": r.get("body", "")})

    return {"search_results": enriched + raw[3:]}


async def run_llm_analysis(state: GrowthMeshState) -> dict:
    chain = ANALYSIS_CHAINS[state["task_type"]]

    prior_audit_str = "No prior audit on record."
    if state["task_type"] == "seo_audit":
        prior = await memory.get_latest_audit(state["input"].get("domain", ""))
        if prior:
            prior_audit_str = prior.model_dump_json()

    invoke_kwargs = {
        **state["input"],
        "crawl_results":  json.dumps(state.get("crawl_results", []), ensure_ascii=False)[:8000],
        "search_results": json.dumps(state.get("search_results", []), ensure_ascii=False)[:8000],
        "prior_audit":    prior_audit_str,
    }

    _cfg = {"run_name": f"analysis_{state['task_type']}"}
    raw_result = await chain.ainvoke(invoke_kwargs, config=_cfg)

    # include_raw=True returns {"raw": AIMessage, "parsed": Pydantic|None, "parsing_error": ...}
    if isinstance(raw_result, dict):
        result = raw_result.get("parsed")
        parse_err = raw_result.get("parsing_error")
        raw_msg = raw_result.get("raw")
        if result is None:
            raw_content = getattr(raw_msg, "content", str(raw_msg))[:500] if raw_msg else "None"
            logger.warning(f"Structured parse failed. Error: {parse_err}. Raw: {raw_content}")
            raise ValueError(
                f"LLM response could not be parsed for task {state['task_type']}: {parse_err} | raw={raw_content[:200]}"
            )
    else:
        result = raw_result

    if result is None:
        raise ValueError(
            f"LLM returned None for task {state['task_type']}. "
            "Check TokenRouter API key and model availability."
        )

    new_tokens = _estimate_tokens(result)
    memory.track_token_spend(state["task_type"], new_tokens, "claude-sonnet-4-6")

    return {
        "structured_output": result.model_dump(),
        "tokens_used":       state["tokens_used"] + new_tokens,
    }


async def create_outline(state: GrowthMeshState) -> dict:
    outline = await outline_chain.ainvoke({
        "keyword":   state["input"].get("keyword") or state["input"].get("topic", ""),
        "serp_gaps": _extract_gaps(state.get("search_results", [])),
        "tone":      state["input"].get("tone", "professional"),
    })
    return {
        "outline":     outline.model_dump(),
        "tokens_used": state["tokens_used"] + 1500,
    }


async def write_content(state: GrowthMeshState) -> dict:
    chain = WRITE_CHAINS[state["task_type"]]
    draft = await chain.ainvoke({
        **state["input"],
        "outline": json.dumps(state.get("outline") or {}, ensure_ascii=False),
    })
    new_tokens = len(draft) // 4
    memory.track_token_spend(state["task_type"], new_tokens, "claude-sonnet-4-6")
    return {
        "draft":       draft,
        "tokens_used": state["tokens_used"] + new_tokens,
    }


async def run_self_review(state: GrowthMeshState) -> dict:
    spec = _build_spec_summary(state)
    content = state.get("draft") or json.dumps(state.get("structured_output", {}), indent=2)[:4000]

    raw_verdict = await review_chain.ainvoke({
        "spec":    spec,
        "content": content,
    })
    verdict: ReviewVerdict = raw_verdict.get("parsed") if isinstance(raw_verdict, dict) else raw_verdict
    if verdict is None:
        err = raw_verdict.get("parsing_error") if isinstance(raw_verdict, dict) else "unknown"
        raise ValueError(f"Review chain parse failed: {err}")

    # Readability penalty for content tasks — Flesch < 40 is too complex
    if state.get("draft"):
        ease = textstat.flesch_reading_ease(state["draft"])
        if ease < 40:
            verdict.score = max(0, verdict.score - 10)
            verdict.specific_feedback = (
                verdict.specific_feedback
                + f"\n\nReadability score too low ({ease:.0f}/100 Flesch ease). "
                "Shorten sentences and use simpler words."
            )

    memory.track_token_spend("review", 4000, "claude-sonnet-4-6")
    return {
        "review_verdict":   verdict.model_dump(),
        "review_iteration": state["review_iteration"] + 1,
        "tokens_used":      state["tokens_used"] + 4000,
    }


async def improve_output(state: GrowthMeshState) -> dict:
    feedback = state["review_verdict"]["specific_feedback"]
    content  = state.get("draft") or json.dumps(state.get("structured_output", {}), indent=2)[:4000]
    improved = await improve_chain.ainvoke({"content": content, "feedback": feedback})
    return {"draft": improved}


async def save_outputs(state: GrowthMeshState) -> dict:
    task = state["task_type"]

    # Fall back to a generic template if specific one missing
    try:
        tpl = _jinja.get_template(f"{task}.md.j2")
    except Exception:
        tpl = _jinja.get_template("generic.md.j2")

    rendered = tpl.render(
        input=state["input"],
        result=state.get("structured_output") or {"content": state.get("draft", "")},
        review=state.get("review_verdict"),
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        tokens=state["tokens_used"],
    )

    path = _output_path(task, state["input"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(rendered)

    # Save to leads CSV/JSON if applicable
    if task == "research_leads" and state.get("structured_output"):
        await _save_leads_files(state["structured_output"], state["input"])

    # Persist to vector store + structured DB
    await memory.store_output(task, rendered, _build_doc_metadata(state))

    if task == "seo_audit" and state.get("structured_output"):
        from src.models.seo import AuditResult
        try:
            result = AuditResult.model_validate(state["structured_output"])
            await memory.save_audit(
                state["input"].get("domain", ""),
                result,
                state["tokens_used"],
            )
        except Exception as exc:
            logger.warning(f"save_audit failed: {exc}")

    _print_summary(task, state, path)
    return {"output_path": path, "final_output": rendered, "memory_saved": True}


async def _save_leads_files(output: dict, inp: dict) -> None:
    import pandas as pd
    leads = output.get("leads", [])
    if not leads:
        return
    df = pd.DataFrame(leads)
    df = df.sort_values("confidence", ascending=False) if "confidence" in df.columns else df
    d = date.today().isoformat()
    slug = _slug(inp)
    base = f"outputs/research/leads-{slug}-{d}"
    df.to_csv(f"{base}.csv", index=False)
    df.to_json(f"{base}.json", orient="records", indent=2)


async def report_to_botlearn(state: GrowthMeshState) -> dict:
    from src.config.settings import get_settings
    if not get_settings().botlearn_api_key:
        return {"botlearn_reported": False}

    try:
        started = datetime.fromisoformat(state["started_at"])
        duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
        from src.modules.botlearn.run_report import report_execution
        await report_execution(
            skill_name=f"growthagent-{state['task_type'].replace('_', '-')}",
            status="success",
            duration_ms=duration_ms,
            tokens_used=state["tokens_used"],
        )
        memory.add_task_since_heartbeat(state["task_type"])
    except Exception as exc:
        logger.warning(f"BotLearn report failed (non-fatal): {exc}")

    return {"botlearn_reported": True}


async def prompt_agenthansa_submit(state: GrowthMeshState) -> dict:
    """Marks submission flag. Actual HTTP submission is handled by execute_quest() wrapper."""
    quest_id = state["input"].get("quest_id")
    if not quest_id:
        return {"agenthansa_submitted": False}
    verdict = state.get("review_verdict")
    submitted = bool(verdict and verdict["score"] >= 75)
    return {"agenthansa_submitted": submitted}
