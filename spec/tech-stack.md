# GrowthMesh Agent — Tech Stack

Everything is in sync. Every layer speaks the same language: async-first, Pydantic-typed,
LangSmith-traced, and ChromaDB-searchable. No library fights another.

---

## Architecture Overview

```
CLI (Typer + Rich)
      │
      ▼
LangGraph StateGraph  ◄─── LangSmith (traces every node)
      │
      ├── LangChain LCEL Chains
      │         │
      │         ├── langchain-anthropic → TokenRouter → Claude (cached)
      │         ├── langchain-community → Web loaders, DuckDuckGo search
      │         └── Pydantic v2 output parsers (all LLM output validated)
      │
      ├── Web Intelligence
      │         ├── httpx (async HTTP — all API calls)
      │         ├── BeautifulSoup4 + extruct (SEO signal extraction)
      │         ├── newspaper3k (article extraction — run in ThreadPoolExecutor)
      │         ├── textstat (readability scoring)
      │         └── KeyBERT (keyword extraction — lazy-loaded, ThreadPoolExecutor)
      │
      └── Memory Layer
                ├── ChromaDB + langchain-chroma (semantic search over past work)
                ├── SQLAlchemy + aiosqlite (structured relational records)
                ├── diskcache / SQLiteCache (LangChain LLM response cache)
                └── Jinja2 + aiofiles (templated async file output)
```

---

## 1. Language & Runtime

| Layer | Choice | Reason |
|---|---|---|
| Language | **Python 3.11+** | `Required`/`NotRequired` in TypedDict, full async, entire AI ecosystem |
| Package manager | **pip + venv** | Zero friction |
| CLI framework | **Typer** | Click on type hints — auto-docs, auto-completions, cleaner than raw Click |
| Terminal output | **Rich** | Tables, progress bars, syntax highlighting — demo looks polished |
| Logging | **Loguru** | Single import, structured JSON log files, zero config |

---

## 2. LangChain + LangGraph Ecosystem

### Core Packages

| Package | Version | Role |
|---|---|---|
| `langchain-core` | `>=0.3` | LCEL primitives: Runnable, RunnablePassthrough, RunnableLambda |
| `langchain-anthropic` | `>=0.3` | Claude via TokenRouter (single `base_url` override) |
| `langchain-community` | `>=0.3` | WebBaseLoader, DuckDuckGoSearchResults, SitemapLoader |
| `langgraph` | `>=0.2` | StateGraph orchestrator — the agent's central nervous system |
| `langsmith` | `>=0.2` | Automatic tracing of every chain, node, and LLM call |

### TokenRouter Integration

```python
# src/utils/llm.py
from langchain_anthropic import ChatAnthropic
from src.config.settings import get_settings

def _make_llm(model: str, max_tokens: int) -> ChatAnthropic:
    s = get_settings()
    return ChatAnthropic(
        model=model,
        anthropic_api_key=s.tokenrouter_api_key,
        anthropic_api_url="https://api.tokenrouter.com",  # TokenRouter endpoint
        max_tokens=max_tokens,
    )

# Module-level singletons — safe because _make_llm only runs on first import,
# not at import of settings (settings are loaded lazily via get_settings()).
llm      = _make_llm("claude-sonnet-4-6",       max_tokens=4096)
llm_fast = _make_llm("claude-haiku-4-5-20251001", max_tokens=1024)
```

### Prompt Caching

```python
from langchain_core.messages import SystemMessage

def cached_system(prompt: str) -> SystemMessage:
    """Wrap a large system prompt with cache_control for 80-90% token savings on repeats."""
    return SystemMessage(
        content=prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}},
    )
```

### LangSmith Observability (free tier, zero config)

```python
# .env — no code changes needed, all chains traced automatically
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=growthagent-hackathon
```

Every LangGraph node, every LLM call, every tool invocation appears in LangSmith with:
input/output at each step, token counts and latency, full chain visualization, cost per run.

