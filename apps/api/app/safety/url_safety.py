"""URL safety helpers."""
from __future__ import annotations

from urllib.parse import urlparse


_FACEBOOK_HOSTS = {"facebook.com", "www.facebook.com", "m.facebook.com"}
_BLOCK_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def is_valid_facebook_url(url: str) -> bool:
    """Return True only for public http(s) facebook.com URLs."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.hostname or ""
    if host in _BLOCK_HOSTS or host.startswith("127.") or host.startswith("192.168."):
        return False
    return host in _FACEBOOK_HOSTS


def sanitize_url_for_display(url: str) -> str:
    return url.strip()[:512]
