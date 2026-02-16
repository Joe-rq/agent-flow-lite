from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast


def _parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iter_audit_entries(path: Path) -> Iterator[dict[str, object]]:
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    obj = cast(object, json.loads(raw))
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    entry: dict[str, object] = {}
                    for k, v in cast(dict[object, object], obj).items():
                        if isinstance(k, str):
                            entry[k] = v
                    yield entry
    except OSError:
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Count template import/execute funnel events from audit.log"
    )
    _ = parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Lookback window in days (default: 7)",
    )
    _ = parser.add_argument(
        "--audit-log",
        type=str,
        default="data/audit.log",
        help="Path to audit.log JSONL (default: data/audit.log)",
    )
    args = parser.parse_args(argv)

    days = cast(int, args.days)
    if days <= 0:
        print("--days must be a positive integer", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    audit_path = Path(cast(str, args.audit_log))

    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"template_import": 0, "template_execute_success": 0}
    )

    for entry in _iter_audit_entries(audit_path):
        action = entry.get("action")
        if action not in ("template_import", "template_execute_success"):
            continue

        ts = _parse_iso_datetime(entry.get("timestamp"))
        if ts is None or ts < cutoff:
            continue

        template_name_obj = entry.get("template_name")
        if not isinstance(template_name_obj, str):
            continue
        template_name = template_name_obj.strip()
        if not template_name:
            continue

        counts[template_name][action] += 1

    templates_out = {k: counts[k] for k in sorted(counts.keys())}
    out = {
        "days": days,
        "generated_at": now.isoformat(),
        "templates": templates_out,
    }
    json.dump(out, sys.stdout, ensure_ascii=False)
    _ = sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