### LCEL Chain Pattern

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Research/SEO chains — structured output via Claude tool-use
audit_chain = (
    ChatPromptTemplate.from_messages([
        cached_system(SEO_SYSTEM_PROMPT),
        ("human", "Domain: {domain}\nCrawl data:\n{crawl_data}\nPrior audit:\n{prior_audit}"),
    ])
    | llm.with_structured_output(AuditResult)   # Pydantic v2 — schema guaranteed by tool-use
)

# Content chains — free-form text
blog_chain = (
    ChatPromptTemplate.from_messages([
        cached_system(BLOG_WRITER_PROMPT),
        ("human", "Outline:\n{outline}\nKeyword: {keyword}\nTone: {tone}"),
    ])
    | llm
    | StrOutputParser()
)

# Nodes call chains directly — prior_audit is awaited before ainvoke(), not inside the chain.
# This avoids mixing sync/async inside LCEL lambdas.
prior = await memory.get_latest_audit(domain)
result: AuditResult = await audit_chain.ainvoke({
    "domain":     domain,
    "crawl_data": crawl_data,
    "prior_audit": prior.model_dump_json() if prior else "No prior audit.",
})
```

---

## 3. LangGraph Orchestrator

### State Schema — Split TypedDict (Python 3.11+)

```python
# src/core/graph_state.py
from __future__ import annotations
from typing import TypedDict, Literal, Any

TaskType = Literal[
    "seo_audit", "research_competitor", "research_market",
    "research_leads", "content_blog", "content_email", "content_social",
]

class _GrowthMeshStateRequired(TypedDict):
    """Fields that MUST be present in the initial state passed to app.ainvoke()."""
    task_type:        TaskType
    input:            dict[str, Any]   # raw CLI or quest input
    run_id:           str              # UUID4 — used for LangSmith trace grouping
    started_at:       str              # datetime.utcnow().isoformat()
    review_iteration: int              # must start at 0
    tokens_used:      int              # must start at 0

class GrowthMeshState(_GrowthMeshStateRequired, total=False):
    """Fields populated during graph execution — absent until set by a node."""
    # Web data
    crawl_results:    list[dict]
    search_results:   list[dict]
    # LLM work
    outline:          dict | None
    draft:            str | None
    structured_output: dict | None
    # Review loop
    review_verdict:   dict | None      # ReviewVerdict.model_dump() stored as dict
    # Output
    final_output:     str
    output_path:      str
    # Side-effect flags
    memory_saved:     bool
    botlearn_reported: bool
    agenthansa_submitted: bool
```

**Initial state construction** — only 6 fields required:

```python
initial_state: GrowthMeshState = {
    "task_type":        "seo_audit",
    "input":            {"url": url, "domain": domain, "competitors": compare},
    "run_id":           str(uuid4()),
    "started_at":       datetime.utcnow().isoformat(),
    "review_iteration": 0,
    "tokens_used":      0,
}
result = await app.ainvoke(initial_state)
```

### Graph Definition

```python
from langgraph.graph import StateGraph, END

g = StateGraph(GrowthMeshState)

g.add_node("route",        route_by_task_type)
g.add_node("crawl",        crawl_web_sources)
g.add_node("search",       search_web)
g.add_node("analyze",      run_llm_analysis)
g.add_node("outline",      create_outline)
g.add_node("write",        write_content)
g.add_node("self_review",  run_self_review)
g.add_node("improve",      improve_output)
g.add_node("save",         save_outputs)
g.add_node("report",       report_to_botlearn)
g.add_node("submit_prompt", prompt_agenthansa_submit)

g.set_entry_point("route")

g.add_conditional_edges("route", _decide_first_node, {
    "crawl":  "crawl",
    "search": "search",
    "write":  "write",   # email/social with no URL product — skip crawl
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
    "force":   "save",    # max retries hit — save best attempt
})
g.add_edge("improve",       "self_review")
g.add_edge("save",          "report")
g.add_edge("report",        "submit_prompt")
g.add_edge("submit_prompt", END)

