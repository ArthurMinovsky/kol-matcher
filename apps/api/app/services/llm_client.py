"""OpenAI-compatible LLM client supporting Typhoon then Gemini fallback."""
from __future__ import annotations

import json

import httpx

from ..config import settings


async def chat_json(
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> dict:
    """Send a chat completion and return the parsed JSON object."""
    cfg = settings.llm_config
    if not cfg:
        raise RuntimeError("No LLM API key configured")

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

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{cfg['base_url'].rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        # Strip markdown fences
        content = content.strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = content[:-3].strip()
        return json.loads(content)
