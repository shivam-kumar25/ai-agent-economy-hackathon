# GrowthMesh — B2B Growth Agent

Autonomous B2B growth agent that delivers SEO audits, competitor teardowns, market intelligence, lead lists, blog posts, email sequences, and social copy — self-reviewed and quality-scored before delivery.

Built for the **AI Agent Economy Hackathon** (AgentHansa × FluxA, April 25-26 2026).

Deployed on AgentHansa as a hireable expert: merchants send a plain-English request, GrowthMesh parses it, runs the full LangGraph pipeline, and replies with a structured markdown report — automatically.

---

## Architecture

```
LangGraph StateGraph (11 nodes)
  ├── crawl_web_sources   — BeautifulSoup + structured-data extraction
  ├── search_web          — DuckDuckGo + newspaper3k article parsing
  ├── run_llm_analysis    — Claude Sonnet via TokenRouter
  ├── create_outline      — structured outline before writing
  ├── write_content       — task-specific writer chain
  ├── run_self_review     — score + textstat readability (Flesch penalty)
  ├── improve_output      — targeted rewrite if score < 75
  ├── save_outputs        — Jinja2 render + ChromaDB + SQLite
  ├── report_to_botlearn  — XP + skill proof reporting
  └── prompt_agenthansa_submit — A2A quest submission flag

Three-tier memory:
  ChromaDB (semantic search) + SQLite/SQLAlchemy (structured) + state.json (runtime)

AgentHansa integration:
  Quest executor  — picks up and completes A2A quests every 3 hours
  Expert mode     — long-polls /api/experts/updates, executes merchant requests live
  Alliance review — grades other agents' submissions, earns reviewer XP
```

---

## Launch Sequence

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# → Fill in TOKENROUTER_API_KEY (required)

# 3. Init database
python -m alembic upgrade head

# 4. Register on AgentHansa
python main.py agent setup
# → Prints your AGENTHANSA_API_KEY (format: tabb_...)
# → Paste it into .env, then run setup again to complete expert registration:
#   - wires FluxA wallet
#   - upgrades to expert
#   - declares 7 services on the marketplace

# 5. Register on BotLearn
python main.py botlearn setup
# → Prints your BOTLEARN_API_KEY and a claim URL
# → Paste key into .env, visit the claim URL to verify ownership

# 6. Go fully live
python main.py agent run --loop --expert
# Runs forever:
#   Every 3h  → AgentHansa tick (checkin, red packets, quest, daily chain, review)
#   Real-time → Expert receive loop (merchant messages → full pipeline → reply)
#   Every 12h → BotLearn heartbeat (feed engagement, DM replies, XP reporting)
```

---

## Direct Task Commands

```bash
# SEO audit
python main.py seo audit https://yoursite.com

# Competitor teardown
python main.py research competitor https://competitor.com

# Market intelligence
python main.py research market "AI marketing automation"

# Lead generation
python main.py research leads "B2B SaaS CFOs in fintech"

# Long-form blog post
python main.py content blog "The Future of AI in B2B Sales"

# Email sequence (URL → crawls product page automatically)
python main.py content email --product https://yourproduct.com --audience "Series A startups"

# Social copy (LinkedIn + Twitter)
python main.py content social "We just launched X feature"
```

Output lands in `outputs/<task>/<slug>-<date>.md`

---

## AgentHansa Commands

```bash
python main.py agent setup       # Register + expert upgrade + declare services
python main.py agent run --loop --expert  # Full live mode (recommended)
python main.py agent run --loop  # Quest scheduler only (no merchant receive)
python main.py agent listen      # Expert receive loop only
python main.py agent quests      # Browse open quests (ranked)
python main.py agent claim <id>  # Execute a specific quest
python main.py agent review      # Grade alliance submissions
python main.py agent earnings    # Balance + XP + tier
python main.py agent profile     # Full profile JSON
```

---

## BotLearn Commands

```bash
python main.py botlearn setup      # Register + print claim URL
python main.py botlearn benchmark  # Run capability assessment
python main.py botlearn heartbeat  # Feed engagement + DM replies
python main.py botlearn status     # Score + tasks + installed skills
```

---

## Memory Commands

```bash
python main.py memory stats               # Token spend + quest history
python main.py memory search "SEO audit"  # Semantic search over past outputs
```

---

## Task Types & Pricing

| CLI command | task_type | Model | Expert price |
| --- | --- | --- | --- |
| `seo audit` | `seo_audit` | `AuditResult` | $49–$199 |
| `research competitor` | `research_competitor` | `CompetitorTeardown` | $79–$299 |
| `research market` | `research_market` | `MarketReport` | $99–$399 |
| `research leads` | `research_leads` | `LeadList` | $79–$249 |
| `content blog` | `content_blog` | `BlogPost` | $49–$149 |
| `content email` | `content_email` | `EmailSequence` | $79–$199 |
| `content social` | `content_social` | `SocialCopy` | $29–$89 |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TOKENROUTER_API_KEY` | Yes | TokenRouter key (`tr_...`) — routes to Claude |
| `AGENTHANSA_API_KEY` | Yes | AgentHansa key (`tabb_...`) — from `agent setup` |
| `BOTLEARN_API_KEY` | No | BotLearn key (`botlearn_...`) — from `botlearn setup` |
| `FLUXA_AGENT_ID` | No | FluxA wallet ID — for receiving payouts |
| `FLUXA_JWT` | No | FluxA auth token |
| `LANGSMITH_API_KEY` | No | LangSmith tracing (free tier) |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
src/
  config/       — Settings (pydantic-settings, lazy singleton)
  core/         — LangGraph graph, nodes, edges, chains, memory, scheduler
  models/       — Pydantic v2 I/O models for every task type
  db/           — SQLAlchemy ORM + async aiosqlite engine
  modules/
    seo/        — Crawler, keyword extractor, LLM prompts
    research/   — Competitor, market, leads helpers
    content/    — Blog, email, social formatters
    agenthansa/ — Client, quest runner, reviewer, expert hire loop, forum
    botlearn/   — Client, benchmark, community, skill reporting
    fluxa/      — Wallet client, A2A UPL payments
  cli/          — Typer CLI apps (agent, botlearn, seo, research, content, memory)
  templates/    — Jinja2 .md.j2 report templates (one per task type)
alembic/        — DB migrations (tables: audits, quests, reviews, token_spend)
tests/          — pytest suite (orchestrator, crawler, memory, reviewer, scheduler, client)
```
