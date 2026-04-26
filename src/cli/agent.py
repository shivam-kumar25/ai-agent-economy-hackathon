from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from src.core.startup import initialize

agent_app = typer.Typer(help="AgentHansa marketplace control")
console = Console()


def _run(coro):
    async def _w():
        await initialize()
        await coro
    asyncio.run(_w())


# ── Registration & identity ───────────────────────────────────────────────────

@agent_app.command("setup")
def setup():
    """Register on AgentHansa, wire FluxA wallet, upgrade to Expert, and declare services."""
    async def _do():
        from src.modules.agenthansa.agent import ensure_registered, wire_fluxa_wallet
        from src.modules.agenthansa.expert import upgrade_to_expert, declare_services

        agent_id = await ensure_registered()
        console.print(f"[green]✓ Agent registered — id: {agent_id}[/green]")

        wallet = await wire_fluxa_wallet()
        if wallet:
            console.print("[green]✓ FluxA wallet linked[/green]")

        await upgrade_to_expert()
        console.print("[green]✓ Expert upgrade submitted (pending admin review)[/green]")

        services = await declare_services()
        console.print(f"[green]✓ {len(services)} services declared on the marketplace[/green]")

        console.print("\n[bold cyan]Next:[/bold cyan] Run [bold]python main.py agent run --loop[/bold] to go live")
    _run(_do())


# ── Quest mode ────────────────────────────────────────────────────────────────

@agent_app.command("quests")
def quests():
    """Browse and triage open alliance quests."""
    async def _do():
        from src.modules.agenthansa.quests import triage_quests
        scored = await triage_quests()
        if not scored:
            console.print("[yellow]No viable quests found[/yellow]")
            return
        from rich.table import Table
        t = Table(title="Open Quests (ranked by value/effort)")
        t.add_column("ID"); t.add_column("Title"); t.add_column("Budget")
        t.add_column("Effort"); t.add_column("Score")
        for sq in scored[:10]:
            q = sq.quest
            t.add_row(
                q.get("id", "")[:8], q.get("title", "")[:40],
                f"${q.get('budget', 0):.2f}", sq.triage.effort, f"{sq.score:.2f}",
            )
        console.print(t)
    _run(_do())


@agent_app.command("claim")
def claim(quest_id: str = typer.Argument(..., help="Quest ID to claim and execute")):
    """Claim and execute a specific quest by ID."""
    async def _do():
        from src.modules.agenthansa.client import ah_client
        from src.modules.agenthansa.quests import execute_quest
        quest_data = await ah_client.get(f"/alliance-war/quests/{quest_id}")
        quest = quest_data.get("quest", quest_data)
        await execute_quest(quest)
    _run(_do())


@agent_app.command("review")
def review():
    """Run alliance reviewer pass — grade all pending submissions."""
    async def _do():
        from src.modules.agenthansa.reviewer import run_alliance_reviewer_pass
        await run_alliance_reviewer_pass()
        console.print("[green]✓ Reviewer pass complete[/green]")
    _run(_do())


# ── Live agent modes ──────────────────────────────────────────────────────────

@agent_app.command("run")
def run(
    loop: bool = typer.Option(False, "--loop", help="Run scheduler in continuous loop"),
    expert: bool = typer.Option(False, "--expert", help="Also start the expert merchant receive loop"),
):
    """Start autonomous mode.

    --loop alone:          quest scheduler ticks every 3h, BotLearn heartbeat every 12h\n
    --loop --expert:       quest scheduler + merchant receive loop (gets hired by real businesses)
    """
    async def _do():
        from src.modules.agenthansa.agent import ensure_registered
        await ensure_registered()

        if loop:
            from src.core.scheduler import scheduler
            scheduler.start()
            console.print("[green]✓ Scheduler started (quest ticks every 3h, BotLearn every 12h)[/green]")

            tasks = []
            if expert:
                from src.modules.agenthansa.expert import run_expert_receive_loop
                console.print("[green]✓ Expert receive loop started — listening for merchant requests[/green]")
                tasks.append(asyncio.create_task(run_expert_receive_loop()))

            console.print("[bold]Agent is live. Press Ctrl+C to stop.[/bold]\n")
            try:
                while True:
                    await asyncio.sleep(3600)
            except (KeyboardInterrupt, asyncio.CancelledError):
                for t in tasks:
                    t.cancel()
                scheduler.shutdown()
                console.print("\n[yellow]Agent stopped.[/yellow]")
        else:
            # Single tick
            from src.modules.agenthansa.scheduler_tasks import run_agenthansa_tick
            await run_agenthansa_tick()
    _run(_do())


@agent_app.command("listen")
def listen():
    """Start ONLY the expert merchant receive loop (no quest scheduler)."""
    async def _do():
        from src.modules.agenthansa.expert import run_expert_receive_loop
        console.print("[green]✓ Expert receive loop started — listening for merchant requests[/green]")
        console.print("[bold]Waiting for merchants... Press Ctrl+C to stop.[/bold]\n")
        try:
            await run_expert_receive_loop()
        except (KeyboardInterrupt, asyncio.CancelledError):
            console.print("\n[yellow]Receive loop stopped.[/yellow]")
    _run(_do())


# ── Status & earnings ─────────────────────────────────────────────────────────

@agent_app.command("earnings")
def earnings():
    """Show current balance, XP, and streak."""
    async def _do():
        from src.modules.agenthansa.agent import get_earnings
        data = await get_earnings()
        console.print(
            f"Balance: [green]${data.get('balance_usd', 0):.2f}[/green]  |  "
            f"XP: [cyan]{data.get('xp', 0)}[/cyan]  |  "
            f"Tier: {data.get('tier', 'unknown')}"
        )
    _run(_do())


@agent_app.command("profile")
def profile():
    """Show full AgentHansa profile including expert status."""
    async def _do():
        from src.modules.agenthansa.agent import get_profile
        data = await get_profile()
        import json
        console.print_json(json.dumps(data, indent=2))
    _run(_do())
