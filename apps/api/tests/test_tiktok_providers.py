"""Contract tests for the hybrid TikTok provider chain."""
from __future__ import annotations

import pytest

from app.config import settings
from app.providers.tiktok import discover_tiktok_creators
from app.providers.tiktok_normalizer import normalize_research_videos


@pytest.mark.asyncio
async def test_hybrid_provider_is_disabled_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "tiktok_research_api_token", "")
    monkeypatch.setattr(settings, "tiktok_browser_enabled", False)

    result = await discover_tiktok_creators(["skincare"])

    assert result.status == "FAILED"
    assert result.provider == "tiktok_hybrid"
    assert result.data == []


def test_normalize_research_videos_aggregates_creator_posts():
    creators = normalize_research_videos(
        [
            {
                "id": "video-1",
                "create_time": 1710000000,
                "username": "thai.derma",
                "region_code": "TH",
                "video_description": "Skincare review for acne care",
                "hashtag_names": ["skincare", "acne"],
                "view_count": 10000,
                "like_count": 700,
                "comment_count": 40,
                "share_count": 20,
            },
            {
                "id": "video-2",
                "create_time": 1710000100,
                "username": "thai.derma",
                "video_description": "Serum routine",
                "hashtag_names": ["serum"],
                "view_count": 5000,
                "like_count": 300,
                "comment_count": 20,
                "share_count": 10,
            },
        ],
        max_results=10,
    )

    assert len(creators) == 1
    creator = creators[0]
    assert creator.username == "thai.derma"
    assert creator.tiktok_url == "https://www.tiktok.com/@thai.derma"
    assert creator.source_type == "live"
    assert creator.topic_tags == ["acne", "serum", "skincare"]
    assert len(creator.recent_posts) == 2
    assert creator.recent_posts[0].views == 10000
