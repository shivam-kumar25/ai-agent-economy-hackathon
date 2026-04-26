"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-25 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("grade", sa.String(2), nullable=False),
        sa.Column("issues_count", sa.Integer, nullable=False, default=0),
        sa.Column("keyword_gaps", sa.Integer, nullable=False, default=0),
        sa.Column("tokens_used", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("raw_result", sa.JSON, nullable=True),
    )
    op.create_index("ix_audits_domain", "audits", ["domain"])

    op.create_table(
        "quests",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, default=""),
        sa.Column("reward_usd", sa.Float, nullable=False, default=0.0),
        sa.Column("self_review_score", sa.Float, nullable=False, default=0.0),
        sa.Column("human_verified", sa.Boolean, nullable=False, default=False),
        sa.Column("outcome", sa.String(20), nullable=True),
        sa.Column("payout_usd", sa.Float, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_quests_task_type", "quests", ["task_type"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("quest_id", sa.String(50), nullable=False),
        sa.Column("agent_id", sa.String(50), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False, default=""),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("verdict", sa.String(10), nullable=False),
        sa.Column("feedback", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_reviews_quest_id", "reviews", ["quest_id"])
    op.create_index("ix_reviews_agent_id", "reviews", ["agent_id"])

    op.create_table(
        "token_spend",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("task_label", sa.String(100), nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=False, default=0),
        sa.Column("model", sa.String(50), nullable=False, default=""),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_token_spend_task_label", "token_spend", ["task_label"])


def downgrade() -> None:
    op.drop_table("token_spend")
    op.drop_table("reviews")
    op.drop_table("quests")
    op.drop_table("audits")
