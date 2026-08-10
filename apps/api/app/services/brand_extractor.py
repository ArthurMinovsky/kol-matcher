"""Brand profile extraction: crawl → keywords → LLM / heuristic."""
from __future__ import annotations

from ..models.brand import BrandProfile
from ..crawlers.facebook_crawler import scrape_facebook_page
from ..crawlers.website_crawler import scrape_website
from ..safety.prompting import brand_extraction_prompt
from ..services.brand_heuristic import extract_brand_profile_heuristic
from ..services.campaign_goals import desired_style_tags_for
from ..services.keyword_extractor import get_keyword_extractor
from ..services.llm_client import chat_json


def extract_brand_profile_from_json(data: dict) -> BrandProfile:
    """Parse a raw dict (from fixture or LLM output) into BrandProfile."""
    return BrandProfile.model_validate(data)


async def extract_brand_profile(
    brand_name: str,
    facebook_url: str,
    website_url: str | None,
    campaign_goal: str,
) -> BrandProfile:
    """Extract brand profile with real crawling + Thai NLP keywords.

    Flow:
    1. Scrape Facebook page → about_text, recent_posts_text
    2. Scrape website → body_text
    3. Combine into BrandProfile.raw_text
    4. Extract keywords from raw_text using ThaiKeywordExtractor
    5. If LLM key available: send raw_text to LLM for structured extraction
    6. If no LLM: use heuristic from keywords + brand name
    """
    # ── 1. Crawl Facebook ────────────────────────────────────────────────
    fb_result = await scrape_facebook_page(facebook_url)
    fb_data = fb_result.data or {}

    # ── 2. Crawl Website ─────────────────────────────────────────────────
    web_data = {}
    if website_url:
        web_result = await scrape_website(website_url)
        web_data = web_result.data or {}

    # ── 3. Combine raw text ────────────────────────────────────────────
    raw_parts = []
    if fb_data.get("about_text"):
        raw_parts.append(fb_data["about_text"])
    if fb_data.get("recent_posts_text"):
        raw_parts.append(fb_data["recent_posts_text"])
    if web_data.get("body_text"):
        raw_parts.append(web_data["body_text"])

    raw_text = "\n\n".join(raw_parts)

    # ── 4. Extract keywords ────────────────────────────────────────────
    keywords = []
    if raw_text:
        try:
            extractor = get_keyword_extractor()
            keywords = extractor.extract_keywords(
                raw_text, max_keywords=15
            )
        except Exception:
            keywords = []

    # ── 5. Try LLM extraction ──────────────────────────────────────────
    try:
        prompt = brand_extraction_prompt(
            brand_name=brand_name,
            facebook_url=facebook_url,
            website_url=website_url,
            campaign_goal=campaign_goal,
        )
        # Enhance prompt with crawled text if available
        if raw_text:
            prompt += (
                f"\n\nExtracted content from brand sources:\n"
                f"<source_content>\n{raw_text[:3000]}\n</source_content>\n"
            )

        data = await chat_json(prompt)
        data["extraction_method"] = "llm"
        data["campaign_goal"] = campaign_goal
        data["facebook_url"] = facebook_url
        data["website_url"] = website_url
        data.setdefault("desired_style_tags", desired_style_tags_for(campaign_goal))
        data["raw_text"] = raw_text

        # Inject extracted keywords if LLM missed them
        if keywords and (
            not data.get("thai_keywords") and not data.get("english_keywords")
        ):
            thai_kw = [k for k, _ in keywords if _is_thai(k)]
            en_kw = [k for k, _ in keywords if not _is_thai(k)]
            if thai_kw:
                data["thai_keywords"] = thai_kw[:10]
            if en_kw:
                data["english_keywords"] = en_kw[:10]

        profile = BrandProfile.model_validate(data)
        if not profile.desired_style_tags:
            profile.desired_style_tags = desired_style_tags_for(campaign_goal)
        return profile

    except Exception:
        # ── 6. Heuristic fallback ──────────────────────────────────────
        profile = extract_brand_profile_heuristic(
            brand_name=brand_name,
            facebook_url=facebook_url,
            website_url=website_url,
            campaign_goal=campaign_goal,
        )
        profile.raw_text = raw_text

        # Inject keywords into heuristic profile
        if keywords:
            thai_kw = [k for k, _ in keywords if _is_thai(k)]
            en_kw = [k for k, _ in keywords if not _is_thai(k)]
            if thai_kw:
                profile.thai_keywords = thai_kw[:10]
            if en_kw:
                profile.english_keywords = en_kw[:10]
            # Update topics from keywords
            profile.topics = en_kw[:8] if en_kw else profile.topics

        return profile


def _is_thai(text: str) -> bool:
    """Check if text contains Thai characters."""
    return any("\u0e00" <= c <= "\u0e7f" for c in text)
