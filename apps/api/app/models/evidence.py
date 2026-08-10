"""Evidence and trust domain models."""
from __future__ import annotations

from pydantic import BaseModel

AudienceVerification = str  # "Verified" | "Partial" | "Unavailable"
RecommendationConfidence = str  # "HIGH" | "MEDIUM" | "LOW"


class Evidence(BaseModel):
    """A single piece of scored evidence contributing to a recommendation.

    Evidence is informational only — it does not affect Match Score.
    Coverage measures information completeness.
    """

    signal: str         # Human-readable name of the signal
    value: str          # Observable value (string representation)
    source: str         # Where this came from: "bio", "posts", "metadata", etc.
    weight: float       # Contribution to evidence coverage (0–100 scale)
    available: bool     # Whether this signal was actually observed


class EvidenceCoverage(BaseModel):
    """Breakdown of evidence coverage for a creator.

    Coverage measures information completeness only.
    It must never affect Match Score.

    Weights (must sum to 100):
      bio_context:     20
      captions_posts:  25
      engagement:      25
      thailand:        20
      metadata:        10
    """

    bio_context: float = 0.0       # 0–20
    captions_posts: float = 0.0    # 0–25
    engagement: float = 0.0        # 0–25
    thailand_signals: float = 0.0  # 0–20
    profile_metadata: float = 0.0  # 0–10

    @property
    def total(self) -> float:
        return (
            self.bio_context
            + self.captions_posts
            + self.engagement
            + self.thailand_signals
            + self.profile_metadata
        )
