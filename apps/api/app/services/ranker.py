"""Recommendation orchestrator — produces a ranked list of Recommendation objects.

This module ties together:
- Fixture loading (providers/fixture_loader.py)
- Deterministic scoring (services/scorer.py)
- Response model construction (models/api.py)

The fixture path does not call any external service.
The live path (P1) additionally calls the scraper and brand extractor.

Invariants:
- Recommendations are sorted by match_score descending, then relevance,
  evidence coverage, and canonical username for deterministic tie-breaking.
- Top-N is configurable (default 15).
- Confidence and audience_verification are derived, not user-input.
"""
from __future__ import annotations

from ..models.api import AnalyzeResponse, Recommendation, SourceStatusMap
from ..models.brand import BrandProfile
from ..models.creator import CreatorProfile
from ..providers.fixture_loader import (
    inject_fixture_embeddings,
    load_drpong_brand_profile,
    load_drpong_creators,
    load_drpong_embeddings,
)
from ..services.scorer import (
    build_engagement_pool,
    build_scoring_evidence,
    compute_engagement,
    compute_evidence_coverage,
    compute_match_score,
    compute_recommendation_confidence,
    compute_relevance,
    compute_style_fit,
    compute_thailand_relevance,
)

_DEFAULT_TOP_N = 15


def _build_explanation(
    creator: CreatorProfile,
    brand: BrandProfile,
    relevance: float,
    engagement: float,
    thailand: float,
    style_fit: float,
) -> str:
    """Build a deterministic, template-based explanation string."""
    top_topics = ", ".join(creator.topic_tags[:3]) if creator.topic_tags else "general content"
    return (
        f"@{creator.username} creates content about {top_topics}, "
        f"aligning with {brand.brand_name}'s focus on {brand.campaign_goal}. "
        f"Relevance: {relevance:.0f}/100, Engagement: {engagement:.0f}/100, "
        f"Thailand signals: {thailand:.0f}/100, Style fit: {style_fit:.0f}/100."
    )


def _build_limitations(creator: CreatorProfile) -> list[str]:
    """Build a list of data limitation strings for this creator."""
    limitations: list[str] = []
    if creator.source_type == "synthetic":
        limitations.append("Creator data is synthetic — metrics are for demonstration only.")
    if creator.source_type == "live":
        limitations.append("Creator data sourced live; metrics are point-in-time and may be incomplete.")
    if not creator.recent_posts:
        limitations.append("Engagement scored from follower estimate only — no post data.")
    if not creator.embedding:
        limitations.append("Relevance scored from keyword overlap — embedding not available.")
    if creator.thai_caption_ratio is None:
        limitations.append("Thai caption ratio unavailable — Thailand score may be underestimated.")
    return limitations


def score_and_rank(
    creators: list[CreatorProfile],
    brand: BrandProfile,
    brand_embedding: list[float] | None,
    top_n: int = _DEFAULT_TOP_N,
    source_type_label: str = "synthetic",
) -> list[Recommendation]:
    """Score and rank creators deterministically.

    Tie-breaker chain:
      1. match_score DESC
      2. relevance DESC
      3. evidence coverage DESC
      4. canonical username ASC

    Malformed creators are skipped safely.
    """
    # Deduplicate by canonical username
    seen: set[str] = set()
    unique: list[CreatorProfile] = []
    for c in creators:
        key = c.username.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    # Build engagement pool once for pool-relative scaling
    pool_rates = build_engagement_pool(unique) if unique else []

    scored: list[tuple[CreatorProfile, float, float, float, float, float, float]] = []
    for creator in unique:
        try:
            relevance = compute_relevance(creator, brand_embedding or [])
            engagement = compute_engagement(creator, pool_rates)
            thailand = compute_thailand_relevance(creator)
            style_fit = compute_style_fit(creator, brand.desired_style_tags)
            match_score = compute_match_score(relevance, engagement, thailand, style_fit)
            coverage, coverage_breakdown = compute_evidence_coverage(creator)
            scored.append((creator, match_score, relevance, engagement, thailand, style_fit, coverage))
        except Exception:
            # Malformed creator: fail safe, skip
            continue

    # Tie-breaker chain
    scored.sort(
        key=lambda x: (
            -x[1],  # match_score DESC
            -x[2],  # relevance DESC
            -x[6],  # evidence coverage DESC
            x[0].username.lower(),  # username ASC
        )
    )

    recommendations: list[Recommendation] = []
    for rank, (creator, match_score, relevance, engagement, thailand, style_fit, coverage) in enumerate(
        scored[:top_n], start=1
    ):
        confidence = compute_recommendation_confidence(coverage, match_score)
        scoring_evidence = build_scoring_evidence(creator, relevance, engagement, thailand, style_fit)

        rec = Recommendation(
            rank=rank,
            creator=creator,
            match_score=round(match_score, 2),
            relevance=round(relevance, 2),
            engagement=round(engagement, 2),
            thailand_relevance=round(thailand, 2),
            style_fit=round(style_fit, 2),
            evidence_coverage=round(coverage, 2),
            evidence_breakdown=coverage_breakdown,
            audience_verification="Unavailable",  # Audience demographics not observable
            recommendation_confidence=confidence,
            explanation=_build_explanation(creator, brand, relevance, engagement, thailand, style_fit),
            limitations=_build_limitations(creator),
            scoring_evidence=scoring_evidence,
        )
        recommendations.append(rec)

    return recommendations


def run_fixture_pipeline(top_n: int = _DEFAULT_TOP_N) -> AnalyzeResponse:
    """Run the complete Dr. Pong fixture demo pipeline.

    Steps:
    1. Load brand profile from fixture.
    2. Load 40 synthetic creators.
    3. Inject pre-computed embeddings.
    4. Score and rank deterministically.
    5. Return top_n recommendations.

    No external service calls. Deterministic given identical fixture data.
    """
    brand = load_drpong_brand_profile()
    creators = load_drpong_creators()

    # Inject embeddings so the relevance scorer can use cosine similarity
    inject_fixture_embeddings(creators)

    embeddings_data = load_drpong_embeddings()
    brand_embedding: list[float] | None = embeddings_data.get("brand_embedding")

    recommendations = score_and_rank(
        creators=creators,
        brand=brand,
        brand_embedding=brand_embedding,
        top_n=top_n,
        source_type_label="cached",
    )

    return AnalyzeResponse(
        brand_profile=brand,
        recommendations=recommendations,
        source_status=SourceStatusMap(
            website="CACHED",
            facebook="CACHED",
            tiktok="CACHED",
            brand_extraction="CACHED",
        ),
        limitations=[
            "All creator data is synthetic and provided for demonstration purposes only.",
            "Audience demographics are not observable from public TikTok data — never assumed.",
            "Engagement data reflects synthetic post metrics, not live TikTok API data.",
        ],
    )
