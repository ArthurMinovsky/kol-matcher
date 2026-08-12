"""Tests for the versioned BM25 KOL matcher."""
from __future__ import annotations

from app.models.brand import BrandProfile
from app.models.creator import CreatorProfile, CreatorPost
from app.services.bm25_matcher import score_creators


def _creator(username: str, topics: list[str], bio: str) -> CreatorProfile:
    return CreatorProfile(
        username=username,
        bio=bio,
        topic_tags=topics,
        recent_posts=[CreatorPost(caption=bio, hashtags=topics)],
    )


def test_bm25_ranks_beauty_creator_above_food_and_travel():
    brand = BrandProfile(
        brand_name="Dr. Pong Clinic",
        industry="Beauty & Skincare",
        topics=["skincare", "dermatology", "acne"],
        english_keywords=["skincare", "dermatology", "acne"],
        campaign_goal="educational skincare",
    )
    creators = [
        _creator("food.creator", ["food", "recipe"], "Thai food recipes"),
        _creator("travel.creator", ["travel", "hotel"], "Travel hotel guide"),
        _creator("beauty.creator", ["skincare", "dermatology"], "Skincare acne education"),
    ]

    results = score_creators(brand, creators)

    assert results[0].username == "beauty.creator"
    assert results[0].algorithm_key == "bm25_v2_lekcut"
    assert results[0].normalized_score > results[1].normalized_score
    assert "skincare" in results[0].matched_keywords
    assert results[0].raw_score > 0


def test_bm25_ranks_travel_creator_for_traveloka():
    brand = BrandProfile(
        brand_name="Traveloka",
        industry="Travel & Hospitality",
        topics=["travel", "hotel", "destination", "itinerary"],
        english_keywords=["travel", "hotel", "destination", "trip"],
        thai_keywords=["ท่องเที่ยว", "โรงแรม"],
        campaign_goal="travel awareness",
    )
    creators = [
        _creator("beauty.creator", ["skincare"], "Skincare education"),
        _creator("travel.creator", ["travel", "hotel", "destination"], "Travel hotel itinerary guide"),
        _creator("food.creator", ["food", "recipe"], "Thai food recipes"),
    ]

    results = score_creators(brand, creators)

    assert results[0].username == "travel.creator"
    assert results[0].normalized_score >= 80


def test_empty_query_does_not_return_neutral_constant_scores():
    brand = BrandProfile(brand_name="Unknown")
    creators = [
        _creator("one", ["beauty"], "Beauty creator"),
        _creator("two", ["food"], "Food creator"),
    ]

    results = score_creators(brand, creators)

    assert [result.normalized_score for result in results] == [0.0, 0.0]
    assert all(result.matched_keywords == [] for result in results)


def test_bm25_reports_lekcut_algorithm_identity():
    brand = BrandProfile(
        brand_name="Dr. Pong Clinic",
        industry="Beauty & Skincare",
        topics=["skincare"],
        english_keywords=["skincare"],
        campaign_goal="product review",
    )
    creators = [_creator("beauty.creator", ["skincare"], "Skincare review")]

    results = score_creators(brand, creators)

    assert results[0].algorithm_key == "bm25_v2_lekcut"
