"""Pydantic models for Phase 3 — LLM Summarization.

Matches Architecture §3.3 and §4.2, and the `themes` table schema.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# LLM response models (used with json_object mode)
# ---------------------------------------------------------------------------


class ThemeResponse(BaseModel):
    """Raw LLM output for label_theme()."""

    label: str = Field(
        ..., description="Short, punchy name (e.g. 'KYC Friction', 'Withdrawal Speed')"
    )
    description: str = Field(..., description="1-2 sentence summary of the cluster feedback")
    sentiment: Literal["negative", "mixed", "positive"]


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


class WhatThisSolvesResponse(BaseModel):
    """Raw LLM output for generate_what_this_solves()."""

    what_this_solves: list[AudienceValue]


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

    id: str
    rank: int
    label: str = Field(..., description="Short, punchy name for the theme (e.g. 'KYC Friction')")
    description: str = Field(..., description="1-2 sentence summary of the cluster feedback")
    sentiment: Literal["negative", "mixed", "positive"]
    review_count: int
    representative_review_ids: list[str] = Field(default_factory=list)


class ActionIdea(BaseModel):
    """An actionable suggestion derived from themes."""

    title: str
    description: str


class AudienceValue(BaseModel):
    """Value proposition for a specific stakeholder audience."""

    audience: Literal["Product", "Support", "Leadership"]
    value: str = Field(..., description="How these findings help this specific audience")


class Window(BaseModel):
    start: date
    end: date
    weeks: int


class PulseStats(BaseModel):
    total_reviews: int
    avg_rating: float
    rating_delta_vs_prev: float | None = None


class PulseSummary(BaseModel):
    """The final summarized report for a run."""

    product: str
    window: Window
    stats: PulseStats
    top_themes: list[Theme] = Field(default_factory=list)
    quotes: list[Quote] = Field(default_factory=list)
    action_ideas: list[ActionIdea] = Field(default_factory=list)
    what_this_solves: list[AudienceValue] = Field(default_factory=list)
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
        super().__init__(f"LLM cost cap exceeded: ${spent:.4f} spent, cap is ${cap:.4f}")


ActionIdeasResponse.model_rebuild()
WhatThisSolvesResponse.model_rebuild()
