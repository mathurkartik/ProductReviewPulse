"""Pydantic models for Phase 3 — LLM Summarization.

Matches Architecture §3.3 and the `themes` table schema.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# LLM response models (used with json_object mode)
# ---------------------------------------------------------------------------


class ThemeResponse(BaseModel):
    """Raw LLM output for label_theme()."""

    name: str = Field(
        ..., description="Short, punchy name (e.g. 'KYC Friction', 'Withdrawal Speed')"
    )
    summary: str = Field(
        ..., description="1-2 sentence summary of the cluster feedback"
    )
    sentiment_weight: float = Field(
        ..., ge=-1.0, le=1.0, description="-1.0 (very negative) to 1.0 (very positive)"
    )


class QuoteCandidate(BaseModel):
    """Raw LLM output for select_quotes()."""

    text: str
    rating: int | None = None
    source: Literal["appstore", "playstore"] = "playstore"


class QuoteListResponse(BaseModel):
    """Wrapper for the LLM quotes response."""

    quotes: list[QuoteCandidate]


class ActionIdeasResponse(BaseModel):
    """Raw LLM output for generate_action_ideas()."""

    action_ideas: list[ActionIdea]


class WhoThisHelpsResponse(BaseModel):
    """Raw LLM output for generate_who_this_helps()."""

    who_this_helps: list[AudienceValue]


# ---------------------------------------------------------------------------
# Domain models (persisted / surfaced in PulseSummary)
# ---------------------------------------------------------------------------


class Quote(BaseModel):
    """A verbatim-validated user quote."""

    text: str
    rating: int | None = None
    source: Literal["appstore", "playstore"]


class Theme(BaseModel):
    """A high-level theme derived from a cluster of reviews."""

    name: str = Field(
        ..., description="Short, punchy name for the theme (e.g. 'KYC Friction')"
    )
    summary: str = Field(
        ..., description="1-2 sentence summary of the cluster feedback"
    )
    review_count: int
    sentiment_weight: float = Field(..., description="-1.0 to 1.0 weight")
    quotes: list[Quote] = Field(default_factory=list)
    cluster_id: str | None = None


class ActionIdea(BaseModel):
    """An actionable suggestion derived from themes."""

    title: str
    description: str


class AudienceValue(BaseModel):
    """Value proposition for a specific stakeholder audience."""

    audience: Literal["Product", "Support", "Leadership"]
    value: str = Field(
        ..., description="How these findings help this specific audience"
    )


class PulseSummary(BaseModel):
    """The final summarized report for a run."""

    run_id: str
    product_key: str
    iso_week: str
    themes: list[Theme] = Field(default_factory=list, max_length=3)
    action_ideas: list[ActionIdea] = Field(default_factory=list)
    who_this_helps: list[AudienceValue] = Field(default_factory=list)
    metrics: LLMMetrics | None = None


class LLMMetrics(BaseModel):
    """Token and cost accounting for the run."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_cost_usd: float = 0.0
    llm_calls: int = 0
    retries: int = 0


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class PulseCostExceeded(Exception):
    """Raised when the per-run LLM cost cap is exceeded."""

    def __init__(self, spent: float, cap: float):
        self.spent = spent
        self.cap = cap
        super().__init__(
            f"LLM cost cap exceeded: ${spent:.4f} spent, cap is ${cap:.4f}"
        )


# Forward-reference fix: QuoteListResponse uses QuoteCandidate which is fine,
# but ActionIdeasResponse and WhoThisHelpsResponse reference ActionIdea and
# AudienceValue which are defined later. Rebuild them.
ActionIdeasResponse.model_rebuild()
WhoThisHelpsResponse.model_rebuild()
