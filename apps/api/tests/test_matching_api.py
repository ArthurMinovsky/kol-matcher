"""Tests for the versioned matching API used by Langflow."""
from __future__ import annotations

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_matching_score_returns_bm25_order_and_evidence_fields():
    payload = {
        "brand_profile": {
            "brand_name": "Traveloka",
            "topics": ["travel", "hotel"],
            "english_keywords": ["travel", "hotel"],
        },
        "creators": [
            {
                "username": "travel_creator",
                "bio": "Thailand travel and hotel reviews",
                "topic_tags": ["travel", "hotel"],
            },
            {
                "username": "beauty_creator",
                "bio": "Skincare and makeup tutorials",
                "topic_tags": ["beauty", "skincare"],
            },
        ],
        "algorithm_key": "bm25_v2_lekcut",
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/matching/score", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm_key"] == "bm25_v2_lekcut"
    assert body["matches"][0]["username"] == "travel_creator"
    assert body["matches"][0]["algorithm_key"] == "bm25_v2_lekcut"
    assert body["matches"][0]["matched_keywords"]
    assert "raw_score" in body["matches"][0]


@pytest.mark.asyncio
async def test_matching_score_rejects_unknown_algorithm_key():
    payload = {
        "brand_profile": {"brand_name": "Traveloka"},
        "creators": [{"username": "creator"}],
        "algorithm_key": "unknown_v1",
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/matching/score", json=payload)

    assert response.status_code == 422
