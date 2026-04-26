# GrowthMesh Agent — Folder Structure

Every file has one job. Every layer speaks the same language.
LangGraph nodes live in `core/nodes.py`. LCEL chains in `core/chains.py`.
Pydantic models in `models/`. Jinja2 templates in `src/templates/`.
No caller ever touches a DB or vector store directly — everything goes through `core/memory.py`.

---

## Full Directory Tree

```
growthagent/
│
├── spec/                                   # Design docs — read before writing code
│   ├── constitution.md                     # Identity, mission, platform stack
│   ├── tech-stack.md                       # All code patterns: LangGraph, LLM, memory
│   ├── workflow.md                         # All node implementations, scheduler, CLI
│   └── folder-structure.md                 # This file
│
├── src/
│   │
│   ├── config/                             # Configuration — nothing else imports settings directly
│   │   ├── __init__.py
│   │   └── settings.py                     # Settings (pydantic-settings) + get_settings() lazy singleton
│   │
│   ├── core/                               # Engine — shared by every task
│   │   ├── __init__.py
│   │   ├── orchestrator.py                 # build_graph() + app (compiled LangGraph singleton)
│   │   ├── graph_state.py                  # GrowthMeshState TypedDict + TaskType literal
│   │   ├── nodes.py                        # All LangGraph node functions (async def)
│   │   ├── edges.py                        # _decide_first_node, _is_content_task, _review_decision
│   │   ├── chains.py                       # ANALYSIS_CHAINS, WRITE_CHAINS, review/outline/improve chains
│   │   ├── memory.py                       # Memory interface — only public API callers use
│   │   ├── scheduler.py                    # build_scheduler() + module-level scheduler instance
│   │   └── startup.py                      # initialize() — dirs, DB, LLM cache, credential check
│   │
│   ├── models/                             # Pydantic v2 models — all LLM I/O validated here
│   │   ├── __init__.py
│   │   ├── seo.py                          # AuditResult, SEOIssue, KeywordGap, ContentOpportunity
│   │   ├── research.py                     # CompetitorTeardown, MarketReport, LeadList, LeadRecord
│   │   ├── content.py                      # BlogPost, EmailSequence, SocialCopy, ContentOutline
│   │   ├── review.py                       # ReviewVerdict, QuestTriage, ScoredQuest
│   │   ├── agenthansa.py                   # QuestRecord, AllianceAgent, CheckinResult, RedPacket
│   │   └── botlearn.py                     # BotLearnState, BenchmarkResult, SkillRecord, AgentState
│   │
│   ├── db/                                 # SQLAlchemy ORM — only memory.py touches these
│   │   ├── __init__.py
│   │   ├── engine.py                       # create_async_engine, AsyncSessionLocal factory
│   │   ├── base.py                         # DeclarativeBase
│   │   ├── tables.py                       # AuditRecord, QuestRecord, ReviewRecord, TokenSpend
│   │   └── queries.py                      # Reusable async query helpers (get_latest_audit, etc.)
│   │
│   ├── modules/
│   │   │
│   │   ├── seo/                            # SEO Audit Engine
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py                  # httpx + BS4 + extruct: all SEO signal extraction
│   │   │   ├── keywords.py                 # KeyBERT lazy singleton + async extract_keywords()
│   │   │   ├── calendar.py                 # Jinja2: 30-day content calendar from AuditResult.content_map
│   │   │   └── prompts.py                  # SEO_ANALYSIS_PROMPT (large — use cached_system())
│   │   │
│   │   ├── research/                       # Research Engine
│   │   │   ├── __init__.py
│   │   │   ├── competitor.py               # Parallel crawl + review signals + CompetitorTeardown chain
│   │   │   ├── market.py                   # DuckDuckGo question loop + MarketReport chain
│   │   │   ├── leads.py                    # ICP parse + scrape + enrich + Pandas CSV/JSON export
│   │   │   └── prompts.py                  # COMPETITOR_ANALYSIS_PROMPT, MARKET_INTEL_PROMPT, LEAD_INTEL_PROMPT
│   │   │
│   │   ├── content/                        # Content Engine
│   │   │   ├── __init__.py
│   │   │   ├── blog.py                     # SERP gap analysis helper for outline chain
│   │   │   ├── email.py                    # 5-email drip structure helpers
│   │   │   ├── social.py                   # Platform-specific format helpers (LinkedIn/Twitter)
│   │   │   └── prompts.py                  # BLOG_WRITER_PROMPT, EMAIL_WRITER_PROMPT, SOCIAL_WRITER_PROMPT
│   │   │
│   │   ├── agenthansa/                     # AgentHansa Marketplace
│   │   │   ├── __init__.py
│   │   │   ├── client.py                   # AgentHansaClient: get/post/put/patch, @retry on all, __aenter__/__aexit__
│   │   │   ├── agent.py                    # register_agent() (unauthenticated), ensure_registered(), wire_fluxa_wallet()
│   │   │   ├── expert.py                   # upgrade_to_expert(), declare_services() (7 tiers), run_expert_receive_loop()
│   │   │   ├── quests.py                   # triage_quests(), execute_quest(), _map_quest_to_task_type()
│   │   │   ├── reviewer.py                 # run_alliance_reviewer_pass(), _record_review()
│   │   │   ├── publisher.py                # Publish A2A task specs to community/collective mesh
│   │   │   ├── red_packets.py              # Detect active packets, solve challenge, join
│   │   │   ├── forum.py                    # Post + vote helpers used by daily quest chain
│   │   │   └── scheduler_tasks.py          # run_agenthansa_tick(), complete_daily_quest_chain()
│   │   │
│   │   ├── botlearn/                       # BotLearn Agent University
│   │   │   ├── __init__.py
│   │   │   ├── client.py                   # BotLearnClient: __aenter__/__aexit__, @retry on all methods
│   │   │   ├── setup.py                    # SDK install, register, claim flow, Botcord subscribe
│   │   │   ├── benchmark.py                # run_benchmark(): scan → exam → report → skill hunt
│   │   │   ├── community.py                # Post, vote, comment, DM — called from heartbeat
│   │   │   ├── heartbeat.py                # run_botlearn_heartbeat(): SDK check → browse → engage → DM
│   │   │   ├── run_report.py               # report_execution() + @botlearn_tracked decorator
│   │   │   └── skills.py                   # _install_skill(), list installed skills
│   │   │
│   │   └── fluxa/                          # FluxA Payment Layer
│   │       ├── __init__.py
│   │       ├── wallet.py                   # Status, x402 payment, payout request
│   │       └── upl.py                      # UPL: construct + execute agent-to-agent transfer
│   │
│   ├── cli/                                # Typer CLI command groups
│   │   ├── __init__.py
│   │   ├── direct.py                       # direct_seo, direct_research, direct_content Typer apps
│   │   ├── agent.py                        # agent_app: setup, run --loop --expert, listen, quests, claim, review, earnings, profile
│   │   ├── botlearn_cli.py                 # botlearn_app: benchmark, heartbeat, setup, status
│   │   └── memory_cli.py                   # memory_app: stats, search
│   │
│   ├── utils/                              # Shared utilities — zero business logic
│   │   ├── __init__.py
│   │   ├── llm.py                          # llm, llm_fast, cached_system() — import everywhere
│   │   ├── scraper.py                      # httpx async fetch + asyncio.to_thread(article.parse)
│   │   ├── logger.py                       # Loguru: console (Rich) + rotating JSON file
│   │   ├── retry.py                        # _api_retry() factory — used by all API clients
│   │   └── exceptions.py                   # GrowthMeshError hierarchy
│   │
│   └── templates/                          # Jinja2 Markdown templates (one per output type)
│       ├── seo_audit.md.j2
│       ├── seo_calendar.md.j2
│       ├── research_competitor.md.j2
│       ├── research_market.md.j2
│       ├── research_leads.md.j2
│       ├── content_blog.md.j2
│       ├── content_email.md.j2
│       └── content_social.md.j2
│
├── skills/                                 # BotLearn SDK (auto-installed via npx, do not edit)
│   └── botlearn/
│       ├── skill.json                      # SDK version manifest
│       ├── core/
│       ├── benchmark/
│       ├── community/
│       └── api/
│
├── .botlearn/                              # BotLearn credentials (never committed)
│   ├── credentials.json                    # {api_key: "botlearn_..."}
│   ├── config.json                         # Permissions + autonomy settings
│   └── state.json                          # Onboarding + benchmark progress (SDK-managed)
│
├── memory/                                 # Persistent memory — all tiers
│   ├── growthagent.db                      # SQLite: AuditRecord, QuestRecord, ReviewRecord, TokenSpend
│   ├── llm_cache.db                        # SQLiteCache: LangChain LLM response cache
│   ├── state.json                          # Runtime state: streak, XP, BotLearn state, last ticks
│   └── chroma/                             # ChromaDB vector store (auto-managed)
│       └── growthagent/                    # Collection — all task types stored here with type filter
│
├── outputs/                                # All agent-generated deliverables
│   ├── audits/
│   │   ├── {domain}-{YYYY-MM-DD}.md
│   │   └── {domain}-{YYYY-MM-DD}-calendar.md
│   ├── research/
│   │   ├── competitor-{slug}-{date}.md
│   │   ├── market-{slug}-{date}.md
│   │   ├── leads-{slug}-{date}.md
│   │   ├── leads-{slug}-{date}.csv
│   │   └── leads-{slug}-{date}.json
│   └── content/
│       ├── blog-{slug}-{date}.md
│       ├── email-seq-{slug}-{date}.md
│       └── social-{slug}-{date}.md
│
├── alembic/                                # DB migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
│
├── tests/
│   ├── conftest.py                         # Fixtures: mock clients, in-memory DB, respx
│   ├── test_orchestrator.py                # Graph routing + state transitions
│   ├── test_seo_crawler.py                 # BS4 + extruct extraction (respx mocked)
│   ├── test_reviewer.py                    # ReviewVerdict score thresholds
│   ├── test_memory.py                      # ChromaDB + SQLAlchemy reads/writes
│   ├── test_agenthansa_client.py           # Retry logic (respx mocked, 429 → backoff)
│   └── test_scheduler.py                   # Tick timing (freezegun)
│
├── .env                                    # Secret keys — never committed
├── .env.example                            # All required keys with inline comments
├── .gitignore                              # .env, .botlearn/, memory/, outputs/, __pycache__/
├── alembic.ini
├── pytest.ini                              # asyncio_mode = auto
├── requirements.txt
├── main.py                                 # Typer root CLI — registers all command groups
└── README.md                               # Launch sequence + task types + pricing table
```

