import socket

import pytest

from app.utils.ssrf_guard import ensure_url_safe


def test_ensure_url_safe_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError):
        ensure_url_safe("file:///etc/passwd")


def test_ensure_url_safe_rejects_missing_host() -> None:
    with pytest.raises(ValueError):
        ensure_url_safe("https://")


def test_ensure_url_safe_enforces_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )

    with pytest.raises(ValueError):
        ensure_url_safe("https://evil.com", allow_domains=["example.com"])


def test_ensure_url_safe_allows_subdomain_in_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )

    assert (
        ensure_url_safe("https://api.example.com/path", allow_domains=["example.com"])
        == "https://api.example.com/path"
    )


def test_ensure_url_safe_blocks_private_ip_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))
        ],
    )

    with pytest.raises(ValueError):
        ensure_url_safe("http://localhost")
