"""Regression tests for the Typhoon-only JSON client."""
from __future__ import annotations

import pytest

from app.config import settings
from app.services import llm_client


@pytest.mark.asyncio
async def test_typhoon_client_uses_requested_model_and_parses_fenced_json(
    monkeypatch,
):
    monkeypatch.setattr(settings, "typhoon_api_key", "test-key")
    monkeypatch.setattr(settings, "typhoon_model", "typhoon-v2.5-30b-a3b-instruct")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    captured: dict[str, object] = {}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {"message": {"content": "```json\n{\"answer\": \"ok\"}\n```"}}
                ]
            }

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, *, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _Response()

    monkeypatch.setattr(llm_client.httpx, "AsyncClient", lambda **_kwargs: _Client())

    result = await llm_client.chat_json("Return JSON")

    assert result == {"answer": "ok"}
    assert captured["url"] == "https://api.opentyphoon.ai/v1/chat/completions"
    assert captured["json"]["model"] == "typhoon-v2.5-30b-a3b-instruct"
    assert captured["json"]["max_tokens"] == 2048


@pytest.mark.asyncio
async def test_typhoon_client_returns_sanitized_unavailable_error(monkeypatch):
    monkeypatch.setattr(settings, "typhoon_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_api_key", "")

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            raise RuntimeError("internal upstream detail")

    monkeypatch.setattr(llm_client.httpx, "AsyncClient", lambda **_kwargs: _Client())

    with pytest.raises(llm_client.LLMUnavailableError, match="LLM providers unavailable"):
        await llm_client.chat_json("Return JSON")
