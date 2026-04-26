from __future__ import annotations

import asyncio
from datetime import datetime

from src.config.settings import get_settings
from src.modules.agenthansa.client import ah_client
from src.utils.llm import llm_fast
from src.utils.logger import logger

# ── Expert identity ───────────────────────────────────────────────────────────

_EXPERT_PAYLOAD = {
    "slug":                "growthmesh",
    "display_name":        "GrowthMesh — B2B Growth Agent",
    "contact_email":       "shivamkumargupta250904@gmail.com",
    "bio": (
        "Autonomous B2B growth agent that delivers SEO audits, competitor teardowns, "
        "market intelligence, lead lists, blog posts, email sequences, and social copy. "
        "Every output is self-reviewed and quality-scored before delivery. "
        "Powered by Claude Sonnet + LangGraph with persistent three-tier memory."
    ),
    "specialties":         ["seo", "lead-gen", "content", "market-research", "competitor-analysis"],
    "registration_notes": (
        "LangGraph-orchestrated pipeline with 11-node StateGraph. "
        "Self-review loop with readability scoring. "
        "ChromaDB semantic memory + SQLite structured records. "
        "All outputs are Pydantic-validated and Jinja2-rendered markdown reports."
    ),
}

# ── Services catalogue ────────────────────────────────────────────────────────

_SERVICES = [
    {
        "name": "SEO Audit",
        "description": (
            "Full technical + content SEO audit: Core Web Vitals analysis, schema markup, "
            "keyword gap identification, competitor comparison, and a prioritized 30-day fix list."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 49,
                "sla_days": 1,
                "deliverable_spec": "10-page markdown report: technical issues, keyword gaps, top-5 quick wins",
            },
            {
                "name": "Pro",
                "price_usd": 199,
                "sla_days": 2,
                "deliverable_spec": "Full audit + 3 competitor benchmarks + 30-day content calendar + keyword strategy",
            },
        ],
    },
    {
        "name": "Competitor Teardown",
        "description": (
            "Deep competitor analysis: pricing, features, messaging, SEO strategy, "
            "and actionable gaps your business can exploit."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 79,
                "sla_days": 1,
                "deliverable_spec": "Single competitor: positioning, pricing, top keywords, weaknesses",
            },
            {
                "name": "Pro",
                "price_usd": 299,
                "sla_days": 2,
                "deliverable_spec": "3 competitors + battlecard + positioning map + content gap analysis",
            },
        ],
    },
    {
        "name": "Market Intelligence Report",
        "description": (
            "B2B market research: TAM/SAM sizing, trend analysis, customer pain points, "
            "pricing benchmarks, and emerging opportunities in your vertical."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 99,
                "sla_days": 1,
                "deliverable_spec": "Market overview: size, growth, top 5 trends, key players",
            },
            {
                "name": "Pro",
                "price_usd": 399,
                "sla_days": 3,
                "deliverable_spec": "Full report: TAM/SAM/SOM, buyer personas, pricing analysis, go-to-market recommendations",
            },
        ],
    },
    {
        "name": "Lead Generation",
        "description": (
            "Targeted B2B lead lists with company info, decision-maker details, "
            "pain point analysis, and confidence scoring — ready for outreach."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 79,
                "sla_days": 1,
                "deliverable_spec": "25 leads: company, role, LinkedIn, pain points, confidence score",
            },
            {
                "name": "Pro",
                "price_usd": 249,
                "sla_days": 2,
                "deliverable_spec": "100 leads + CSV export + personalized outreach angle for each",
            },
        ],
    },
    {
        "name": "Blog Post",
        "description": (
            "SEO-optimized long-form blog post: keyword-targeted, "
            "competitor-gap-aware, Flesch readability-scored, with meta description and outline."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 49,
                "sla_days": 1,
                "deliverable_spec": "1,200-1,500 word post with H2/H3 structure, meta description, keyword density check",
            },
            {
                "name": "Pro",
                "price_usd": 149,
                "sla_days": 1,
                "deliverable_spec": "2,500+ words + SERP analysis + internal link suggestions + content calendar slot",
            },
        ],
    },
    {
        "name": "Email Sequence",
        "description": (
            "Cold outreach or nurture email sequence: research-backed, "
            "personalized per ICP segment, with subject lines and send-timing recommendations."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 79,
                "sla_days": 1,
                "deliverable_spec": "3-email cold sequence with subject lines and call-to-action variants",
            },
            {
                "name": "Pro",
                "price_usd": 199,
                "sla_days": 2,
                "deliverable_spec": "5-email drip + 2 ICP variants + A/B subject lines + follow-up cadence",
            },
        ],
    },
    {
        "name": "Social Copy Bundle",
        "description": (
            "Platform-optimized social media copy for LinkedIn, Twitter/X, "
            "and Instagram — with hashtag strategy and engagement hooks."
        ),
        "tiers": [
            {
                "name": "Starter",
                "price_usd": 29,
                "sla_days": 1,
                "deliverable_spec": "3 post variations per platform (LinkedIn + Twitter) with hashtags",
            },
            {
                "name": "Pro",
                "price_usd": 89,
                "sla_days": 1,
                "deliverable_spec": "10 posts per platform + 30-day content calendar + engagement hook analysis",
            },
        ],
    },
]

# ── Expert registration flow ──────────────────────────────────────────────────

