from __future__ import annotations

import asyncio
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

import typer
from rich.console import Console

from src.core.startup import initialize

console = Console()

direct_seo = typer.Typer(help="SEO audit with 30-day content calendar")
direct_research = typer.Typer(help="Competitor, market, and lead intelligence")
direct_content = typer.Typer(help="Blog posts, email sequences, and social copy")


def _base_state(task_type: str, input_dict: dict) -> dict:
    return {
        "task_type":        task_type,
        "input":            input_dict,
        "run_id":           str(uuid4()),
        "started_at":       datetime.utcnow().isoformat(),
        "review_iteration": 0,
        "tokens_used":      0,
    }


def _run(coro):
    """Run an async coroutine from a sync Typer command."""
    async def _wrapped():
        await initialize()
        await coro
    asyncio.run(_wrapped())


# ── SEO ──────────────────────────────────────────────────────────────

@direct_seo.command("audit")
def seo_audit(
    url:     str       = typer.Argument(..., help="Target URL to audit"),
    compare: list[str] = typer.Option([], "--compare", "-c", help="Competitor URLs"),
):
    """Full SEO audit: crawl → analyse → self-review → 30-day content calendar."""
    from src.core.orchestrator import app
    domain = urlparse(url).netloc or url
    _run(app.ainvoke(_base_state("seo_audit", {
        "url": url, "domain": domain, "competitors": list(compare),
    })))


# ── Research ─────────────────────────────────────────────────────────

@direct_research.command("competitor")
def research_competitor(
    target: str = typer.Argument(..., help="Competitor URL or company name"),
):
    """Competitor teardown: features, pricing, positioning, weaknesses."""
    from src.core.orchestrator import app
    url = target if target.startswith("http") else f"https://{target}"
    _run(app.ainvoke(_base_state("research_competitor", {"target": target, "url": url})))


@direct_research.command("market")
def research_market(
    description: str = typer.Argument(..., help="Industry + ICP description"),
):
    """Market intelligence: trends, buyer triggers, underserved niches."""
    from src.core.orchestrator import app
    _run(app.ainvoke(_base_state("research_market", {
        "icp": description, "industry": description,
    })))


@direct_research.command("leads")
def research_leads(
    icp: str = typer.Argument(..., help="ICP description (title, industry, stage)"),
):
    """Lead intelligence: ICP → qualified lead list (.md + .csv + .json)."""
    from src.core.orchestrator import app
    _run(app.ainvoke(_base_state("research_leads", {"icp": icp})))


# ── Content ───────────────────────────────────────────────────────────

@direct_content.command("blog")
def content_blog(
    keyword: str = typer.Argument(..., help="Target keyword or topic"),
    tone:    str = typer.Option("professional", "--tone", "-t"),
    words:   int = typer.Option(1500, "--words", "-w"),
):
    """SEO blog post: SERP research → outline → write → self-review."""
    from src.core.orchestrator import app
    _run(app.ainvoke(_base_state("content_blog", {
        "keyword": keyword, "tone": tone, "words": words,
    })))


@direct_content.command("email")
def content_email(
    product: str = typer.Argument(..., help="Product name or URL"),
    icp:     str = typer.Option(..., "--icp", "-i", help="Target persona description"),
):
    """5-email cold outreach drip sequence."""
    from src.core.orchestrator import app
    _run(app.ainvoke(_base_state("content_email", {"product": product, "icp": icp})))


@direct_content.command("social")
def content_social(
    platform: str = typer.Argument(..., help="linkedin or twitter"),
    topic:    str = typer.Argument(..., help="Topic or angle"),
    voice:    str = typer.Option("professional", "--voice", "-v"),
):
    """3 ranked social copy variations per platform."""
    from src.core.orchestrator import app
    _run(app.ainvoke(_base_state("content_social", {
        "platform": platform, "topic": topic, "voice": voice,
    })))