app = g.compile()   # singleton — imported everywhere
```

### Edge Functions

```python
# src/core/edges.py

def _decide_first_node(state: GrowthMeshState) -> str:
    t = state["task_type"]
    if t == "content_email":
        # If product is a URL, crawl it to build context before writing
        product = state["input"].get("product", "")
        if product.startswith(("http://", "https://")):
            return "crawl"
        return "write"
    if t == "content_social":
        return "write"   # topic only — no crawl needed
    if t in ("seo_audit", "research_competitor"):
        return "crawl"
    return "search"      # market, leads, blog

def _is_content_task(state: GrowthMeshState) -> bool:
    return state["task_type"].startswith("content_")

def _review_decision(state: GrowthMeshState) -> str:
    v = state.get("review_verdict")
    if v and v["score"] >= 75:
        return "pass"
    if state["review_iteration"] >= 2:
        return "force"   # never improve more than twice
    return "improve"
```

---

## 4. Web Intelligence Layer

### HTTP Client

```python
# Used inside node async context managers — not as a module-level singleton
# to avoid resource leaks when the process exits without explicit cleanup.

async def _make_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(15.0, connect=5.0),
        headers={"User-Agent": "GrowthMesh/1.0 (B2B growth agent)"},
        follow_redirects=True,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    )
```

### Web Loaders (LangChain-community)

```python
from langchain_community.document_loaders import WebBaseLoader
import asyncio

# WebBaseLoader.load() is synchronous — run in thread pool to avoid blocking the event loop.
loader = WebBaseLoader(
    web_paths=["https://example.com", "https://example.com/pricing"],
    requests_per_second=2,     # rate limit politely
    continue_on_failure=True,  # don't crash on 403s
)
docs = await asyncio.to_thread(loader.load)
```

### Article Extraction

```python
import newspaper  # package: newspaper3k, import: newspaper

# newspaper3k .download() and .parse() are synchronous and CPU-bound.
# Always run them in a thread to avoid blocking the event loop.
async def extract_article(url: str, html: str) -> tuple[str, str]:
    article = newspaper.Article(url)
    article.set_html(html)
    await asyncio.to_thread(article.parse)
    return article.title, article.text
```

### Web Search

```python
from langchain_community.tools import DuckDuckGoSearchResults
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_duckduckgo = DuckDuckGoSearchResults(output_format="list", num_results=8)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def web_search(query: str) -> list[dict]:
    """DuckDuckGo can rate-limit aggressively — retry with backoff."""
    return await _duckduckgo.arun(query)
```

### SEO Signal Extraction

```python
from bs4 import BeautifulSoup
import extruct

soup = BeautifulSoup(html, "lxml")
title   = soup.find("title").text if soup.find("title") else ""
meta    = (soup.find("meta", attrs={"name": "description"}) or {}).get("content", "")
h_tags  = [(t.name, t.text.strip()) for t in soup.find_all(["h1", "h2", "h3"])]
images  = soup.find_all("img")
alt_cov = sum(1 for i in images if i.get("alt")) / max(len(images), 1)

# Structured data — JSON-LD, microdata, OpenGraph in one call
data = extruct.extract(html, base_url=url, syntaxes=["json-ld", "opengraph", "microdata"])
schema_types = [item.get("@type") for item in data.get("json-ld", [])]
```

### Keyword Extraction — Lazy-loaded, Thread-safe

```python
# src/modules/seo/keywords.py
from keybert import KeyBERT
import asyncio

_keybert_instance: KeyBERT | None = None

def _get_keybert() -> KeyBERT:
    """Lazy singleton — ~500 MB sentence-transformers model loaded only when first called."""
    global _keybert_instance
    if _keybert_instance is None:
        _keybert_instance = KeyBERT()
    return _keybert_instance

def _sync_extract(text: str) -> list[tuple[str, float]]:
    return _get_keybert().extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=15,
        use_mmr=True,
        diversity=0.7,
    )

