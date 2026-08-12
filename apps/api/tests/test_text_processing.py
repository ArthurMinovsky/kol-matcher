"""Tests for deterministic Thai/English text processing."""
from __future__ import annotations

from app.services import text_processing
from app.services.text_processing import extract_terms, tokenize_text


def test_tokenize_text_normalizes_thai_english_hashtags_and_urls():
    tokens = tokenize_text(
        "รีวิวสกินแคร์ #Skincare https://example.com gelato review"
    )

    assert "skincare" in tokens
    assert "gelato" in tokens
    assert "review" in tokens
    assert "#skincare" not in tokens
    assert all(not token.startswith("http") for token in tokens)


def test_tokenize_text_preserves_thai_terms_without_external_tokenizer():
    tokens = tokenize_text("คลินิกดูแลผิว สกินแคร์ และสิว")

    assert "คลินิก" in tokens
    assert "ผิว" in tokens
    assert "แคร์" in tokens
    assert "สิว" in tokens
    assert "และ" not in tokens


def test_extract_terms_removes_generic_stop_words():
    terms = extract_terms("the best gelato in Bangkok and the best dessert")

    assert "the" not in terms
    assert "and" not in terms
    assert "gelato" in terms
    assert "dessert" in terms


def test_tokenize_text_delegates_to_lekcut_deepcut(monkeypatch):
    captured: dict[str, object] = {}

    def fake_lekcut(text: str, *, model: str) -> list[str]:
        captured["text"] = text
        captured["model"] = model
        return ["คลินิก", "skincare", "และ"]

    monkeypatch.setattr(text_processing, "lekcut_word_tokenize", fake_lekcut)

    assert tokenize_text("คลินิก Skincare") == ["คลินิก", "skincare"]
    assert captured == {"text": "คลินิก skincare", "model": "deepcut"}


def test_tokenize_text_falls_back_when_lekcut_fails(monkeypatch):
    def fail_lekcut(_text: str, *, model: str) -> list[str]:
        raise RuntimeError("ONNX runtime unavailable")

    monkeypatch.setattr(text_processing, "lekcut_word_tokenize", fail_lekcut)

    assert tokenize_text("Skincare และ travel") == ["skincare", "travel"]
