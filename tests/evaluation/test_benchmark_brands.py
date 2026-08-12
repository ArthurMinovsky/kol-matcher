"""Deterministic cross-industry benchmark for BM25 KOL matching."""
from __future__ import annotations

from copy import deepcopy

import pytest

from app.models.api import AnalyzeRequest
from app.models.brand import BrandProfile
from app.providers.base import SourceResult
from app.services import pipeline
from app.services.pipeline import analyze_brand


BEAUTY_CREATORS = {
    "beauty.noon", "derma.doc.view", "glow.with.june", "skinlab.min", "makeup.pim"
}
FOOD_CREATORS = {
    "foodie.bank", "chef.nok", "sweet.tooth.mint", "mukbang.ton", "easy.recipe.aom"
}
TRAVEL_CREATORS = {
    "travel.with.ink", "hotel.hunter.jay", "backpack.beam", "sea.sun.sand", "city.walker.too"
}


BENCHMARKS = [
    (
        "Dr. Pong Clinic",
        "https://www.facebook.com/drpongclinic",
        "educational skincare",
        BEAUTY_CREATORS,
        BrandProfile(
            brand_name="Dr. Pong Clinic",
            industry="Beauty & Skincare",
            topics=["skincare", "dermatology", "acne", "beauty education"],
            english_keywords=["skincare", "dermatology", "acne", "serum"],
            thai_keywords=["สิว", "ดูแลผิว", "เซรั่ม"],
            campaign_goal="educational skincare",
            raw_text="evidence based skincare dermatology acne clinic",
        ),
    ),
    (
        "Parameter",
        "https://www.facebook.com/parameterthailand/",
        "product review",
        FOOD_CREATORS,
        BrandProfile(
            brand_name="Parameter",
            industry="Food & Beverage",
            topics=["food", "cooking", "restaurant", "dessert", "gelato"],
            english_keywords=["food", "restaurant", "dessert", "gelato", "ice cream"],
            thai_keywords=["อาหาร", "ร้านอาหาร", "ของหวาน"],
            campaign_goal="product review",
            raw_text="gelato ice cream dessert food shop",
        ),
    ),
    (
        "Traveloka",
        "https://www.facebook.com/TravelokaTH/?locale=th_TH",
        "travel awareness",
        TRAVEL_CREATORS,
        BrandProfile(
            brand_name="Traveloka",
            industry="Travel & Hospitality",
            topics=["travel", "hotel", "destination", "itinerary", "flight"],
            english_keywords=["travel", "hotel", "destination", "trip", "flight"],
            thai_keywords=["ท่องเที่ยว", "โรงแรม", "เที่ยว"],
            campaign_goal="travel awareness",
            raw_text="travel hotel destination trip booking flight",
        ),
    ),
]


@pytest.fixture
def deterministic_pipeline(monkeypatch):
    profiles = {name: profile for name, _url, _goal, _expected, profile in BENCHMARKS}

    async def fake_extract_brand_profile(brand_name, facebook_url, website_url, campaign_goal):
        return deepcopy(profiles[brand_name])

    async def fake_discover_tiktok_creators(_keywords):
        return SourceResult(status="FAILED", data=[], provider="test")

    monkeypatch.setattr(pipeline, "extract_brand_profile", fake_extract_brand_profile)
    monkeypatch.setattr(pipeline, "discover_tiktok_creators", fake_discover_tiktok_creators)


@pytest.mark.asyncio
@pytest.mark.parametrize("brand_name,facebook_url,campaign_goal,expected, _profile", BENCHMARKS)
async def test_benchmark_brand_precision_at_five(
    deterministic_pipeline,
    brand_name,
    facebook_url,
    campaign_goal,
    expected,
    _profile,
):
    response = await analyze_brand(
        AnalyzeRequest(
            brand_name=brand_name,
            facebook_url=facebook_url,
            campaign_goal=campaign_goal,
        )
    )

    top5 = [recommendation.creator.username for recommendation in response.recommendations[:5]]
    precision = len(set(top5).intersection(expected)) / 5

    assert len(response.recommendations) == 15
    assert precision >= 0.80, f"{brand_name} top 5: {top5}"
    assert all(
        evidence.algorithm_key == "bm25_v2_lekcut"
        for recommendation in response.recommendations
        for evidence in recommendation.scoring_evidence
        if evidence.signal == "BM25 Content Match"
    )


@pytest.mark.asyncio
async def test_three_benchmarks_have_distinct_top_fives(deterministic_pipeline):
    top_fives = []
    for brand_name, facebook_url, campaign_goal, _expected, _profile in BENCHMARKS:
        response = await analyze_brand(
            AnalyzeRequest(
                brand_name=brand_name,
                facebook_url=facebook_url,
                campaign_goal=campaign_goal,
            )
        )
        top_fives.append(tuple(r.creator.username for r in response.recommendations[:5]))

    assert len(set(top_fives)) == 3
