from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.documents import Document
from langchain_chroma import Chroma

try:
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2 as _ChromaEF
    _CHROMA_EF = _ChromaEF()
except Exception:
    _CHROMA_EF = None  # chromadb will use its own default

from src.config.settings import get_settings
from src.db.engine import AsyncSessionLocal
from src.db import queries as q
from src.db.tables import AuditRecord, ReviewRecord, QuestRecord
from src.models.seo import AuditResult
from src.models.agenthansa import AgentState
from src.models.botlearn import BotLearnState

if TYPE_CHECKING:
    pass


def _state_path() -> Path:
    return Path(get_settings().memory_dir) / "state.json"


def _load_state_file() -> dict:
    p = _state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state_file(data: dict) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class Memory:
    """Single interface for all three memory tiers.
    No module outside memory.py should import sqlalchemy, chromadb, or state.json directly."""

    def __init__(self) -> None:
        s = get_settings()
        self._chroma_dir = f"{s.memory_dir}/chroma"
        self._vector_store: Chroma | None = None

    def _vs(self) -> Chroma:
        if self._vector_store is None:
            kwargs: dict = {
                "collection_name": "growthagent",
                "persist_directory": self._chroma_dir,
            }
            if _CHROMA_EF is not None:
                kwargs["embedding_function"] = _CHROMA_EF
            self._vector_store = Chroma(**kwargs)
        return self._vector_store

    # ── Semantic (ChromaDB) ───────────────────────────────────────────

    async def find_similar(self, query: str, task_type: str, k: int = 3) -> list[Document]:
        try:
            return await self._vs().asimilarity_search(
                query, k=k, filter={"type": task_type}
            )
        except Exception:
            return []

    async def store_output(self, task_type: str, content: str, metadata: dict) -> None:
        try:
            await self._vs().aadd_documents([
                Document(
                    page_content=content,
                    metadata={"type": task_type, "date": datetime.utcnow().isoformat(), **metadata},
                )
            ])
        except Exception:
            pass

    # ── Structured (SQLAlchemy async) ─────────────────────────────────

    async def save_audit(self, domain: str, result: AuditResult, tokens: int) -> None:
        async with AsyncSessionLocal() as session:
            await q.save_audit(session, AuditRecord(
                domain=domain,
                score=result.score,
                grade=result.grade,
                issues_count=len(result.critical_issues),
                keyword_gaps=len(result.keyword_gaps),
                tokens_used=tokens,
                created_at=datetime.utcnow(),
                raw_result=result.model_dump(),
            ))

    async def get_latest_audit(self, domain: str) -> AuditResult | None:
        if not domain:
            return None
        async with AsyncSessionLocal() as session:
            record = await q.get_latest_audit(session, domain)
            if record and record.raw_result:
                try:
                    return AuditResult.model_validate(record.raw_result)
                except Exception:
                    pass
        return None

    async def save_quest(self, record: QuestRecord) -> None:
        async with AsyncSessionLocal() as session:
            await q.save_quest(session, record)

    async def update_quest_outcome(self, quest_id: str, outcome: str, payout: float) -> None:
        async with AsyncSessionLocal() as session:
            await q.update_quest_outcome(session, quest_id, outcome, payout)

    async def save_review(self, record: ReviewRecord) -> None:
        async with AsyncSessionLocal() as session:
            await q.save_review(session, record)

    async def already_reviewed(self, quest_id: str, agent_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            return await q.already_reviewed(session, quest_id, agent_id)

    # ── Runtime state (state.json — sync key-value store) ─────────────

    def get_state(self) -> AgentState:
        data = _load_state_file()
        return AgentState.model_validate(data.get("agent", {}))

    def update_state(self, **kwargs) -> None:
        data = _load_state_file()
        agent = data.get("agent", {})
        agent.update(kwargs)
        data["agent"] = agent
        _save_state_file(data)

    def get_last_task_tokens(self) -> int:
        return _load_state_file().get("agent", {}).get("last_task_tokens", 0)

    def track_token_spend(self, label: str, tokens: int, model: str = "unknown") -> None:
        data = _load_state_file()
        agent = data.get("agent", {})
        agent["total_tokens_used"] = agent.get("total_tokens_used", 0) + tokens
        agent["last_task_tokens"] = tokens
        data["agent"] = agent
        _save_state_file(data)

    def get_remaining_budget(self) -> int:
        s = get_settings()
        used = _load_state_file().get("agent", {}).get("total_tokens_used", 0)
        return max(0, s.token_budget_total - used)

    # ── BotLearn state (state.json sub-key) ───────────────────────────

    def get_botlearn_state(self) -> BotLearnState:
        data = _load_state_file()
        return BotLearnState.model_validate(data.get("botlearn", {}))

    def update_botlearn_state(self, **kwargs) -> None:
        data = _load_state_file()
        bl = data.get("botlearn", {})
        bl.update(kwargs)
        data["botlearn"] = bl
        _save_state_file(data)

    def add_task_since_heartbeat(self, label: str) -> None:
        data = _load_state_file()
        agent = data.get("agent", {})
        tasks = agent.get("tasks_since_heartbeat", [])
        tasks.append(label)
        agent["tasks_since_heartbeat"] = tasks
        data["agent"] = agent
        _save_state_file(data)

    def flush_tasks_since_heartbeat(self) -> list[str]:
        data = _load_state_file()
        agent = data.get("agent", {})
        tasks = agent.get("tasks_since_heartbeat", [])
        agent["tasks_since_heartbeat"] = []
        data["agent"] = agent
        _save_state_file(data)
        return tasks


# Module-level singleton — import this everywhere
memory = Memory()
