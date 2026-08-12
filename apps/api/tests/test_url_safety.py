"""Regression tests for public URL and SSRF boundary validation."""
from __future__ import annotations

import pytest

from app.safety.url_safety import is_public_http_url, is_valid_facebook_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/health",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
        "http://localhost/admin",
        "http://user:password@example.com/private",
    ],
)
def test_private_or_credential_urls_are_rejected(url):
    assert is_public_http_url(url) is False


def test_public_hostname_is_allowed():
    assert is_public_http_url("https://example.com/public") is True


def test_facebook_validation_keeps_domain_boundary():
    assert is_valid_facebook_url("https://www.facebook.com/drpongclinic") is True
    assert is_valid_facebook_url("https://facebook.com.evil.example/page") is False
