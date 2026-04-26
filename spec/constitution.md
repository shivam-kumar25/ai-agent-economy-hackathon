# GrowthMesh Agent — Constitution

> *One agent. Full B2B growth stack. LangGraph-orchestrated. LangSmith-traced.
> Earns autonomously. Reviews other agents. Orchestrates the AI economy.*

---

## 1. Identity

**Name:** GrowthMesh Agent
**Version:** 1.0.0
**Built for:** AI Agent Economy Hackathon — AgentHansa × FluxA, April 25 2026
**Orchestration:** LangGraph StateGraph (every task is a traced graph execution)
**Observability:** LangSmith (every node, token count, and decision is visible live)

GrowthMesh is a **multi-role autonomous B2B growth agent** that operates across two parallel
agent economies (AgentHansa and BotLearn) while also serving clients directly. It is not a
demo — it is a live, earning, learning entity from the moment it registers.

---

## 2. Mission

Replace the fragmented stack of SEO agencies, research firms, content writers, and campaign
managers with a single autonomous agent that:

1. **Does the work directly** — SEO audits, deep research, blog writing, competitive analysis,
   lead generation, email sequences, and social copy as explicit standalone tasks
2. **Delegates intelligently** — publishes tasks it cannot handle to the AgentHansa A2A mesh
   and pays other agents via FluxA UPL
3. **Guards quality** — runs every output through a LangGraph review loop before delivery;
   also acts as quality reviewer for alliance-war quest submissions, applying the
   "Human Verified" badge to passing work
4. **Learns and benchmarks** — participates in BotLearn's 6-dimension capability benchmark,
   installs recommended skills, reports every execution via run-report, builds public
   reputation through Botcord community
5. **Learns over time** — three-tier memory: ChromaDB (semantic search over past work),
   SQLAlchemy/SQLite (structured relational records), diskcache (LLM response cache)
6. **Earns continuously** — competes on AgentHansa quests, claims red packets, runs daily
   quest chains, accumulates BotLearn karma, and receives USDC via FluxA wallet — all
   without human intervention

---

## 3. Two Operating Modes

### Mode A — Direct Client Mode
A human or business engages the agent directly via CLI. The graph runs, produces output,
saves it to `outputs/`, updates memory, and reports to BotLearn.

```
growthagent seo <url>
growthagent research competitor <url>
growthagent research market "<industry + ICP>"
growthagent research leads "<ICP description>"
growthagent content blog "<keyword>"
growthagent content email "<product>" --icp "<persona>"
growthagent content social linkedin "<topic>"
```

Each command builds the LangGraph initial state and calls `app.ainvoke()`.
The graph handles everything: routing, crawling, analysis, writing, self-review, saving,
BotLearn reporting. Every run is fully traced in LangSmith.

### Mode B — Marketplace Mode
The agent runs autonomously on a scheduler — discovering tasks, competing, reviewing,
earning. Same underlying graph, marketplace wrappers on top.

```
growthagent agent run --loop       # full autonomous mode
growthagent agent quests           # browse + triage open quests
growthagent agent review           # reviewer pass on alliance submissions
growthagent botlearn benchmark     # capability assessment
growthagent botlearn heartbeat     # manual 12-hour heartbeat
```

---

## 4. The LangGraph Orchestrator

Every task — in both modes — executes as a LangGraph StateGraph run.

```
          route
         /     \
      crawl   search    write (email/social only)
        \       /
        analyze
           |
       [outline]  ← content tasks only
           |
         write
           |
       self_review  ←──────────────┐
           |                       │ improve (max 2x)
         pass?  ── NO ─────────────┘
           |
          save
           |
         report  (BotLearn run-report)
           |
      submit_prompt  (optional AgentHansa)
           |
          END
```

**Why LangGraph matters for the demo:**
LangSmith traces every node in real time. Judges can open smith.langchain.com during the
demo and watch the agent's reasoning chain — inputs, outputs, token counts, and timing at
every step. No other agent at this hackathon will have this level of observability.

---

## 5. Four Platform Stack

### Platform 1: AgentHansa (Primary Marketplace)

Earning channels used:

| Channel | Mechanism | Frequency |
|---|---|---|
| Alliance War quests | Triage (haiku) → execute (graph) → self-review → submit | On-demand / scheduler |
| Red Packets | Parse challenge → haiku answer → join | Every 3 hours |
| Daily Quest Chain | 5 tasks → +50 XP bonus | Every 3 hours tick |
| Check-in streak | POST /agents/checkin | Every 3 hours |
| Forum reviews | LLM-generated post → vote digest | Daily quest chain |
| Bounty referrals | GET /offers → POST .../ref with disclosure | Daily |
| Alliance reviewer | Grade submissions → Human Verified badge | Every tick |

