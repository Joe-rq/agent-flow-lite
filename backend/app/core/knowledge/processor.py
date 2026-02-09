"""Document processing and high-level knowledge-base operations.

Business logic extracted from the knowledge API layer: background document
processing, KB CRUD orchestration, and helpers that compose multiple
store-level operations.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.chroma_client import get_chroma_client
from app.core.knowledge.store import (
    add_task,
    get_kb_directories,
    get_kb_document_count,
    get_upload_path,
    load_documents_metadata,
    load_kb_metadata,
    processing_tasks,
    remove_kb_directories,
    save_documents_metadata,
    save_kb_metadata,
    update_document_status,
    update_task,
    validate_kb_id,
)
from app.core.rag import get_rag_pipeline
from app.models.document import DocumentResponse, DocumentStatus, KnowledgeBase


# ---------------------------------------------------------------------------
# Document-level operations
# ---------------------------------------------------------------------------

async def process_document_task(
    kb_id: str, doc_id: str, task_id: str | None = None
) -> None:
    """Background task to process (chunk + embed) a single document."""
    all_metadata = load_documents_metadata(kb_id)
    if doc_id not in all_metadata:
        return

    file_path = all_metadata[doc_id]["file_path"]
    update_document_status(kb_id, doc_id, DocumentStatus.PROCESSING)
    if task_id and task_id in processing_tasks:
        update_task(task_id, {"status": "processing", "progress": 10})

    try:
        rag_pipeline = get_rag_pipeline()
        result = await rag_pipeline.process_document(kb_id, doc_id, file_path)

        if result["status"] == "completed":
            update_document_status(kb_id, doc_id, DocumentStatus.COMPLETED)
            if task_id and task_id in processing_tasks:
                update_task(task_id, {"status": "completed", "progress": 100})
        else:
            error_msg = result.get("message", "Unknown error")
            update_document_status(kb_id, doc_id, DocumentStatus.FAILED, error_msg)
            if task_id and task_id in processing_tasks:
                update_task(task_id, {"status": "failed", "error": error_msg})
    except Exception as e:
        update_document_status(kb_id, doc_id, DocumentStatus.FAILED, str(e))
        if task_id and task_id in processing_tasks:
            update_task(task_id, {"status": "failed", "error": str(e)})


def create_document_record(
    kb_id: str, filename: str, content: bytes
) -> tuple[str, str, Path, dict]:
    """Save an uploaded file and create its metadata record.

    Returns (doc_id, task_id, file_path, metadata_dict).
    """
    doc_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    file_path, stored_filename = get_upload_path(kb_id, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    metadata = {
        "id": doc_id,
        "kb_id": kb_id,
        "filename": filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_size": len(content),
        "status": DocumentStatus.PENDING.value,
        "created_at": timestamp.isoformat(),
        "updated_at": None,
    }

    all_metadata = load_documents_metadata(kb_id)
    all_metadata[doc_id] = metadata
    save_documents_metadata(kb_id, all_metadata)

    chroma_client = get_chroma_client()
    chroma_client.get_or_create_collection(kb_id)

    add_task(task_id, {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": timestamp.isoformat(),
    })

    return doc_id, task_id, file_path, metadata


def build_document_responses(kb_id: str) -> list[DocumentResponse]:
    """Build a sorted list of DocumentResponse for all docs in a KB."""
    all_metadata = load_documents_metadata(kb_id)
    documents = [
        DocumentResponse(
            id=doc["id"],
            kb_id=doc["kb_id"],
            filename=doc["filename"],
            status=DocumentStatus(doc["status"]),
            file_size=doc["file_size"],
            created_at=datetime.fromisoformat(doc["created_at"]),
        )
        for doc in all_metadata.values()
    ]
    documents.sort(key=lambda d: d.created_at, reverse=True)
    return documents


def delete_document_files(kb_id: str, doc_id: str) -> dict:
    """Delete a document's file, metadata entry, and chroma vectors.

    Returns the removed metadata dict, or raises KeyError if not found.
    """
    all_metadata = load_documents_metadata(kb_id)
    if doc_id not in all_metadata:
        raise KeyError(doc_id)

    doc_data = all_metadata.pop(doc_id)
    file_path = Path(doc_data["file_path"])
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass

    save_documents_metadata(kb_id, all_metadata)
    chroma_client = get_chroma_client()
    chroma_client.delete_document(kb_id, doc_id)
    return doc_data


def start_document_processing(kb_id: str, doc_id: str) -> tuple[str | None, str, int]:
    """Check document status and create a processing task if eligible.

    Returns (task_id, message, http_status_code).
    task_id is None when processing is not started (already done / in progress).
    """
    all_metadata = load_documents_metadata(kb_id)
    if doc_id not in all_metadata:
        return None, "Document not found.", 404

    current = DocumentStatus(all_metadata[doc_id]["status"])
    if current == DocumentStatus.PROCESSING:
        return None, "Document is already being processed.", 200
    if current == DocumentStatus.COMPLETED:
        return None, "Document has already been processed.", 200

    task_id = str(uuid.uuid4())
    add_task(task_id, {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })
    return task_id, "Document processing started.", 202


# ---------------------------------------------------------------------------
# Knowledge-base-level operations
# ---------------------------------------------------------------------------

def build_kb_list() -> list[KnowledgeBase]:
    """Build a sorted list of KnowledgeBase models."""
    metadata = load_kb_metadata()
    items = []
    for kb_id, kb_data in metadata.items():
        created_at = datetime.fromisoformat(
            kb_data.get("created_at", datetime.now(timezone.utc).isoformat())
        )
        items.append(KnowledgeBase(
            id=kb_id, name=kb_data.get("name", kb_id),
            document_count=get_kb_document_count(kb_id), created_at=created_at,
        ))
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items


def create_kb(name: str) -> KnowledgeBase:
    """Create a new knowledge base (metadata + chroma collection)."""
    kb_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    metadata = load_kb_metadata()
    metadata[kb_id] = {"id": kb_id, "name": name, "created_at": timestamp.isoformat()}
    save_kb_metadata(metadata)
    chroma_client = get_chroma_client()
    chroma_client.get_or_create_collection(kb_id)
    return KnowledgeBase(id=kb_id, name=name, document_count=0, created_at=timestamp)


class KBNotFoundError(Exception):
    """Raised when a knowledge base ID does not exist."""


class InvalidKBIdError(Exception):
    """Raised when a knowledge base ID has invalid format or path."""


def delete_kb(kb_id: str, project_root: Path) -> None:
    """Delete a knowledge base: chroma, files, and metadata.

    Raises InvalidKBIdError for bad format or path traversal.
    Raises KBNotFoundError when kb_id is missing from metadata.
    """
    if not validate_kb_id(kb_id):
        raise InvalidKBIdError(f"Invalid kb_id format: {kb_id}")

    metadata = load_kb_metadata()
    if kb_id not in metadata:
        raise KBNotFoundError(f"Knowledge base '{kb_id}' not found")

    chroma_client = get_chroma_client()
    chroma_client.delete_collection(kb_id)

    upload_dir, metadata_dir = get_kb_directories(kb_id)
    try:
        upload_dir.resolve().relative_to(project_root.resolve())
        metadata_dir.resolve().relative_to(project_root.resolve())
    except ValueError:
        raise InvalidKBIdError("Invalid kb_id: path outside allowed directory")

    remove_kb_directories(kb_id)
    del metadata[kb_id]
    save_kb_metadata(metadata)
