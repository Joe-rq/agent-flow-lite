"""
RAG (Retrieval-Augmented Generation) Pipeline using LlamaIndex.

This module provides core RAG functionality:
- Document loading from file paths
- Text chunking using SentenceSplitter
- Vectorization using SiliconFlow embeddings (BGE-M3)
- Storage to ChromaDB
- Retrieval of top-k relevant chunks
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding

from app.core.chroma_client import get_chroma_client
from app.core.config import settings


# Configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
TOP_K = 5

# SiliconFlow BGE-M3 embedding model
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"


class SiliconFlowEmbedding(OpenAIEmbedding):
    """SiliconFlow embedding adapter using OpenAI-compatible API."""

    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        api_key: Optional[str] = None,
        api_base: str = SILICONFLOW_API_BASE,
        **kwargs
    ):
        api_key = api_key or settings().siliconflow_api_key
        super().__init__(
            model=model,
            api_key=api_key,
            api_base=api_base,
            **kwargs
        )


class RAGPipeline:
    """RAG Pipeline for document processing and retrieval."""

    def __init__(self, embedding_model: Optional[str] = None):
        """Initialize the RAG pipeline."""
        self.embedding_model_name = embedding_model or DEFAULT_EMBEDDING_MODEL
        self.embed_model = SiliconFlowEmbedding(model=self.embedding_model_name)
        self.chroma_client = get_chroma_client()

        # Initialize sentence splitter for chunking
        self.node_parser = SentenceSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
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

    def chunk_document(self, content: str, doc_id: str) -> List[dict]:
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

    def process_document(self, kb_id: str, doc_id: str, file_path: str) -> dict:
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
            raw_embeddings = self.embed_model.get_text_embedding_batch(texts)
            embeddings: list[list[float]] = [
                [float(value) for value in embedding]
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

        except Exception as e:
            return {
                "status": "error",
                "doc_id": doc_id,
                "chunk_count": 0,
                "message": f"Error processing document: {str(e)}"
            }

    def search(
        self,
        kb_id: str,
        query: str,
        top_k: int = TOP_K
    ) -> List[dict]:
        """Search for relevant chunks in a knowledge base."""
        # Get collection
        try:
            collection = self.chroma_client.get_or_create_collection(kb_id)
        except Exception as e:
            raise ValueError(f"Knowledge base not found: {kb_id}") from e

        # Embed query
        query_embedding = self.embed_model.get_text_embedding(query)

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

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
    return RAGPipeline()
