"""Deterministic four-factor KOL scoring engine.

Match Score = 0.45 × Relevance
            + 0.25 × Engagement
            + 0.15 × ThailandRelevance
            + 0.15 × StyleFit

All component scores are in [0, 100].
Evidence Coverage is computed separately and does NOT affect Match Score.

The scoring is intentionally deterministic:
- No LLM calls at scoring time.
- Given identical inputs, identical outputs.
- All magic numbers live in config.py.
"""
from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

import numpy as np

from ..config import settings
from ..models.creator import CreatorProfile, CreatorPost
from ..models.evidence import Evidence, EvidenceCoverage

if TYPE_CHECKING:
    from ..models.brand import BrandProfile


# ── 1. Relevance Score ─────────────────────────────────────────────────────

def compute_relevance(
    creator: CreatorProfile,
    brand_embedding: list[float],
) -> float:
    """Cosine similarity between creator and brand embeddings → 0..100.

    Uses the creator's pre-computed embedding when available.
    Falls back to a keyword-overlap heuristic when embeddings are unavailable.
    """
    if creator.embedding and brand_embedding:
        return _embedding_relevance(creator.embedding, brand_embedding)
    # Keyword fallback (used when embeddings are unavailable)
    return _keyword_relevance(creator, brand_embedding)


