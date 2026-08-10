"""Apify TikTok scraper provider adapter."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import settings
from ..models.creator import CreatorPost, CreatorProfile
from .base import SourceResult


APIFY_API_BASE = "https://api.apify.com/v2"


async def discover_tiktok_creators(
    keywords: list[str],
    max_results: int | None = None,
) -> SourceResult[list[CreatorProfile]]:
    """Run the configured Apify TikTok actor and normalize to CreatorProfile.

    Search queries are constructed from brand keywords. The actor is
    expected to accept a list of search keywords; if it does not, this
    adapter gracefully returns FAILED.
    """
    if not settings.apify_api_token:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="apify",
            error="APIFY_API_TOKEN not configured",
        )

    max_results = max_results or settings.apify_max_creators
    query = " ".join(keywords[:5]) if keywords else "tiktok thailand"

    try:
        async with httpx.AsyncClient(timeout=float(settings.apify_timeout_seconds)) as client:
            # Start actor run
            run_resp = await client.post(
                f"{APIFY_API_BASE}/acts/{settings.apify_tiktok_actor}/runs",
                params={"token": settings.apify_api_token},
                json={"queries": [query], "resultsPerPage": max_results, "maxResults": max_results},
            )
            run_resp.raise_for_status()
            run_id = run_resp.json()["data"]["id"]

            # Poll for completion
            dataset_id = await _poll_run(client, run_id)
            if not dataset_id:
                return SourceResult(
                    status="FAILED",
                    data=[],
                    provider="apify",
                    error="Apify run did not produce a dataset",
                )

            # Fetch dataset items
            items_resp = await client.get(
                f"{APIFY_API_BASE}/datasets/{dataset_id}/items",
                params={"token": settings.apify_api_token, "clean": "true"},
            )
            items_resp.raise_for_status()
            items = items_resp.json()

        creators = [_normalize_item(item) for item in items[:max_results]]
        creators = [c for c in creators if c is not None]
        return SourceResult(
            status="LIVE" if creators else "PARTIAL",
            data=creators,
            captured_at=datetime.now(timezone.utc),
            provider="apify",
            error=None if creators else "Apify returned no usable creator records",
        )
    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="apify",
            error=f"Apify error: {exc}",
        )


async def _poll_run(client: httpx.AsyncClient, run_id: str, max_attempts: int = 30) -> str | None:
    import asyncio

    for _ in range(max_attempts):
        resp = await client.get(
            f"{APIFY_API_BASE}/acts/{settings.apify_tiktok_actor}/runs/{run_id}",
            params={"token": settings.apify_api_token},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        if data.get("status") in ("SUCCEEDED", "READY"):
            return data.get("defaultDatasetId")
        if data.get("status") in ("FAILED", "TIMED-OUT", "ABORTED"):
            return None
        await asyncio.sleep(2.0)
    return None


def _normalize_item(item: dict) -> CreatorProfile | None:
    """Normalize one Apify TikTok item into CreatorProfile, or None if unusable."""
    username = item.get("authorMeta", {}).get("name") or item.get("username") or item.get("author")
    if not username:
        return None
    author = item.get("authorMeta", item)
    return CreatorProfile(
        username=str(username),
        display_name=author.get("nickName") or author.get("nickname"),
        bio=author.get("signature") or author.get("bio"),
        tiktok_url=f"https://www.tiktok.com/@{username}",
        follower_count=_int_or_none(author.get("fans")),
        following_count=_int_or_none(author.get("following")),
        total_likes=_int_or_none(author.get("heart")),
        verified=_bool_or_none(author.get("verified")),
        topic_tags=[],
        style_tags=[],
        recent_posts=[_normalize_post(item)] if "text" in item else [],
        source_type="live",
    )


def _normalize_post(item: dict) -> CreatorPost:
    return CreatorPost(
        post_id=str(item.get("id", "")),
        caption=item.get("text") or item.get("caption"),
        hashtags=[str(t).lstrip("#") for t in item.get("hashtags", [])],
        views=_int_or_none(item.get("playCount")),
        likes=_int_or_none(item.get("diggCount")),
        comments=_int_or_none(item.get("commentCount")),
        shares=_int_or_none(item.get("shareCount")),
        posted_at=item.get("createTimeISO"),
    )


def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _bool_or_none(value):
    if value is None:
        return None
    return bool(value)
