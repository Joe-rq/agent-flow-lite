import subprocess

import pytest

from app.utils.code_sandbox import (
    SandboxResult,
    _build_env,
    _truncate_text,
    execute_python,
    validate_python_code,
)


def test_validate_python_code_blocks_banned_imports() -> None:
    with pytest.raises(ValueError):
        validate_python_code("import socket\nprint('x')")

    with pytest.raises(ValueError):
        validate_python_code("from subprocess import run\nprint('x')")


def test_validate_python_code_blocks_banned_calls() -> None:
    with pytest.raises(ValueError):
        validate_python_code("import os\nos.system('echo hi')")


def test_build_env_filters_keys() -> None:
    env = _build_env({"good": "1", "bad-key": "2", "": "3", "MiXeD": "4"})
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["GOOD"] == "1"
    assert env["MIXED"] == "4"
    assert "BAD-KEY" not in env


def test_truncate_text_limits_bytes() -> None:
    text = "a" * 100
    assert len(_truncate_text(text, 10)) == 10


def test_execute_python_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["python"], timeout=1)

    monkeypatch.setattr("app.utils.code_sandbox.subprocess.run", _fake_run)

    result = execute_python("print('ok')", env={}, timeout_seconds=1)
    assert isinstance(result, SandboxResult)
    assert result.ok is False
    assert "timed out" in result.error


def test_execute_python_handles_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Completed:
        returncode = 1
        stdout = "out"
        stderr = "err"

    monkeypatch.setattr(
        "app.utils.code_sandbox.subprocess.run", lambda *a, **k: _Completed()
    )

    result = execute_python("print('ok')", env={})
    assert result.ok is False
    assert result.stdout == "out"
    assert result.stderr == "err"


def test_execute_python_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Completed:
        returncode = 0
        stdout = "hello\n"
        stderr = ""

    monkeypatch.setattr(
        "app.utils.code_sandbox.subprocess.run", lambda *a, **k: _Completed()
    )

    result = execute_python("print('ok')", env={"x": "y"})
    assert result.ok is True
    assert "hello" in result.stdout
