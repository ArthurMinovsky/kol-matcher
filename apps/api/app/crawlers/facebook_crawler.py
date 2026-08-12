"""Direct HTTP Facebook page crawler for public page metadata."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..providers.base import SourceResult


async def scrape_facebook_page(url: str) -> SourceResult[dict]:
    """Fetch public Facebook metadata without third-party scraping actors."""
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=None,
            provider="facebook_http",
            error=f"Direct HTTP fetch failed: {type(exc).__name__}",
        )

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc.get("content", description)
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", title)

        text_parts = [part for part in [title, description] if part]
        for paragraph in soup.find_all("p"):
            text = paragraph.get_text(strip=True)
            if len(text) > 20:
                text_parts.append(text)

        about_text = "\n".join(text_parts)
        if not about_text:
            return SourceResult(
                status="FAILED",
                data=None,
                provider="facebook_http",
                error="Facebook page returned no extractable text",
            )

        return SourceResult(
            status="LIVE",
            data={
                "page_name": title,
                "about_text": about_text,
                "category": None,
                "recent_posts_text": "",
                "follower_count": None,
            },
            captured_at=datetime.now(timezone.utc),
            provider="facebook_http",
        )
    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=None,
            provider="facebook_http",
            error=f"HTML parsing failed: {type(exc).__name__}",
        )
