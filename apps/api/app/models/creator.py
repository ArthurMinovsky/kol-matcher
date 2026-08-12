"""Creator domain models."""
from __future__ import annotations

from pydantic import BaseModel


class CreatorPost(BaseModel):
    """A single TikTok post from a creator."""

    post_id: str | None = None
    caption: str | None = None
    hashtags: list[str] = []
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    posted_at: str | None = None  # ISO date string
    language: str | None = None  # "th", "en", "mixed", etc.


class CreatorProfile(BaseModel):
    """Structured representation of a TikTok creator.

    Rules:
    - Never use 0 to represent unavailable data — use None.
    - follower_count and following_count are from public profile.
    - engagement data comes from observable post metrics only.
    """

    username: str  # Canonical username (used as deduplication key)
    display_name: str | None = None
    bio: str | None = None
    tiktok_url: str | None = None

    # Profile metadata
    follower_count: int | None = None
    following_count: int | None = None
    total_likes: int | None = None
    verified: bool | None = None
    location: str | None = None

    # Content intelligence (derived from posts + bio)
    topic_tags: list[str] = []
    style_tags: list[str] = []  # e.g. ["review", "tutorial", "lifestyle"]
    language_primary: str | None = None  # "th", "en", "mixed"

    # Thailand market signals (observable, not demographic)
    thai_caption_ratio: float | None = None   # 0.0–1.0
    thai_hashtag_count: int | None = None
    has_thai_bio: bool | None = None
    has_thailand_location: bool | None = None

    # Recent posts (used for engagement scoring)
    recent_posts: list[CreatorPost] = []

    # Raw combined text from bio + post captions for BM25 matching
    raw_text: str | None = None

    # Provenance
    source_type: str = "synthetic"  # "synthetic" | "cached" | "live"
    relevance_label: int | None = None  # 2=relevant, 1=plausible, 0=irrelevant (evaluation only)
