from __future__ import annotations

import asyncio

import typer
from rich.console import Console

memory_app = typer.Typer(help="Inspect and search agent memory")
console = Console()


@memory_app.command("stats")
def stats():
    """Show memory stats: budget remaining, tokens used, streak."""
    from src.core.memory import memory
    state = memory.get_state()
    remaining = memory.get_remaining_budget()
    console.print(f"Agent ID:       {state.agent_id or 'not registered'}")
    console.print(f"Streak days:    {state.streak_days}")
    console.print(f"XP:             {state.xp}")
    console.print(f"Tokens used:    {state.total_tokens_used:,}")
    console.print(f"Budget left:    {remaining:,}")


@memory_app.command("search")
def search(
    query: str          = typer.Argument(..., help="Search query"),
    task_type: str      = typer.Option("", "--type", "-t", help="Filter by task type"),
    k: int              = typer.Option(3, "--results", "-n"),
):
    """Semantic search over past outputs."""
    async def _do():
        from src.core.memory import memory
        docs = await memory.find_similar(query, task_type or "seo_audit", k=k)
        if not docs:
            console.print("[yellow]No results found[/yellow]")
            return
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            console.print(f"\n[bold]{i}. {meta.get('type', 'unknown')} — {meta.get('date', '')}[/bold]")
            console.print(doc.page_content[:400] + "...")
    asyncio.run(_do())
