"""
RAG (Retrieval-Augmented Generation) Pipeline using LlamaIndex.

This module provides core RAG functionality:
- Document loading from file paths
- Text chunking using SentenceSplitter
- Vectorization using HuggingFace embeddings
- Storage to ChromaDB
- Retrieval of top-k relevant chunks
"""
import os
from pathlib import Path
from typing import List, Optional

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.core.chroma_client import get_chroma_client


# Configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
TOP_K = 5

# Use a lightweight multilingual embedding model
# BAAI/bge-small-zh-v1.5 is good for Chinese and English
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


class RAGPipeline:
    """
    RAG Pipeline for document processing and retrieval.
    
    Uses LlamaIndex for document processing and ChromaDB for vector storage.
    """
    
    def __init__(self, embedding_model: Optional[str] = None):
        """
        Initialize the RAG pipeline.
        
        Args:
            embedding_model: HuggingFace model name for embeddings.
                           Defaults to BAAI/bge-small-zh-v1.5
        """
        self.embedding_model_name = embedding_model or DEFAULT_EMBEDDING_MODEL
        self.embed_model = HuggingFaceEmbedding(model_name=self.embedding_model_name)
        self.chroma_client = get_chroma_client()
        
        # Initialize sentence splitter for chunking
        self.node_parser = SentenceSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
    
    def load_document(self, file_path: str) -> str:
        """
        Load document content from a file path.
        
        Supports .txt and .md files.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
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
        """
        Split document content into chunks.
        
        Args:
            content: Document content
            doc_id: Document ID for metadata
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
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
        """
        Process a document: load, chunk, embed, and store.
        
        Args:
            kb_id: Knowledge base ID
            doc_id: Document ID
            file_path: Path to the document file
            
        Returns:
            Processing result with chunk count and status
        """
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
            embeddings = self.embed_model.get_text_embedding_batch(texts)
            
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
        """
        Search for relevant chunks in a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            query: Search query
            top_k: Number of top results to return (default: 5)
            
        Returns:
            List of result dictionaries with text, metadata, and score
        """
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
                similarity = max(0, 1 - distance)
                
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": round(similarity, 4)
                })
        
        return formatted_results


# Global RAG pipeline instance
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Get the global RAG pipeline instance.
    
    Returns:
        RAGPipeline instance
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
