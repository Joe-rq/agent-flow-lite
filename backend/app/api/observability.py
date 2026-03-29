"""Observability API - Token usage statistics for LLM cost monitoring."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.admin import require_admin
from app.core.llm import TOKEN_USAGE_LOG
from app.models.user import User

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


class TokenUsageSummary(BaseModel):
    """Token usage summary response."""

    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")
    total_requests: int = Field(..., description="Total number of requests")
    by_provider: dict[str, dict[str, int]] = Field(
        default_factory=dict, description="Usage grouped by provider"
    )
    by_model: dict[str, dict[str, int]] = Field(
        default_factory=dict, description="Usage grouped by model"
    )


def _parse_token_log(hours: int) -> list[dict[str, Any]]:
    """Parse token_usage.log and filter by time range."""
    if not TOKEN_USAGE_LOG.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries: list[dict[str, Any]] = []

    try:
        with open(TOKEN_USAGE_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("timestamp", "")
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts >= cutoff:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        pass

    return entries


def _aggregate_usage(entries: list[dict[str, Any]]) -> TokenUsageSummary:
    """Aggregate token usage from log entries."""
    total_input = 0
    total_output = 0
    by_provider: dict[str, dict[str, int]] = {}
    by_model: dict[str, dict[str, int]] = {}

    for entry in entries:
        provider = entry.get("provider", "unknown")
        model = entry.get("model", "unknown")
        input_tokens = int(entry.get("input_tokens", 0))
        output_tokens = int(entry.get("output_tokens", 0))

        total_input += input_tokens
        total_output += output_tokens

        # Aggregate by provider
        if provider not in by_provider:
            by_provider[provider] = {"input_tokens": 0, "output_tokens": 0, "requests": 0}
        by_provider[provider]["input_tokens"] += input_tokens
        by_provider[provider]["output_tokens"] += output_tokens
        by_provider[provider]["requests"] += 1

        # Aggregate by model
        if model not in by_model:
            by_model[model] = {"input_tokens": 0, "output_tokens": 0, "requests": 0}
        by_model[model]["input_tokens"] += input_tokens
        by_model[model]["output_tokens"] += output_tokens
        by_model[model]["requests"] += 1

    return TokenUsageSummary(
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_requests=len(entries),
        by_provider=by_provider,
        by_model=by_model,
    )


@router.get("/token-usage", response_model=TokenUsageSummary)
async def get_token_usage(
    hours: int = Query(default=24, ge=1, le=720, description="Time range in hours"),
    admin: User = Depends(require_admin),
) -> TokenUsageSummary:
    """Get token usage statistics for the specified time range."""
    entries = _parse_token_log(hours)
    return _aggregate_usage(entries)
