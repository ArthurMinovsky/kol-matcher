"""Offline brand profile extraction from brand name using an industry dictionary."""
from __future__ import annotations

from ..models.brand import BrandProfile
from .campaign_goals import desired_style_tags_for


_INDUSTRY_MAP: dict[str, dict] = {
    "beauty": {
        "industry": "Beauty & Skincare",
        "topics": ["skincare", "makeup", "beauty", "self-care", "dermatology"],
        "thai_keywords": ["ผิว", "สกินแคร์", "ความงาม", "เมคอัพ", "เซรั่ม"],
        "english_keywords": ["skincare", "beauty", "makeup", "serum", "glow"],
        "content_styles": ["review", "tutorial", "before-after"],
    },
    "food": {
        "industry": "Food & Beverage",
        "topics": ["food", "cooking", "restaurant", "street food", "recipe"],
        "thai_keywords": ["อาหาร", "ร้านอาหาร", "สตรีทฟู้ด", "สูตรอาหาร", "กิน"],
        "english_keywords": ["food", "restaurant", "recipe", "street food", "cooking"],
        "content_styles": ["review", "mukbang", "tutorial", "lifestyle"],
    },
    "travel": {
        "industry": "Travel & Hospitality",
        "topics": ["travel", "hotel", "tourism", "destination", "itinerary"],
        "thai_keywords": ["ท่องเที่ยว", "โรงแรม", "ที่พัก", "เที่ยว", "กระเป๋าเดินทาง"],
        "english_keywords": ["travel", "hotel", "trip", "destination", "vlog"],
        "content_styles": ["vlog", "lifestyle", "review", "ugc"],
    },
    "fashion": {
        "industry": "Fashion & Apparel",
        "topics": ["fashion", "style", "outfit", "clothing", "trend"],
        "thai_keywords": ["แฟชั่น", "สไตล์", "เสื้อผ้า", "แต่งตัว", "ลุค"],
        "english_keywords": ["fashion", "style", "outfit", "clothing", "trend"],
        "content_styles": ["lifestyle", "lookbook", "review", "ugc"],
    },
    "fitness": {
        "industry": "Fitness & Wellness",
        "topics": ["fitness", "workout", "health", "wellness", "nutrition"],
        "thai_keywords": ["ฟิตเนส", "ออกกำลังกาย", "สุขภาพ", "โภชนาการ", "คาร์ดิโอ"],
        "english_keywords": ["fitness", "workout", "health", "wellness", "gym"],
        "content_styles": ["tutorial", "motivation", "lifestyle", "review"],
    },
    "tech": {
        "industry": "Technology & Gadgets",
        "topics": ["technology", "gadget", "review", "smartphone", "app"],
        "thai_keywords": ["เทคโนโลยี", "แกดเจ็ต", "รีวิว", "สมาร์ทโฟน", "แอป"],
        "english_keywords": ["tech", "gadget", "review", "smartphone", "app"],
        "content_styles": ["review", "tutorial", "unboxing", "short-demo"],
    },
    "finance": {
        "industry": "Finance & Insurance",
        "topics": ["finance", "investment", "insurance", "money", "credit"],
        "thai_keywords": ["การเงิน", "ลงทุน", "ประกัน", "เงิน", "บัตรเครดิต"],
        "english_keywords": ["finance", "investment", "insurance", "money", "credit"],
        "content_styles": ["educational", "expert", "review", "news"],
    },
    "gaming": {
        "industry": "Gaming & Esports",
        "topics": ["gaming", "esports", "mobile game", "stream", "review"],
        "thai_keywords": ["เกม", "อีสปอร์ต", "สตรีม", "รีวิวเกม", "มือถือ"],
        "english_keywords": ["gaming", "esports", "stream", "game review", "mobile"],
        "content_styles": ["entertainment", "review", "stream", "lifestyle"],
    },
}


# Manual overrides for known brands (exact or substring match)
_BRAND_OVERRIDES: dict[str, str] = {
    "dr. pong": "beauty",
    "drpong": "beauty",
    "dr pong": "beauty",
    "parameter": "food",
    "traveloka": "travel",
}

