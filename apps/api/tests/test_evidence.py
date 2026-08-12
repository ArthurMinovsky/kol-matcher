"""Tests for evidence coverage and confidence invariants."""
from __future__ import annotations

from app.models.creator import CreatorPost, CreatorProfile
from app.services.ranker import score_and_rank
from app.services.scorer import (
    compute_evidence_coverage,
    compute_recommendation_confidence,
)


def test_evidence_coverage_full():
    creator = CreatorProfile(
        username="full",
        bio="bio",
        location="BKK",
        verified=False,
        recent_posts=[
            CreatorPost(post_id="p1", views=1000, likes=50),
            CreatorPost(post_id="p2", views=1000, likes=50),
            CreatorPost(post_id="p3", views=1000, likes=50),
            CreatorPost(post_id="p4", views=1000, likes=50),
            CreatorPost(post_id="p5", views=1000, likes=50),
        ],
        follower_count=1000,
        thai_caption_ratio=0.5,
        thai_hashtag_count=5,
        has_thai_bio=True,
        has_thailand_location=True,
    )
    total, _ = compute_evidence_coverage(creator)
    assert total == 100.0


def test_evidence_coverage_empty():
    creator = CreatorProfile(
        username="empty",
        bio=None,
        recent_posts=[],
        follower_count=None,
        location=None,
        thai_caption_ratio=None,
        thai_hashtag_count=None,
        has_thai_bio=None,
        has_thailand_location=None,
    )
    total, _ = compute_evidence_coverage(creator)
    assert total < 50.0


def test_confidence_rules():
    assert compute_recommendation_confidence(80.0, 70.0) == "HIGH"
    assert compute_recommendation_confidence(50.0, 50.0) == "MEDIUM"
    assert compute_recommendation_confidence(30.0, 80.0) == "MEDIUM"
    assert compute_recommendation_confidence(20.0, 30.0) == "LOW"


import pytest

@pytest.mark.asyncio
async def test_removing_bio_does_not_change_match_score():
    from app.models.brand import BrandProfile

    brand = BrandProfile(brand_name="Dr. Pong", desired_style_tags=["educational", "expert", "tutorial"])
    full = CreatorProfile(
        username="creator",
        bio="dermatology tips",
        topic_tags=["dermatology", "skincare"],
        style_tags=["educational"],
        thai_caption_ratio=0.9,
        thai_hashtag_count=10,
        has_thai_bio=True,
        has_thailand_location=True,
        follower_count=10000,
    )
    no_bio = full.model_copy(update={"bio": None})

    full_recs = await score_and_rank([full], brand, top_n=1)
    no_bio_recs = await score_and_rank([no_bio], brand, top_n=1)

    assert full_recs[0].match_score == no_bio_recs[0].match_score
    assert full_recs[0].evidence_coverage > no_bio_recs[0].evidence_coverage
