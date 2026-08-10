"""Brand profile extraction: fixture / LLM / heuristic."""
from __future__ import annotations

from ..models.brand import BrandProfile
from ..safety.prompting import brand_extraction_prompt
from ..services.brand_heuristic import extract_brand_profile_heuristic
from ..services.campaign_goals import desired_style_tags_for
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
    """Return BrandProfile using LLM when keys exist, else heuristic fallback."""
    prompt = brand_extraction_prompt(
        brand_name=brand_name,
        facebook_url=facebook_url,
        website_url=website_url,
        campaign_goal=campaign_goal,
    )
    try:
        data = await chat_json(prompt)
        data["extraction_method"] = "llm"
        data["campaign_goal"] = campaign_goal
        data["facebook_url"] = facebook_url
        data["website_url"] = website_url
        data.setdefault("desired_style_tags", desired_style_tags_for(campaign_goal))
        profile = BrandProfile.model_validate(data)
        # Enforce desired style mapping even if LLM omitted it
        if not profile.desired_style_tags:
            profile.desired_style_tags = desired_style_tags_for(campaign_goal)
        return profile
    except Exception:
        return extract_brand_profile_heuristic(
            brand_name=brand_name,
            facebook_url=facebook_url,
            website_url=website_url,
            campaign_goal=campaign_goal,
        )
