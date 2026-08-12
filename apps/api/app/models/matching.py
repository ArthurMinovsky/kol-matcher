"""Public contract for running named matching algorithms."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .brand import BrandProfile
from .creator import CreatorProfile


AlgorithmKey = Literal["bm25_v2_lekcut"]


class MatchingRequest(BaseModel):
    brand_profile: BrandProfile
    creators: list[CreatorProfile] = Field(default_factory=list)
    algorithm_key: AlgorithmKey = "bm25_v2_lekcut"


class CandidateMatch(BaseModel):
    rank: int
    username: str
    normalized_score: float
    raw_score: float
    matched_keywords: list[str] = Field(default_factory=list)
    algorithm_key: str


class MatchingResponse(BaseModel):
    algorithm_key: str
    matches: list[CandidateMatch]
