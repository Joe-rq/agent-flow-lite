from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_SANDBOX_ESCAPE_PROBES = [
    "import os",
    "from os import path",
    "__import__('os')",
    "eval('1+1')",
    "exec('x=1')",
]


def _probe_sandbox() -> list[str]:
    from app.utils.code_sandbox import validate_python_code

    failures: list[str] = []
    for payload in _SANDBOX_ESCAPE_PROBES:
        try:
            validate_python_code(payload)
            failures.append(payload)
        except ValueError:
            pass
    return failures


def _probe_ssrf_transport() -> bool:
    try:
        from app.utils.ssrf_guard import SSRFSafeTransport

        _ = SSRFSafeTransport()
        return True
    except Exception:
        return False


def run_safety_checks() -> None:
    cfg = settings()

    if cfg.enable_code_node:
        failures = _probe_sandbox()
        if failures:
            msg = (
                "SAFETY CHECK FAILED: Code node is enabled but sandbox "
                "failed to block the following payloads:\n"
                + "\n".join(f"  - {p}" for p in failures)
                + "\nRefusing to start. Fix the sandbox or disable "
                "ENABLE_CODE_NODE."
            )
            raise RuntimeError(msg)
        logger.info("Safety check passed: code sandbox OK")

    if cfg.enable_http_node:
        if not _probe_ssrf_transport():
            raise RuntimeError(
                "SAFETY CHECK FAILED: HTTP node is enabled but "
                "SSRFSafeTransport is not available. Refusing to start."
            )
        logger.info("Safety check passed: SSRF transport OK")
