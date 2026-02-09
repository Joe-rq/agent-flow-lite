"""SSE (Server-Sent Events) utility functions."""
import json


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
