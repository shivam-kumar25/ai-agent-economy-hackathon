from __future__ import annotations

import os
import sys

# Force UTF-8 I/O on Windows so Rich can render unicode (✓, ✗, emoji)
if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import typer

from src.cli.agent import agent_app
from src.cli.botlearn_cli import botlearn_app
from src.cli.direct import direct_content, direct_research, direct_seo
from src.cli.memory_cli import memory_app

cli = typer.Typer(
    name="growthagent",
    help="GrowthMesh — Full B2B Growth Agent. SEO · Research · Content · AgentHansa · BotLearn.",
    no_args_is_help=True,
)

cli.add_typer(direct_seo,      name="seo",      help="SEO audit with 30-day content calendar")
cli.add_typer(direct_research, name="research", help="Competitor, market, and lead intelligence")
cli.add_typer(direct_content,  name="content",  help="Blog posts, email sequences, social copy")
cli.add_typer(agent_app,       name="agent",    help="AgentHansa marketplace control")
cli.add_typer(botlearn_app,    name="botlearn", help="BotLearn benchmark and community")
cli.add_typer(memory_app,      name="memory",   help="Inspect and search agent memory")

if __name__ == "__main__":
    cli()
