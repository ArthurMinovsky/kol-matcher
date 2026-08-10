"""Campaign goal → desired style tags."""
from __future__ import annotations


_GOAL_STYLE_MAP: dict[str, list[str]] = {
    "product review": ["review", "tutorial", "short-demo"],
    "awareness": ["lifestyle", "entertainment", "ugc"],
    "educational skincare": ["educational", "expert", "tutorial"],
    "educational": ["educational", "expert", "tutorial"],
    "conversion": ["review", "before-after", "short-demo"],
    "launch": ["review", "unboxing", "short-demo"],
}


def desired_style_tags_for(goal: str) -> list[str]:
    """Return style tags for a campaign goal (case-insensitive, partial match)."""
    key = goal.strip().lower()
    for k, tags in _GOAL_STYLE_MAP.items():
        if k in key or key in k:
            return tags
    # Fallback: split goal into plausible style tags
    return [t.strip() for t in key.replace(",", " ").split() if t.strip()] or ["ugc"]