---

## Key File Responsibilities

### `src/config/settings.py`

Single source of truth for all configuration. Never import `Settings` directly — always use
`get_settings()` so the `.env` is loaded lazily and tests can override without side effects.

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    tokenrouter_api_key: str = Field(..., description="Required — app fails here if missing")
    # ... all other fields
    agenthansa_tick_hours:    int = Field(3)
    botlearn_heartbeat_hours: int = Field(12)

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

---

### `src/core/orchestrator.py`

Builds and exports the compiled LangGraph app. Only file that defines graph topology.
Import `app` from here — never rebuild the graph outside this module.

```python
from langgraph.graph import StateGraph, END
from src.core.graph_state import GrowthMeshState
from src.core.nodes import *
from src.core.edges import *

def build_graph() -> StateGraph:
    g = StateGraph(GrowthMeshState)
    # ... node + edge registration (see workflow.md §3)
    return g

app = build_graph().compile()   # compiled singleton — import everywhere
```

---

### `src/core/nodes.py`

All LangGraph node functions. Each is an `async def` that takes `GrowthMeshState`
and returns a **partial** state dict — only the keys it sets.

Async boundaries are explicit:
- `WebBaseLoader.load()` → `asyncio.to_thread(loader.load)`
- `newspaper.Article.parse()` → `asyncio.to_thread(article.parse)`
- File writes → `aiofiles.open()`
- Vector store → `await vector_store.aadd_documents()`
- Memory queries → `await memory.get_latest_audit()`

