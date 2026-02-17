import socket

import httpx
import pytest

from app.utils.ssrf_guard import SSRFSafeTransport, _resolve_addresses, create_ssrf_safe_client


def _mock_getaddrinfo_factory(ip: str):
    def _mock(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 80))]
    return _mock


@pytest.mark.asyncio
async def test_transport_blocks_private_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _mock_getaddrinfo_factory("127.0.0.1"))
    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "http://evil.com/data")
    with pytest.raises(ValueError, match="SSRF blocked"):
        await transport.handle_async_request(request)


@pytest.mark.asyncio
async def test_transport_blocks_10_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _mock_getaddrinfo_factory("10.0.0.1"))
    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "http://internal.corp/api")
    with pytest.raises(ValueError, match="SSRF blocked"):
        await transport.handle_async_request(request)


@pytest.mark.asyncio
async def test_transport_blocks_172_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _mock_getaddrinfo_factory("172.16.0.1"))
    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "http://docker-host/")
    with pytest.raises(ValueError, match="SSRF blocked"):
        await transport.handle_async_request(request)


@pytest.mark.asyncio
async def test_transport_blocks_192_168(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _mock_getaddrinfo_factory("192.168.1.1"))
    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "http://router.local/")
    with pytest.raises(ValueError, match="SSRF blocked"):
        await transport.handle_async_request(request)


@pytest.mark.asyncio
async def test_transport_https_uses_port_443(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify HTTPS requests resolve DNS with port 443, not 80."""
    captured_ports: list[int] = []
    original_resolve = _resolve_addresses

    def _spy(hostname: str, port: int) -> set[str]:
        captured_ports.append(port)
        return original_resolve(hostname, port)

    monkeypatch.setattr("app.utils.ssrf_guard._resolve_addresses", _spy)
    monkeypatch.setattr(socket, "getaddrinfo", _mock_getaddrinfo_factory("93.184.216.34"))
    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "https://example.com/path")
    try:
        await transport.handle_async_request(request)
    except Exception:
        pass
    assert 443 in captured_ports, f"Expected port 443, got {captured_ports}"


def test_create_ssrf_safe_client_returns_async_client() -> None:
    client = create_ssrf_safe_client(follow_redirects=False, trust_env=False)
    assert isinstance(client, httpx.AsyncClient)
    assert isinstance(client._transport, SSRFSafeTransport)
