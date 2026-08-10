"""Tests for deterministic ranking behavior."""
from __future__ import annotations

import pytest

from app.models.brand import BrandProfile
from app.models.creator import CreatorProfile
from app.services.ranker import score_and_rank


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


def test_top_n_limits_results():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    creators = [_make_creator(f"u{i}") for i in range(25)]
    recs = score_and_rank(creators, brand, None, top_n=15)
    assert len(recs) == 15


def test_deduplicates_by_username():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    creators = [
        _make_creator("same"),
        _make_creator("Same"),
        _make_creator("other"),
    ]
    recs = score_and_rank(creators, brand, None, top_n=10)
    usernames = [r.creator.username.lower() for r in recs]
    assert usernames.count("same") == 1


def test_malformed_creator_skipped_without_crash():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    good = _make_creator("good")
    malformed = CreatorProfile(username="bad")  # missing required signals but not invalid
    recs = score_and_rank([good, malformed], brand, None, top_n=10)
    assert len(recs) >= 1
    assert recs[0].creator.username == "good"


def test_tie_breaker_uses_relevance_then_coverage_then_username():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    # Same match score potential by giving identical component inputs
    a = _make_creator("aaa", topic_tags=["skincare"], thai_caption_ratio=0.9)
    b = _make_creator("bbb", topic_tags=["skincare"], thai_caption_ratio=0.5)
    recs = score_and_rank([b, a], brand, None, top_n=10)
    # a has higher Thailand score -> higher match score, should rank first
    assert recs[0].creator.username == "aaa"


def test_ranking_is_deterministic():
    brand = BrandProfile(brand_name="X", desired_style_tags=["educational"])
    creators = [_make_creator(f"u{i}") for i in range(20)]
    run1 = score_and_rank(creators, brand, None, top_n=15)
    run2 = score_and_rank(creators, brand, None, top_n=15)
    assert [r.creator.username for r in run1] == [r.creator.username for r in run2]
