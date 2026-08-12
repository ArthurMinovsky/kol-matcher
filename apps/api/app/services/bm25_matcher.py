"""Versioned corpus-level BM25 matcher for KOL relevance."""
from __future__ import annotations

from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from ..models.brand import BrandProfile
from ..models.creator import CreatorProfile
from .text_processing import tokenize_text


ALGORITHM_KEY = "bm25_v2_lekcut"


@dataclass(frozen=True)
class BM25Match:
    username: str
    normalized_score: float
    raw_score: float
    matched_keywords: list[str]
    algorithm_key: str = ALGORITHM_KEY


def score_creators(
    brand: BrandProfile,
    creators: list[CreatorProfile],
    algorithm_key: str = ALGORITHM_KEY,
) -> list[BM25Match]:
    """Score all creators against one brand query using corpus-level BM25."""
    if algorithm_key != ALGORITHM_KEY:
        raise ValueError(f"Unsupported matching algorithm: {algorithm_key}")
    if not creators:
        return []

    documents = [_creator_document_tokens(creator) for creator in creators]
    query_tokens = _brand_query_tokens(brand)

    if query_tokens and any(documents):
        bm25 = BM25Okapi(documents)
        raw_scores = [max(float(score), 0.0) for score in bm25.get_scores(query_tokens)]
    else:
        raw_scores = [0.0] * len(creators)

    max_raw = max(raw_scores, default=0.0)
    if max_raw > 0:
        normalized_scores = [score / max_raw * 100.0 for score in raw_scores]
    else:
        normalized_scores = _structured_topic_fallback(brand, creators)

    query_set = set(query_tokens)
    matches = [
        BM25Match(
            username=creator.username,
            normalized_score=round(normalized, 6),
            raw_score=round(raw, 6),
            matched_keywords=sorted(query_set.intersection(document_tokens)),
        )
        for creator, document_tokens, raw, normalized in zip(
            creators, documents, raw_scores, normalized_scores
        )
    ]
    return sorted(
        matches,
        key=lambda match: (
            -match.normalized_score,
            -match.raw_score,
            match.username.lower(),
        ),
    )


def _brand_query_tokens(brand: BrandProfile) -> list[str]:
    parts = [
        brand.brand_name,
        brand.industry or "",
        " ".join(brand.topics),
        " ".join(brand.thai_keywords),
        " ".join(brand.english_keywords),
        " ".join(brand.products),
        brand.raw_text or "",
    ]
    return tokenize_text(" ".join(parts))


def _creator_document_tokens(creator: CreatorProfile) -> list[str]:
    parts = [creator.bio or "", " ".join(creator.topic_tags)]
    for post in creator.recent_posts:
        parts.extend(
            [post.caption or "", " ".join(post.hashtags)]
        )
    if creator.raw_text:
        parts.append(creator.raw_text)
    return tokenize_text(" ".join(parts))


def _structured_topic_fallback(
    brand: BrandProfile,
    creators: list[CreatorProfile],
) -> list[float]:
    """Use explicit structured topics only when BM25 has no positive signal."""
    brand_topics = set(tokenize_text(" ".join(brand.topics + brand.english_keywords + brand.thai_keywords)))
    if not brand_topics:
        return [0.0] * len(creators)

    scores: list[float] = []
    for creator in creators:
        creator_topics = set(tokenize_text(" ".join(creator.topic_tags)))
        overlap = len(brand_topics.intersection(creator_topics))
        scores.append(overlap / len(brand_topics) * 100.0)
    return scores
