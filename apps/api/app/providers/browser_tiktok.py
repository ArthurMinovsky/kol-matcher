"""Opt-in public TikTok browser provider using Playwright or a CDP browser."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

from ..config import settings
from ..models.creator import CreatorProfile
from .base import SourceResult
from .tiktok_normalizer import normalize_browser_creators


_USERNAME_RE = re.compile(r"/(@[^/?#]+)")


async def discover_browser_tiktok_creators(
    keywords: list[str],
    max_results: int | None = None,
) -> SourceResult[list[CreatorProfile]]:
    """Collect only visible public profile links when explicitly enabled."""
    if not settings.tiktok_browser_enabled:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="tiktok_browser",
            error="Browser provider disabled by default",
        )

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="tiktok_browser",
            error="Playwright optional dependency is not installed",
        )

    limit = min(
        max_results or settings.tiktok_browser_max_creators,
        settings.tiktok_browser_max_creators,
    )
    query = quote_plus(" ".join(str(keyword).strip() for keyword in keywords[:3]))
    browser = None
    context = None
    try:
        async with async_playwright() as playwright:
            if settings.tiktok_browser_cdp_url:
                browser = await playwright.chromium.connect_over_cdp(
                    settings.tiktok_browser_cdp_url
                )
            else:
                browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(
                f"https://www.tiktok.com/search?q={query}",
                wait_until="domcontentloaded",
                timeout=settings.tiktok_browser_timeout_seconds * 1000,
            )
            links = page.locator('a[href*="/@"]')
            await links.first.wait_for(
                state="attached",
                timeout=settings.tiktok_browser_timeout_seconds * 1000,
            )

            records: list[dict[str, str]] = []
            for index in range(min(await links.count(), limit)):
                link = links.nth(index)
                href = await link.get_attribute("href")
                match = _USERNAME_RE.search(href or "")
                if not match:
                    continue
                records.append(
                    {
                        "username": match.group(1),
                        "display_name": (await link.inner_text()).strip(),
                        "url": href or "",
                    }
                )

            creators = normalize_browser_creators(records, max_results=limit)
            return SourceResult(
                status="LIVE" if creators else "PARTIAL",
                data=creators,
                provider="tiktok_browser",
                error=None if creators else "Browser search returned no public profiles",
                captured_at=datetime.now(timezone.utc),
            )
    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=[],
            provider="tiktok_browser",
            error=f"Browser provider failed: {type(exc).__name__}",
        )
    finally:
        if context is not None:
            await context.close()
        if browser is not None and not settings.tiktok_browser_cdp_url:
            await browser.close()
