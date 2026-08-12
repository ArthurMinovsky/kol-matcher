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

from ..models.evidence import EvidenceCoverage
from ..models.api import AnalyzeResponse, Recommendation, SourceStatusMap
from ..models.brand import BrandProfile
from ..models.creator import CreatorProfile
from ..providers.fixture_loader import (
    load_drpong_brand_profile,
    load_drpong_creators,
)
from ..services.bm25_matcher import ALGORITHM_KEY, BM25Match, score_creators
from ..services.brand_heuristic import build_brand_analysis_rationale
from ..services.llm_judge import judge_relevance_batch
from ..services.scorer import (
    build_engagement_pool,
    build_scoring_evidence,
    compute_engagement,
    compute_effective_relevance,
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
    if not creator.raw_text:
        limitations.append("BM25 relevance uses structured profile fields because raw content is unavailable.")
    if creator.thai_caption_ratio is None:
        limitations.append("Thai caption ratio unavailable — Thailand score may be underestimated.")
    return limitations


def _brand_summary(brand: BrandProfile) -> str:
    return "\n".join(
        [
            f"Brand: {brand.brand_name}",
            f"Industry: {brand.industry or 'unknown'}",
            f"Campaign goal: {brand.campaign_goal or 'not provided'}",
            f"Topics: {', '.join(brand.topics)}",
            f"Products: {', '.join(brand.products)}",
            f"Description: {brand.description or 'not provided'}",
            f"Raw source text: {brand.raw_text or 'not provided'}",
        ]
    )


def _creator_summary(creator: CreatorProfile) -> str:
    posts = []
    for post in creator.recent_posts[:10]:
        hashtags = " ".join(post.hashtags)
        posts.append(f"{post.caption or ''} {hashtags}".strip())
    return "\n".join(
        [
            f"Creator: @{creator.username}",
            f"Bio: {creator.bio or 'not provided'}",
            f"Topics: {', '.join(creator.topic_tags)}",
            f"Styles: {', '.join(creator.style_tags)}",
            f"Recent posts: {' | '.join(posts) if posts else 'not provided'}",
        ]
    )


def _neutral_judge_result() -> dict[str, float | str | bool]:
    return {
        "score": 50.0,
        "reasoning": "LLM judge unavailable; neutral relevance fallback used.",
        "available": False,
    }


def _build_rationale(
    creator: CreatorProfile,
    brand: BrandProfile,
    bm25_relevance: float,
    bm25_match: BM25Match,
    judge_result: dict[str, float | str | bool],
) -> str:
    if judge_result.get("available"):
        return str(judge_result.get("reasoning") or "LLM judge supplied no rationale.")

    matched = ", ".join(bm25_match.matched_keywords[:5])
    if matched:
        fit = f"matched terms include {matched}"
    else:
        fit = "no direct BM25 terms were matched"
    return (
        f"This recommendation reflects {fit} for {brand.brand_name}; "
        f"BM25 relevance is {bm25_relevance:.0f}/100 from observable profile and post text. "
        "The LLM judge was unavailable, so its displayed relevance component uses a neutral 50; "
        "effective relevance is renormalized to the available BM25 signal."
    )


async def score_and_rank(
    creators: list[CreatorProfile],
    brand: BrandProfile,
    top_n: int = _DEFAULT_TOP_N,
    source_type_label: str = "synthetic",
    algorithm_key: str = ALGORITHM_KEY,
    use_llm_judge: bool = False,
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

    if not brand.analysis_rationale:
        brand.analysis_rationale = build_brand_analysis_rationale(brand)

    # Build one BM25 corpus score before composite ranking.
    bm25_matches = score_creators(brand, unique, algorithm_key=algorithm_key)
    match_by_username: dict[str, BM25Match] = {
        match.username.lower().strip(): match for match in bm25_matches
    }

    # Build engagement pool once for pool-relative scaling
    pool_rates = build_engagement_pool(unique) if unique else []

    judge_by_username: dict[str, dict[str, float | str | bool]] = {
        creator.username.lower().strip(): _neutral_judge_result()
        for creator in unique
    }
    if use_llm_judge and unique:
        try:
            judge_results = await judge_relevance_batch(
                _brand_summary(brand),
                [_creator_summary(creator) for creator in unique],
            )
            for creator, judge_result in zip(unique, judge_results):
                judge_by_username[creator.username.lower().strip()] = judge_result
        except Exception:
            # A judge outage must not discard deterministic recommendations.
            pass

    scored: list[
        tuple[
            CreatorProfile,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            EvidenceCoverage,
            BM25Match,
            dict[str, float | str | bool],
        ]
    ] = []
    for creator in unique:
        try:
            bm25_match = match_by_username[creator.username.lower().strip()]
            bm25_relevance = compute_relevance(bm25_match)
            judge_result = judge_by_username[creator.username.lower().strip()]
            llm_relevance = float(judge_result.get("score", 50.0))
            llm_available = bool(judge_result.get("available"))
            relevance = compute_effective_relevance(
                bm25_relevance,
                llm_relevance,
                llm_available=llm_available,
            )

            engagement = compute_engagement(creator, pool_rates)
            thailand = compute_thailand_relevance(creator)
            style_fit = compute_style_fit(creator, brand.desired_style_tags)
            match_score = compute_match_score(
                bm25_relevance,
                llm_relevance,
                engagement,
                thailand,
                style_fit,
                llm_available=llm_available,
            )
            coverage, coverage_breakdown = compute_evidence_coverage(creator)
            scored.append(
                (
                    creator,
                    match_score,
                    relevance,
                    bm25_relevance,
                    llm_relevance,
                    engagement,
                    thailand,
                    style_fit,
                    coverage,
                    coverage_breakdown,
                    bm25_match,
                    judge_result,
                )
            )
        except Exception:
            # Malformed creator: fail safe, skip
            continue

    # Tie-breaker chain
    scored.sort(
        key=lambda x: (
            -x[1],  # match_score DESC
            -x[2],  # relevance DESC
            -x[8],  # evidence coverage DESC
            x[0].username.lower(),  # username ASC
        )
    )

    recommendations: list[Recommendation] = []
    for rank, (
        creator,
        match_score,
        relevance,
        bm25_relevance,
        llm_relevance,
        engagement,
        thailand,
        style_fit,
        coverage,
        coverage_breakdown,
        bm25_match,
        judge_result,
    ) in enumerate(scored[:top_n], start=1):
        confidence = compute_recommendation_confidence(coverage, match_score)
        scoring_evidence = build_scoring_evidence(
            creator,
            relevance,
            engagement,
            thailand,
            style_fit,
            bm25_match=bm25_match,
            bm25_relevance=bm25_relevance,
            llm_relevance=llm_relevance,
            llm_available=bool(judge_result.get("available")),
        )

        rec = Recommendation(
            rank=rank,
            creator=creator,
            match_score=round(match_score, 2),
            bm25_relevance=round(bm25_relevance, 2),
            llm_relevance=round(llm_relevance, 2),
            relevance=round(relevance, 2),
            engagement=round(engagement, 2),
            thailand_relevance=round(thailand, 2),
            style_fit=round(style_fit, 2),
            evidence_coverage=round(coverage, 2),
            evidence_breakdown=coverage_breakdown,
            audience_verification="Unavailable",
            recommendation_confidence=confidence,
            rationale=_build_rationale(
                creator,
                brand,
                bm25_relevance,
                bm25_match,
                judge_result,
            ),
            explanation=_build_explanation(
                creator, brand, relevance, engagement, thailand, style_fit
            ),
            limitations=_build_limitations(creator),
            scoring_evidence=scoring_evidence,
        )
        recommendations.append(rec)

    return recommendations


async def run_fixture_pipeline(top_n: int = _DEFAULT_TOP_N) -> AnalyzeResponse:
    """Run the complete Dr. Pong fixture demo pipeline.

    Steps:
    1. Load brand profile from fixture.
    2. Load 40 synthetic creators.
    3. Score and rank deterministically with BM25.
    4. Return top_n recommendations.

    No external service calls. Deterministic given identical fixture data.
    """
    brand = load_drpong_brand_profile()
    creators = load_drpong_creators()

    recommendations = await score_and_rank(
        creators=creators,
        brand=brand,
        top_n=top_n,
        source_type_label="cached",
        use_llm_judge=False,
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
        provider_provenance={
            "facebook": "fixture",
            "website": "fixture",
            "tiktok": "demo_pool",
            "brand_extraction": "fixture",
        },
        limitations=[
            "All creator data is synthetic and provided for demonstration purposes only.",
            "Audience demographics are not observable from public TikTok data — never assumed.",
            "Engagement data reflects synthetic post metrics, not live TikTok API data.",
        ],
    )