```python
async def route_by_task_type(state: GrowthMeshState) -> dict: ...
async def crawl_web_sources(state: GrowthMeshState) -> dict: ...
async def search_web(state: GrowthMeshState) -> dict: ...
async def run_llm_analysis(state: GrowthMeshState) -> dict: ...
async def create_outline(state: GrowthMeshState) -> dict: ...
async def write_content(state: GrowthMeshState) -> dict: ...
async def run_self_review(state: GrowthMeshState) -> dict: ...
async def improve_output(state: GrowthMeshState) -> dict: ...
async def save_outputs(state: GrowthMeshState) -> dict: ...
async def report_to_botlearn(state: GrowthMeshState) -> dict: ...
async def prompt_agenthansa_submit(state: GrowthMeshState) -> dict: ...
```

---

### `src/core/chains.py`

All LCEL chain definitions — one file, one dict per chain type. Nodes import from here.
Chains are module-level singletons (prompt templates and models are stateless).

```python
ANALYSIS_CHAINS: dict[str, Runnable] = {
    "seo_audit":           ... | llm.with_structured_output(AuditResult),
    "research_competitor": ... | llm.with_structured_output(CompetitorTeardown),
    "research_market":     ... | llm.with_structured_output(MarketReport),
    "research_leads":      ... | llm.with_structured_output(LeadList),
}

WRITE_CHAINS: dict[str, Runnable] = {
    "content_blog":   ... | llm | StrOutputParser(),
    "content_email":  ... | llm | StrOutputParser(),
    "content_social": ... | llm | StrOutputParser(),
}

review_chain:  Runnable  # → ReviewVerdict
outline_chain: Runnable  # → ContentOutline (llm_fast / haiku)
improve_chain: Runnable  # → str (StrOutputParser)
triage_chain:  Runnable  # → QuestTriage (llm_fast / haiku)
```

