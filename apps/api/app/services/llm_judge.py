"""LLM-as-judge for brand-creator relevance scoring.

Caches results to avoid repeated LLM calls for the same brand-creator pair.
Supports batch scoring (up to N creators in one prompt) for efficiency.
"""
from __future__ import annotations

from ..config import settings
from ..services.llm_client import chat_json


# In-memory cache (keyed by hash of brand summary + creator summary)
_judge_cache: dict[str, dict] = {}


async def judge_relevance(brand_summary: str, creator_summary: str) -> dict:
    """Score brand-creator relevance using LLM rubric.

    Returns: {"score": float (0-100), "reasoning": str}

    Caches results to avoid repeated LLM calls.
    """
    cache_key = _make_cache_key(brand_summary, creator_summary)
    if cache_key in _judge_cache:
        return _judge_cache[cache_key]

    prompt = _judge_prompt(brand_summary, creator_summary)

    try:
        result = await chat_json(
            prompt, temperature=0.0, max_tokens=settings.llm_judge_max_tokens
        )
        score = float(result.get("score", 50.0))
        score = max(0.0, min(100.0, score))
        reasoning = str(result.get("reasoning", ""))

        output = {"score": score, "reasoning": reasoning}
        _judge_cache[cache_key] = output
        return output
    except Exception:
        # Fallback: return neutral score if LLM fails
        return {
            "score": 50.0,
            "reasoning": "LLM judge unavailable — using neutral fallback.",
        }


async def judge_relevance_batch(
    brand_summary: str,
    creator_summaries: list[str],
) -> list[dict]:
    """Batch relevance scoring for efficiency.

    Scores up to `llm_judge_batch_size` creators in a single prompt.
    """
    batch_size = settings.llm_judge_batch_size
    results: list[dict] = []

    for i in range(0, len(creator_summaries), batch_size):
        batch = creator_summaries[i : i + batch_size]
        prompt = _judge_prompt_batch(brand_summary, batch, start_index=i)

        try:
            result = await chat_json(
                prompt,
                temperature=0.0,
                max_tokens=settings.llm_judge_max_tokens,
            )
            scores = result.get("scores", [])
            for j, score_entry in enumerate(scores):
                if i + j < len(creator_summaries):
                    score = float(score_entry.get("score", 50.0))
                    score = max(0.0, min(100.0, score))
                    reasoning = str(score_entry.get("reasoning", ""))
                    results.append({"score": score, "reasoning": reasoning})
        except Exception:
            # Fallback for failed batch
            for _ in batch:
                results.append(
                    {"score": 50.0, "reasoning": "Batch LLM judge unavailable."}
                )

    return results[: len(creator_summaries)]


def _make_cache_key(brand_summary: str, creator_summary: str) -> str:
    import hashlib

    combined = f"{brand_summary}|||{creator_summary}"
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def _condense_brand(brand) -> str:
    """Create a condensed summary of brand for the judge prompt."""
    parts = [
        f"Brand: {brand.brand_name}",
        f"Industry: {brand.industry or 'unknown'}",
        f"Topics: {', '.join(brand.topics[:8])}",
        f"Products: {', '.join(brand.products[:5])}",
        f"Campaign goal: {brand.campaign_goal}",
    ]
    return "\n".join(parts)


def _condense_creator(creator) -> str:
    """Create a condensed summary of creator for the judge prompt."""
    parts = [
        f"Creator: @{creator.username}",
        f"Bio: {creator.bio or 'N/A'}",
        f"Topics: {', '.join(creator.topic_tags[:8])}",
        f"Style: {', '.join(creator.style_tags[:5])}",
    ]
    if creator.recent_posts:
        post_topics = [
            p.caption[:80]
            for p in creator.recent_posts[:3]
            if p.caption
        ]
        parts.append(f"Recent posts: {' | '.join(post_topics)}")
    return "\n".join(parts)


def _judge_prompt(brand_summary: str, creator_summary: str) -> str:
    return f"""You are an expert KOL (Key Opinion Leader) marketing analyst.

Your task: Score how relevant a TikTok creator is for a brand's campaign.

## BRAND
{brand_summary}

## CREATOR
{creator_summary}

## SCORING RUBRIC

Score the relevance on a scale of 0-100:

- 90-100: PERFECT MATCH — Creator's content directly aligns with brand's products, topics, and campaign goal. Would drive strong campaign results.
- 70-89: STRONG MATCH — Significant overlap. Creator's audience and content style fit the brand well.
- 50-69: MODERATE MATCH — Some overlap exists, but not ideal. May work with adjustments.
- 30-49: WEAK MATCH — Minimal connection. Unlikely to drive meaningful results.
- 0-29: POOR MATCH — No meaningful connection between creator and brand.

## RULES
- Base your score ONLY on the information provided above.
- Do not invent demographics or audience data.
- Consider: topic overlap, product relevance, content style alignment, language match.

Return ONLY a JSON object:
{{"score": <number 0-100>, "reasoning": "<one sentence explaining the score>"}}

JSON:
"""


def _judge_prompt_batch(
    brand_summary: str, creator_summaries: list[str], start_index: int = 0
) -> str:
    creators_block = "\n\n".join(
        f"### CREATOR {start_index + i + 1}\n{summary}"
        for i, summary in enumerate(creator_summaries)
    )

    return f"""You are an expert KOL marketing analyst.

Score each creator's relevance to the brand using the rubric below.

## BRAND
{brand_summary}

{creators_block}

## SCORING RUBRIC
- 90-100: PERFECT MATCH — Direct alignment with brand products, topics, and campaign goal.
- 70-89: STRONG MATCH — Significant overlap in audience and content style.
- 50-69: MODERATE MATCH — Some overlap, but not ideal.
- 30-49: WEAK MATCH — Minimal connection.
- 0-29: POOR MATCH — No meaningful connection.

Return ONLY a JSON object with a "scores" array:
{{"scores": [
  {{"score": <number>, "reasoning": "<one sentence>"}},
  ...
]}}

JSON:
"""
