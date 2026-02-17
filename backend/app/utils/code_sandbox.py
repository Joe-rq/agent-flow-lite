from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

BANNED_MODULES = {
    "importlib",
    "os",
    "socket",
    "subprocess",
    "ctypes",
    "shutil",
}

BANNED_BUILTINS = {
    "exec",
    "eval",
    "__import__",
    "compile",
    "open",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "breakpoint",
}


@dataclass
class SandboxResult:
    ok: bool
    stdout: str
    stderr: str
    error: str


def _truncate_text(text: str, max_bytes: int) -> str:
    raw = text.encode("utf-8", errors="ignore")
    if len(raw) <= max_bytes:
        return text
    return raw[:max_bytes].decode("utf-8", errors="ignore")


def validate_python_code(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_MODULES:
                    raise ValueError(f"Import not allowed: {root}")
        if isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            if module in BANNED_MODULES:
                raise ValueError(f"Import not allowed: {module}")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BANNED_BUILTINS:
                raise ValueError(f"Builtin not allowed: {func.id}")
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name) and func.value.id == "__builtins__":
                    raise ValueError(f"Builtin access not allowed: __builtins__.{func.attr}")
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
                raise ValueError("Builtin access not allowed: __builtins__[...]")


def _build_env(user_env: dict[str, str]) -> dict[str, str]:
    clean_env = {"PYTHONIOENCODING": "utf-8"}
    for key, value in user_env.items():
        safe_key = str(key).strip().upper()
        if not safe_key or not safe_key.replace("_", "").isalnum():
            continue
        clean_env[safe_key] = str(value)
    return clean_env


def _preexec_limit(memory_limit_mb: int):
    def _set_limits() -> None:
        import resource

        bytes_limit = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

    return _set_limits


def execute_python(
    code: str,
    env: dict[str, str],
    timeout_seconds: int = 30,
    memory_limit_mb: int = 256,
    stdout_limit_bytes: int = 10 * 1024,
) -> SandboxResult:
    validate_python_code(code)

    with tempfile.TemporaryDirectory(prefix="afl-code-node-") as temp_dir:
        script_path = Path(temp_dir) / "run.py"
        script_path.write_text(code, encoding="utf-8")
        command = [sys.executable, str(script_path)]
        try:
            if os.name != "nt":
                completed = subprocess.run(
                    command,
                    cwd=temp_dir,
                    env=_build_env(env),
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    shell=False,
                    preexec_fn=_preexec_limit(memory_limit_mb),
                )
            else:
                completed = subprocess.run(
                    command,
                    cwd=temp_dir,
                    env=_build_env(env),
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    shell=False,
                )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                ok=False,
                stdout="",
                stderr="",
                error="Code execution timed out",
            )
        except Exception as exc:
            return SandboxResult(
                ok=False,
                stdout="",
                stderr="",
                error=f"Code execution failed: {exc}",
            )

        stdout = _truncate_text(completed.stdout or "", stdout_limit_bytes)
        stderr = _truncate_text(completed.stderr or "", stdout_limit_bytes)
        if completed.returncode != 0:
            return SandboxResult(
                ok=False,
                stdout=stdout,
                stderr=stderr,
                error="Code execution returned non-zero status",
            )
        return SandboxResult(ok=True, stdout=stdout, stderr=stderr, error="")
