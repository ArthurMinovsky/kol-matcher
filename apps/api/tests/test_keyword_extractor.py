"""Tests for Thai keyword extraction and semantic similarity."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from app.services.keyword_extractor import ThaiKeywordExtractor


@pytest.fixture
def extractor():
    """Create a mock extractor with patched dependencies."""
    mock_keybert_cls = MagicMock()
    mock_keybert = MagicMock()
    mock_keybert_cls.return_value = mock_keybert
    
    mock_st_cls = MagicMock()
    mock_encoder = MagicMock()
    mock_st_cls.return_value = mock_encoder
    
    with patch("pythainlp.summarize.keybert.KeyBERT", mock_keybert_cls), \
         patch("sentence_transformers.SentenceTransformer", mock_st_cls):
        ext = ThaiKeywordExtractor()
        # Replace with our mocks
        ext.keybert = mock_keybert
        ext.encoder = mock_encoder
        return ext


def test_extract_keywords_returns_tuples(extractor):
    extractor.keybert.extract_keywords.return_value = [
        ("ice cream", 0.8),
        ("gelato", 0.7),
    ]
    results = extractor.extract_keywords(
        "Best gelato ice cream in Bangkok", max_keywords=5
    )
    assert len(results) == 2
    assert results[0][0] == "ice cream"
    assert results[0][1] == 0.8


def test_extract_keywords_returns_empty_for_short_text(extractor):
    results = extractor.extract_keywords("Hi", max_keywords=5)
    assert results == []


def test_semantic_similarity_returns_0_to_1(extractor):
    extractor.encoder.encode.return_value = np.array([
        [1.0, 0.0, 0.0],
        [0.9, 0.1, 0.0],
    ])
    sim = extractor.semantic_similarity("gelato", "ice cream")
    assert 0.0 <= sim <= 1.0
    assert sim > 0.5


def test_semantic_similarity_returns_0_for_empty(extractor):
    sim = extractor.semantic_similarity("", "test")
    assert sim == 0.0


def test_keyword_overlap_score_returns_0_to_1(extractor):
    brand_kw = [("gelato", 0.8), ("ice cream", 0.7), ("dessert", 0.6)]
    creator_kw = [("ice cream", 0.9), ("dessert", 0.8), ("chocolate", 0.7)]
    overlap = extractor.keyword_overlap_score(brand_kw, creator_kw)
    assert 0.0 <= overlap <= 1.0
    assert overlap == pytest.approx(2 / 3, abs=1e-6)


def test_keyword_overlap_score_returns_0_for_empty(extractor):
    assert extractor.keyword_overlap_score([], [("test", 0.5)]) == 0.0
    assert extractor.keyword_overlap_score([("test", 0.5)], []) == 0.0
