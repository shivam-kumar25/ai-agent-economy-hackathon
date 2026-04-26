from __future__ import annotations

from pydantic import BaseModel, Field


class ContentOutline(BaseModel):
    title: str
    meta_description: str = Field(..., max_length=160)
    h2_sections: list[str]
    target_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    tone: str = "professional"
    estimated_word_count: int = 1500


class EmailMessage(BaseModel):
    subject: str
    preview_text: str
    body: str
    cta: str


class EmailSequence(BaseModel):
    product: str
    icp: str
    emails: list[EmailMessage]


class SocialVariation(BaseModel):
    copy: str
    score: int = Field(..., ge=0, le=100)
    rationale: str


class SocialCopy(BaseModel):
    platform: str
    topic: str
    variations: list[SocialVariation]
    recommended_index: int = 0


class BlogPost(BaseModel):
    title: str
    meta_description: str = Field(..., max_length=160)
    content: str
    word_count: int
    target_keyword: str
    readability_score: float
    internal_link_placeholders: list[str] = Field(default_factory=list)
