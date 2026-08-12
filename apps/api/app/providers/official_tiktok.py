"""Official TikTok Research API provider."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from ..config import settings
from ..models.creator import CreatorProfile
from .base import SourceResult
from .tiktok_normalizer import normalize_research_videos


RESEARCH_VIDEO_FIELDS = ",".join(
    [
        "id",
        "create_time",
        "username",
        "region_code",
        "video_description",
        "hashtag_names",
        "view_count",
        "like_count",
        "comment_count",
        "share_count",
    ]
)


async def discover_official_tiktok_creators(
    keywords: list[str],
    max_results: int | None = None,
) -> SourceResult[list[CreatorProfile]]:
    """Query the approved TikTok Research API when credentials are configured."""
    if not settings.tiktok_research_api_token:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="tiktok_research_api",
            error="TIKTOK_RESEARCH_API_TOKEN not configured",
        )

    limit = min(
        max_results or settings.tiktok_max_creators,
        settings.tiktok_max_creators,
        100,
    )
    values = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
    if not values:
        values = ["thailand"]

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=30)
    payload: dict[str, Any] = {
        "fields": RESEARCH_VIDEO_FIELDS,
        "query": {
            "and": [
                {
                    "operation": "IN",
                    "field_name": "keyword",
                    "field_values": values[:5],
                },
                {
                    "operation": "EQ",
                    "field_name": "region_code",
                    "field_values": ["TH"],
                },
            ]
        },
        "start_date": start_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "max_count": limit,
    }

    try:
        async with httpx.AsyncClient(
            base_url=settings.tiktok_research_api_base_url.rstrip("/"),
            timeout=float(settings.tiktok_research_timeout_seconds),
        ) as client:
            response = await client.post(
                "/v2/research/video/query/",
                headers={
                    "Authorization": f"Bearer {settings.tiktok_research_api_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            body = response.json()

        items = body.get("data", {}).get("videos", [])
        if not isinstance(items, list):
            return SourceResult(
                status="FAILED",
                data=[],
                provider="tiktok_research_api",
                error="TikTok Research API returned an invalid video list",
            )
        creators = normalize_research_videos(items, max_results=limit)
        return SourceResult(
            status="LIVE" if creators else "PARTIAL",
            data=creators,
            provider="tiktok_research_api",
            error=None if creators else "TikTok Research API returned no usable creators",
            captured_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="tiktok_research_api",
            error=f"TikTok Research API request failed: {type(exc).__name__}",
        )
