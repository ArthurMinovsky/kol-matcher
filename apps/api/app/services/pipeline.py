"""General analyze pipeline: brand + creators + ranking."""
from __future__ import annotations

from ..models.api import AnalyzeRequest, AnalyzeResponse, SourceStatusMap
from ..config import settings
from ..providers.base import SourceResult
from ..providers.fixture_loader import load_demo_pool_creators
from ..providers.tiktok import discover_tiktok_creators
from ..services.brand_extractor import extract_brand_profile
from ..services.ranker import score_and_rank


async def analyze_brand(req: AnalyzeRequest) -> AnalyzeResponse:
    """Run the real KOL matching pipeline with live TikTok discovery.

    Flow:
    1. Crawl Facebook + Website → extract brand profile + keywords
    2. Discover real TikTok creators via the configured official/browser providers
    3. Score creators with keyword matching + LLM judge
    4. Return top 15 ranked recommendations
    """
    # ── 1. Brand extraction ──────────────────────────────────────────────
    brand = await extract_brand_profile(
        brand_name=req.brand_name,
        facebook_url=req.facebook_url,
        website_url=req.website_url,
        campaign_goal=req.campaign_goal,
    )

    brand_extraction_status = "LIVE" if brand.extraction_method == "llm" else "PARTIAL"
    if not brand.raw_text:
        brand_extraction_status = "CACHED"  # no crawling data at all

    # ── 2. Build search queries ──────────────────────────────────────────
    # Combine keywords, topics, and brand name into rich search queries
    search_terms = []

    # Primary: English keywords (most useful for TikTok search)
    if brand.english_keywords:
        search_terms.extend(brand.english_keywords[:8])

    # Secondary: Thai keywords
    if brand.thai_keywords:
        search_terms.extend(brand.thai_keywords[:4])

    # Tertiary: topics
    if brand.topics and len(search_terms) < 5:
        search_terms.extend(brand.topics[:5])

    # Fallback: brand name + campaign goal
    if len(search_terms) < 3:
        search_terms.extend([req.brand_name, req.campaign_goal])

    # ── 3. Discover TikTok creators ───────────────────────────────────────
    creator_result = await discover_tiktok_creators(search_terms)

    # Fallback to demo pool if discovery failed
    creators = creator_result.data or load_demo_pool_creators()
    if creator_result.status == "FAILED" or not creators:
        creators = load_demo_pool_creators()
        creator_result = SourceResult(
            status="CACHED",
            data=creators,
            provider="demo_pool",
        )

    if creator_result.status == "FAILED":
        for c in creators:
            c.source_type = "synthetic"

    # ── 4. Build raw_text for each creator (bio + posts) ──────────────────
    for c in creators:
        parts = []
        if c.bio:
            parts.append(c.bio)
        for p in c.recent_posts:
            if p.caption:
                parts.append(p.caption)
            # Also include hashtags as they indicate topic focus
            if p.hashtags:
                parts.append(" ".join(f"#{h}" for h in p.hashtags))
        c.raw_text = "\n".join(parts) if parts else None

    # ── 5. Score and rank ────────────────────────────────────────────────
    recommendations = await score_and_rank(
        creators=creators,
        brand=brand,
        top_n=15,
        source_type_label="live" if creator_result.status == "LIVE" else "synthetic",
        algorithm_key=settings.matching_algorithm,
        use_llm_judge=True,
    )

    # ── 6. Source status ─────────────────────────────────────────────────
    has_facebook_text = bool(brand.raw_text and req.facebook_url)
    has_website_text = bool(
        brand.raw_text and req.website_url and req.website_url in brand.raw_text[:500]
    )

    facebook_status = "LIVE" if has_facebook_text else "FAILED"
    website_status = "LIVE" if has_website_text else "FAILED"

    # If we have real text but no LLM, mark as PARTIAL
    if brand.raw_text and brand.extraction_method == "heuristic":
        brand_extraction_status = "PARTIAL"
        facebook_status = "LIVE" if has_facebook_text else "PARTIAL"
        website_status = "LIVE" if has_website_text else "PARTIAL"

    limitations = [
        "Creator data is sourced live from TikTok unless discovery failed.",
        "Audience demographics are not observable from public TikTok data.",
    ]
    if brand.extraction_method == "heuristic":
        limitations.append(
            "Brand profile was inferred from crawled text and brand name — "
            "medium confidence."
        )
    if not brand.raw_text:
        limitations.append(
            "Could not extract text from Facebook page or website. "
            "Brand profile may be inaccurate."
        )
    if creator_result.status in ("FAILED", "CACHED"):
        limitations.append(
            "TikTok creator discovery failed or used demo pool — "
            "recommendations may not reflect live TikTok data."
        )

    return AnalyzeResponse(
        brand_profile=brand,
        recommendations=recommendations,
        source_status=SourceStatusMap(
            website=website_status,
            facebook=facebook_status,
            tiktok=creator_result.status,
            brand_extraction=brand_extraction_status,
        ),
        provider_provenance={
            "facebook": "facebook_http",
            "website": "website" if req.website_url else "not_requested",
            "tiktok": creator_result.provider,
            "brand_extraction": brand.extraction_method,
        },
        limitations=limitations,
    )
