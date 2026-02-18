"""SSE (Server-Sent Events) utility functions."""
import asyncio
import json
from collections.abc import AsyncGenerator


def format_sse_event(event: str, data: dict) -> str:
    """
    Format data as SSE event string.

    Args:
        event: SSE event type (e.g., "token", "thought", "done", "citation")
        data: Dictionary containing event payload data

    Returns:
        Formatted SSE event string in the format:
        "event: {event}\ndata: {json_data}\n\n"
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


SSE_HEARTBEAT = ": heartbeat\n\n"


async def with_heartbeat(
    source: AsyncGenerator[str, None],
    interval: float = 15.0,
) -> AsyncGenerator[str, None]:
    """Wrap an SSE generator to automatically inject heartbeat comments.

    Runs a background heartbeat task that emits ``: heartbeat`` SSE comments
    at the given *interval* (seconds) while the *source* generator is active.
    This keeps reverse-proxy connections alive during long LLM thinking pauses.
    """
    _SENTINEL = object()
    queue: asyncio.Queue[str | object] = asyncio.Queue()
    pump_error: BaseException | None = None

    async def _pump() -> None:
        nonlocal pump_error
        try:
            async for chunk in source:
                await queue.put(chunk)
        except BaseException as exc:
            pump_error = exc
        finally:
            await queue.put(_SENTINEL)

    async def _heartbeat() -> None:
        while True:
            await asyncio.sleep(interval)
            await queue.put(SSE_HEARTBEAT)

    pump_task = asyncio.create_task(_pump())
    hb_task = asyncio.create_task(_heartbeat())

    try:
        while True:
            item = await queue.get()
            if item is _SENTINEL:
                if pump_error is not None:
                    raise pump_error
                break
            yield item  # type: ignore[misc]
    finally:
        hb_task.cancel()
        if not pump_task.done():
            pump_task.cancel()
        for t in (pump_task, hb_task):
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