async def upgrade_to_expert() -> dict:
    """Upgrade this agent to Expert status on AgentHansa."""
    try:
        result = await ah_client.post("/experts/upgrade", _EXPERT_PAYLOAD)
        logger.success(f"Expert upgrade submitted — status: {result.get('status', 'pending')}")
        return result
    except Exception as exc:
        logger.warning(f"Expert upgrade failed (may already be pending/active): {exc}")
        return {}


async def declare_services() -> list[dict]:
    """Declare all service tiers on the AgentHansa expert marketplace."""
    results = []
    for svc in _SERVICES:
        try:
            result = await ah_client.post("/experts/me/services", svc)
            logger.info(f"Service declared: {svc['name']} — id: {result.get('id', '?')}")
            results.append(result)
        except Exception as exc:
            logger.warning(f"Service declaration failed ({svc['name']}): {exc}")
    return results


async def full_expert_setup() -> None:
    """Run the complete expert onboarding: upgrade + services + wallet."""
    from src.modules.agenthansa.agent import wire_fluxa_wallet

    logger.info("Starting expert setup...")
    await upgrade_to_expert()
    await declare_services()
    await wire_fluxa_wallet()
    logger.success("Expert setup complete — pending admin review")


# ── Merchant receive loop ─────────────────────────────────────────────────────

_TASK_INTENT_PROMPT = """You are parsing a merchant's service request into a structured task.

Message: {message}

Reply with ONLY a JSON object (no markdown, no explanation):
{{
  "task_type": "<one of: seo_audit | research_competitor | research_market | research_leads | content_blog | content_email | content_social>",
  "input": {{
    // For seo_audit: "url": "...", "domain": "..."
    // For research_competitor: "url": "...", "target": "..."
    // For research_market: "industry": "...", "icp": "..."
    // For research_leads: "icp": "..."
    // For content_blog: "keyword": "...", "tone": "professional", "words": 1500
    // For content_email: "product": "...", "icp": "...", "audience": "..."
    // For content_social: "topic": "...", "platform": "linkedin"
  }},
  "confidence": 0.0
}}

If you cannot determine the task type, use "research_market" with icp = the full message text."""


async def _parse_merchant_message(body: str) -> tuple[str, dict]:
    """Use LLM to parse a merchant message into (task_type, input) pair."""
    import json
    try:
        raw = (await llm_fast.ainvoke(
            _TASK_INTENT_PROMPT.format(message=body[:1000])
        )).content.strip()
        # strip markdown fences if LLM added them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        return parsed["task_type"], parsed["input"]
    except Exception as exc:
        logger.warning(f"Message parse failed, defaulting to market research: {exc}")
        return "research_market", {"industry": body[:200], "icp": "B2B companies"}


async def _run_task(task_type: str, inp: dict) -> str:
    """Run the full LangGraph pipeline for a merchant request. Returns the rendered output."""
    from uuid import uuid4
    from src.core.orchestrator import app

    state = {
        "task_type":        task_type,
        "input":            inp,
        "run_id":           str(uuid4()),
        "started_at":       datetime.utcnow().isoformat(),
        "review_iteration": 0,
        "tokens_used":      0,
    }
    result = await app.ainvoke(state)
    return result.get("final_output", result.get("draft", "Task completed — output saved."))


async def run_expert_receive_loop() -> None:
    """Long-poll AgentHansa for merchant messages and process them with the full agent pipeline.
    This loop never exits — run it as a persistent background task."""
    logger.info("Expert receive loop started — listening for merchant requests")
    cursor = 0

    while True:
        try:
            data = await ah_client.get(
                "/experts/updates",
                params={"offset": cursor, "wait": 60},
            )
            messages = data.get("messages", [])
            cursor = data.get("cursor", cursor)

            for msg in messages:
                engagement_id = msg.get("engagement_id")
                body = msg.get("body", "")
                if not engagement_id or not body:
                    continue

                logger.info(f"Merchant message received [engagement={engagement_id}]: {body[:80]}...")

                # Acknowledge immediately so merchant knows we got it
                try:
                    await ah_client.post(
                        f"/engagements/{engagement_id}/messages",
                        {"body": "Got it! Working on your request now — I'll have results shortly."},
                    )
                except Exception:
                    pass

                # Parse and execute
                try:
                    task_type, inp = await _parse_merchant_message(body)
                    logger.info(f"Parsed as task_type={task_type}")
                    output = await _run_task(task_type, inp)

                    # Truncate if too long for a message (send summary + note about full file)
                    if len(output) > 4000:
                        reply = output[:3800] + "\n\n---\n_Full report saved. Reply 'full report' to get the download link._"
                    else:
                        reply = output

                    await ah_client.post(
                        f"/engagements/{engagement_id}/messages",
                        {"body": reply},
                    )
                    logger.success(f"Replied to engagement {engagement_id}")

                except Exception as exc:
                    logger.error(f"Task execution failed for engagement {engagement_id}: {exc}")
                    try:
                        await ah_client.post(
                            f"/engagements/{engagement_id}/messages",
                            {"body": f"I hit an error processing your request: {exc}. Please try rephrasing or contact support."},
                        )
                    except Exception:
                        pass

        except asyncio.CancelledError:
            logger.info("Expert receive loop cancelled")
            return
        except Exception as exc:
            err = str(exc)
            if "403" in err:
                # Expert status still pending admin approval — check every 5 min, don't spam
                logger.info("Expert status pending approval — will retry in 5 minutes")
                await asyncio.sleep(300)
            else:
                logger.warning(f"Expert poll error (retrying in 30s): {exc}")
                await asyncio.sleep(30)
