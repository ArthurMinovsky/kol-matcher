"""Tests for deterministic ranking behavior."""
from __future__ import annotations

import pytest

from app.models.brand import BrandProfile
from app.models.creator import CreatorPost, CreatorProfile
from app.services.ranker import score_and_rank
from app.services.scorer import compute_combined_relevance
from unittest.mock import AsyncMock


def _make_creator(username: str, **overrides) -> CreatorProfile:
    defaults = {
        "topic_tags": ["skincare"],
        "style_tags": ["educational"],
        "thai_caption_ratio": 0.8,
        "thai_hashtag_count": 10,
        "has_thai_bio": True,
        "has_thailand_location": True,
        "recent_posts": [],
        "follower_count": 10000,
    }
    defaults.update(overrides)
    return CreatorProfile(username=username, **defaults)


@pytest.mark.asyncio
async def test_top_n_limits_results():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    creators = [_make_creator(f"u{i}") for i in range(25)]
    recs = await score_and_rank(creators, brand, top_n=15)
    assert len(recs) == 15


@pytest.mark.asyncio
async def test_deduplicates_by_username():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    creators = [
        _make_creator("same"),
        _make_creator("Same"),
        _make_creator("other"),
    ]
    recs = await score_and_rank(creators, brand, top_n=10)
    usernames = [r.creator.username.lower() for r in recs]
    assert usernames.count("same") == 1


@pytest.mark.asyncio
async def test_malformed_creator_skipped_without_crash():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    good = _make_creator("good")
    malformed = CreatorProfile(username="bad")
    recs = await score_and_rank([good, malformed], brand, top_n=10)
    assert len(recs) >= 1
    assert recs[0].creator.username == "good"


@pytest.mark.asyncio
async def test_tie_breaker_uses_relevance_then_coverage_then_username():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    a = _make_creator("aaa", topic_tags=["skincare"], thai_caption_ratio=0.9)
    b = _make_creator("bbb", topic_tags=["skincare"], thai_caption_ratio=0.5)
    recs = await score_and_rank([b, a], brand, top_n=10)
    assert recs[0].creator.username == "aaa"


@pytest.mark.asyncio
async def test_ranking_is_deterministic():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    creators = [_make_creator(f"u{i}") for i in range(20)]
    run1 = await score_and_rank(creators, brand, top_n=15)
    run2 = await score_and_rank(creators, brand, top_n=15)
    assert [r.creator.username for r in run1] == [r.creator.username for r in run2]


@pytest.mark.asyncio
async def test_ranking_exposes_hybrid_relevance_and_llm_rationale(monkeypatch):
    judge = AsyncMock(
        return_value=[
            {
                "score": 80.0,
                "reasoning": "Strong skincare topic fit.",
                "available": True,
            }
        ]
    )
    monkeypatch.setattr("app.services.ranker.judge_relevance_batch", judge)

    brand = BrandProfile(
        brand_name="Dr. Pong Clinic",
        topics=["skincare"],
        english_keywords=["skincare"],
        desired_style_tags=["review"],
        campaign_goal="product review",
    )
    creator = _make_creator(
        "derma",
        bio="Skincare product review creator",
        topic_tags=["skincare"],
        style_tags=["review"],
    )

    recommendations = await score_and_rank(
        [creator],
        brand,
        top_n=1,
        use_llm_judge=True,
    )

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.bm25_relevance > 0
    assert recommendation.llm_relevance == 80.0
    assert recommendation.relevance == pytest.approx(
        compute_combined_relevance(
            recommendation.bm25_relevance,
            recommendation.llm_relevance,
        ),
        abs=0.01,
    )
    assert recommendation.rationale == "Strong skincare topic fit."
    assert any(
        item.signal == "LLM Judge Relevance" and item.available
        for item in recommendation.scoring_evidence
    )
    judge.assert_awaited_once()


@pytest.mark.asyncio
async def test_unavailable_llm_does_not_add_neutral_relevance_to_unmatched_creator(monkeypatch):
    judge = AsyncMock(
        return_value=[
            {
                "score": 50.0,
                "reasoning": "LLM judge unavailable; neutral relevance fallback used.",
                "available": False,
            },
            {
                "score": 50.0,
                "reasoning": "LLM judge unavailable; neutral relevance fallback used.",
                "available": False,
            },
        ]
    )
    monkeypatch.setattr("app.services.ranker.judge_relevance_batch", judge)

    brand = BrandProfile(
        brand_name="Dr. Pong Clinic",
        topics=["skincare", "dermatology"],
        english_keywords=["skincare", "dermatology"],
        campaign_goal="product review",
    )
    relevant = _make_creator(
        "relevant",
        bio="Skincare dermatology education",
        topic_tags=["skincare", "dermatology"],
        recent_posts=[CreatorPost(views=100, likes=1, comments=0, shares=0)],
    )
    unmatched = _make_creator(
        "unmatched",
        bio="Gaming livestreams",
        topic_tags=["gaming"],
        recent_posts=[CreatorPost(views=100, likes=100, comments=0, shares=0)],
    )

    recommendations = await score_and_rank(
        [relevant, unmatched],
        brand,
        top_n=2,
        use_llm_judge=True,
    )

    assert [recommendation.creator.username for recommendation in recommendations] == [
        "relevant",
        "unmatched",
    ]
    assert recommendations[1].llm_relevance == 50.0
    assert recommendations[1].relevance == 0.0
    assert any(
        item.signal == "LLM Judge Relevance"
        and item.value == "50.0/100"
        and item.available is False
        for item in recommendations[1].scoring_evidence
    )
    judge.assert_awaited_once()
