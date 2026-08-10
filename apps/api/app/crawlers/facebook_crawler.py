"""Facebook page crawler using Apify cloud actor.

Uses apify/facebook-pages-scraper which handles anti-bot, CAPTCHA,
and dynamic loading without requiring local Playwright.
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import settings
from ..providers.base import SourceResult


APIFY_API_BASE = "https://api.apify.com/v2"


async def scrape_facebook_page(url: str) -> SourceResult[dict]:
    """Scrape a public Facebook page and return structured data.

    Returns:
        SourceResult with data keys:
        - page_name: str
        - about_text: str  (page description + about section)
        - category: str
        - recent_posts_text: str  (concatenated recent post captions)
        - follower_count: int | None
    """
    if not settings.apify_api_token:
        return SourceResult(
            status="FAILED",
            data=None,
            provider="apify_facebook",
            error="APIFY_API_TOKEN not configured",
        )

    try:
        async with httpx.AsyncClient(
            timeout=float(settings.apify_facebook_timeout_seconds)
        ) as client:
            # Start actor run
            run_resp = await client.post(
                f"{APIFY_API_BASE}/acts/{settings.apify_facebook_actor}/runs",
                params={"token": settings.apify_api_token},
                json={
                    "startUrls": [{"url": url}],
                    "resultsLimit": 20,
                    "maxPosts": 10,
                },
            )
            run_resp.raise_for_status()
            run_id = run_resp.json()["data"]["id"]

            # Poll for completion
            dataset_id = await _poll_run(client, run_id)
            if not dataset_id:
                return SourceResult(
                    status="FAILED",
                    data=None,
                    provider="apify_facebook",
                    error="Facebook scraper run did not produce a dataset",
                )

            # Fetch dataset items
            items_resp = await client.get(
                f"{APIFY_API_BASE}/datasets/{dataset_id}/items",
                params={"token": settings.apify_api_token, "clean": "true"},
            )
            items_resp.raise_for_status()
            items = items_resp.json()

        if not items:
            return SourceResult(
                status="FAILED",
                data=None,
                provider="apify_facebook",
                error="Facebook scraper returned no items",
            )

        # Normalize first page result
        page = items[0]
        about_text = " ".join(
            filter(
                None,
                [
                    page.get("pageName"),
                    page.get("about"),
                    page.get("description"),
                ],
            )
        )

        recent_posts_text = " ".join(
            p.get("text", "") for p in page.get("posts", [])[:10]
        )

        data = {
            "page_name": page.get("pageName"),
            "about_text": about_text,
            "category": page.get("category"),
            "recent_posts_text": recent_posts_text,
            "follower_count": _int_or_none(page.get("followers")),
        }

        return SourceResult(
            status="LIVE",
            data=data,
            captured_at=datetime.now(timezone.utc),
            provider="apify_facebook",
        )

    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=None,
            provider="apify_facebook",
            error=f"Facebook scraping error: {exc}",
        )


async def _poll_run(
    client: httpx.AsyncClient, run_id: str, max_attempts: int = 30
) -> str | None:
    import asyncio

    for _ in range(max_attempts):
        resp = await client.get(
            f"{APIFY_API_BASE}/acts/{settings.apify_facebook_actor}/runs/{run_id}",
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


def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None
