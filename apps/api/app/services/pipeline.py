"""General analyze pipeline: brand + creators + ranking."""
from __future__ import annotations

from ..models.api import AnalyzeRequest, AnalyzeResponse, SourceStatusMap, is_drpong_request
from ..providers.apify import discover_tiktok_creators
from ..providers.base import SourceResult
from ..providers.fixture_loader import load_demo_pool_creators
from ..services.brand_extractor import extract_brand_profile
from ..services.ranker import run_fixture_pipeline, score_and_rank


async def analyze_brand(req: AnalyzeRequest) -> AnalyzeResponse:
    """Run the generalized KOL matching pipeline."""
    # Dr. Pong deterministic path
    if is_drpong_request(req):
        return await run_fixture_pipeline(top_n=15)

    # Brand extraction
    brand = await extract_brand_profile(
        brand_name=req.brand_name,
        facebook_url=req.facebook_url,
        website_url=req.website_url,
        campaign_goal=req.campaign_goal,
    )
    brand_extraction_status = "LIVE" if brand.extraction_method == "llm" else "CACHED"

    # Creator acquisition
    if brand.extraction_method == "llm":
        keywords = brand.thai_keywords + brand.english_keywords
        creator_result = await discover_tiktok_creators(keywords)
    else:
        # Heuristic path uses demo pool directly (no live call)
        creators = load_demo_pool_creators()
        creator_result = SourceResult(
            status="CACHED",
            data=creators,
            provider="demo_pool",
        )

    creators = creator_result.data or load_demo_pool_creators()
    if creator_result.status == "FAILED":
        for c in creators:
            c.source_type = "synthetic"

    # Build raw_text for each creator from bio + posts (for keyword extraction)
    for c in creators:
        parts = []
        if c.bio:
            parts.append(c.bio)
        for p in c.recent_posts:
            if p.caption:
                parts.append(p.caption)
        c.raw_text = "\n".join(parts)

    recommendations = await score_and_rank(
        creators=creators,
        brand=brand,
        brand_embedding=None,  # general path uses keyword + LLM relevance
        top_n=15,
        source_type_label="live" if creator_result.status == "LIVE" else "synthetic",
    )

    # Determine source status from real crawling results
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
        "Creator data is synthetic/demo pool unless Apify returned LIVE records.",
        "Audience demographics are not observable from public TikTok data.",
    ]
    if brand.extraction_method == "heuristic":
        limitations.append(
            "Brand profile was inferred from crawled text and brand name — "
            "low confidence."
        )
    if not brand.raw_text:
        limitations.append(
            "Could not extract text from Facebook page or website. "
            "Brand profile may be inaccurate."
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
        limitations=limitations,
    )
