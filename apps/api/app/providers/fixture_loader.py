"""Fixture data loader — loads the Dr. Pong demo data from disk.

This module is the sole gateway to fixture data.
It is intentionally synchronous so it can also be called in unit tests
without an async runtime.

Design decisions:
- All data is read once at import time and cached in module-level constants.
- JSON parsing is validated against Pydantic models before returning.
- The fixture path is configurable via FIXTURE_DIR env variable for testing.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from ..models.brand import BrandProfile
from ..models.creator import CreatorProfile

# ── Fixture location ────────────────────────────────────────────────────────

def _fixture_dir() -> Path:
    """Resolve the fixture data directory.

    Checks FIXTURE_DIR env var first (useful in tests),
    then falls back to the standard location relative to the repo root.
    """
    env_override = os.getenv("FIXTURE_DIR")
    if env_override:
        return Path(env_override)
    # In Docker: /app/data/fixtures (data/ is volume-mounted read-only)
    # In local dev: discovered relative to this file
    candidates = [
        Path("/app/data/fixtures"),
        Path(__file__).parent.parent.parent.parent.parent / "data" / "fixtures",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Return the first candidate even if it doesn't exist — caller will fail
    return candidates[0]


FIXTURE_DIR = _fixture_dir()


# ── Public API ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_drpong_brand_profile() -> BrandProfile:
    """Load the pre-computed Dr. Pong brand profile.

    Returns:
        BrandProfile: Validated Pydantic model.

    Raises:
        FileNotFoundError: If the fixture file is missing.
        ValidationError: If the JSON does not match the schema.
    """
    path = FIXTURE_DIR / "drpong" / "brand_profile.json"
    with open(path) as f:
        data = json.load(f)
    return BrandProfile.model_validate(data)


@lru_cache(maxsize=1)
def load_drpong_creators() -> list[CreatorProfile]:
    """Load the 40 synthetic creator profiles for the Dr. Pong demo.

    Returns:
        list[CreatorProfile]: Validated list of creator models.

    Raises:
        FileNotFoundError: If the fixture file is missing.
        ValidationError: If any creator does not match the schema.
    """
    path = FIXTURE_DIR / "drpong" / "creators.json"
    with open(path) as f:
        data = json.load(f)
    return [CreatorProfile.model_validate(item) for item in data]


@lru_cache(maxsize=1)
def load_demo_pool_creators() -> list[CreatorProfile]:
    """Load the mixed-industry synthetic demo pool."""
    path = FIXTURE_DIR / "demo_pool" / "creators.json"
    with open(path) as f:
        data = json.load(f)
    return [CreatorProfile.model_validate(item) for item in data]


@lru_cache(maxsize=1)
def load_demo_pool_metadata() -> dict:
    """Load demo pool provenance metadata."""
    path = FIXTURE_DIR / "demo_pool" / "metadata.json"
    with open(path) as f:
        return json.load(f)
