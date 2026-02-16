#!/usr/bin/env python3
"""
Phase Gate Verifier — 机器可执行的阶段闸门检查。

用法:
    uv run --project backend --group dev python scripts/verify_gates.py --phase p1_to_p2
    uv run --project backend --group dev python scripts/verify_gates.py --phase p2_to_p3
    uv run --project backend --group dev python scripts/verify_gates.py --phase p3_to_p4
    uv run --project backend --group dev python scripts/verify_gates.py --all

退出码:
    0 = 所有检查通过
    1 = 有检查失败（阻断 merge）

设计原则:
    - 使用 stdlib + PyYAML
    - 每条规则输出 PASS/FAIL + 原因
    - CI 中作为 merge 前置条件
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    yaml = importlib.import_module("yaml")
except ModuleNotFoundError:
    print("ERROR: PyYAML is required. Install with `uv sync --group dev` in backend.")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
GATES_FILE = ROOT / "gates.yaml"
SEARCHABLE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".yml",
    ".yaml",
    ".toml",
    ".md",
    ".json",
    ".ini",
}

USE_COLOR = (
    sys.stdout.isatty()
    and os.getenv("NO_COLOR") is None
    and os.getenv("CI", "").lower() not in {"1", "true"}
)
GREEN = "\033[92m" if USE_COLOR else ""
RED = "\033[91m" if USE_COLOR else ""
YELLOW = "\033[93m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""


def load_gates() -> dict[str, Any]:
    """Load gates.yaml."""
    if not GATES_FILE.exists():
        print(f"{RED}ERROR: {GATES_FILE} not found{RESET}")
        sys.exit(1)
    with open(GATES_FILE) as f:
        return yaml.safe_load(f)


def _iter_text_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.exists():
        return
    for candidate in path.rglob("*"):
        if candidate.is_file():
            yield candidate


def check_grep_code(rule: dict[str, Any]) -> tuple[bool, str]:
    """Check if a pattern exists in specified paths."""
    pattern = rule["pattern"]
    paths = rule.get("paths", ["backend/", "frontend/src/"])
    min_matches = rule.get("min_matches", 1)
    try:
        regex = re.compile(pattern, re.MULTILINE)
    except re.error as exc:
        return False, f"invalid regex '{pattern}': {exc}"

    total_matches = 0
    for p in paths:
        full_path = ROOT / p
        for file_path in _iter_text_files(full_path):
            if file_path.suffix.lower() not in SEARCHABLE_SUFFIXES:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            total_matches += len(regex.findall(content))

    if total_matches >= min_matches:
        return True, f"found {total_matches} matches (need >= {min_matches})"
    return False, f"found {total_matches} matches (need >= {min_matches})"


def check_file_exists(rule: dict[str, Any]) -> tuple[bool, str]:
    """Check if specified files/directories exist."""
    paths = rule.get("paths", [])
    missing = []
    for p in paths:
        if not (ROOT / p).exists():
            missing.append(p)
    if not missing:
        return True, "all files exist"
    return False, f"missing: {', '.join(missing)}"


def check_json_log_schema(rule: dict[str, Any]) -> tuple[bool, str]:
    """Check if log files contain required JSON fields."""
    required = rule.get("required_fields", [])
    log_pattern = rule.get("log_pattern", "*.log")

    # Search for log files
    log_files = list(ROOT.rglob(log_pattern))
    if not log_files:
        backend_path = ROOT / "backend"
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        try:
            audit_module = importlib.import_module("app.core.audit")
            build_audit_entry = getattr(audit_module, "build_audit_entry")
            write_audit_entry = getattr(audit_module, "write_audit_entry")

            entry = build_audit_entry(
                user_id="gate-check",
                action="gate_probe",
                resource_id="gate_probe",
                ip="127.0.0.1",
            )
            write_audit_entry(entry)
            log_files = list(ROOT.rglob(log_pattern))
        except Exception:
            return (
                False,
                f"no log files matching '{log_pattern}' found and failed to generate sample entry",
            )

    if not log_files:
        return False, f"no log files matching '{log_pattern}' found"

    for lf in log_files[:3]:  # Check up to 3 files
        try:
            with open(lf) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        missing = [k for k in required if k not in entry]
                        if not missing:
                            return True, f"valid entry found in {lf.name}"
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue

    return False, f"no log entry with all required fields: {required}"


def check_command(rule: dict[str, Any]) -> tuple[bool, str]:
    """Run a shell command and check exit code."""
    cmd = rule["cmd"]
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=180, cwd=str(ROOT)
        )
        if result.returncode == 0:
            return True, "command succeeded"
        # Extract last 3 lines of stderr for context
        err_lines = result.stderr.strip().split("\n")[-3:]
        return False, f"exit code {result.returncode}: {' | '.join(err_lines)}"
    except subprocess.TimeoutExpired:
        return False, "command timed out (180s)"


CHECKERS: dict[str, Callable[[dict[str, Any]], tuple[bool, str]]] = {
    "grep_code": check_grep_code,
    "file_exists": check_file_exists,
    "json_log_schema": check_json_log_schema,
    "command": check_command,
}


def verify_gate(gate_name: str, gate_def: dict[str, Any]) -> bool:
    """Verify all checks for a single gate. Returns True if all pass."""
    desc = gate_def.get("description", "")
    print(f"\n{BOLD}=== Gate: {gate_name} ==={RESET}")
    print(f"    {desc}\n")

    checks = gate_def.get("checks", {})
    all_passed = True

    for check_name, check_def in checks.items():
        check_desc = check_def.get("description", check_name)
        rules = check_def.get("rules", [])
        check_passed = True

        for rule in rules:
            rule_type = rule.get("type", "")
            checker = CHECKERS.get(rule_type)
            if not checker:
                print(
                    f"  {YELLOW}SKIP{RESET} [{check_name}] unknown rule type: {rule_type}"
                )
                continue

            passed, detail = checker(rule)
            message = rule.get("message", "")
            success_message = rule.get("success_message", "")
            status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
            if passed:
                output_message = success_message or detail
            else:
                output_message = message or detail
            print(f"  {status} [{check_name}] {output_message}")
            if not passed and detail:
                print(f"         detail: {detail}")
                check_passed = False

        if not check_passed:
            all_passed = False

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Phase Gate Verifier")
    parser.add_argument("--phase", type=str, help="Gate to verify (e.g., p1_to_p2)")
    parser.add_argument("--all", action="store_true", help="Verify all gates")
    args = parser.parse_args()

    if not args.phase and not args.all:
        parser.print_help()
        sys.exit(1)

    gates_data = load_gates()
    gates = gates_data.get("gates", {})

    if args.all:
        targets = list(gates.keys())
    else:
        if args.phase not in gates:
            print(
                f"{RED}ERROR: gate '{args.phase}' not found. Available: {list(gates.keys())}{RESET}"
            )
            sys.exit(1)
        targets = [args.phase]

    print(f"{BOLD}Phase Gate Verifier{RESET}")
    print(f"Root: {ROOT}")
    print(f"Gates file: {GATES_FILE}")

    all_passed = True
    for gate_name in targets:
        if not verify_gate(gate_name, gates[gate_name]):
            all_passed = False

    print(f"\n{'=' * 50}")
    if all_passed:
        print(f"{GREEN}{BOLD}ALL GATES PASSED{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}GATE CHECK FAILED — merge blocked{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
