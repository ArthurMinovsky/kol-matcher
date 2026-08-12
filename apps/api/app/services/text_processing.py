"""Deterministic Thai/English tokenization for BM25 matching."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from lekcut import word_tokenize as lekcut_word_tokenize


_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_VALID_TOKEN_RE = re.compile(r"^[a-z0-9_\u0e00-\u0e7f]+$", re.IGNORECASE)

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "were", "with", "ภายใน", "ของ", "และ", "ที่", "เป็น", "ได้",
    "ให้", "ใน", "ไป", "มา", "ก็", "แต่", "หรือ", "กับ", "แล้ว", "คือ",
    "จาก", "นี้", "นั้น", "อยู่", "จะ", "ต้อง", "ไม่", "ถ้า", "เมื่อ",
    "เพราะ", "ว่า", "ทั้ง", "ทุก", "ทาง", "ตาม", "ขึ้น", "ลง", "เขา",
    "คุณ", "ฉัน", "เรา", "พวก", "อีก", "อย่าง", "ต่าง", "เช่น", "เดียว",
    "กว่า", "ทั้งหมด", "ยิ่ง", "เพียง", "เพื่อ", "ต่อ", "ทำ", "น่า", "ขอ",
    "เอา", "เข้า", "ออก", "เอง", "อาจ", "บาง", "หลาย", "ด้วย",
}


def tokenize_text(text: str | None) -> list[str]:
    """Normalize and tokenize Thai/English text for lexical matching."""
    if not text:
        return []

    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = _URL_RE.sub(" ", normalized)

    try:
        raw_tokens = lekcut_word_tokenize(normalized, model="deepcut")
    except Exception:
        raw_tokens = re.findall(r"[a-z0-9_]+|[\u0e00-\u0e7f]+", normalized)

    tokens: list[str] = []
    for raw in raw_tokens:
        token = raw.strip().lstrip("#").strip(".,!?;:()[]{}\"'“”‘’")
        if not token or token in _STOP_WORDS:
            continue
        if not _VALID_TOKEN_RE.fullmatch(token):
            continue
        if token.isdigit():
            continue
        tokens.append(token)
    return tokens


def extract_terms(text: str | None, max_terms: int = 15) -> list[str]:
    """Return deterministic frequency-ranked terms for brand intelligence."""
    tokens = tokenize_text(text)
    if not tokens:
        return []

    counts = Counter(tokens)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [term for term, _count in ranked[:max_terms]]
