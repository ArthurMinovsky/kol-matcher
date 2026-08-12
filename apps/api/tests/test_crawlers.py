"""Tests for Facebook and website crawlers."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.crawlers.facebook_crawler import scrape_facebook_page
from app.crawlers.website_crawler import scrape_website


@pytest.mark.asyncio
async def test_scrape_facebook_falls_back_to_http_without_token():
    """Facebook uses the direct public HTTP path without a third-party actor."""
    with patch("app.crawlers.facebook_crawler.httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text = (
            "<!DOCTYPE html><html><head>"
            "<title>Test Page</title>"
            "<meta name='description' content='Test description'>"
            "</head><body></body></html>"
        )
        mock_resp.is_redirect = False
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp

        result = await scrape_facebook_page("https://www.facebook.com/test")
        assert result.status == "LIVE"
        assert result.provider == "facebook_http"


@pytest.mark.asyncio
async def test_scrape_website_returns_live_for_static_page():
    with patch("app.crawlers.website_crawler.httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text = (
            "<!DOCTYPE html><html><head>"
            "<title>Parameter Gelato</title>"
            "<meta name='description' content='Best gelato in Bangkok'>"
            "</head><body><article>"
            "<h1>Parameter Gelato</h1>"
            "<p>We make artisanal gelato ice cream using fresh ingredients.</p>"
            "<p>Visit our shop at Siam Paragon for delicious desserts.</p>"
            "</article></body></html>"
        )
        mock_resp.is_redirect = False
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp

        result = await scrape_website("https://parameter.co.th")
        assert result.status == "LIVE"
        assert result.data["title"] == "Parameter Gelato"
        assert "gelato" in result.data["body_text"].lower()
        assert "Bangkok" in result.data["description"]


@pytest.mark.asyncio
async def test_scrape_website_returns_failed_for_empty_page():
    with patch("app.crawlers.website_crawler.httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text = "<!DOCTYPE html><html><body></body></html>"
        mock_resp.is_redirect = False
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp

        result = await scrape_website("https://empty.com")
        assert result.status == "FAILED"
