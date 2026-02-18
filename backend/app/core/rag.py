"""
RAG Pipeline: document loading, chunking, embedding, and retrieval.

Uses SiliconFlow BGE-M3 for embeddings via OpenAI-compatible API,
LlamaIndex for text chunking, and ChromaDB for vector storage.
"""

import logging
import asyncio
import os
from functools import lru_cache
from pathlib import Path
import re
import importlib
from typing import Any

from chromadb.errors import InvalidArgumentError
from chromadb.api.types import Embedding
import numpy as np
from openai import AsyncOpenAI
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from app.core.chroma_client import get_chroma_client
from app.core.config import settings

logger = logging.getLogger(__name__)


CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
TOP_K = 5
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"


class EmbeddingDimensionMismatchError(RuntimeError):
    """Raised when embedding dimensions do not match collection dimensions."""


def _parse_dimension_mismatch(message: str) -> tuple[int | None, int | None]:
    """Extract (incoming, existing) dimensions from Chroma error text.

    Returns:
        (incoming_dim, existing_collection_dim) or (None, None).
    """
    # Each entry: (pattern, swap) — swap=True when group order is (existing, incoming)
    patterns: list[tuple[str, bool]] = [
        (r"expecting embedding with dimension of\s+(\d+),\s+got\s+(\d+)", True),
        (
            r"Embedding dimension\s+(\d+)\s+does not match collection dimensionality\s+(\d+)",
            False,
        ),
        (
            r"Dimensionality of\s*\((\d+)\)\s*does not match index dimensionality\s*\((\d+)\)",
            False,
        ),
    ]

    for pattern, swap in patterns:
        match = re.search(pattern, message)
        if match:
            first, second = int(match.group(1)), int(match.group(2))
            return (second, first) if swap else (first, second)

    return None, None


class OpenAICompatibleEmbedding:
    """Embedding client using any OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def get_text_embedding(self, text: str) -> list[float]:
        """Get embedding for a single text."""
        resp = await self.client.embeddings.create(model=self.model, input=[text])
        return resp.data[0].embedding

    async def get_text_embedding_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a batch of texts."""
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in resp.data]


# Backwards-compatible alias
SiliconFlowEmbedding = OpenAICompatibleEmbedding

_EMBEDDING_PROVIDERS = ("siliconflow", "openai", "ollama")


def create_embedding_model(
    provider: str | None = None,
    model: str | None = None,
) -> OpenAICompatibleEmbedding:
    """Create an embedding client based on the configured provider.

    Args:
        provider: Override embedding provider (siliconflow/openai/ollama).
                  Defaults to settings().embedding_provider.
        model: Override embedding model name.
               Defaults to the model configured for the chosen provider.
    """
    s = settings()
    provider = (provider or s.embedding_provider).strip().lower()

    if provider == "openai":
        api_key = s.openai_api_key
        base_url = s.openai_api_base
        default_model = s.openai_embedding_model
    elif provider == "ollama":
        api_key = s.ollama_api_key
        base_url = s.ollama_api_base
        default_model = s.ollama_embedding_model
    else:
        # Default: siliconflow
        api_key = s.siliconflow_api_key
        base_url = s.siliconflow_api_base
        default_model = s.embedding_model

    resolved_model = (model or default_model).strip()
    if not resolved_model:
        raise ValueError(
            f"Embedding model not configured for provider '{provider}'"
        )

    return OpenAICompatibleEmbedding(
        api_key=api_key,
        base_url=base_url,
        model=resolved_model,
    )


