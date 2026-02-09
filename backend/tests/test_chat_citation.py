import json

import pytest

from app.api.chat_stream import chat_stream_generator
from app.models.chat import ChatRequest


@pytest.mark.asyncio
async def test_citation_payload_includes_excerpt() -> None:
    long_text = "A" * 260
    request = ChatRequest(session_id="s-1", message="hi", kb_id="kb-1")
    pre_retrieved_results = [
        {
            "text": long_text,
            "score": 0.9,
            "metadata": {"doc_id": "doc-1", "chunk_index": 2}
        }
    ]

    citation_payload = None
    async for chunk in chat_stream_generator(request, [], pre_retrieved_results):
        if chunk.startswith("event: citation"):
            data_line = next(
                line for line in chunk.split("\n") if line.startswith("data: ")
            )
            citation_payload = json.loads(data_line[6:])
            break

    assert citation_payload is not None
    sources = citation_payload.get("sources", [])
    assert len(sources) == 1
    assert sources[0]["doc_id"] == "doc-1"
    assert sources[0]["chunk_index"] == 2
    assert sources[0]["text"].endswith("...")
    assert len(sources[0]["text"]) == 203