async def extract_keywords(text: str) -> list[tuple[str, float]]:
    """Run CPU-bound KeyBERT in a thread pool — never blocks the event loop."""
    loop = asyncio.get_running_loop()  # get_running_loop() — get_event_loop() is deprecated
    return await loop.run_in_executor(None, _sync_extract, text)
```

### Readability Scoring

```python
import textstat

def score_readability(text: str) -> dict:
    return {
        "flesch_reading_ease":  textstat.flesch_reading_ease(text),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "avg_sentence_length":  textstat.avg_sentence_length(text),
        "word_count":           textstat.lexicon_count(text),
        "reading_time_min":     textstat.reading_time(text, ms_per_char=14.69),
    }
```

---

## 5. Memory Layer

### Three Tiers — All In Sync

```
Tier 1 — Semantic (ChromaDB)           Tier 2 — Structured (SQLAlchemy)   Tier 3 — Cache (SQLiteCache)
────────────────────────────────────   ─────────────────────────────────   ────────────────────────────
"Find similar past research"            "Get client's last 3 audits"        LLM response cache
"Any blog near this keyword"            "Quest outcomes by task type"       100% savings on repeats
Vector similarity search                SQL joins and filters               Keyed by (prompt + model)
```

### ChromaDB — Semantic Memory

```python
# src/core/memory.py
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# FastEmbed: fast CPU-friendly embeddings, no API key, ~90MB model.
# Switch to langchain_anthropic.AnthropicEmbeddings(model="voyage-3") only after
# confirming TokenRouter supports Voyage embedding endpoints.
embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

vector_store = Chroma(
    collection_name="growthagent",
    embedding_function=embeddings,
    persist_directory="./memory/chroma",
)

# Store after every task — use the async version
await vector_store.aadd_documents([
    Document(
        page_content=output_markdown,
        metadata={
            "type":    "seo_audit",    # seo_audit | research | blog | quest
            "domain":  "example.com",
            "date":    "2026-04-25",
            "score":   74,
        }
    )
])

# Semantic search before any task — use async version
similar_docs = await vector_store.asimilarity_search(
    query="B2B SaaS competitor analysis HR tools",
    k=3,
    filter={"type": "research"},
)
```

### SQLAlchemy — Structured Memory

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import String, Float, Integer, Boolean, DateTime, JSON, Text

class Base(DeclarativeBase):
    pass

class AuditRecord(Base):
    __tablename__ = "audits"
    id:            Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    domain:        Mapped[str]      = mapped_column(String(255), index=True)
    score:         Mapped[float]    = mapped_column(Float)
    issues_count:  Mapped[int]      = mapped_column(Integer)
    keyword_gaps:  Mapped[int]      = mapped_column(Integer)
    tokens_used:   Mapped[int]      = mapped_column(Integer)
    created_at:    Mapped[datetime] = mapped_column(DateTime)
    raw_result:    Mapped[dict]     = mapped_column(JSON)

class QuestRecord(Base):
    __tablename__ = "quests"
    id:                Mapped[str]       = mapped_column(String(50), primary_key=True)
    task_type:         Mapped[str]       = mapped_column(String(50), index=True)
    reward_usd:        Mapped[float]     = mapped_column(Float)
    self_review_score: Mapped[float]     = mapped_column(Float)
    human_verified:    Mapped[bool]      = mapped_column(Boolean, default=False)
    outcome:           Mapped[str | None]= mapped_column(String(20), nullable=True)
    payout_usd:        Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used:       Mapped[int]       = mapped_column(Integer)
    created_at:        Mapped[datetime]  = mapped_column(DateTime)

class ReviewRecord(Base):
    __tablename__ = "reviews"
    id:           Mapped[int]    = mapped_column(primary_key=True, autoincrement=True)
    quest_id:     Mapped[str]    = mapped_column(String(50), index=True)
    agent_id:     Mapped[str]    = mapped_column(String(50))
    agent_name:   Mapped[str]    = mapped_column(String(100))
    score:        Mapped[float]  = mapped_column(Float)
    verdict:      Mapped[str]    = mapped_column(String(10))   # "pass" | "fail"
    feedback:     Mapped[str]    = mapped_column(Text)
    created_at:   Mapped[datetime] = mapped_column(DateTime)

class TokenSpend(Base):
    __tablename__ = "token_spend"
    id:           Mapped[int]    = mapped_column(primary_key=True, autoincrement=True)
    task_label:   Mapped[str]    = mapped_column(String(100))
    tokens_used:  Mapped[int]    = mapped_column(Integer)
    model:        Mapped[str]    = mapped_column(String(50))
    created_at:   Mapped[datetime] = mapped_column(DateTime)

engine       = create_async_engine("sqlite+aiosqlite:///./memory/growthagent.db", echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

### SQLiteCache — LLM Response Cache

```python
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

