"""Hybrid TikTok provider orchestration."""
from __future__ import annotations

from ..models.creator import CreatorProfile
from .base import SourceResult
from .browser_tiktok import discover_browser_tiktok_creators
from .official_tiktok import discover_official_tiktok_creators


async def discover_tiktok_creators(
    keywords: list[str],
    max_results: int | None = None,
) -> SourceResult[list[CreatorProfile]]:
    """Try official access, then explicit browser access, without stealth bypasses."""
    failures: list[str] = []

    official = await discover_official_tiktok_creators(keywords, max_results=max_results)
    if official.data:
        return official
    if official.error:
        failures.append(official.error)

    browser = await discover_browser_tiktok_creators(keywords, max_results=max_results)
    if browser.data:
        return browser
    if browser.error:
        failures.append(browser.error)

    return SourceResult(
        status="FAILED",
        data=[],
        provider="tiktok_hybrid",
        error="; ".join(failures)[:500] or "No TikTok provider returned creators",
    )
