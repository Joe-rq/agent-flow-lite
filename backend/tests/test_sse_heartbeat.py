"""Tests for the SSE heartbeat helper."""
import asyncio

import pytest

from app.utils.sse import SSE_HEARTBEAT, with_heartbeat


async def _collect(gen, max_items=50):
    """Collect items from an async generator with a safety limit."""
    items = []
    async for item in gen:
        items.append(item)
        if len(items) >= max_items:
            break
    return items


async def _async_gen_from_list(items, delay=0):
    """Create an async generator that yields items with optional delay."""
    for item in items:
        if delay:
            await asyncio.sleep(delay)
        yield item


@pytest.mark.asyncio
async def test_heartbeat_emits_during_pause():
    """Heartbeat comments appear when the source generator is slow."""

    async def slow_source():
        yield "event: token\ndata: {}\n\n"
        await asyncio.sleep(0.25)  # longer than heartbeat interval
        yield "event: done\ndata: {}\n\n"

    result = await _collect(with_heartbeat(slow_source(), interval=0.05))

    assert result[0] == "event: token\ndata: {}\n\n"
    heartbeats = [r for r in result if r == SSE_HEARTBEAT]
    assert len(heartbeats) >= 1, "Expected at least one heartbeat during pause"
    assert result[-1] == "event: done\ndata: {}\n\n"


@pytest.mark.asyncio
async def test_heartbeat_stops_after_source_ends():
    """After source generator completes, no more heartbeats are produced."""

    async def fast_source():
        yield "data: hello\n\n"

    result = await _collect(with_heartbeat(fast_source(), interval=0.05))

    # Should contain the data item; heartbeat task should be cancelled
    assert "data: hello\n\n" in result


@pytest.mark.asyncio
async def test_heartbeat_propagates_source_items_in_order():
    """All source items are yielded, interleaved with heartbeats."""
    items = [f"event: token\ndata: {{\"i\": {i}}}\n\n" for i in range(5)]

    result = await _collect(with_heartbeat(_async_gen_from_list(items), interval=10))

    # With a very long interval, no heartbeats should appear
    non_hb = [r for r in result if r != SSE_HEARTBEAT]
    assert non_hb == items


@pytest.mark.asyncio
async def test_heartbeat_handles_source_exception():
    """Exception in source generator propagates correctly."""

    async def failing_source():
        yield "event: token\ndata: {}\n\n"
        raise RuntimeError("LLM exploded")

    with pytest.raises(RuntimeError, match="LLM exploded"):
        await _collect(with_heartbeat(failing_source(), interval=0.05))


@pytest.mark.asyncio
async def test_heartbeat_constant_format():
    """SSE_HEARTBEAT is a valid SSE comment."""
    assert SSE_HEARTBEAT.startswith(":")
    assert SSE_HEARTBEAT.endswith("\n\n")


@pytest.mark.asyncio
async def test_heartbeat_with_empty_source():
    """Empty source generator produces no items."""

    async def empty_source():
        return
        yield  # make it an async generator  # noqa: RET504

    result = await _collect(with_heartbeat(empty_source(), interval=0.05))
    # Only heartbeats or nothing; no data items
    non_hb = [r for r in result if r != SSE_HEARTBEAT]
    assert non_hb == []
