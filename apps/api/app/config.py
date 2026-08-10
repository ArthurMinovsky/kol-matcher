"""Configuration constants for the KOL Matcher.

All calibration constants live here so they are visible and testable.
Scoring weights are documented here — do not scatter magic numbers.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    # ── LLM providers (OpenAI-compatible endpoints) ───────────────────────
    # Priority: Typhoon first, then Gemini.
    typhoon_api_key: str = ""
    typhoon_base_url: str = "https://api.opentyphoon.ai/v1"
    typhoon_model: str = "typhoon-v2.1-72b-instruct"

    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-2.0-flash"

    # ── Creator data providers ────────────────────────────────────────────
    apify_api_token: str = ""
    apify_tiktok_actor: str = "clockworks/free-tiktok-scraper"  # configurable
    apify_timeout_seconds: int = 120
    apify_max_creators: int = 30

    # ── Match Score weights (must sum to 1.0) ─────────────────────────────
    RELEVANCE_WEIGHT: float = 0.45
    ENGAGEMENT_WEIGHT: float = 0.25
    THAILAND_WEIGHT: float = 0.15
    STYLE_WEIGHT: float = 0.15

    # ── Thailand Market Relevance signal weights (must sum to 100) ─────────
    THAILAND_CAPTION_RATIO_WEIGHT: int = 40
    THAILAND_HASHTAG_WEIGHT: int = 25
    THAILAND_BIO_WEIGHT: int = 20
    THAILAND_LOCATION_WEIGHT: int = 15

    # ── Evidence Coverage component weights (must sum to 100) ──────────────
    EVIDENCE_BIO_WEIGHT: int = 20
    EVIDENCE_CAPTIONS_WEIGHT: int = 25
    EVIDENCE_ENGAGEMENT_WEIGHT: int = 25
    EVIDENCE_THAILAND_WEIGHT: int = 20
    EVIDENCE_METADATA_WEIGHT: int = 10

    # ── Engagement scoring ─────────────────────────────────────────────────
    # Per-post rate = (likes + 2*comments + 3*shares) / max(views, 1)
    # Median across posts, clip to this max before pool-relative scaling.
    ENGAGEMENT_CLIP_MAX: float = 0.30

    # ── Relevance: cosine similarity → 0..100 mapping ─────────────────────
    # score = clip(similarity * RELEVANCE_SIM_SCALE + RELEVANCE_SIM_OFFSET, 0, 100)
    # Calibrated so that:
    #   similarity=0.80 → ~86, similarity=0.50 → ~50, similarity=0.20 → ~14
    RELEVANCE_SIM_SCALE: float = 120.0
    RELEVANCE_SIM_OFFSET: float = -10.0

    # ── Facebook scraping (Apify cloud actor) ─────────────────────────────
    apify_facebook_actor: str = "apify/facebook-pages-scraper"
    apify_facebook_timeout_seconds: int = 120

    # ── Thai NLP / semantic similarity ─────────────────────────────────────
    sentence_transformer_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    keyword_max_count: int = 15

    # ── LLM-as-judge ──────────────────────────────────────────────────────
    llm_judge_batch_size: int = 5
    llm_judge_max_tokens: int = 1024

    # ── Relevance component weights (within the 45% relevance bucket) ─────
    # relevance_total = keyword_weight * keyword_score + llm_weight * llm_score
    # These must sum to 1.0 (they're relative weights within relevance)
    relevance_keyword_weight: float = 0.5556  # = 25/45
    relevance_llm_weight: float = 0.4444      # = 20/45

    @property
    def llm_api_key(self) -> str:
        """Return the first available LLM key in priority order."""
        return self.typhoon_api_key or self.gemini_api_key

    @property
    def llm_config(self) -> dict | None:
        """Return {base_url, api_key, model} for the active provider."""
        if self.typhoon_api_key:
            return {
                "base_url": self.typhoon_base_url,
                "api_key": self.typhoon_api_key,
                "model": self.typhoon_model,
            }
        if self.gemini_api_key:
            return {
                "base_url": self.gemini_base_url,
                "api_key": self.gemini_api_key,
                "model": self.gemini_model,
            }
        return None


settings = Settings()
