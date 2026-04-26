from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import typer
from rich.console import Console

from src.core.startup import initialize

botlearn_app = typer.Typer(help="BotLearn benchmark and community")
console = Console()

_CRED_PATH = Path(".botlearn/credentials.json")
_SDK_PATH  = Path("skills/botlearn/bin/botlearn.sh")


def _run(coro):
    async def _w():
        await initialize()
        await coro
    asyncio.run(_w())


def _read_creds() -> dict:
    if _CRED_PATH.exists():
        try:
            return json.loads(_CRED_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


@botlearn_app.command("setup")
def setup():
    """Register on BotLearn and show the claim URL."""
    creds = _read_creds()

    if creds.get("api_key"):
        api_key = creds["api_key"]
        agent_name = creds.get("agent_name", "GrowthMesh")
        console.print(f"[green]✓ Already registered as [bold]{agent_name}[/bold][/green]")
        console.print(f"  API key: [cyan]{api_key}[/cyan]")
        console.print(f"\n[bold yellow]1. Add to .env:[/bold yellow]  BOTLEARN_API_KEY={api_key}")
        console.print(f"\n[bold yellow]2. Claim your agent:[/bold yellow]  https://www.botlearn.ai/claim/{api_key}")
        console.print("   Log in with Twitter / Google / Email to verify ownership.\n")
        return

    # SDK not installed yet — download and register
    if not _SDK_PATH.exists():
        console.print("[yellow]Downloading BotLearn SDK...[/yellow]")
        Path("skills/botlearn").mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            "curl -sL https://www.botlearn.ai/sdk/botlearn-sdk.tar.gz | tar -xz -C skills/botlearn/",
            shell=True, capture_output=True, text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]SDK download failed: {result.stderr}[/red]")
            return

    console.print("[yellow]Registering on BotLearn...[/yellow]")
    result = subprocess.run(
        ["bash", str(_SDK_PATH), "register",
         "🚀 GrowthMesh",
         "Autonomous B2B growth agent. SEO audits, competitor research, market intelligence, lead generation, and content creation. Powered by Claude Sonnet + LangGraph."],
        capture_output=True, text=True,
    )
    console.print(result.stdout)
    if result.returncode != 0:
        console.print(f"[red]Registration failed: {result.stderr}[/red]")
        return

    creds = _read_creds()
    if creds.get("api_key"):
        api_key = creds["api_key"]
        console.print(f"\n[bold yellow]1. Add to .env:[/bold yellow]  BOTLEARN_API_KEY={api_key}")
        console.print(f"\n[bold yellow]2. Claim your agent:[/bold yellow]  https://www.botlearn.ai/claim/{api_key}")
        console.print("   Log in with Twitter / Google / Email to verify ownership.\n")


@botlearn_app.command("benchmark")
def benchmark():
    """Run the 6-dimension capability benchmark."""
    async def _do():
        from src.modules.botlearn.benchmark import run_benchmark
        report = await run_benchmark()
        console.print(f"\n[bold]Benchmark score: {report.get('overall_score', 0)}/100[/bold]")
        for k, v in report.get("dimensions", {}).items():
            console.print(f"  {k}: {v}")
    _run(_do())


@botlearn_app.command("heartbeat")
def heartbeat():
    """Run manual BotLearn heartbeat: browse feed, engage, reply DMs."""
    async def _do():
        from src.modules.botlearn.heartbeat import run_botlearn_heartbeat
        await run_botlearn_heartbeat()
        console.print("[green]✓ Heartbeat complete[/green]")
    _run(_do())


@botlearn_app.command("status")
def status():
    """Show BotLearn state: benchmark score, last heartbeat, installed skills."""
    creds = _read_creds()
    if creds.get("api_key"):
        console.print(f"Registered as: [bold]{creds.get('agent_name', '?')}[/bold]")
        console.print(f"API key: [cyan]{creds['api_key']}[/cyan]")
    else:
        console.print("[yellow]Not registered — run: python main.py botlearn setup[/yellow]")
        return

    from src.core.memory import memory
    bl = memory.get_botlearn_state()
    console.print(f"Benchmark run:    {bl.benchmark_run}")
    console.print(f"Score:            {bl.benchmark_score}")
    console.print(f"Last heartbeat:   {bl.last_heartbeat or 'never'}")
    console.print(f"Installed skills: {len(bl.installed_skills or [])}")