# Must be called once at startup, before any LLM calls.
# Caches by (prompt + model) hash — identical calls hit disk, not API.
set_llm_cache(SQLiteCache(database_path="./memory/llm_cache.db"))
```

---

## 6. Configuration — pydantic-settings (Lazy Singleton)

```python
# src/config/settings.py
from __future__ import annotations
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # TokenRouter / LLM
    tokenrouter_api_key: str = Field(..., description="TokenRouter API key — required")
    llm_model_quality:   str = Field("claude-sonnet-4-6")
    llm_model_fast:      str = Field("claude-haiku-4-5-20251001")

    # AgentHansa
    agenthansa_api_key:  str = Field("", description="Set after registration")
    agenthansa_base_url: str = Field("https://www.agenthansa.com/api")
    agenthansa_alliance: str = Field("heavenly")

    # BotLearn
    botlearn_api_key:    str = Field("", description="Set after BotLearn setup")
    botlearn_base_url:   str = Field("https://www.botlearn.ai")

    # FluxA
    fluxa_agent_id:      str = Field("")
    fluxa_jwt:           str = Field("")
    fluxa_wallet_api:    str = Field("https://walletapi.fluxapay.xyz")

    # LangSmith
    langchain_tracing_v2: bool = Field(True)
    langsmith_api_key:     str = Field("", alias="LANGSMITH_API_KEY")
    langchain_project:     str = Field("growthagent-hackathon")

    # Token budget
    token_budget_total:   int = Field(5_000_000)
    token_warn_threshold: int = Field(500_000)

    # Scheduler
    scheduler_enabled:          bool = Field(True)
    agenthansa_tick_hours:      int  = Field(3)
    botlearn_heartbeat_hours:   int  = Field(12)

    # Paths
    memory_dir:  str = Field("./memory")
    outputs_dir: str = Field("./outputs")
    skills_dir:  str = Field("./skills")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazy singleton — Settings() is never called at import time.
    If .env is missing, this fails loudly on first call, not at module import."""
    return Settings()
```

**Usage everywhere:**
```python
from src.config.settings import get_settings
s = get_settings()
```

---

## 7. AgentHansa Integration — Typed Async Client

```python
# src/modules/agenthansa/client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from loguru import logger
from src.config.settings import get_settings

def _api_retry():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )

class AgentHansaClient:
    """Async HTTP client for AgentHansa API. Use as async context manager."""

    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            base_url=s.agenthansa_base_url,
            headers={"Authorization": f"Bearer {s.agenthansa_api_key}"},
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def __aenter__(self) -> "AgentHansaClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.aclose()

    @_api_retry()
    async def get(self, path: str, **kwargs) -> dict:
        r = await self._client.get(path, **kwargs)
        r.raise_for_status()
        return r.json()

    @_api_retry()
    async def post(self, path: str, json: dict | None = None, **kwargs) -> dict:
        r = await self._client.post(path, json=json, **kwargs)
        r.raise_for_status()
        return r.json()

    @_api_retry()
    async def patch(self, path: str, json: dict | None = None) -> dict:
        r = await self._client.patch(path, json=json)
        r.raise_for_status()
        return r.json()

# Module-level singleton — client is created once and reused for the process lifetime.
# In tests, override with a mock client.
ah_client = AgentHansaClient()
```

---

## 8. BotLearn Integration

### Typed API Client (same pattern as AgentHansa)

```python
# src/modules/botlearn/client.py
class BotLearnClient:
    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            base_url=s.botlearn_base_url,
            headers={"Authorization": f"Bearer {s.botlearn_api_key}"},
            timeout=httpx.Timeout(20.0, connect=10.0),
        )

    async def __aenter__(self) -> "BotLearnClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.aclose()

    @_api_retry()
    async def get(self, path: str, **kwargs) -> dict:
        r = await self._client.get(path, **kwargs)
        r.raise_for_status()
        return r.json()

    @_api_retry()
    async def post(self, path: str, json: dict | None = None) -> dict:
        r = await self._client.post(path, json=json)
        r.raise_for_status()
        return r.json()

bl_client = BotLearnClient()
```

### Run-report Decorator

```python
# src/modules/botlearn/run_report.py
from functools import wraps
import time
from loguru import logger
from src.core.memory import memory   # module-level Memory singleton

async def report_execution(skill_name: str, status: str, duration_ms: int, tokens_used: int) -> None:
    """POST execution stats to BotLearn. Never raises — failure is logged and swallowed."""
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
    """Decorator — wraps any async task function with automatic BotLearn run-report."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            status = "success"
            tokens_before = memory.get_last_task_tokens()
            try:
                return await fn(*args, **kwargs)
            except Exception:
                status = "failure"
                raise
            finally:
                tokens_used = memory.get_last_task_tokens() - tokens_before
                await report_execution(
                    skill_name=skill_name,
                    status=status,
                    duration_ms=int((time.monotonic() - start) * 1000),
                    tokens_used=max(0, tokens_used),
                )
        return wrapper
    return decorator

