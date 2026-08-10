"""Thai keyword extraction and semantic similarity using pythainlp + sentence-transformers.

Singleton pattern: models load once at first use and are cached.
"""
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import numpy as np

from ..config import settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


# ── Singleton model cache ──────────────────────────────────────────────────

_keyword_extractor: "ThaiKeywordExtractor | None" = None


def get_keyword_extractor() -> "ThaiKeywordExtractor":
    global _keyword_extractor
    if _keyword_extractor is None:
        _keyword_extractor = ThaiKeywordExtractor()
    return _keyword_extractor


class ThaiKeywordExtractor:
    """Extract Thai/English keywords and compute semantic similarity."""

    def __init__(self) -> None:
        from pythainlp.summarize.keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        self.keybert = KeyBERT()
        self.encoder: SentenceTransformer = SentenceTransformer(
            settings.sentence_transformer_model,
            cache_folder="/app/models"
            if settings.app_env == "development"
            else None,
        )

    def extract_keywords(
        self, text: str, max_keywords: int = 15
    ) -> list[tuple[str, float]]:
        """Extract keywords from text using pythainlp KeyBERT.

        Returns list of (keyword, score) tuples sorted by score desc.
        Handles both Thai and English text.
        """
        if not text or len(text.strip()) < 10:
            return []

        try:
            results = self.keybert.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                max_keywords=max_keywords,
                tokenizer="newmm",
                return_similarity=True,
            )
            # results is list of (keyword, score) tuples
            return sorted(results, key=lambda x: x[1], reverse=True)
        except Exception:
            return []

    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts using sentence-transformers.

        Returns float in [0, 1].
        """
        if not text_a or not text_b:
            return 0.0

        embeddings = self.encoder.encode(
            [text_a, text_b], convert_to_numpy=True
        )
        a, b = embeddings[0], embeddings[1]

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = float(np.dot(a, b) / (norm_a * norm_b))
        # Map from [-1, 1] to [0, 1]
        return (similarity + 1.0) / 2.0

    def keyword_overlap_score(
        self,
        brand_keywords: list[tuple[str, float]],
        creator_keywords: list[tuple[str, float]],
    ) -> float:
        """Compute overlap ratio between two keyword sets.

        Returns float in [0, 1].
        """
        if not brand_keywords or not creator_keywords:
            return 0.0

        brand_set = {k.lower().strip() for k, _ in brand_keywords}
        creator_set = {k.lower().strip() for k, _ in creator_keywords}

        if not brand_set or not creator_set:
            return 0.0

        overlap = len(brand_set & creator_set)
        return overlap / max(len(brand_set), len(creator_set))


def _text_hash(text: str) -> str:
    """Fast hash for caching."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
