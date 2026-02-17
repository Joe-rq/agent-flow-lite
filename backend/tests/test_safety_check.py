from types import SimpleNamespace

import pytest

import app.core.safety_check as safety_check


def test_run_safety_checks_noop_when_flags_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = SimpleNamespace(enable_code_node=False, enable_http_node=False)
    monkeypatch.setattr(safety_check, "settings", lambda: cfg)

    called = {"sandbox": 0, "ssrf": 0}

    def _probe_sandbox() -> list[str]:
        called["sandbox"] += 1
        return ["unexpected"]

    def _probe_ssrf() -> bool:
        called["ssrf"] += 1
        return False

    monkeypatch.setattr(safety_check, "_probe_sandbox", _probe_sandbox)
    monkeypatch.setattr(safety_check, "_probe_ssrf_transport", _probe_ssrf)

    safety_check.run_safety_checks()
    assert called == {"sandbox": 0, "ssrf": 0}


def test_run_safety_checks_blocks_on_probe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = SimpleNamespace(enable_code_node=True, enable_http_node=False)
    monkeypatch.setattr(safety_check, "settings", lambda: cfg)
    monkeypatch.setattr(safety_check, "_probe_sandbox", lambda: ["import os"])

    with pytest.raises(RuntimeError) as exc:
        safety_check.run_safety_checks()

    msg = str(exc.value)
    assert "SAFETY CHECK FAILED" in msg
    assert "import os" in msg