# Usage
@botlearn_tracked("growthagent-seo-audit")
async def run_seo_audit(url: str) -> AuditResult:
    ...
```

---

## 9. Pydantic v2 Data Models

All inputs and outputs are Pydantic models. `.with_structured_output()` uses Claude's
native tool-use to guarantee schema compliance — no fragile JSON parsing.

```python
# src/models/seo.py
from pydantic import BaseModel, Field
from typing import Literal

class SEOIssue(BaseModel):
    issue:  str
    impact: Literal["high", "medium", "low"]
    fix:    str
    effort: Literal["low", "medium", "high"]

class KeywordGap(BaseModel):
    topic:               str
    competitor_ranking:  str
    difficulty:          Literal["low", "medium", "high"]
    search_intent:       Literal["informational", "commercial", "transactional"]

class ContentOpportunity(BaseModel):
    title:                       str
    target_keyword:              str
    search_intent:               str
    estimated_traffic_potential: Literal["low", "medium", "high"]

class AuditResult(BaseModel):
    score:            int   = Field(..., ge=0, le=100)
    grade:            Literal["A", "B", "C", "D", "F"]
    critical_issues:  list[SEOIssue]
    quick_wins:       list[SEOIssue]
    keyword_gaps:     list[KeywordGap]
    content_map:      list[ContentOpportunity]
    delta:            dict | None = None

# src/models/review.py
class ReviewVerdict(BaseModel):
    score:             int  = Field(..., ge=0, le=100)
    passed:            bool
    spec_compliance:   bool
    depth:             Literal["shallow", "adequate", "deep"]
    factual_issues:    list[str]
    format_correct:    bool
    specific_feedback: str

# src/models/research.py
class LeadRecord(BaseModel):
    name:         str
    title:        str
    company:      str
    linkedin_url: str | None
    signals:      list[str]
    confidence:   int = Field(..., ge=0, le=100)

# src/models/content.py
class ContentOutline(BaseModel):
    title:            str
    meta_description: str = Field(..., max_length=160)
    h2_sections:      list[str]
    target_keyword:   str
    tone:             str
