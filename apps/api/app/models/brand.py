"""Brand domain models."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, HttpUrl

SourceState = Literal["LIVE", "CACHED", "PARTIAL", "FAILED"]


class BrandProfile(BaseModel):
    """Structured representation of a brand extracted from public sources."""

    brand_name: str
    industry: str | None = None
    description: str | None = None
    products: list[str] = []
    audience_hypothesis: str | None = None  # Always labelled as hypothesis, never demographic fact
    topics: list[str] = []
    tone: str | None = None
    content_styles: list[str] = []
    thai_keywords: list[str] = []
    english_keywords: list[str] = []
    campaign_goal: str | None = None
    website_url: str | None = None
    facebook_url: str | None = None

    # Desired style tags derived from campaign_goal (used for Style Fit scoring)
    desired_style_tags: list[str] = []

    # Raw combined text from Facebook + website for keyword extraction
    raw_text: str | None = None

    extraction_method: Literal["fixture", "llm", "heuristic"] = "fixture"
