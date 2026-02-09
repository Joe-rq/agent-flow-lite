"""
RAG Pipeline: document loading, chunking, embedding, and retrieval.

Uses SiliconFlow BGE-M3 for embeddings via OpenAI-compatible API,
LlamaIndex for text chunking, and ChromaDB for vector storage.
"""
from functools import lru_cache
from pathlib import Path
import re

from chromadb.errors import InvalidArgumentError
from chromadb.api.types import Embedding
import numpy as np
from openai import AsyncOpenAI
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from app.core.chroma_client import get_chroma_client
from app.core.config import settings


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
        (r"Embedding dimension\s+(\d+)\s+does not match collection dimensionality\s+(\d+)", False),
        (r"Dimensionality of\s*\((\d+)\)\s*does not match index dimensionality\s*\((\d+)\)", False),
    ]

    for pattern, swap in patterns:
        match = re.search(pattern, message)
        if match:
            first, second = int(match.group(1)), int(match.group(2))
            return (second, first) if swap else (first, second)

    return None, None


class SiliconFlowEmbedding:
    """SiliconFlow embedding client using OpenAI-compatible API."""

    def __init__(self, model: str = DEFAULT_EMBEDDING_MODEL):
        s = settings()
        self.model = model
        self.client = AsyncOpenAI(
            api_key=s.siliconflow_api_key,
            base_url=s.siliconflow_api_base,
        )

    async def get_text_embedding(self, text: str) -> list[float]:
        """Get embedding for a single text."""
        resp = await self.client.embeddings.create(model=self.model, input=[text])
        return resp.data[0].embedding

    async def get_text_embedding_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a batch of texts."""
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in resp.data]


class RAGPipeline:
    """RAG Pipeline for document processing and retrieval."""

    def __init__(self, embedding_model: str | None = None):
        self.embedding_model_name = embedding_model or DEFAULT_EMBEDDING_MODEL
        self.embed_model = SiliconFlowEmbedding(model=self.embedding_model_name)
        self.chroma_client = get_chroma_client()
        self.node_parser = SentenceSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )

    def load_document(self, file_path: str) -> str:
        """Load document content from a file path."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in [".txt", ".md"]:
            raise ValueError(f"Unsupported file type: {path.suffix}. Only .txt and .md are supported.")

        # Read file content
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return content

    def chunk_document(self, content: str, doc_id: str) -> list[dict]:
        """Split document content into chunks."""
        # Create LlamaIndex document
        doc = LlamaDocument(text=content)

        # Parse into nodes (chunks)
        nodes = self.node_parser.get_nodes_from_documents([doc])

        chunks = []
        for idx, node in enumerate(nodes):
            chunk_text = node.get_content()
            chunk = {
                "text": chunk_text,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "chunk_size": len(chunk_text),
                }
            }
            chunks.append(chunk)

        return chunks

    async def process_document(self, kb_id: str, doc_id: str, file_path: str) -> dict:
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
                    "message": "Document processed but no chunks generated (empty file)"
                }

            # Step 3: Get collection and prepare for insertion
            collection = self.chroma_client.get_or_create_collection(kb_id)

            # Step 4: Embed and store chunks
            texts = [chunk["text"] for chunk in chunks]
            raw_embeddings = await self.embed_model.get_text_embedding_batch(texts)
            embeddings: list[Embedding] = [
                np.asarray(embedding, dtype=np.float32)
                for embedding in raw_embeddings
            ]

            # Prepare IDs and metadata for ChromaDB
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [chunk["metadata"] for chunk in chunks]

            # Add to ChromaDB
            collection.add(
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )

            return {
                "status": "completed",
                "doc_id": doc_id,
                "chunk_count": len(chunks),
                "message": f"Successfully processed document into {len(chunks)} chunks"
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
                "message": mismatch_detail
            }

        except Exception as e:
            return {
                "status": "error",
                "doc_id": doc_id,
                "chunk_count": 0,
                "message": f"Error processing document: {str(e)}"
            }

    async def search(
        self,
        kb_id: str,
        query: str,
        top_k: int = TOP_K
    ) -> list[dict]:
        """Search for relevant chunks in a knowledge base."""
        # Get collection
        try:
            collection = self.chroma_client.get_or_create_collection(kb_id)
        except Exception as e:
            raise ValueError(f"Knowledge base not found: {kb_id}") from e

        # Embed query
        query_embedding = await self.embed_model.get_text_embedding(query)
        query_vector: Embedding = np.asarray(query_embedding, dtype=np.float32)

        # Query ChromaDB
        try:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        except InvalidArgumentError as exc:
            incoming_dim, existing_dim = _parse_dimension_mismatch(str(exc))
            raise EmbeddingDimensionMismatchError(
                f"Embedding dimension mismatch for knowledge base '{kb_id}'"
                f" (incoming={incoming_dim}, existing={existing_dim}). "
                "Rebuild the knowledge base index after changing embedding model."
            ) from exc

        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                # Convert distance to similarity score (ChromaDB returns L2 distance)
                # Lower distance = higher similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                # Normalize to 0-1 range (approximate)
                similarity = 1 / (1 + distance)

                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": round(similarity, 4)
                })

        return formatted_results


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    """Get the global RAG pipeline instance."""
    return RAGPipeline(embedding_model=settings().embedding_model)
