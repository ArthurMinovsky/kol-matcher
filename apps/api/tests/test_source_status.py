"""Tests for source status and provenance."""
from __future__ import annotations

import pytest

from app.models.api import AnalyzeRequest
from app.services.pipeline import analyze_brand


@pytest.mark.asyncio
async def test_drpong_request_returns_cached_status():
    req = AnalyzeRequest(
        brand_name="Dr. Pong",
        facebook_url="https://www.facebook.com/drpongclinic",
        campaign_goal="educational skincare",
    )
    resp = await analyze_brand(req)
    assert resp.source_status.tiktok == "CACHED"
    assert resp.source_status.brand_extraction == "CACHED"
    assert resp.brand_profile.extraction_method == "fixture"


@pytest.mark.asyncio
async def test_heuristic_request_returns_demo_pool():
    req = AnalyzeRequest(
        brand_name="Yummy Food Brand",
        facebook_url="https://www.facebook.com/yummyfood",
        campaign_goal="product review",
    )
    resp = await analyze_brand(req)
    assert resp.brand_profile.extraction_method == "heuristic"
    assert resp.source_status.brand_extraction in ("CACHED", "PARTIAL")
    assert len(resp.recommendations) == 15
    assert all(r.creator.source_type == "synthetic" for r in resp.recommendations)


@pytest.mark.asyncio
async def test_invalid_facebook_url_rejected_by_validator():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AnalyzeRequest(
            brand_name="X",
            facebook_url="not-a-url",
            campaign_goal="awareness",
        )
