from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
]


def _normalize_allowlist(allow_domains: list[str] | None) -> set[str]:
    if not allow_domains:
        return set()
    return {item.strip().lower() for item in allow_domains if item.strip()}


def _is_blocked_ip(ip_text: str) -> bool:
    try:
        address = ipaddress.ip_address(ip_text)
    except ValueError:
        return True
    return any(address in network for network in BLOCKED_NETWORKS)


def _resolve_addresses(hostname: str, port: int) -> set[str]:
    infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    addresses: set[str] = set()
    for info in infos:
        sockaddr = info[4]
        addresses.add(str(sockaddr[0]))
    return addresses


def ensure_url_safe(url: str, allow_domains: list[str] | None = None) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http:// and https:// URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL host is required")

    hostname = parsed.hostname.lower()
    allowlist = _normalize_allowlist(allow_domains)
    if allowlist:
        if hostname not in allowlist and not any(
            hostname.endswith(f".{domain}") for domain in allowlist
        ):
            raise ValueError("URL host is not in allowlist")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = _resolve_addresses(hostname, port)
    if not addresses:
        raise ValueError("Unable to resolve target host")

    for address in addresses:
        if _is_blocked_ip(address):
            raise ValueError("Target host resolves to blocked IP")
    return url
