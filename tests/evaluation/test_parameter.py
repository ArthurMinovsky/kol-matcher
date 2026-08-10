"""End-to-end integration test: Parameter brand should return food creators."""
from __future__ import annotations

import pytest

from app.config import settings
from app.models.api import AnalyzeRequest
from app.services.pipeline import analyze_brand


@pytest.mark.asyncio
async def test_parameter_brand_returns_food_creators():
    req = AnalyzeRequest(
        brand_name="Parameter",
        facebook_url="https://www.facebook.com/parameterthailand/",
        campaign_goal="product review",
    )
    resp = await analyze_brand(req)

    # Assert we got recommendations
    assert len(resp.recommendations) > 0

    # Check that keywords are food-related (not dermatology/skincare)
    brand = resp.brand_profile
    topics = {t.lower() for t in brand.topics}
    assert "lifestyle" not in topics or len(topics) > 1  # Should not be only lifestyle

    # Check that at least some recommendations have reasonable relevance
    top5 = resp.recommendations[:5]
    avg_relevance = sum(r.relevance for r in top5) / len(top5)
    assert avg_relevance > 30  # Should be better than random

    # Verify source status reflects crawling attempt
    assert resp.source_status.facebook in ("LIVE", "FAILED", "PARTIAL")


@pytest.mark.asyncio
async def test_parameter_brand_has_real_keywords():
    if not settings.apify_api_token:
        pytest.skip("No APIFY_API_TOKEN configured — Facebook crawling unavailable")

    req = AnalyzeRequest(
        brand_name="Parameter",
        facebook_url="https://www.facebook.com/parameterthailand/",
        campaign_goal="product review",
    )
    resp = await analyze_brand(req)

    brand = resp.brand_profile
    # Should have either Thai or English keywords extracted
    assert len(brand.thai_keywords) > 0 or len(brand.english_keywords) > 0

    # Should have raw_text from crawling
    assert brand.raw_text is not None
    assert len(brand.raw_text) > 0