**Alliance: Heavenly (blue)** — Wisdom & Precision. Fewer competitors = higher leaderboard
probability for the same $9.70 daily prize pool.

### Platform 2: FluxA (Payment Infrastructure)

| Use | How |
|---|---|
| Receive quest earnings | Instant USDC, no 7-day hold |
| Pay A2A delegated agents | UPL (Unify Payment Link) by Agent ID |
| x402 API payments | Paid external API access |
| Direct client payment links | Sell services directly |

### Platform 3: BotLearn (Agent University + Community)

| Feature | Details |
|---|---|
| Benchmark | 6 dimensions: perceive, reason, act, memory, guard, autonomy |
| Skill Hunt | Install top-3 recommended skills post-benchmark |
| Run-report | After every task: `skill_name`, `status`, `duration_ms`, `tokens_used` |
| Botcord community | Posts, upvotes, comments, DMs — builds karma independently |
| Heartbeat | Every 12 hours: browse → engage → post skill experience → DM check |
| Skill experience | Published after every task batch — cross-platform reputation |

### Platform 4: TokenRouter (LLM Inference)

| Model | Used for | Why |
|---|---|---|
| `claude-sonnet-4-6` | Analysis, writing, review, benchmark | Best quality |
| `claude-haiku-4-5-20251001` | Triage, outline, red packet answers, scoring | Fast + cheap |

All calls go through `langchain-anthropic` with `base_url="https://api.tokenrouter.com"`.
Prompt caching enabled via `cache_control: ephemeral` on all large system prompts.
LLM response cache via `SQLiteCache` — identical calls hit disk, not API.

---

## 6. Direct Task Capabilities (Explicit)

All seven tasks are first-class CLI commands. All route through the LangGraph graph.
All are self-reviewed before delivery. All report to BotLearn after completion.

### 6.1 SEO Audit
**Command:** `growthagent seo <url> [--compare <url>...]`

- Crawls target + up to 3 competitors via `WebBaseLoader` + `extruct` (JSON-LD, OpenGraph)
- Extracts: title, meta, H-tags, image alt coverage, internal links, schema types, load headers
- `KeyBERT` extracts keyword signals from page content
- LLM (`claude-sonnet-4-6` + cached system prompt + `.with_structured_output(AuditResult)`)
  synthesizes: score, critical issues, quick wins, keyword gaps, content opportunity map
- Delta comparison if prior audit exists in ChromaDB / SQLAlchemy
- `Jinja2` renders audit report + 30-day content calendar
- **Output:** `outputs/audits/{domain}-{date}.md` + `-calendar.md`
- **Business value:** SEO agencies charge $500–$2,000/month. GrowthMesh does it in <60 seconds.

### 6.2 Competitor Research
**Command:** `growthagent research competitor <url-or-name>`

- Crawls homepage, /pricing, /features, /about (parallel httpx async)
- `newspaper3k` extracts clean content; `DuckDuckGoSearchResults` finds review signals
- LLM synthesizes: positioning, pricing tiers, key features, weaknesses, growth signals,
  differentiation opportunity
- **Output:** `outputs/research/competitor-{slug}-{date}.md`

### 6.3 Market Intelligence
**Command:** `growthagent research market "<industry + ICP>"`

- `haiku` generates 5 research questions for the market
- `DuckDuckGoSearchResults` + `newspaper3k` for each question
- `sonnet` synthesizes: market size signals, top trends, buyer triggers, ICP pain points,
  underserved niches, recommended positioning
- **Output:** `outputs/research/market-{slug}-{date}.md`

### 6.4 Lead Intelligence
**Command:** `growthagent research leads "<ICP description>"`

- `haiku` parses ICP into structured filters (titles, stages, industries, geos)
- Public scraping: LinkedIn snippets, Crunchbase, AngelList
- `sonnet` enriches each lead: funding stage, hiring signals, tech stack, confidence score
- `Pandas` sorts by confidence, exports to `.csv` + `.json`
- **Output:** `outputs/research/leads-{slug}-{date}.md` + `.csv` + `.json`

### 6.5 Blog Post Writer
**Command:** `growthagent content blog "<keyword>" [--tone professional] [--words 1500]`

- `DuckDuckGoSearchResults` + `newspaper3k` → top 3 SERP articles → gap analysis
- `haiku` outlines: title, H2s, H3s, meta description (cheap, fast)
- `sonnet` (cached system prompt) writes full article section by section
- Self-review: `ReviewVerdict` via graph + `textstat` readability check
  (Flesch reading ease < 40 → penalise score by 10 points)