# Additional trigger words that hint at industry (not in _INDUSTRY_MAP keys)
_EXTRA_TRIGGERS: dict[str, str] = {
    "clinic": "beauty",
    "dermatology": "beauty",
    "dermatologist": "beauty",
    "aesthetic": "beauty",
    "spa": "beauty",
    "salon": "beauty",
    "gelato": "food",
    "ice cream": "food",
    "dessert": "food",
    "bakery": "food",
    "cafe": "food",
    "coffee": "food",
    "bistro": "food",
    "kitchen": "food",
    "chef": "food",
    "michelin": "food",
    "brewery": "food",
    "hotel": "travel",
    "resort": "travel",
    "airline": "travel",
    "tour": "travel",
    "hostel": "travel",
    "boutique": "fashion",
    "apparel": "fashion",
    "wardrobe": "fashion",
    "sneaker": "fashion",
    "jewelry": "fashion",
    "gym": "fitness",
    "yoga": "fitness",
    "crossfit": "fitness",
    "nutrition": "fitness",
    "protein": "fitness",
    "app": "tech",
    "software": "tech",
    "startup": "tech",
    "fintech": "finance",
    "bank": "finance",
    "crypto": "finance",
    "broker": "finance",
    "esports": "gaming",
    "game": "gaming",
    "streamer": "gaming",
    "console": "gaming",
}


def build_brand_analysis_rationale(profile: BrandProfile) -> str:
    """Explain the profile using only supplied brand and source signals."""
    industry = profile.industry or "general/lifestyle"
    topics = ", ".join(profile.topics[:4]) if profile.topics else "available profile terms"
    if profile.raw_text:
        basis = "the supplied brand details and crawled public source text"
    else:
        basis = "the supplied brand name and campaign goal"
    goal = profile.campaign_goal or "the requested campaign"
    return (
        f"This profile is based on {basis} for the {goal} campaign, "
        f"mapping the brand to {industry} topics such as {topics}."
    )


def _infer_industry(brand_name: str, campaign_goal: str = "") -> str | None:
    """Infer industry from brand name, manual overrides, and campaign goal."""
    lowered_name = brand_name.lower()
    lowered_goal = campaign_goal.lower()

    # 1. Manual brand overrides (exact/substring)
    for pattern, industry in _BRAND_OVERRIDES.items():
        if pattern in lowered_name:
            return industry

    # 2. Check _INDUSTRY_MAP keywords in brand name
    for industry, data in _INDUSTRY_MAP.items():
        if industry in lowered_name:
            return industry
        for kw in data["english_keywords"]:
            if kw in lowered_name:
                return industry
        for kw in data["thai_keywords"]:
            if kw in lowered_name:
                return industry

    # 3. Check extra triggers in brand name
    for trigger, industry in _EXTRA_TRIGGERS.items():
        if trigger in lowered_name:
            return industry

    # 4. Check campaign goal for industry keywords (strong signal)
    for industry, data in _INDUSTRY_MAP.items():
        if industry in lowered_goal:
            return industry
        for kw in data["english_keywords"]:
            if kw in lowered_goal:
                return industry
        for kw in data["thai_keywords"]:
            if kw in lowered_goal:
                return industry

    # 5. Check extra triggers in campaign goal
    for trigger, industry in _EXTRA_TRIGGERS.items():
        if trigger in lowered_goal:
            return industry

    return None


def extract_brand_profile_heuristic(
    brand_name: str,
    facebook_url: str,
    website_url: str | None,
    campaign_goal: str,
) -> BrandProfile:
    industry_key = _infer_industry(brand_name, campaign_goal)
    data = _INDUSTRY_MAP.get(industry_key, {})
    profile = BrandProfile(
        brand_name=brand_name,
        industry=data.get("industry", "General / Lifestyle"),
        description=f"{brand_name} brand ({data.get('industry', 'General / Lifestyle')}).",
        products=[],
        audience_hypothesis=(
            f"Hypothesis: consumers interested in {data.get('industry', 'general lifestyle')} "
            "(inferred from brand name only)."
        ),
        topics=data.get("topics", ["lifestyle", "entertainment"]),
        tone="Approachable",
        content_styles=data.get("content_styles", ["lifestyle", "ugc"]),
        thai_keywords=data.get("thai_keywords", ["ไลฟ์สไตล์"]),
        english_keywords=data.get("english_keywords", ["lifestyle"]),
        campaign_goal=campaign_goal,
        website_url=website_url,
        facebook_url=facebook_url,
        desired_style_tags=desired_style_tags_for(campaign_goal),
        extraction_method="heuristic",
    )
    profile.analysis_rationale = build_brand_analysis_rationale(profile)
    return profile
