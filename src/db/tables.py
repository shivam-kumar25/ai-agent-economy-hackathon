from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class AuditRecord(Base):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    score: Mapped[float] = mapped_column(Float)
    grade: Mapped[str] = mapped_column(String(2))
    issues_count: Mapped[int] = mapped_column(Integer)
    keyword_gaps: Mapped[int] = mapped_column(Integer)
    tokens_used: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    raw_result: Mapped[dict] = mapped_column(JSON)


class QuestRecord(Base):
    __tablename__ = "quests"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    reward_usd: Mapped[float] = mapped_column(Float)
    self_review_score: Mapped[float] = mapped_column(Float)
    human_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payout_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ReviewRecord(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quest_id: Mapped[str] = mapped_column(String(50), index=True)
    agent_id: Mapped[str] = mapped_column(String(50), index=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String(10))
    feedback: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TokenSpend(Base):
    __tablename__ = "token_spend"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_label: Mapped[str] = mapped_column(String(100), index=True)
    tokens_used: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime)
