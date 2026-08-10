"""Tests for LLM-as-judge relevance scoring."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.services.llm_judge import judge_relevance


@pytest.mark.asyncio
async def test_judge_relevance_returns_score_and_reasoning():
    mock_result = {
        "score": 85.0,
        "reasoning": "Strong food content alignment with gelato brand",
    }
    with patch(
        "app.services.llm_judge.chat_json", new=AsyncMock(return_value=mock_result)
    ):
        result = await judge_relevance(
            "Brand: Parameter\nTopics: gelato, ice cream, dessert",
            "Creator: food blogger\nBio: Reviews Bangkok desserts",
        )
        assert result["score"] == 85.0
        assert "food" in result["reasoning"]


@pytest.mark.asyncio
async def test_judge_relevance_uses_cache():
    mock_result = {
        "score": 85.0,
        "reasoning": "Strong food content alignment",
    }
    with patch(
        "app.services.llm_judge.chat_json", new=AsyncMock(return_value=mock_result)
    ) as mock:
        brand = "Brand: Parameter"
        creator = "Creator: food blogger"
        await judge_relevance(brand, creator)
        await judge_relevance(brand, creator)
        assert mock.call_count == 1


@pytest.mark.asyncio
async def test_judge_relevance_fallback_on_error():
    with patch(
        "app.services.llm_judge.chat_json", new=AsyncMock(side_effect=Exception("LLM error"))
    ):
        result = await judge_relevance("Brand: X", "Creator: Y")
        assert result["score"] == 50.0
        assert "unavailable" in result["reasoning"].lower()


@pytest.mark.asyncio
async def test_judge_relevance_clamps_score():
    # Use unique inputs to avoid cache conflicts
    with patch(
        "app.services.llm_judge.chat_json", new=AsyncMock(return_value={"score": 150.0, "reasoning": "Way too high"})
    ):
        result = await judge_relevance("Brand: ClampTest1", "Creator: X")
        assert result["score"] == 100.0

    with patch(
        "app.services.llm_judge.chat_json", new=AsyncMock(return_value={"score": -50.0, "reasoning": "Way too low"})
    ):
        result = await judge_relevance("Brand: ClampTest2", "Creator: X")
        assert result["score"] == 0.0
