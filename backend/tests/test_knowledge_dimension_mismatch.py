"""Tests for embedding dimension mismatch handling in knowledge retrieval."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from chromadb.errors import InvalidArgumentError
from fastapi import HTTPException

from app.api.knowledge import search_documents
from app.core.rag import EmbeddingDimensionMismatchError, RAGPipeline


@pytest.mark.asyncio
async def test_rag_search_raises_domain_error_on_dimension_mismatch() -> None:
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chroma_client = MagicMock()
    pipeline.embed_model = MagicMock()

    collection = MagicMock()
    pipeline.chroma_client.get_or_create_collection.return_value = collection
    pipeline.embed_model.get_text_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    collection.query.side_effect = InvalidArgumentError(
        "Collection expecting embedding with dimension of 512, got 1024"
    )

    with pytest.raises(EmbeddingDimensionMismatchError) as exc_info:
        await pipeline.search("kb-1", "AI", top_k=5)

    message = str(exc_info.value)
    assert "kb-1" in message
    assert "incoming=1024" in message
    assert "existing=512" in message


@pytest.mark.asyncio
async def test_search_documents_returns_409_on_dimension_mismatch() -> None:
    rag_pipeline = MagicMock()
    rag_pipeline.search.side_effect = EmbeddingDimensionMismatchError("dimension mismatch")

    with patch("app.api.knowledge.get_rag_pipeline", return_value=rag_pipeline):
        with pytest.raises(HTTPException) as exc_info:
            await search_documents(kb_id="kb-1", query="AI", top_k=5, user=MagicMock())

    assert exc_info.value.status_code == 409
    assert "incompatible with current embedding model" in str(exc_info.value.detail)