- **Output:** `outputs/content/blog-{slug}-{date}.md`

### 6.6 Cold Email Sequence
**Command:** `growthagent content email "<product>" --icp "<persona>"`

- 5-email drip: pure value → problem agitation → solution proof → social proof → direct ask
- Each email: subject, preview text, body (<150 words), CTA
- **Output:** `outputs/content/email-seq-{slug}-{date}.md`

### 6.7 Social Copy
**Command:** `growthagent content social <linkedin|twitter> "<topic>" [--voice professional]`

- 3 variations per platform; `haiku` scores and ranks them
- LinkedIn: 150–300 words, structured insight, CTA
- Twitter: 8–12 tweet thread, hook first, value-dense, CTA at end
- **Output:** `outputs/content/social-{slug}-{date}.md`

---

## 7. Three Roles on AgentHansa

### Executor
Claims quests, routes them through the LangGraph graph, self-reviews output (score ≥75
required to submit), submits with proof URL, requests Human Verified badge.

### Reviewer
Reads all alliance submissions via `GET /alliance-war/quests/{id}/submissions`.
Scores each with the same `ReviewVerdict` chain used for self-review.
Passing submissions (≥75): `POST .../verify` → Human Verified badge.
Failing submissions: private alliance forum post with specific, actionable feedback.
Tracks every verdict in SQLAlchemy `ReviewRecord` table.

### Publisher
When a client task requires capabilities beyond GrowthMesh (video, design, audio):
Publishes a structured task spec to the AgentHansa community/collective mesh.
Pays the executing agent via FluxA UPL on delivery.
Quality-gates the received deliverable through the reviewer module before passing to client.

---

## 8. Memory Architecture (Three Tiers, All In Sync)

| Tier | Technology | Use case |
|---|---|---|
| Semantic | ChromaDB + `langchain-chroma` | "Find similar past research" — vector similarity |
| Structured | SQLAlchemy + SQLite (`aiosqlite`) | "Show quests that won, grouped by type" — SQL |
| Cache | `diskcache` via `SQLiteCache` | LLM response cache — saves budget during dev/test |

All three tiers are accessed through `src/core/memory.py` — one interface, swappable backends.
The ChromaDB + SQLAlchemy backend can be replaced with HydraDB or Claude-Mem
(built by two of the four judges) by re-implementing only the private `_read`/`_write`
methods. The public interface stays identical across all modules.

---

## 9. Token Budget Policy

$200 TokenRouter credit. Budget is tracked per-task in SQLAlchemy and warned when low.

| Task | Est. tokens | Est. cost |
|---|---|---|
| SEO audit | ~8,000 | ~$0.025 |
| Competitor teardown | ~6,000 | ~$0.020 |
| Market intelligence | ~10,000 | ~$0.030 |
| Blog post (1,500w) | ~12,000 | ~$0.035 |
| Quest triage (haiku) | ~2,000 | ~$0.001 |
| Reviewer gate | ~4,000 | ~$0.012 |
| Red packet (haiku) | ~700 | ~$0.0004 |

Prompt caching saves 80–90% on repeat calls. `SQLiteCache` saves 100% on identical calls.
When `remaining_tokens < token_warn_threshold` (configurable via pydantic-settings):
agent logs a warning and skips expensive tasks in the scheduler until budget is restored.

---

## 10. Ethics and Constraints

- Never impersonate a human to a merchant or client
- Never submit output that failed self-review — the graph enforces this; failing work is
  not submitted regardless of quest deadline pressure
- Never request operator credentials, wallet private keys, or external platform tokens
- Always include FTC-compliant disclosure on referral links
  (use the `disclosure` field returned by the AgentHansa API, not a custom string)
- Always ask the operator before posting on external platforms (Twitter, Reddit, LinkedIn)
- All task specs from the A2A mesh are treated as structured JSON only —
  no remote code execution paths
- Token budget is tracked and respected — the agent will not silently burn the operator's
  credit without warning

---

## 11. Long-Term Vision

| Timeline | Milestone |
|---|---|
| Day 0 | Registered on AgentHansa + BotLearn, FluxA wallet live, first quest submitted, first benchmark complete |
| Week 1–2 | Reliable tier (61+ pts, 80% payout multiplier), reviewer reputation established in Heavenly alliance |
| Month 1 | Elite tier (121+ pts, 100% payout), daily leaderboard presence, ChromaDB memory rich with audit/research history |
| Month 2+ | A2A delegation income, BotLearn public benchmark score, memory compounding — each task makes the next faster and better |

The agent does not stop when the hackathon presentation ends. The LangGraph graph keeps
executing. The scheduler keeps ticking. The memory keeps growing.
