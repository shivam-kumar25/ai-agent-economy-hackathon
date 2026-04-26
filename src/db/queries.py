from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import AuditRecord, QuestRecord, ReviewRecord, TokenSpend


async def get_latest_audit(session: AsyncSession, domain: str) -> AuditRecord | None:
    result = await session.execute(
        select(AuditRecord)
        .where(AuditRecord.domain == domain)
        .order_by(AuditRecord.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_audit(session: AsyncSession, record: AuditRecord) -> None:
    session.add(record)
    await session.commit()


async def already_reviewed(session: AsyncSession, quest_id: str, agent_id: str) -> bool:
    result = await session.execute(
        select(func.count(ReviewRecord.id))
        .where(ReviewRecord.quest_id == quest_id)
        .where(ReviewRecord.agent_id == agent_id)
    )
    return result.scalar_one() > 0


async def save_review(session: AsyncSession, record: ReviewRecord) -> None:
    session.add(record)
    await session.commit()


async def save_quest(session: AsyncSession, record: QuestRecord) -> None:
    session.add(record)
    await session.commit()


async def update_quest_outcome(
    session: AsyncSession, quest_id: str, outcome: str, payout: float
) -> None:
    result = await session.execute(
        select(QuestRecord).where(QuestRecord.id == quest_id)
    )
    record = result.scalar_one_or_none()
    if record:
        record.outcome = outcome
        record.payout_usd = payout
        await session.commit()


async def get_total_tokens_used(session: AsyncSession) -> int:
    result = await session.execute(select(func.sum(TokenSpend.tokens_used)))
    return result.scalar_one() or 0


async def save_token_spend(
    session: AsyncSession, label: str, tokens: int, model: str
) -> None:
    session.add(TokenSpend(
        task_label=label,
        tokens_used=tokens,
        model=model,
        created_at=datetime.utcnow(),
    ))
    await session.commit()
