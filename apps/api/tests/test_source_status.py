"""Tests for source status and provenance."""
from __future__ import annotations

import pytest

from app.models.api import AnalyzeRequest
from app.services.pipeline import analyze_brand


@pytest.mark.asyncio
async def test_drpong_request_uses_general_pipeline():
    """Dr. Pong is now treated as any other brand — goes through general pipeline."""
    req = AnalyzeRequest(
        brand_name="Dr. Pong",
        facebook_url="https://www.facebook.com/drpongclinic",
        campaign_goal="educational skincare",
    )
    resp = await analyze_brand(req)
    # Dr. Pong now uses the general pipeline (not fixture shortcut)
    assert resp.brand_profile.extraction_method in ("heuristic", "llm")
    assert resp.source_status.brand_extraction in ("CACHED", "PARTIAL", "LIVE")
    assert resp.source_status.tiktok in ("CACHED", "FAILED", "LIVE")
    assert resp.provider_provenance["tiktok"] == "demo_pool"
    assert len(resp.recommendations) == 15


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
    assert resp.provider_provenance["tiktok"] == "demo_pool"
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
