"""Unit tests for the deterministic scoring engine.

Tests verify:
- All component functions return values in [0, 100]
- Weight invariants (weights sum to 1.0)
- Specific ordering invariants (dermatologist > gaming creator)
- Style fit edge cases

These tests run without any external service or Docker.
Run with: pytest apps/api/tests/test_scorer.py -v
"""
from __future__ import annotations

import pytest

from app.config import settings
from app.models.creator import CreatorPost, CreatorProfile
from app.services.scorer import (
    compute_engagement,
    compute_evidence_coverage,
    compute_match_score,
    compute_recommendation_confidence,
    compute_relevance,
    compute_style_fit,
    compute_thailand_relevance,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

def make_skincare_creator(**overrides) -> CreatorProfile:
    """Highly relevant dermatology creator."""
    defaults = dict(
        username="test_derma",
        bio="แพทย์ผิวหนัง ให้ความรู้เรื่องผิวฟรี",
        follower_count=500000,
        location="Bangkok, Thailand",
        verified=False,
        topic_tags=["dermatology", "skincare", "acne", "UV protection"],
        style_tags=["educational", "expert", "tutorial"],
        thai_caption_ratio=0.90,
        thai_hashtag_count=18,
        has_thai_bio=True,
        has_thailand_location=True,
        recent_posts=[
            CreatorPost(post_id="t1", caption="สกินแคร์", views=400000, likes=34000, comments=2100, shares=2800),
            CreatorPost(post_id="t2", caption="สิว", views=350000, likes=29000, comments=1800, shares=2400),
            CreatorPost(post_id="t3", caption="ครีมกันแดด", views=500000, likes=42000, comments=2600, shares=3500),
            CreatorPost(post_id="t4", caption="เซรั่ม", views=300000, likes=21000, comments=1500, shares=2000),
            CreatorPost(post_id="t5", caption="ผิวสวย", views=280000, likes=18000, comments=1200, shares=1600),
        ],
        embedding=[0.90, 0.87, 0.84, 0.78, 0.72, 0.64, 0.28, 0.22, 0.18, 0.16, 0.13, 0.11, 0.09, 0.07, 0.04, 0.02],
        source_type="synthetic",
    )
    defaults.update(overrides)
    return CreatorProfile(**defaults)


def make_gaming_creator(**overrides) -> CreatorProfile:
    """Irrelevant gaming creator."""
    defaults = dict(
        username="test_gaming",
        bio="Pro gamer ROV Mobile Legends",
        follower_count=3000000,
        topic_tags=["gaming", "esports", "streaming"],
        style_tags=["entertainment", "lifestyle"],
        thai_caption_ratio=0.70,
        thai_hashtag_count=8,
        has_thai_bio=True,
        has_thailand_location=True,
        recent_posts=[
            CreatorPost(post_id="g1", caption="ROV", views=3000000, likes=250000, comments=16000, shares=21000),
            CreatorPost(post_id="g2", caption="gaming", views=2500000, likes=208000, comments=13000, shares=17000),
        ],
        embedding=[0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.90, 0.85, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20, 0.10],
        source_type="synthetic",
    )
    defaults.update(overrides)
    return CreatorProfile(**defaults)


BRAND_EMBEDDING = [0.92, 0.88, 0.85, 0.78, 0.72, 0.65, 0.30, 0.25, 0.20, 0.18, 0.15, 0.12, 0.10, 0.08, 0.05, 0.03]


# ── Weight invariants ──────────────────────────────────────────────────────

def test_weights_sum_to_one():
    """Config weights must sum exactly to 1.0."""
    total = (
        settings.RELEVANCE_WEIGHT
        + settings.ENGAGEMENT_WEIGHT
        + settings.THAILAND_WEIGHT
        + settings.STYLE_WEIGHT
    )
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, not 1.0"


def test_thailand_signal_weights_sum_to_100():
    total = (
        settings.THAILAND_CAPTION_RATIO_WEIGHT
        + settings.THAILAND_HASHTAG_WEIGHT
        + settings.THAILAND_BIO_WEIGHT
        + settings.THAILAND_LOCATION_WEIGHT
    )
    assert total == 100, f"Thailand signal weights sum to {total}, not 100"


def test_evidence_weights_sum_to_100():
    total = (
        settings.EVIDENCE_BIO_WEIGHT
        + settings.EVIDENCE_CAPTIONS_WEIGHT
        + settings.EVIDENCE_ENGAGEMENT_WEIGHT
        + settings.EVIDENCE_THAILAND_WEIGHT
        + settings.EVIDENCE_METADATA_WEIGHT
    )
    assert total == 100, f"Evidence weights sum to {total}, not 100"


# ── Relevance ─────────────────────────────────────────────────────────────

def test_relevance_in_range():
    creator = make_skincare_creator()
    score = compute_relevance(creator, BRAND_EMBEDDING)
    assert 0.0 <= score <= 100.0


def test_skincare_creator_higher_relevance_than_gaming():
    derma = make_skincare_creator()
    gaming = make_gaming_creator()
    derma_score = compute_relevance(derma, BRAND_EMBEDDING)
    gaming_score = compute_relevance(gaming, BRAND_EMBEDDING)
    assert derma_score > gaming_score, (
        f"Derma ({derma_score:.1f}) should outrank gaming ({gaming_score:.1f})"
    )


def test_relevance_fallback_without_embedding():
    creator = make_skincare_creator(embedding=None)
    score = compute_relevance(creator, BRAND_EMBEDDING)
    assert 0.0 <= score <= 100.0


# ── Engagement ────────────────────────────────────────────────────────────

def test_engagement_in_range():
    creator = make_skincare_creator()
    score = compute_engagement(creator)
    assert 0.0 <= score <= 100.0


def test_engagement_no_posts_fallback():
    creator = make_skincare_creator(recent_posts=[], follower_count=500000)
    score = compute_engagement(creator)
    assert 0.0 <= score <= 100.0
    assert score > 0.0, "Should get non-zero score from follower fallback"


def test_engagement_no_signal_returns_zero():
    creator = make_skincare_creator(recent_posts=[], follower_count=None)
    score = compute_engagement(creator)
    assert score == 0.0


def test_engagement_clips_viral_outlier():
    """A post with 50% engagement rate must be clipped to ENGAGEMENT_CLIP_MAX."""
    posts = [CreatorPost(post_id="x", views=100, likes=50, comments=0, shares=0)]
    creator = make_skincare_creator(recent_posts=posts)
    score = compute_engagement(creator)
    # 50% > ENGAGEMENT_CLIP_MAX so clipped to 100
    assert score == 100.0


def test_engagement_uses_weighted_formula():
    post = CreatorPost(post_id="x", views=1000, likes=10, comments=5, shares=2)
    # (10 + 2*5 + 3*2) / 1000 = 0.026
    from app.services.scorer import _post_engagement_rate
    assert abs(_post_engagement_rate(post) - 0.026) < 1e-6


def test_engagement_median_across_posts():
    posts = [
        CreatorPost(post_id="a", views=1000, likes=30, comments=0, shares=0),  # 0.03
        CreatorPost(post_id="b", views=1000, likes=50, comments=0, shares=0),  # 0.05
        CreatorPost(post_id="c", views=1000, likes=10, comments=0, shares=0),  # 0.01
    ]
    creator = make_skincare_creator(recent_posts=posts, follower_count=None)
    score = compute_engagement(creator)
    # median = 0.03, clipped to 0.03, /0.30 *100 = 10
    assert abs(score - 10.0) < 0.5


# ── Thailand relevance ────────────────────────────────────────────────────

def test_thailand_relevance_in_range():
    creator = make_skincare_creator()
    score = compute_thailand_relevance(creator)
    assert 0.0 <= score <= 100.0


def test_thailand_full_signals_scores_100():
    creator = make_skincare_creator(
        thai_caption_ratio=1.0,
        thai_hashtag_count=20,
        has_thai_bio=True,
        has_thailand_location=True,
    )
    score = compute_thailand_relevance(creator)
    assert score == 100.0


def test_thailand_no_signals_scores_zero():
    creator = make_skincare_creator(
        thai_caption_ratio=None,
        thai_hashtag_count=None,
        has_thai_bio=False,
        has_thailand_location=False,
    )
    score = compute_thailand_relevance(creator)
    assert score == 0.0


# ── Style fit ─────────────────────────────────────────────────────────────

def test_style_fit_perfect():
    creator = make_skincare_creator(style_tags=["educational", "expert", "tutorial"])
    score = compute_style_fit(creator, ["educational", "expert", "tutorial"])
    assert score == 100.0


def test_style_fit_partial():
    creator = make_skincare_creator(style_tags=["educational", "lifestyle"])
    score = compute_style_fit(creator, ["educational", "expert", "tutorial"])
    assert abs(score - 33.33) < 0.1


def test_style_fit_no_desired_styles():
    creator = make_skincare_creator()
    score = compute_style_fit(creator, [])
    assert score == 50.0  # Neutral


# ── Composite match score ─────────────────────────────────────────────────

def test_match_score_in_range():
    score = compute_match_score(80.0, 60.0, 90.0, 70.0)
    assert 0.0 <= score <= 100.0


def test_match_score_weighted_correctly():
    # With known values, verify the weighted sum
    r, e, t, s = 100.0, 100.0, 100.0, 100.0
    expected = (
        r * settings.RELEVANCE_WEIGHT
        + e * settings.ENGAGEMENT_WEIGHT
        + t * settings.THAILAND_WEIGHT
        + s * settings.STYLE_WEIGHT
    )
    assert compute_match_score(r, e, t, s) == expected


def test_match_score_ordering():
    """A highly relevant skincare creator must outscore a high-follower gaming creator."""
    derma = make_skincare_creator()
    gaming = make_gaming_creator()

    def score(creator):
        r = compute_relevance(creator, BRAND_EMBEDDING)
        e = compute_engagement(creator)
        t = compute_thailand_relevance(creator)
        s = compute_style_fit(creator, ["educational", "expert", "tutorial"])
        return compute_match_score(r, e, t, s)

    assert score(derma) > score(gaming), "Derma creator must outscore gaming creator"


# ── Evidence coverage ─────────────────────────────────────────────────────

def test_evidence_coverage_in_range():
    creator = make_skincare_creator()
    total, breakdown = compute_evidence_coverage(creator)
    assert 0.0 <= total <= 100.0
    assert 0.0 <= breakdown.total <= 100.0


def test_evidence_coverage_full():
    """Creator with all signal types should score 100."""
    creator = make_skincare_creator()
    total, _ = compute_evidence_coverage(creator)
    assert total == 100.0


def test_evidence_coverage_empty_creator():
    """Creator with minimal data should score below 50."""
    creator = CreatorProfile(
        username="empty_creator",
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


# ── Confidence ───────────────────────────────────────────────────────────

def test_confidence_high():
    assert compute_recommendation_confidence(80.0, 75.0) == "HIGH"


def test_confidence_medium():
    assert compute_recommendation_confidence(50.0, 50.0) == "MEDIUM"


def test_confidence_low():
    assert compute_recommendation_confidence(20.0, 30.0) == "LOW"