---

### `src/core/memory.py` — Complete Public Interface

The only file in the codebase that touches ChromaDB, SQLAlchemy, or state.json.
All other modules call this interface — swapping backends requires changes here only.

```python
class Memory:
    # ── Semantic (ChromaDB) ────────────────────────────────────────────────
    async def find_similar(self, query: str, task_type: str, k: int = 3) -> list[Document]: ...
    async def store_output(self, task_type: str, content: str, metadata: dict) -> None: ...

    # ── Structured (SQLAlchemy async) ──────────────────────────────────────
    async def save_audit(self, domain: str, result: AuditResult, tokens: int) -> None: ...
    async def get_latest_audit(self, domain: str) -> AuditResult | None: ...
    async def save_quest(self, record: QuestRecord) -> None: ...
    async def update_quest_outcome(self, quest_id: str, outcome: str, payout: float) -> None: ...
    async def save_review(self, record: ReviewRecord) -> None: ...
    async def already_reviewed(self, quest_id: str, agent_id: str) -> bool: ...

    # ── Runtime state (state.json — synchronous key-value) ────────────────
    def get_state(self) -> AgentState: ...
    def update_state(self, **kwargs) -> None: ...          # NOT async — local file write
    def get_last_task_tokens(self) -> int: ...             # last value from track_token_spend
    def track_token_spend(self, label: str, tokens: int, model: str) -> None: ...
    def get_remaining_budget(self) -> int: ...             # token_budget_total − sum(token_spend)

    # ── BotLearn state (state.json sub-key) ───────────────────────────────
    def get_botlearn_state(self) -> BotLearnState: ...
    def update_botlearn_state(self, **kwargs) -> None: ...  # NOT async — local file write
    def add_task_since_heartbeat(self, label: str) -> None: ...
    def flush_tasks_since_heartbeat(self) -> list[str]: ... # returns and clears the list

memory = Memory()   # module-level singleton — import everywhere
```

**Important:** `update_state()` and `update_botlearn_state()` are **synchronous** — they
write to a local JSON file. Never call them with `await`. Async DB methods (`save_audit`,
`get_latest_audit`, etc.) must always be `await`ed.

**Swap note:** To replace ChromaDB with HydraDB or Claude-Mem (built by two of the four
hackathon judges), re-implement only `find_similar()` and `store_output()`. SQLAlchemy,
state.json, and the public interface stay unchanged.

