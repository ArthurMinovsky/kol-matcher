"""Website text extraction using trafilatura + fallback to requests+BS4."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..providers.base import SourceResult


try:
    import trafilatura
except ImportError:
    trafilatura = None


try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


async def scrape_website(url: str) -> SourceResult[dict]:
    """Extract article text from a website.

    Primary: trafilatura (handles paywalls, boilerplate removal)
    Fallback: requests + BeautifulSoup (simple static pages)

    Returns:
        SourceResult with data keys:
        - title: str
        - description: str
        - body_text: str  (main article text)
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            await resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        return SourceResult(
            status="FAILED",
            data=None,
            provider="website",
            error=f"Website fetch failed: {exc}",
        )

    body_text = None

    # Primary: trafilatura
    if trafilatura is not None:
        try:
            body_text = trafilatura.extract(
                html, include_comments=False, include_tables=False
            )
        except Exception:
            pass

    # Fallback: BeautifulSoup (extract paragraphs)
    if not body_text and BeautifulSoup is not None:
        try:
            soup = BeautifulSoup(html, "lxml")
            # Remove script/style/nav/footer
            for tag in soup(
                ["script", "style", "nav", "footer", "header", "aside"]
            ):
                tag.decompose()
            paragraphs = [
                p.get_text(strip=True)
                for p in soup.find_all("p")
                if len(p.get_text(strip=True)) > 30
            ]
            body_text = "\n".join(paragraphs)
        except Exception:
            pass

    if not body_text:
        return SourceResult(
            status="FAILED",
            data=None,
            provider="website",
            error="Could not extract readable text from website",
        )

    # Extract title
    title = None
    description = ""
    if BeautifulSoup is not None:
        try:
            soup = BeautifulSoup(html, "lxml")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")
        except Exception:
            pass

    return SourceResult(
        status="LIVE",
        data={
            "title": title or "",
            "description": description,
            "body_text": body_text[:10000],  # cap to avoid memory issues
        },
        captured_at=datetime.now(timezone.utc),
        provider="website",
    )
