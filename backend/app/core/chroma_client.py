"""
ChromaDB client wrapper for knowledge base storage.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings


class ChromaClient:
    """ChromaDB client wrapper for managing knowledge base collections."""

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist ChromaDB data.
                              Defaults to data/chromadb in project root.
        """
        if persist_directory is None:
            # Default to data/chromadb in project root
            project_root = Path(__file__).parent.parent.parent
            persist_directory = str(project_root / "data" / "chromadb")

        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

    def get_or_create_collection(self, kb_id: str) -> chromadb.Collection:
        """
        Get or create a collection for a knowledge base.

        Each knowledge base gets its own collection in ChromaDB.

        Args:
            kb_id: Knowledge base ID

        Returns:
            ChromaDB collection for the knowledge base
        """
        collection_name = f"kb_{kb_id}"
        return self._client.get_or_create_collection(name=collection_name)

    def delete_collection(self, kb_id: str) -> bool:
        """
        Delete a knowledge base collection.

        Args:
            kb_id: Knowledge base ID

        Returns:
            True if collection was deleted, False if it didn't exist
        """
        collection_name = f"kb_{kb_id}"
        try:
            self._client.delete_collection(name=collection_name)
            return True
        except (ValueError, Exception) as e:
            # Collection doesn't exist or other error
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                return False
            raise

    def collection_exists(self, kb_id: str) -> bool:
        """
        Check if a knowledge base collection exists.

        Args:
            kb_id: Knowledge base ID

        Returns:
            True if collection exists, False otherwise
        """
        collection_name = f"kb_{kb_id}"
        try:
            self._client.get_collection(name=collection_name)
            return True
        except ValueError:
            return False

    def add_document(
        self,
        kb_id: str,
        document_id: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Add a document to a knowledge base collection.

        Args:
            kb_id: Knowledge base ID
            document_id: Unique document ID
            content: Document content to embed
            metadata: Optional metadata dict
        """
        collection = self.get_or_create_collection(kb_id)

        # Prepare metadata
        doc_metadata = metadata or {}
        doc_metadata["document_id"] = document_id

        collection.add(
            documents=[content],
            ids=[document_id],
            metadatas=[doc_metadata]
        )

    def delete_document(self, kb_id: str, document_id: str) -> bool:
        """
        Delete a document from a knowledge base collection.

        Args:
            kb_id: Knowledge base ID
            document_id: Document ID to delete

        Returns:
            True if document was deleted, False if it didn't exist
        """
        try:
            collection = self._client.get_collection(name=f"kb_{kb_id}")
            collection.delete(where={"doc_id": document_id})
            return True
        except ValueError:
            return False
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False

    def get_collection_info(self, kb_id: str) -> dict:
        """
        Get information about a knowledge base collection.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Dict with collection info (count, etc.)
        """
        try:
            collection = self._client.get_collection(name=f"kb_{kb_id}")
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except ValueError:
            return {
                "name": f"kb_{kb_id}",
                "count": 0,
                "metadata": None
            }


@lru_cache(maxsize=1)
def get_chroma_client() -> ChromaClient:
    """
    Get the global ChromaDB client instance.

    Returns:
        ChromaClient instance
    """
    return ChromaClient()
