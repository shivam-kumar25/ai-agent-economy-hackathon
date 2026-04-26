from __future__ import annotations

from datetime import datetime

from src.core.memory import memory
from src.modules.agenthansa.agent import do_checkin
from src.modules.agenthansa.client import ah_client
from src.modules.agenthansa.quests import execute_quest, triage_quests
from src.modules.agenthansa.reviewer import run_alliance_reviewer_pass
from src.utils.llm import llm, llm_fast
from src.utils.logger import logger


async def run_agenthansa_tick() -> None:
    """Full 3-hour AgentHansa tick: checkin → red packets → quest → daily chain → review → earnings."""
    logger.info("AgentHansa tick — start")

    # 1 — Check-in (streak maintenance)
    try:
        checkin = await do_checkin()
        logger.info(f"Check-in: streak day {checkin.get('streak_day')} — ${checkin.get('payout_usd', 0):.2f}")
    except Exception as e:
        logger.warning(f"Check-in failed: {e}")

    # 2 — Red packets
    try:
        packets = await ah_client.get("/red-packets")
        for p in packets.get("active", []):
            try:
                challenge = await ah_client.get(f"/red-packets/{p['id']}/challenge")
                answer = (await llm_fast.ainvoke(
                    f"Answer in one word or number only. Question: {challenge.get('question', '')}"
                )).content.strip()
                await ah_client.post(f"/red-packets/{p['id']}/join", {"answer": answer})
                logger.success(f"Joined red packet {p['id']}")
            except Exception as e:
                logger.warning(f"Red packet {p.get('id')} failed: {e}")
    except Exception as e:
        logger.warning(f"Red packets fetch failed: {e}")

    # 3 — Execute best quest
    try:
        top = await triage_quests()
        if top:
            best = top[0]
            logger.info(f"Executing quest: '{best.quest.get('title')}' — ${best.quest.get('budget', 0):.2f}")
            await execute_quest(best.quest)
    except Exception as e:
        logger.warning(f"Quest execute failed: {e}")

    # 4 — Daily quest chain
    try:
        daily = await ah_client.get("/agents/daily-quests")
        await complete_daily_quest_chain(daily)
    except Exception as e:
        logger.warning(f"Daily quest chain failed: {e}")

    # 5 — Alliance reviewer pass
    try:
        await run_alliance_reviewer_pass()
    except Exception as e:
        logger.warning(f"Reviewer pass failed: {e}")

    # 6 — Earnings snapshot
    try:
        earnings = await ah_client.get("/agents/earnings")
        logger.info(f"Balance: ${earnings.get('balance_usd', 0):.2f} | XP: {earnings.get('xp', 0)}")
        memory.update_state(xp=earnings.get("xp", 0))
    except Exception as e:
        logger.warning(f"Earnings fetch failed: {e}")

    logger.success("AgentHansa tick — done")


async def complete_daily_quest_chain(daily: dict) -> None:
    """Complete the 5-task daily quest chain for +50 XP bonus."""
    done = set(daily.get("completed", []))

    if "content" not in done:
        try:
            body = (await llm.ainvoke(
                "Write a 120-word market insight post about B2B growth trends for an AI agent marketplace. "
                "Be specific. No fluff. No intro sentence."
            )).content
            await ah_client.post("/forum", {
                "title":    f"B2B Growth Intelligence — {datetime.utcnow().strftime('%b %d')}",
                "body":     body,
                "category": "review",
            })
        except Exception as e:
            logger.warning(f"Daily content post failed: {e}")

    if "curate" not in done:
        try:
            posts = (await ah_client.get("/forum")).get("posts", [])[:10]
            scored = []
            for post in posts:
                try:
                    raw = (await llm_fast.ainvoke(
                        f"Rate this post quality 1-5 (number only):\n{post.get('body', '')[:200]}"
                    )).content.strip()
                    scored.append((post, int(raw)))
                except (ValueError, Exception):
                    scored.append((post, 3))

            scored.sort(key=lambda x: x[1], reverse=True)
            for post, _ in scored[:5]:
                await ah_client.post(f"/forum/{post['id']}/vote", {"direction": "up"})
            for post, _ in scored[-3:]:
                await ah_client.post(f"/forum/{post['id']}/vote", {"direction": "down"})
        except Exception as e:
            logger.warning(f"Daily curate step failed: {e}")

    if "distribute" not in done:
        try:
            offers = (await ah_client.get("/offers")).get("offers", [])
            if offers:
                best = max(offers, key=lambda o: o.get("conversion_rate", 0))
                await ah_client.post(f"/offers/{best['id']}/ref", {
                    "disclosure": best.get("disclosure", "Sponsored referral link."),
                })
        except Exception as e:
            logger.warning(f"Daily distribute step failed: {e}")

    if "digest" not in done:
        try:
            await ah_client.get("/forum/digest")
        except Exception as e:
            logger.warning(f"Daily digest step failed: {e}")

    logger.success("Daily quest chain complete")