```

---

## 10. Output Templating — Jinja2 + aiofiles

```python
# src/core/nodes.py — save_outputs node
from jinja2 import Environment, FileSystemLoader, select_autoescape
import aiofiles
from pathlib import Path

_jinja = Environment(
    loader=FileSystemLoader("src/templates/"),
    autoescape=select_autoescape([]),   # Markdown output — no HTML escaping
    keep_trailing_newline=True,
)

async def save_outputs(state: GrowthMeshState) -> dict:
    task = state["task_type"]
    tpl  = _jinja.get_template(f"{task}.md.j2")
    rendered = tpl.render(
        input=state["input"],
        result=state.get("structured_output") or {"content": state.get("draft")},
        review=state.get("review_verdict"),
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        tokens=state["tokens_used"],
    )

    path = _output_path(task, state["input"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Async file I/O — never block the event loop with Path.write_text()
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(rendered)

    await memory.store_output(task, rendered, _build_metadata(state))
    await vector_store.aadd_documents([
        Document(
            page_content=rendered,
            metadata={"type": task, "date": datetime.utcnow().isoformat(), **_meta(state)},
        )
    ])

    return {"output_path": path, "final_output": rendered, "memory_saved": True}
```

---

## 11. Data Processing — Pandas

```python
import pandas as pd

df = pd.DataFrame([lead.model_dump() for lead in leads])
df = df.sort_values("confidence", ascending=False)
df.to_csv(f"outputs/research/leads-{slug}-{date}.csv",   index=False)
df.to_json(f"outputs/research/leads-{slug}-{date}.json", orient="records", indent=2)
```

---

## 12. Async Best Practices

| Situation | Pattern |
|---|---|
| CPU-bound (KeyBERT, textstat) | `asyncio.get_running_loop().run_in_executor(None, fn, arg)` |
| Sync library (newspaper3k, WebBaseLoader) | `await asyncio.to_thread(fn, *args)` |
| File I/O | `aiofiles.open(path, "w")` |
| Multiple independent I/O tasks | `await asyncio.gather(*[task1(), task2(), ...])` |
| External API calls | `httpx.AsyncClient` + tenacity `@retry` on every method |
| Vector store writes | `await vector_store.aadd_documents([...])` |
| Vector store reads | `await vector_store.asimilarity_search(...)` |

```python
# Example: parallel competitor crawl
async def crawl_all_competitors(urls: list[str]) -> list[dict]:
    return await asyncio.gather(*[crawl_single(url) for url in urls])
```

---

## 13. Testing Stack

```python
import pytest, respx, httpx
from freezegun import freeze_time

@pytest.mark.asyncio
async def test_seo_crawler_extracts_title():
    with respx.mock:
        respx.get("https://example.com").mock(
            return_value=httpx.Response(200, text="<html><title>Example</title></html>")
        )
        result = await crawl_url("https://example.com")
        assert result["title"] == "Example"

@pytest.mark.asyncio
async def test_review_gate_passes_quality_content():
    verdict = await run_self_review_chain(quest_spec=SAMPLE_SPEC, content=QUALITY_CONTENT)
    assert verdict.passed is True
    assert verdict.score >= 75

@freeze_time("2026-04-25 19:00:00")
def test_scheduler_tick_timing():
    assert scheduler.get_job("agenthansa_tick").next_run_time is not None
```

---

## 14. Full Requirements

```txt
# ── LangChain Ecosystem ──────────────────────────────────────────────
langchain-core>=0.3.0
langchain-anthropic>=0.3.0
langchain-community>=0.3.0
langchain-chroma>=0.1.0
langgraph>=0.2.0
langsmith>=0.2.0

# ── LLM Caching ──────────────────────────────────────────────────────
langchain[sqlite]>=0.3.0      # SQLiteCache backend
diskcache>=5.6.0

# ── Embeddings (CPU-local, no API key required) ───────────────────────
fastembed>=0.3.0              # BAAI/bge-small-en-v1.5 — fast, ~90MB

# ── HTTP & Web Intelligence ───────────────────────────────────────────
httpx>=0.27.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
extruct>=0.16.0               # JSON-LD, microdata, OpenGraph
newspaper3k>=0.2.8            # clean article extraction (sync — use asyncio.to_thread)
duckduckgo-search>=6.0.0      # free web search, no API key

# ── NLP & Content Quality ─────────────────────────────────────────────
keybert>=0.8.0                # keyword extraction (lazy-loaded singleton)
textstat>=0.7.0               # readability scoring

# ── Memory ────────────────────────────────────────────────────────────
chromadb>=0.5.0
sqlalchemy[asyncio]>=2.0.0
aiosqlite>=0.20.0
alembic>=1.13.0

# ── Async File I/O ────────────────────────────────────────────────────
aiofiles>=23.2.0              # async file writes in save_outputs node

# ── Config ────────────────────────────────────────────────────────────
pydantic>=2.7.0
pydantic-settings>=2.3.0

# ── Scheduling ────────────────────────────────────────────────────────
APScheduler>=3.10.0

# ── Data ──────────────────────────────────────────────────────────────
pandas>=2.2.0
jinja2>=3.1.0

# ── CLI & Terminal ────────────────────────────────────────────────────
typer>=0.12.0
rich>=13.0.0
loguru>=0.7.0

# ── Resilience ────────────────────────────────────────────────────────
tenacity>=8.2.0
anyio>=4.0.0

# ── Testing ───────────────────────────────────────────────────────────
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
respx>=0.21.0
freezegun>=1.5.0

# ── Stretch: Webhook endpoint ─────────────────────────────────────────
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
```

---

## 15. Key Design Decisions

**Why lazy Settings singleton?**
`settings = Settings()` at module level fails loudly at import if `.env` is missing — even
in test environments where only a subset of modules is loaded. `@lru_cache` on `get_settings()`
delays initialization to first call and provides a single override point for tests.

**Why FastEmbed instead of Voyage-3?**
`AnthropicEmbeddings(model="voyage-3")` requires TokenRouter to proxy Voyage embedding endpoints.
That is unconfirmed at time of writing. FastEmbed (`BAAI/bge-small-en-v1.5`) is ~90 MB,
runs on CPU with no API key, and produces high-quality dense vectors for retrieval tasks.
Swap to Voyage later by re-implementing only `find_similar()` and `store_output()` in `memory.py`.

**Why `asyncio.to_thread()` for newspaper3k and WebBaseLoader?**
Both libraries use synchronous HTTP internally. Calling them directly in an async node blocks
the event loop for the duration of the HTTP request — typically 2–10 seconds per URL.
`asyncio.to_thread()` moves the blocking call to a thread pool, freeing the event loop.

**Why `asyncio.get_running_loop()` not `get_event_loop()`?**
`asyncio.get_event_loop()` is deprecated in Python 3.10+ and raises `DeprecationWarning` in 3.12.
`get_running_loop()` is the correct API inside an async context — it raises `RuntimeError`
if called outside a running loop, which is the desired failure mode.

**Why `@retry` on all HTTP methods (not just `get`)?**
AgentHansa and BotLearn can return 429 or 503 on any method — POST submissions and PATCH
updates fail just as often as GETs under load. Retry on all methods; idempotency is the
caller's responsibility (quest claim is idempotent by quest ID).

**Why LangGraph + LangSmith?**
The orchestrator needs conditional routing, a review retry loop, and consistent state tracking
across every task type. LangGraph makes all of that explicit in a visual graph — and LangSmith
traces it natively. Judges can open smith.langchain.com during the demo and watch the agent's
reasoning in real time. No other agent at this hackathon will have this level of observability.

**Why `.with_structured_output()` instead of JSON prompt engineering?**
Claude's tool-use mode guarantees the output matches the Pydantic schema — no parsing failures
mid-demo. The model retries internally rather than returning malformed JSON.
