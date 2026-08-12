"""API request/response models."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .brand import BrandProfile, SourceState
from .creator import CreatorProfile
from .evidence import AudienceVerification, Evidence, EvidenceCoverage, RecommendationConfidence


class Recommendation(BaseModel):
    """A single ranked KOL recommendation.

    Match Score = 0.20*bm25_relevance + 0.25*llm_relevance
               + 0.25*engagement + 0.15*thailand_relevance + 0.15*style_fit
    All component scores are clamped to 0..100.
    Evidence Coverage and Recommendation Confidence do NOT affect Match Score.
    """

    rank: int
    creator: CreatorProfile

    # Match Score components (all 0..100, stored unrounded for stable sort)
    match_score: float
    bm25_relevance: float
    llm_relevance: float
    relevance: float
    engagement: float
    thailand_relevance: float
    style_fit: float

    # Trust metadata (independent from ranking)
    evidence_coverage: float        # 0..100
    evidence_breakdown: EvidenceCoverage
    audience_verification: AudienceVerification
    recommendation_confidence: RecommendationConfidence

    # Explanation (deterministic template — not LLM output for fixture path)
    rationale: str
    explanation: str
    limitations: list[str]
    scoring_evidence: list[Evidence]


class AnalyzeRequest(BaseModel):
    """Request body for POST /api/analyze."""

    brand_name: str
    facebook_url: str
    campaign_goal: str
    website_url: str | None = None

    @field_validator("brand_name")
    @classmethod
    def brand_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("brand_name is required")
        return v

    @field_validator("facebook_url")
    @classmethod
    def must_be_facebook_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("facebook_url must start with http:// or https://")
        return v

    @field_validator("website_url")
    @classmethod
    def website_optional_http(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.startswith(("http://", "https://")):
            raise ValueError("website_url must start with http:// or https://")
        return v


class SourceStatusMap(BaseModel):
    """Provider status for each data source."""

    website: SourceState = "FAILED"
    facebook: SourceState = "FAILED"
    tiktok: SourceState = "FAILED"
    brand_extraction: SourceState = "FAILED"


DR_PONG_NAMES = {"dr pong", "drpong", "dr. pong clinic", "drpong clinic"}
DR_PONG_FB_URLS = {
    "https://www.facebook.com/drpongclinic",
    "https://facebook.com/drpongclinic",
    "www.facebook.com/drpongclinic",
    "facebook.com/drpongclinic",
}


def is_drpong_request(req: AnalyzeRequest) -> bool:
    name = req.brand_name.lower().strip()
    fb = req.facebook_url.lower().rstrip("/")
    return (
        any(trigger in name for trigger in DR_PONG_NAMES)
        or any(fb.endswith(u.lower().rstrip("/")) for u in DR_PONG_FB_URLS)
    )


class AnalyzeResponse(BaseModel):
    """Response body for POST /api/analyze and GET /api/demo/drpong."""

    brand_profile: BrandProfile
    recommendations: list[Recommendation]
    source_status: SourceStatusMap
    provider_provenance: dict[str, str] = Field(default_factory=dict)
    limitations: list[str]


class HealthResponse(BaseModel):
    """Response body for GET /api/health."""

    status: str
    fixture_demo: bool