def _embedding_relevance(creator_emb: list[float], brand_emb: list[float]) -> float:
    """Cosine similarity → 0..100 with configurable scale/offset."""
    a = np.array(creator_emb, dtype=float)
    b = np.array(brand_emb, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    similarity = float(np.dot(a, b) / (norm_a * norm_b))
    raw = similarity * settings.RELEVANCE_SIM_SCALE + settings.RELEVANCE_SIM_OFFSET
    return float(np.clip(raw, 0.0, 100.0))


def _keyword_relevance(creator: CreatorProfile, _: list[float]) -> float:
    """Topic-tag overlap heuristic — used only when embeddings are absent."""
    skincare_topics = {
        "dermatology", "skincare", "acne", "skin brightening", "UV protection",
        "anti-aging", "beauty education", "sensitive skin", "oily skin",
        "moisturizing", "hydration", "sunscreen", "skin health", "eczema",
        "ingredient science", "product review", "skincare review", "skin tips",
    }
    creator_topics = {t.lower() for t in creator.topic_tags}
    overlap = len(creator_topics & skincare_topics)
    return float(min(overlap / max(len(skincare_topics), 1) * 100 * 2.5, 100.0))


# ── 2. Engagement Score ────────────────────────────────────────────────────

def compute_engagement(
    creator: CreatorProfile,
    pool_rates: list[float] | None = None,
) -> float:
    """Median weighted engagement rate → 0..100, pool-relative when pool given.

    Per-post rate = (likes + 2*comments + 3*shares) / max(views, 1)
    Uses the median across posts, clips at ENGAGEMENT_CLIP_MAX.
    If pool_rates is provided, scores are min-max normalized across the pool.
    If no posts, falls back to follower-normalised estimate.
    If no signal, returns 0.0 (evidence layer marks unavailable).
    """
    posts = creator.recent_posts
    if posts:
        rates = [_post_engagement_rate(p) for p in posts]
        raw_rate = float(np.median(rates))
    elif creator.follower_count:
        raw_rate = 0.03  # follower-normalised fallback
    else:
        return 0.0

    clipped = min(raw_rate, settings.ENGAGEMENT_CLIP_MAX)
    if not pool_rates:
        # absolute mapping when no pool context
        return float(min(clipped / settings.ENGAGEMENT_CLIP_MAX * 100.0, 100.0))

    return _pool_relative_score(clipped, pool_rates)


def _post_engagement_rate(post: CreatorPost) -> float:
    """Engagement rate for a single post = (likes + 2*comments + 3*shares) / views."""
    if not post.views or post.views == 0:
        return 0.03
    interactions = (post.likes or 0) + 2 * (post.comments or 0) + 3 * (post.shares or 0)
    return interactions / post.views


def _pool_relative_score(value: float, pool: list[float]) -> float:
    if not pool:
        return 0.0
    lo, hi = min(pool), max(pool)
    if hi == lo:
        return 50.0
    return float(np.clip((value - lo) / (hi - lo) * 100.0, 0.0, 100.0))


def build_engagement_pool(creators: list[CreatorProfile]) -> list[float]:
    """Compute the median per-creator engagement rate for pool normalization."""
    rates: list[float] = []
    for c in creators:
        posts = c.recent_posts
        if posts:
            rates.append(float(np.median([_post_engagement_rate(p) for p in posts])))
        elif c.follower_count:
            rates.append(0.03)
    return rates


# ── 3. Thailand Relevance Score ────────────────────────────────────────────

def compute_thailand_relevance(creator: CreatorProfile) -> float:
    """Observable Thailand market relevance → 0..100.

    Weights (must sum to 100):
      Thai caption ratio:  40
      Thai hashtag count:  25
      Has Thai bio:        20
      Thailand location:   15

    All signals are observable content signals only.
    Never uses demographic assumptions.
    """
    score = 0.0

    # Signal 1: Thai caption ratio (0–40)
    caption_ratio = creator.thai_caption_ratio
    if caption_ratio is not None:
        score += caption_ratio * settings.THAILAND_CAPTION_RATIO_WEIGHT

    # Signal 2: Thai hashtag count (0–25)
    # Calibrated: 20+ hashtags = full score
    hashtag_count = creator.thai_hashtag_count
    if hashtag_count is not None:
        hashtag_score = min(hashtag_count / 20.0, 1.0) * settings.THAILAND_HASHTAG_WEIGHT
        score += hashtag_score

    # Signal 3: Thai bio (0–20)
    if creator.has_thai_bio:
        score += settings.THAILAND_BIO_WEIGHT

    # Signal 4: Thailand location in profile (0–15)
    if creator.has_thailand_location:
        score += settings.THAILAND_LOCATION_WEIGHT

    return float(min(score, 100.0))


# ── 4. Style Fit Score ─────────────────────────────────────────────────────

def compute_style_fit(creator: CreatorProfile, brand_desired_styles: list[str]) -> float:
    """Fraction of brand's desired style tags present in creator's style_tags → 0..100.

    Example: brand wants ["educational", "tutorial", "expert"].
    Creator has ["educational", "tutorial", "lifestyle"] → 2/3 = 66.7
    """
    if not brand_desired_styles:
        return 50.0  # Neutral when brand has no style preference
    desired = {s.lower() for s in brand_desired_styles}
    creator_styles = {s.lower() for s in creator.style_tags}
    overlap = len(desired & creator_styles)
    return float(overlap / len(desired) * 100.0)


# ── 5. Composite Match Score ───────────────────────────────────────────────

def compute_match_score(
    relevance: float,
    engagement: float,
    thailand_relevance: float,
    style_fit: float,
) -> float:
    """Weighted sum of the four component scores → 0..100.

    Weights are defined in Settings and must sum to 1.0.
    """
    return (
        relevance * settings.RELEVANCE_WEIGHT
        + engagement * settings.ENGAGEMENT_WEIGHT
        + thailand_relevance * settings.THAILAND_WEIGHT
        + style_fit * settings.STYLE_WEIGHT
    )


# ── 6. Evidence Coverage ───────────────────────────────────────────────────

def compute_evidence_coverage(creator: CreatorProfile) -> tuple[float, EvidenceCoverage]:
    """Information completeness measure — does NOT affect Match Score.

    Component weights (must sum to 100):
      bio_context:     20
      captions_posts:  25
      engagement:      25
      thailand:        20
      metadata:        10
    """
    # Bio context (0–20)
    bio_score = settings.EVIDENCE_BIO_WEIGHT if creator.bio else 0.0

    # Captions / posts (0–25)
    post_count = len(creator.recent_posts)
    captions_score = min(post_count / 5.0, 1.0) * settings.EVIDENCE_CAPTIONS_WEIGHT

    # Engagement data (0–25)
    has_engagement = any(
        p.views is not None or p.likes is not None
        for p in creator.recent_posts
    )
    engagement_score = settings.EVIDENCE_ENGAGEMENT_WEIGHT if has_engagement else 0.0

    # Thailand signals (0–20)
    thai_signals_present = sum([
        creator.thai_caption_ratio is not None,
        creator.thai_hashtag_count is not None,
        creator.has_thai_bio is not None,
        creator.has_thailand_location is not None,
    ])
    thailand_score = (thai_signals_present / 4.0) * settings.EVIDENCE_THAILAND_WEIGHT

    # Metadata (0–10)
    meta_present = sum([
        creator.follower_count is not None,
        creator.location is not None,
        creator.verified is not None,
    ])
    metadata_score = (meta_present / 3.0) * settings.EVIDENCE_METADATA_WEIGHT

    breakdown = EvidenceCoverage(
        bio_context=round(bio_score, 2),
        captions_posts=round(captions_score, 2),
        engagement=round(engagement_score, 2),
        thailand_signals=round(thailand_score, 2),
        profile_metadata=round(metadata_score, 2),
    )
    return round(breakdown.total, 2), breakdown


# ── 7. Recommendation Confidence ───────────────────────────────────────────

def compute_recommendation_confidence(
    evidence_coverage: float,
    match_score: float,
) -> str:
    """Derive confidence label from evidence coverage only.

    HIGH   = coverage >= 70 and match_score >= 60
    MEDIUM = coverage >= 40 or match_score >= 45
    LOW    = otherwise
    """
    if evidence_coverage >= 70 and match_score >= 60:
        return "HIGH"
    if evidence_coverage >= 40 or match_score >= 45:
        return "MEDIUM"
    return "LOW"


# ── 8. Build Evidence List ─────────────────────────────────────────────────

def build_scoring_evidence(
    creator: CreatorProfile,
    relevance: float,
    engagement: float,
    thailand_relevance: float,
    style_fit: float,
) -> list[Evidence]:
    """Build a human-readable evidence list for the recommendation."""
    evidence: list[Evidence] = []

    # Relevance
    evidence.append(Evidence(
        signal="Content Relevance",
        value=f"{relevance:.1f}/100",
        source="embedding" if creator.embedding else "keyword_overlap",
        weight=settings.RELEVANCE_WEIGHT * 100,
        available=True,
    ))

    # Engagement
    evidence.append(Evidence(
        signal="Engagement Rate",
        value=f"{engagement:.1f}/100",
        source="recent_posts" if creator.recent_posts else "follower_estimate",
        weight=settings.ENGAGEMENT_WEIGHT * 100,
        available=bool(creator.recent_posts) or creator.follower_count is not None,
    ))

    # Thailand relevance
    evidence.append(Evidence(
        signal="Thailand Market Signals",
        value=f"{thailand_relevance:.1f}/100",
        source="bio+posts+location",
        weight=settings.THAILAND_WEIGHT * 100,
        available=any([
            creator.thai_caption_ratio is not None,
            creator.thai_hashtag_count is not None,
            creator.has_thai_bio,
        ]),
    ))

    # Style fit
    evidence.append(Evidence(
        signal="Style Fit",
        value=f"{style_fit:.1f}/100",
        source="style_tags",
        weight=settings.STYLE_WEIGHT * 100,
        available=bool(creator.style_tags),
    ))

    # Follower count (informational)
    evidence.append(Evidence(
        signal="Follower Count",
        value=f"{creator.follower_count:,}" if creator.follower_count else "unavailable",
        source="profile_metadata",
        weight=0.0,
        available=creator.follower_count is not None,
    ))

    return evidence
