"""OpenAI-compatible LLM client supporting Typhoon then Gemini fallback."""
from __future__ import annotations

import json

import httpx

from ..config import settings


class LLMUnavailableError(RuntimeError):
    """Raised without exposing upstream provider details."""


async def chat_json(
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> dict:
    """Send a chat completion and return the parsed JSON object."""
    cfg = settings.llm_config
    if not cfg:
        raise LLMUnavailableError("LLM providers unavailable")

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{cfg['base_url'].rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("invalid completion content")
            # Strip markdown fences.
            content = content.strip()
            if content.startswith("```"):
                content = "\n".join(content.split("\n")[1:])
                if content.endswith("```"):
                    content = content[:-3].strip()
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError("completion must be a JSON object")
            return result
    except Exception as exc:
        raise LLMUnavailableError("LLM providers unavailable") from exc
