"""Normalize official and browser TikTok records into CreatorProfile objects."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..models.creator import CreatorPost, CreatorProfile


def normalize_research_videos(
    items: list[dict[str, Any]],
    max_results: int,
) -> list[CreatorProfile]:
    """Aggregate TikTok Research API video records by creator username."""
    creators: dict[str, CreatorProfile] = {}
    topic_sets: dict[str, set[str]] = {}

    for item in items:
        username = _clean_username(item.get("username"))
        if not username:
            continue

        if username not in creators:
            creators[username] = CreatorProfile(
                username=username,
                display_name=username,
                tiktok_url=f"https://www.tiktok.com/@{username}",
                source_type="live",
                recent_posts=[],
            )
            topic_sets[username] = set()

        creator = creators[username]
        hashtags = _string_list(item.get("hashtag_names"))
        topic_sets[username].update(tag.lower() for tag in hashtags if tag)
        post = _normalize_research_post(item, hashtags)
        if post:
            creator.recent_posts.append(post)

        region = str(item.get("region_code") or "").upper()
        if region == "TH":
            creator.has_thailand_location = True
        if hashtags:
            thai_tags = sum(_contains_thai(tag) for tag in hashtags)
            creator.thai_hashtag_count = (creator.thai_hashtag_count or 0) + thai_tags

    result = list(creators.values())
    for username, creator in creators.items():
        creator.topic_tags = sorted(topic_sets[username])
        creator.raw_text = _creator_raw_text(creator)
        creator.thai_caption_ratio = _thai_caption_ratio(creator)
        creator.has_thai_bio = _contains_thai(creator.bio or "")

    return result[: max(0, max_results)]


def normalize_browser_creators(
    items: list[dict[str, Any]],
    max_results: int,
) -> list[CreatorProfile]:
    """Normalize public browser search links without inventing metrics."""
    creators: list[CreatorProfile] = []
    seen: set[str] = set()
    for item in items:
        username = _clean_username(item.get("username"))
        if not username or username in seen:
            continue
        seen.add(username)
        creators.append(
            CreatorProfile(
                username=username,
                display_name=str(item.get("display_name") or username),
                tiktok_url=str(
                    item.get("url") or f"https://www.tiktok.com/@{username}"
                ),
                source_type="live",
                raw_text=str(item.get("display_name") or username),
            )
        )
        if len(creators) >= max_results:
            break
    return creators


def _normalize_research_post(
    item: dict[str, Any],
    hashtags: list[str],
) -> CreatorPost | None:
    caption = str(item.get("video_description") or "").strip()
    if not caption and not hashtags:
        return None
    return CreatorPost(
        post_id=_string_or_none(item.get("id")),
        caption=caption or None,
        hashtags=hashtags,
        views=_int_or_none(item.get("view_count")),
        likes=_int_or_none(item.get("like_count")),
        comments=_int_or_none(item.get("comment_count")),
        shares=_int_or_none(item.get("share_count")),
        posted_at=_timestamp_to_iso(item.get("create_time")),
    )


def _creator_raw_text(creator: CreatorProfile) -> str | None:
    parts: list[str] = []
    for post in creator.recent_posts:
        if post.caption:
            parts.append(post.caption)
        if post.hashtags:
            parts.extend(post.hashtags)
    return "\n".join(parts) or None


def _thai_caption_ratio(creator: CreatorProfile) -> float | None:
    captions = [post.caption for post in creator.recent_posts if post.caption]
    if not captions:
        return None
    return sum(_contains_thai(caption or "") for caption in captions) / len(captions)


def _contains_thai(value: str) -> bool:
    return any("\u0e00" <= char <= "\u0e7f" for char in value)


def _clean_username(value: object) -> str | None:
    if value is None:
        return None
    username = str(value).strip().lstrip("@").split("/")[0]
    return username or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip().lstrip("#")
        if text and text not in result:
            result.append(text)
    return result


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _timestamp_to_iso(value: object) -> str | None:
    timestamp = _int_or_none(value)
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None