---

### `src/modules/botlearn/run_report.py`

Decorator and direct function. Applied to every major task entry point.

```python
async def report_execution(
    skill_name: str,
    status: str,
    duration_ms: int,
    tokens_used: int,
) -> None:
    """Never raises — BotLearn failure is non-fatal."""
    try:
        await bl_client.post("/api/v2/run-report", {
            "skill_name":  skill_name,
            "status":      status,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
        })
    except Exception as exc:
        logger.warning(f"BotLearn run-report failed (non-fatal): {exc}")

def botlearn_tracked(skill_name: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            start         = time.monotonic()
            tokens_before = memory.get_last_task_tokens()
            status        = "success"
            try:
                return await fn(*args, **kwargs)
            except Exception:
                status = "failure"
                raise
            finally:
                await report_execution(
                    skill_name=skill_name,
                    status=status,
                    duration_ms=int((time.monotonic() - start) * 1000),
                    tokens_used=max(0, memory.get_last_task_tokens() - tokens_before),
                )
        return wrapper
    return decorator
```

---

### `src/db/tables.py` — SQLAlchemy ORM

```python
class AuditRecord(Base):
    __tablename__ = "audits"
    id, domain (indexed), score, issues_count, keyword_gaps, tokens_used, created_at, raw_result (JSON)

class QuestRecord(Base):
    __tablename__ = "quests"
    id (PK), task_type (indexed), reward_usd, self_review_score, human_verified,
    outcome, payout_usd, tokens_used, created_at

class ReviewRecord(Base):
    __tablename__ = "reviews"
    id, quest_id (indexed), agent_id, agent_name, score, verdict, feedback, created_at

class TokenSpend(Base):
    __tablename__ = "token_spend"
    id, task_label, tokens_used, model, created_at
```

---

### `src/modules/agenthansa/client.py` — API Client Contract

All client methods have `@_api_retry()` (tenacity, 3 attempts, exponential backoff).
Client is used as a module-level singleton — it is created at import and its `httpx.AsyncClient`
is kept alive for the process lifetime. In tests, inject a mock client.

```python
class AgentHansaClient:
    async def __aenter__(self) -> "AgentHansaClient": ...
    async def __aexit__(self, *_) -> None: ...         # aclose() the httpx client
    async def get(self, path: str, **kwargs) -> dict: ...     # @retry
    async def post(self, path: str, json: dict | None, **kwargs) -> dict: ...  # @retry
    async def patch(self, path: str, json: dict | None) -> dict: ...  # @retry

ah_client = AgentHansaClient()   # singleton
```

---

### `src/modules/agenthansa/agent.py` — Registration (Idempotent)

```python
async def ensure_registered() -> str:
    """Register on AgentHansa if not already. Returns agent_id. Safe to call multiple times."""
    state = memory.get_state()
    if state.agent_id:
        return state.agent_id
    result = await ah_client.post("/agents/register", {
        "name":        "GrowthMesh",
        "description": "Full B2B growth agent. SEO, research, content, reviewer.",
        "alliance":    get_settings().agenthansa_alliance,
    })
    memory.update_state(agent_id=result["id"])
    return result["id"]
```

---

### `main.py` — Typer Root CLI

Three separate Typer apps for the three direct task groups, plus agent/botlearn/memory.

```python
import typer
from src.cli.direct    import direct_seo, direct_research, direct_content
from src.cli.agent     import agent_app
from src.cli.botlearn_cli import botlearn_app
from src.cli.memory_cli   import memory_app

cli = typer.Typer(name="growthagent", help="GrowthMesh — Full B2B Growth Agent")
cli.add_typer(direct_seo,      name="seo",       help="SEO audit with calendar")
cli.add_typer(direct_research, name="research",  help="Competitor, market, lead intelligence")
cli.add_typer(direct_content,  name="content",   help="Blog, email, social copy")
cli.add_typer(agent_app,       name="agent",     help="AgentHansa marketplace control")
cli.add_typer(botlearn_app,    name="botlearn",  help="BotLearn benchmark and heartbeat")
cli.add_typer(memory_app,      name="memory",    help="Inspect and search agent memory")

if __name__ == "__main__":
    cli()
```

