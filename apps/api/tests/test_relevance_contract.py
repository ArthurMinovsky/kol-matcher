"""Regression tests for the BM25 + LLM-judge relevance contract."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.models.brand import BrandProfile
from app.models.creator import CreatorProfile
from app.services.brand_heuristic import extract_brand_profile_heuristic
from app.services.bm25_matcher import BM25Match
from app.services.llm_judge import judge_relevance
from app.services.scorer import build_scoring_evidence, compute_effective_relevance


def test_relevance_weights_are_bm25_20_and_llm_judge_25():
    assert settings.BM25_RELEVANCE_WEIGHT == 0.20
    assert settings.LLM_RELEVANCE_WEIGHT == 0.25
    assert settings.RELEVANCE_WEIGHT == 0.45


@pytest.mark.asyncio
async def test_llm_judge_returns_bounded_score_and_reasoning(monkeypatch):
    mocked_chat = AsyncMock(
        return_value={
            "score": 87,
            "reasoning": "The creator's skincare education matches the brand topics.",
        }
    )
    monkeypatch.setattr("app.services.llm_judge.chat_json", mocked_chat)

    result = await judge_relevance(
        "Brand: Dr. Pong Clinic\nTopics: skincare, dermatology",
        "Creator: @thai_derma\nBio: skincare education",
    )

    assert result["score"] == 87.0
    assert "skincare" in result["reasoning"]
    assert result["available"] is True


@pytest.mark.asyncio
async def test_llm_judge_uses_neutral_fallback_when_provider_fails(monkeypatch):
    mocked_chat = AsyncMock(side_effect=RuntimeError("provider unavailable"))
    monkeypatch.setattr("app.services.llm_judge.chat_json", mocked_chat)

    result = await judge_relevance("brand", "creator")

    assert result["score"] == 50.0
    assert "unavailable" in result["reasoning"].lower()
    assert result["available"] is False


def test_heuristic_brand_profile_contains_analysis_rationale():
    profile = extract_brand_profile_heuristic(
        brand_name="Dr. Pong Clinic",
        facebook_url="https://www.facebook.com/drpongclinic",
        website_url=None,
        campaign_goal="product review",
    )

    assert profile.analysis_rationale
    assert "brand name" in profile.analysis_rationale.lower()


def test_scoring_evidence_separates_bm25_and_llm_weights():
    creator = CreatorProfile(username="creator", bio="skincare")
    bm25_match = BM25Match(
        username="creator",
        normalized_score=80.0,
        raw_score=2.0,
        matched_keywords=["skincare"],
    )

    evidence = build_scoring_evidence(
        creator=creator,
        relevance=72.22,
        bm25_relevance=80.0,
        llm_relevance=66.0,
        engagement=50.0,
        thailand_relevance=40.0,
        style_fit=60.0,
        bm25_match=bm25_match,
        llm_available=False,
    )
    by_signal = {item.signal: item for item in evidence}

    assert by_signal["Combined Relevance"].weight == 45.0
    assert by_signal["BM25 Content Match"].weight == 20.0
    assert by_signal["LLM Judge Relevance"].weight == 25.0
    assert by_signal["LLM Judge Relevance"].available is False


def test_unavailable_llm_keeps_neutral_evidence_but_not_effective_relevance():
    assert compute_effective_relevance(0.0, 50.0, llm_available=False) == 0.0
    assert compute_effective_relevance(72.0, 50.0, llm_available=False) == 72.0
