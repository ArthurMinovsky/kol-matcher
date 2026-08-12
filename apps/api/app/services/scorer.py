"""Hybrid KOL scoring engine with deterministic component calculations.

Match Score = 0.20 × BM25 Relevance
            + 0.25 × LLM Judge Relevance
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

from typing import TYPE_CHECKING

import numpy as np

from ..config import settings
from ..models.creator import CreatorProfile, CreatorPost
from ..models.evidence import Evidence, EvidenceCoverage
from .bm25_matcher import BM25Match

if TYPE_CHECKING:
    from ..models.brand import BrandProfile


# ── 1. Relevance Score ─────────────────────────────────────────────────────

def compute_relevance(match: BM25Match) -> float:
    """Return the normalized BM25 relevance produced by the selected matcher."""
    return float(np.clip(match.normalized_score, 0.0, 100.0))


def compute_combined_relevance(bm25_relevance: float, llm_relevance: float) -> float:
    """Combine BM25 and LLM relevance inside the 45% relevance bucket."""
    bm25 = float(np.clip(bm25_relevance, 0.0, 100.0))
    llm = float(np.clip(llm_relevance, 0.0, 100.0))
    return float(
        np.clip(
            bm25 * settings.RELEVANCE_BM25_BUCKET_WEIGHT
            + llm * settings.RELEVANCE_LLM_BUCKET_WEIGHT,
            0.0,
            100.0,
        )
    )


def compute_effective_relevance(
    bm25_relevance: float,
    llm_relevance: float,
    *,
    llm_available: bool,
) -> float:
    """Return relevance after excluding unavailable judge evidence.

    The displayed unavailable judge score remains neutral at 50, but it must
    not contribute to ordering. When unavailable, the relevance bucket is
    renormalized to the available BM25 signal.
    """
    if not llm_available:
        return float(np.clip(bm25_relevance, 0.0, 100.0))
    return compute_combined_relevance(bm25_relevance, llm_relevance)


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
    bm25_relevance: float,
    llm_relevance: float,
    engagement: float,
    thailand_relevance: float,
    style_fit: float,
    llm_available: bool = True,
) -> float:
    """Weighted sum of effective relevance and remaining scores → 0..100.

    When the judge is unavailable, its displayed neutral score is excluded and
    the relevance bucket is renormalized to BM25. Weights are defined in
    Settings and must sum to 1.0.
    """
    effective_relevance = compute_effective_relevance(
        bm25_relevance,
        llm_relevance,
        llm_available=llm_available,
    )
    return (
        effective_relevance * settings.RELEVANCE_WEIGHT
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
    bm25_match: BM25Match,
    *,
    bm25_relevance: float | None = None,
    llm_relevance: float = 50.0,
    llm_available: bool = False,
) -> list[Evidence]:
    """Build a human-readable evidence list for the recommendation."""
    evidence: list[Evidence] = []

    bm25_score = (
        bm25_match.normalized_score
        if bm25_relevance is None
        else bm25_relevance
    )
    bm25_available = bm25_match.raw_score > 0 or bool(bm25_match.matched_keywords)

    # Combined/effective relevance
    combined_source = (
        "hybrid_relevance" if llm_available else "bm25_relevance_renormalized"
    )
    evidence.append(Evidence(
        signal="Combined Relevance",
        value=f"{relevance:.1f}/100",
        source=combined_source,
        weight=settings.RELEVANCE_WEIGHT * 100,
        available=bm25_available or llm_available,
        algorithm_key=bm25_match.algorithm_key,
        raw_score=relevance,
        matched_keywords=bm25_match.matched_keywords,
    ))

    # BM25 relevance
    evidence.append(Evidence(
        signal="BM25 Content Match",
        value=f"{bm25_score:.1f}/100",
        source="rank_bm25",
        weight=settings.BM25_RELEVANCE_WEIGHT * 100,
        available=bm25_available,
        algorithm_key=bm25_match.algorithm_key,
        raw_score=bm25_match.raw_score,
        matched_keywords=bm25_match.matched_keywords,
    ))

    # LLM judge relevance
    evidence.append(Evidence(
        signal="LLM Judge Relevance",
        value=f"{llm_relevance:.1f}/100",
        source="llm_judge",
        weight=settings.LLM_RELEVANCE_WEIGHT * 100,
        available=llm_available,
        raw_score=llm_relevance,
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