CLI commands this produces:

```
growthagent seo audit <url> [--compare <url>...]
growthagent research competitor <target>
growthagent research market "<description>"
growthagent research leads "<icp>"
growthagent content blog "<keyword>" [--tone] [--words]
growthagent content email "<product>" --icp "<persona>"
growthagent content social <linkedin|twitter> "<topic>" [--voice]
growthagent agent run --loop
growthagent agent quests
growthagent agent claim <quest-id>
growthagent agent review
growthagent botlearn benchmark
growthagent botlearn heartbeat
growthagent botlearn setup
growthagent memory search "<query>"
growthagent memory stats
```

---

## Build Priority Order

Each step unblocks the next. MVP demo achievable at step 10.

| Step | Files | What it unlocks |
|---|---|---|
| 1 | `src/config/settings.py` + `.env` + `.env.example` | All platform clients |
| 2 | `src/utils/exceptions.py` + `retry.py` + `logger.py` | Safe, observable calls |
| 3 | `src/utils/llm.py` — `llm`, `llm_fast`, `cached_system()` | All LCEL chains |
| 4 | `src/models/` — all Pydantic models | Typed I/O everywhere |
| 5 | `src/db/` — engine, tables, queries + `alembic` migration | Structured memory |
| 6 | `src/core/memory.py` — all three tiers wired | Graph nodes can persist |
| 7 | `src/modules/agenthansa/client.py` + `agent.py` | Live agent registration |
| 8 | `src/core/graph_state.py` + `chains.py` | Graph foundation |
| 9 | `src/modules/seo/crawler.py` + `keywords.py` | Crawl node ready |
| 10 | `src/core/nodes.py` (crawl + analyze + save) + `orchestrator.py` | **First demo-able run** |
| 11 | `src/core/nodes.py` (self_review + improve) + `edges.py` | Review loop active |
| 12 | `src/modules/agenthansa/quests.py` + `reviewer.py` | First real quest submitted |
| 13 | `src/modules/botlearn/client.py` + `setup.py` + `run_report.py` | BotLearn reporting live |
| 14 | `src/modules/botlearn/benchmark.py` | Public capability score |
| 15 | `src/modules/research/` all files | Research tasks complete |
| 16 | `src/modules/content/blog.py` | Blog writer complete |
| 17 | `src/modules/content/email.py` + `social.py` | Full content suite |
| 18 | `src/modules/botlearn/heartbeat.py` + `community.py` | BotLearn active |
| 19 | `src/core/scheduler.py` + `scheduler_tasks.py` | Full autonomous mode |
| 20 | `main.py` full CLI wiring + `src/templates/` all Jinja2 | Polished demo |
| 21 | `src/modules/fluxa/` | Payment features |
| 22 | `src/modules/agenthansa/publisher.py` | A2A orchestration |
| 23 | `tests/` all files | Judge-ready GitHub repo |

Steps 1–12 = minimum viable demo (SEO audit + quest + BotLearn registered).
Steps 13–20 = full feature demo.
Steps 21–23 = polish + stretch goals.

---

## Critical Invariants (never break these)

| Invariant | Enforced by |
|---|---|
| Only `memory.py` touches the DB or vector store | Module boundary — no direct SQLAlchemy imports outside `db/` and `memory.py` |
| All LLM output is Pydantic-validated | `.with_structured_output(Model)` on every analysis chain |
| No sync I/O inside async graph nodes | `asyncio.to_thread()` for blocking libs, `aiofiles` for file writes |
| `settings` never read at import time | `get_settings()` lazy singleton via `@lru_cache` |
| Self-review score < 75 is never submitted to AgentHansa | `_review_decision` returns `"force"` → save locally, no submit |
| BotLearn `report_execution()` never raises | try/except inside the function — logging only |
| API clients retry on all methods | `@_api_retry()` on `get`, `post`, `patch` |
| APScheduler exceptions are logged | `_on_job_error` listener registered at startup |
| Agent registration is idempotent | `ensure_registered()` checks state.json before POST |
