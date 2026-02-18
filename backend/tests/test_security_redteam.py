"""Red-team tests for code sandbox and SSRF guard.

Authorized security testing on own codebase — purely defensive.
Each test probes a known attack vector. If the guard blocks it, the test
passes. If a bypass is discovered, the test is marked xfail with a
'Known limitation' reason and documented in README.md.
"""

from __future__ import annotations

import socket

import pytest

from app.utils.code_sandbox import validate_python_code
from app.utils.ssrf_guard import ensure_url_safe


# ---------------------------------------------------------------------------
# Code Sandbox — Red Team
# ---------------------------------------------------------------------------


class TestSandboxImportBypass:
    """Attempts to import banned modules through indirect paths."""

    def test_builtins_dunder_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("__builtins__.__import__('os')")

    def test_importlib_import_module(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import importlib\nimportlib.import_module('os')")

    def test_bare_dunder_import_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("__import__('os')")

    def test_from_importlib(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("from importlib import import_module")


class TestSandboxAttributeChainEscape:
    """Probe MRO / __subclasses__ chains that bypass AST module checks."""

    @pytest.mark.xfail(
        reason="Known limitation: AST checker does not block __class__.__bases__ "
        "attribute chain traversal. Runtime subprocess may still execute it.",
        strict=False,
    )
    def test_mro_subclasses_enumeration(self) -> None:
        """().__class__.__bases__[0].__subclasses__() bypasses AST check."""
        with pytest.raises(ValueError):
            validate_python_code(
                "classes = ().__class__.__bases__[0].__subclasses__()\n"
                "print(len(classes))"
            )

    @pytest.mark.xfail(
        reason="Known limitation: AST checker does not block __class__.__mro__ traversal.",
        strict=False,
    )
    def test_mro_direct_access(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code(
                "mro = ''.__class__.__mro__\nprint(mro)"
            )

    @pytest.mark.xfail(
        reason="Known limitation: AST checker does not block type() constructor.",
        strict=False,
    )
    def test_type_constructor(self) -> None:
        """type('X', (object,), {}) can create arbitrary types."""
        with pytest.raises(ValueError):
            validate_python_code("T = type('X', (object,), {'run': lambda s: 1})")


class TestSandboxFileSystemAccess:
    """Attempts to read/write the file system."""

    def test_open_etc_passwd(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("f = open('/etc/passwd')")

    def test_open_with_mode(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("open('/tmp/x', 'w').write('pwned')")

    def test_pathlib_read(self) -> None:
        """pathlib is not in BANNED_MODULES but Path.read_text uses open()
        internally at runtime. The AST checker should block the import
        if pathlib were banned; currently it is NOT banned."""
        # pathlib is allowed by the validator — it's not in BANNED_MODULES.
        # The actual file read would happen at runtime in a subprocess.
        # This test verifies the AST validator allows pathlib (expected behavior).
        # The subprocess's clean env and resource limits provide the secondary barrier.
        validate_python_code("from pathlib import Path\nprint(Path('.'))")


class TestSandboxNetworkAccess:
    """Attempts to make network connections."""

    def test_import_socket(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import socket\nsocket.socket()")

    def test_from_socket(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("from socket import socket")

    def test_urllib_request(self) -> None:
        """urllib is not in BANNED_MODULES — only os, socket, subprocess,
        importlib, ctypes, shutil are banned."""
        # urllib is allowed at AST level; runtime subprocess env is clean
        # but urllib could still reach the network.
        validate_python_code(
            "from urllib.request import urlopen"
        )


class TestSandboxCodeExecution:
    """Attempts to use exec/eval/compile."""

    def test_exec_import_os(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("exec('import os')")

    def test_eval_dunder_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("eval('__import__(\"os\")')")

    def test_compile_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("compile('import os', '', 'exec')")

    def test_exec_as_variable_name(self) -> None:
        """Assigning to a variable named 'exec' is not a call — should pass."""
        # This is NOT a bypass; it's just naming a variable
        validate_python_code("exec_result = 42")


class TestSandboxEnvironmentVariables:
    """Attempts to access environment variables."""

    def test_os_environ(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import os\nprint(os.environ)")

    def test_os_getenv(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import os\nos.getenv('PATH')")

    def test_from_os_environ(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("from os import environ")


# ---------------------------------------------------------------------------
# SSRF Guard — Red Team
# ---------------------------------------------------------------------------


def _mock_resolve(ip: str):
    """Create a monkeypatch factory that resolves any hostname to a given IP."""

    def _mock(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 80))]

    return _mock


class TestSSRFPrivateIPs:
    """Direct private IP access attempts."""

    def test_loopback_127(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("127.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://127.0.0.1")

    def test_all_zeros(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("0.0.0.0"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://0.0.0.0")

    def test_ipv6_loopback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _mock_v6(*args, **kwargs):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 80, 0, 0))]

        monkeypatch.setattr(socket, "getaddrinfo", _mock_v6)
        with pytest.raises(ValueError):
            ensure_url_safe("http://[::1]")

    def test_metadata_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("169.254.169.254"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://169.254.169.254/latest/meta-data/")

    def test_10_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("10.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://10.0.0.1")

    def test_172_16_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("172.16.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://172.16.0.1")

    def test_192_168_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("192.168.1.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://192.168.1.1")


class TestSSRFDNSTricks:
    """DNS-based bypass attempts."""

    def test_localhost_hostname(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("127.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://localhost")

    def test_hex_ip_0x7f000001(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """0x7f000001 = 127.0.0.1 in hex notation."""
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("127.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://0x7f000001")

    def test_decimal_ip_2130706433(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """2130706433 = 127.0.0.1 in decimal notation."""
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("127.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://2130706433")

    def test_ipv6_mapped_ipv4(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """::ffff:127.0.0.1 is IPv4-mapped IPv6."""
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("127.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://[::ffff:127.0.0.1]")


class TestSSRFURLTricks:
    """URL parsing tricks to smuggle internal targets."""

    def test_userinfo_with_internal_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """http://evil.com@127.0.0.1 — Python urlparse extracts hostname=127.0.0.1."""
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("127.0.0.1"))
        with pytest.raises(ValueError):
            ensure_url_safe("http://evil.com@127.0.0.1")

    def test_port_in_userinfo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """http://127.0.0.1:80@evil.com — Python urlparse extracts hostname=evil.com.
        This is NOT a bypass: the actual target is evil.com (a public host)."""
        monkeypatch.setattr(socket, "getaddrinfo", _mock_resolve("93.184.216.34"))
        # This should pass because hostname resolves to a public IP
        result = ensure_url_safe("http://127.0.0.1:80@evil.com")
        assert result == "http://127.0.0.1:80@evil.com"

    def test_non_http_scheme_rejected(self) -> None:
        with pytest.raises(ValueError, match="Only http"):
            ensure_url_safe("gopher://127.0.0.1")

    def test_ftp_scheme_rejected(self) -> None:
        with pytest.raises(ValueError, match="Only http"):
            ensure_url_safe("ftp://127.0.0.1/etc/passwd")

    def test_file_scheme_rejected(self) -> None:
        with pytest.raises(ValueError, match="Only http"):
            ensure_url_safe("file:///etc/passwd")
