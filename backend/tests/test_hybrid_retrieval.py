from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.rag import RAGPipeline


@pytest.mark.asyncio
async def test_hybrid_retrieval_returns_fts_results_when_embeddings_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from app.core.knowledge import fts as fts_module

    monkeypatch.setattr(fts_module, "DATA_DIR", tmp_path)

    kb_id = "kb-1"
    doc_id = "doc-1"
    chunks = [
        {"text": "alpha beta gamma", "metadata": {"doc_id": doc_id, "chunk_index": 0}},
        {"text": "delta epsilon", "metadata": {"doc_id": doc_id, "chunk_index": 1}},
    ]
    fts_module.index_document_chunks(kb_id, doc_id, chunks)

    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chroma_client = MagicMock()
    pipeline.chroma_client.get_or_create_collection.return_value = MagicMock()
    pipeline.embed_model = MagicMock()
    pipeline.embed_model.get_text_embedding = AsyncMock(
        side_effect=RuntimeError("no key")
    )

    results = await pipeline.search(kb_id, "beta", top_k=5)
    assert results
    assert results[0]["text"] == "alpha beta gamma"
    assert set(results[0].keys()) == {"text", "metadata", "score"}


@pytest.mark.asyncio
async def test_hybrid_retrieval_vector_path_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chroma_client = MagicMock()
    collection = MagicMock()
    pipeline.chroma_client.get_or_create_collection.return_value = collection

    pipeline.embed_model = MagicMock()
    pipeline.embed_model.get_text_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

    collection.query.return_value = {
        "documents": [["hello world"]],
        "metadatas": [[{"doc_id": "d1", "chunk_index": 2}]],
        "distances": [[0.0]],
    }

    monkeypatch.setattr("app.core.knowledge.fts.keyword_search", lambda *a, **k: [])

    results = await pipeline.search("kb-1", "hello", top_k=5)
    assert results == [
        {
            "text": "hello world",
            "metadata": {"doc_id": "d1", "chunk_index": 2},
            "score": 1.0,
        }
    ]


@pytest.mark.asyncio
async def test_hybrid_retrieval_merges_and_dedupes_vector_and_fts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chroma_client = MagicMock()
    collection = MagicMock()
    pipeline.chroma_client.get_or_create_collection.return_value = collection

    pipeline.embed_model = MagicMock()
    pipeline.embed_model.get_text_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    collection.query.return_value = {
        "documents": [["same chunk"]],
        "metadatas": [[{"doc_id": "d1", "chunk_index": 0, "chunk_id": "d1_chunk_0"}]],
        "distances": [[0.0]],
    }

    monkeypatch.setattr(
        "app.core.knowledge.fts.keyword_search",
        lambda *a, **k: [
            {
                "text": "same chunk",
                "metadata": {
                    "doc_id": "d1",
                    "chunk_index": 0,
                    "chunk_id": "d1_chunk_0",
                },
                "score": 0.2,
            }
        ],
    )

    results = await pipeline.search("kb-1", "same", top_k=5)
    assert len(results) == 1
    assert results[0]["text"] == "same chunk"
    assert results[0]["score"] == 1.0


@pytest.mark.asyncio
async def test_hybrid_retrieval_rerank_failure_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAG_ENABLE_RERANK", "1")
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chroma_client = MagicMock()
    collection = MagicMock()
    pipeline.chroma_client.get_or_create_collection.return_value = collection

    pipeline.embed_model = MagicMock()
    pipeline.embed_model.get_text_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    collection.query.return_value = {
        "documents": [["hello"]],
        "metadatas": [[{"doc_id": "d1", "chunk_index": 0}]],
        "distances": [[0.0]],
    }

    monkeypatch.setattr("app.core.knowledge.fts.keyword_search", lambda *a, **k: [])

    def _bad_import(_name: str):
        return SimpleNamespace(
            rerank=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom"))
        )

    monkeypatch.setattr("app.core.rag.importlib.import_module", _bad_import)

    results = await pipeline.search("kb-1", "hello", top_k=5)
    assert results and results[0]["text"] == "hello"
