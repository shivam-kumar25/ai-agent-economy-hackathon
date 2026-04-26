from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.models.content import ContentOutline
from src.models.research import CompetitorTeardown, LeadList, MarketReport
from src.models.review import QuestTriage, ReviewVerdict
from src.models.seo import AuditResult
from src.modules.seo.prompts import (
    BLOG_WRITER_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    EMAIL_WRITER_PROMPT,
    LEAD_INTEL_PROMPT,
    MARKET_INTEL_PROMPT,
    OUTLINE_PROMPT,
    REVIEWER_PROMPT,
    SEO_ANALYSIS_PROMPT,
    SOCIAL_WRITER_PROMPT,
)
from src.utils.llm import cached_system, llm, llm_fast

# ── Analysis chains — guaranteed Pydantic output via Claude tool-use ──

ANALYSIS_CHAINS: dict[str, Runnable] = {
    "seo_audit": (
        ChatPromptTemplate.from_messages([
            cached_system(SEO_ANALYSIS_PROMPT),
            ("human", "Crawl data:\n{crawl_results}\n\nPrior audit:\n{prior_audit}"),
        ])
        | llm.with_structured_output(AuditResult, include_raw=True)
    ),
    "research_competitor": (
        ChatPromptTemplate.from_messages([
            cached_system(COMPETITOR_ANALYSIS_PROMPT),
            ("human", "Crawl data:\n{crawl_results}"),
        ])
        | llm.with_structured_output(CompetitorTeardown, include_raw=True)
    ),
    "research_market": (
        ChatPromptTemplate.from_messages([
            cached_system(MARKET_INTEL_PROMPT),
            ("human", "Search results:\n{search_results}\n\nICP / Industry: {icp}"),
        ])
        | llm.with_structured_output(MarketReport, include_raw=True)
    ),
    "research_leads": (
        ChatPromptTemplate.from_messages([
            cached_system(LEAD_INTEL_PROMPT),
            ("human", "Sources:\n{search_results}\n\nICP filters: {icp}"),
        ])
        | llm.with_structured_output(LeadList, include_raw=True)
    ),
}

# ── Write chains — free-form text output ─────────────────────────────

WRITE_CHAINS: dict[str, Runnable] = {
    "content_blog": (
        ChatPromptTemplate.from_messages([
            cached_system(BLOG_WRITER_PROMPT),
            ("human", "Outline:\n{outline}\n\nTarget keyword: {keyword}\nTone: {tone}"),
        ])
        | llm
        | StrOutputParser()
    ),
    "content_email": (
        ChatPromptTemplate.from_messages([
            cached_system(EMAIL_WRITER_PROMPT),
            ("human", "Product: {product}\nICP persona: {icp}"),
        ])
        | llm
        | StrOutputParser()
    ),
    "content_social": (
        ChatPromptTemplate.from_messages([
            cached_system(SOCIAL_WRITER_PROMPT),
            ("human", "Platform: {platform}\nTopic: {topic}\nVoice: {voice}"),
        ])
        | llm
        | StrOutputParser()
    ),
}

# ── Utility chains ─────────────────────────────────────────────────────

outline_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        (
            "system",
            OUTLINE_PROMPT,
        ),
        ("human", "Keyword: {keyword}\nSERP gaps:\n{serp_gaps}\nTone: {tone}"),
    ])
    | llm_fast.with_structured_output(ContentOutline)
)

review_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        cached_system(REVIEWER_PROMPT),
        ("human", "Task spec:\n{spec}\n\nContent to review:\n{content}"),
    ])
    | llm.with_structured_output(ReviewVerdict, include_raw=True)
)

improve_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a precise editor. Fix only the specific issues listed. "
            "Do not rewrite unnecessarily. Return the improved version only.",
        ),
        ("human", "Original:\n{content}\n\nIssues to fix:\n{feedback}"),
    ])
    | llm
    | StrOutputParser()
)

triage_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a task router for a B2B growth agent. "
            "Classify this quest and estimate effort conservatively.",
        ),
        ("human", "Quest spec:\n{quest_json}"),
    ])
    | llm_fast.with_structured_output(QuestTriage)
)