class RAGPipeline:
    """RAG Pipeline for document processing and retrieval."""

    def __init__(self, embedding_model: str | None = None):
        self.embedding_model_name = embedding_model or DEFAULT_EMBEDDING_MODEL
        self.embed_model = create_embedding_model(model=self.embedding_model_name)
        self.chroma_client = get_chroma_client()
        self.node_parser = SentenceSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )

    def _load_text_document(self, path: Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_pdf_document(self, path: Path) -> str:
        fitz = importlib.import_module("fitz")
        pages: list[str] = []
        with fitz.open(path) as pdf:
            for page in pdf:
                page_text = page.get_text("text")
                if page_text:
                    pages.append(page_text)
        return "\n\n".join(pages)

    def _load_docx_document(self, path: Path) -> str:
        docx = importlib.import_module("docx")
        document = docx.Document(path)
        lines = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        return "\n".join(lines)

    def load_document(self, file_path: str) -> str:
        """Load document content from a file path."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return self._load_text_document(path)
        if suffix == ".pdf":
            return self._load_pdf_document(path)
        if suffix == ".docx":
            return self._load_docx_document(path)
        raise ValueError(
            f"Unsupported file type: {path.suffix}. "
            "Only .txt, .md, .pdf, and .docx are supported."
        )

    def chunk_document(self, content: str, doc_id: str) -> list[dict[str, Any]]:
        """Split document content into chunks."""
        # Create LlamaIndex document
        doc = LlamaDocument(text=content)

        # Parse into nodes (chunks)
        nodes = self.node_parser.get_nodes_from_documents([doc])

        chunks = []
        for idx, node in enumerate(nodes):
            chunk_text = node.get_content()
            chunk_id = f"{doc_id}_chunk_{idx}"
            chunk = {
                "text": chunk_text,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                    "chunk_size": len(chunk_text),
                },
            }
            chunks.append(chunk)

        return chunks

    async def process_document(
        self, kb_id: str, doc_id: str, file_path: str
    ) -> dict[str, Any]:
        """Process a document: load, chunk, embed, and store."""
        try:
            # Step 1: Load document
            content = self.load_document(file_path)

            # Step 2: Chunk document
            chunks = self.chunk_document(content, doc_id)

            if not chunks:
                return {
                    "status": "completed",
                    "doc_id": doc_id,
                    "chunk_count": 0,
                    "message": "Document processed but no chunks generated (empty file)",
                }

            try:
                from app.core.knowledge.fts import index_document_chunks

                await asyncio.to_thread(index_document_chunks, kb_id, doc_id, chunks)
            except Exception:
                logger.warning(
                    "FTS indexing failed for doc '%s' in kb '%s'",
                    doc_id,
                    kb_id,
                    exc_info=True,
                )

            # Step 3: Get collection and prepare for insertion
            collection = await asyncio.to_thread(
                self.chroma_client.get_or_create_collection,
                kb_id,
            )

            # Step 4: Embed and store chunks
            texts = [chunk["text"] for chunk in chunks]
            raw_embeddings = await self.embed_model.get_text_embedding_batch(texts)
            embeddings: list[Embedding] = [
                np.asarray(embedding, dtype=np.float32) for embedding in raw_embeddings
            ]

            # Prepare IDs and metadata for ChromaDB
            ids = [
                str(chunk.get("metadata", {}).get("chunk_id") or f"{doc_id}_chunk_{i}")
                for i, chunk in enumerate(chunks)
            ]
            metadatas = [chunk["metadata"] for chunk in chunks]

            # Add to ChromaDB
            await asyncio.to_thread(
                collection.add,
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
            )

            return {
                "status": "completed",
                "doc_id": doc_id,
                "chunk_count": len(chunks),
                "message": f"Successfully processed document into {len(chunks)} chunks",
            }

        except InvalidArgumentError as exc:
            incoming_dim, existing_dim = _parse_dimension_mismatch(str(exc))
            mismatch_detail = (
                f"Embedding dimension mismatch for knowledge base '{kb_id}'"
                f" (incoming={incoming_dim}, existing={existing_dim}). "
                "Rebuild the knowledge base index after changing embedding model."
            )
            return {
                "status": "error",
                "doc_id": doc_id,
                "chunk_count": 0,
                "message": mismatch_detail,
            }

        except Exception as e:
            logger.warning(
                "Error processing document '%s' in kb '%s'",
                doc_id,
                kb_id,
                exc_info=True,
            )
            return {
                "status": "error",
                "doc_id": doc_id,
                "chunk_count": 0,
                "message": f"Error processing document: {str(e)}",
            }

    async def search(
        self, kb_id: str, query: str, top_k: int = TOP_K
    ) -> list[dict[str, Any]]:
        """Search for relevant chunks in a knowledge base."""
        # Get collection
        try:
            collection = await asyncio.to_thread(
                self.chroma_client.get_or_create_collection,
                kb_id,
            )
        except Exception as e:
            logger.warning("Failed to get collection for kb '%s'", kb_id, exc_info=True)
            raise ValueError(f"Knowledge base not found: {kb_id}") from e

        vector_results: list[dict[str, Any]] = []
        try:
            query_embedding = await self.embed_model.get_text_embedding(query)
            query_vector: Embedding = np.asarray(query_embedding, dtype=np.float32)

            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 / (1 + distance)
                    vector_results.append(
                        {
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i]
                            if results["metadatas"]
                            else {},
                            "score": round(similarity, 4),
                        }
                    )
        except InvalidArgumentError as exc:
            incoming_dim, existing_dim = _parse_dimension_mismatch(str(exc))
            raise EmbeddingDimensionMismatchError(
                f"Embedding dimension mismatch for knowledge base '{kb_id}'"
                f" (incoming={incoming_dim}, existing={existing_dim}). "
                "Rebuild the knowledge base index after changing embedding model."
            ) from exc
        except Exception:
            logger.warning("Vector retrieval failed for kb '%s'", kb_id, exc_info=True)

        fts_results: list[dict[str, Any]] = []
        try:
            from app.core.knowledge.fts import keyword_search

            fts_results = await asyncio.to_thread(
                keyword_search, kb_id, query, limit=max(top_k, 1)
            )
        except Exception:
            logger.warning("FTS retrieval failed for kb '%s'", kb_id, exc_info=True)

        merged = self._merge_and_dedupe(vector_results, fts_results)
        merged = self._maybe_rerank(query, merged)
        return merged[:top_k]

    @staticmethod
    def _result_key(item: dict[str, Any]) -> str:
        meta = item.get("metadata")
        if isinstance(meta, dict):
            chunk_id = meta.get("chunk_id")
            if isinstance(chunk_id, str) and chunk_id:
                return f"chunk:{chunk_id}"
            doc_id = meta.get("doc_id")
            chunk_index = meta.get("chunk_index")
            if doc_id and isinstance(chunk_index, int):
                return f"doc:{doc_id}:chunk:{chunk_index}"
        return f"text:{str(item.get('text') or '')}"

    def _merge_and_dedupe(
        self,
        vector_results: list[dict[str, Any]],
        fts_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for item in vector_results + fts_results:
            if not isinstance(item, dict):
                continue
            key = self._result_key(item)
            if key not in merged:
                merged[key] = item
                continue
            try:
                merged[key]["score"] = round(
                    max(
                        float(merged[key].get("score", 0.0)),
                        float(item.get("score", 0.0)),
                    ),
                    4,
                )
            except Exception:
                pass

        items = list(merged.values())
        items.sort(
            key=lambda x: (
                -float(x.get("score") or 0.0),
                self._result_key(x),
            )
        )
        return items

    def _maybe_rerank(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        flag = os.getenv("RAG_ENABLE_RERANK", "").strip().lower()
        if flag not in {"1", "true", "yes", "on"}:
            return results

        try:
            module = importlib.import_module("app.core.rerank")
            rerank_fn = getattr(module, "rerank", None)
            if not callable(rerank_fn):
                logger.warning(
                    "Rerank enabled but app.core.rerank.rerank is unavailable; falling back"
                )
                return results

            reranked = rerank_fn(query, results)
            if not isinstance(reranked, list):
                logger.warning("Rerank returned non-list; falling back")
                return results
            return reranked
        except Exception:
            logger.warning("Rerank failed; falling back", exc_info=True)
            return results


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    """Get the global RAG pipeline instance."""
    return RAGPipeline(embedding_model=settings().embedding_model)
