"""URL safety helpers."""
from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


_FACEBOOK_HOSTS = {"facebook.com", "www.facebook.com", "m.facebook.com"}
_BLOCK_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}


def is_public_http_url(url: str) -> bool:
    """Return True for an HTTP(S) URL whose literal host is publicly routable."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False

    host = parsed.hostname.rstrip(".").lower()
    if host in _BLOCK_HOSTS or host.endswith((".local", ".internal", ".localhost")):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return address.is_global


def is_valid_facebook_url(url: str) -> bool:
    """Return True only for public http(s) facebook.com URLs."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    host = parsed.hostname or ""
    if not is_public_http_url(url):
        return False
    return host.lower().rstrip(".") in _FACEBOOK_HOSTS


def sanitize_url_for_display(url: str) -> str:
    return url.strip()[:512]
