"""
Knowledge base API endpoints for document management.
"""
import json
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from filelock import FileLock

from app.core.chroma_client import get_chroma_client
from app.core.rag import get_rag_pipeline
from app.models.document import (
    DocumentResponse,
    DocumentStatus,
    DocumentListResponse,
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
)
from app.core.auth import User, get_current_user


router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

KB_METADATA_FILE = Path(__file__).parent.parent.parent / "data" / "kb_metadata.json"
processing_tasks: dict[str, dict] = {}
processing_tasks: dict[str, dict] = {}


def load_kb_metadata() -> dict:
    lock = FileLock(str(KB_METADATA_FILE) + ".lock")
    with lock:
        if not KB_METADATA_FILE.exists():
            return {}
        try:
            with open(KB_METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_kb_metadata(metadata: dict) -> None:
    KB_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(KB_METADATA_FILE) + ".lock")
    with lock:
        with open(KB_METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


def get_kb_document_count(kb_id: str) -> int:
    return len(load_documents_metadata(kb_id))
ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def secure_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal."""
    filename = Path(filename).name
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = filename.lstrip(".")
    filename = " ".join(filename.split())
    return filename or "unnamed_file"


def get_upload_path(kb_id: str, filename: str) -> tuple[Path, str]:
    """Get a safe path for saving an uploaded file."""
    safe_kb_id = re.sub(r"[^\w-]", "", kb_id) or "default"
    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / safe_kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(filename)
    unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    full_path = upload_dir / unique_filename

    try:
        full_path.resolve().relative_to(upload_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid file path detected") from exc

    return full_path, unique_filename


def get_metadata_path(kb_id: str) -> Path:
    """Get the path for document metadata JSON file."""
    project_root = Path(__file__).parent.parent.parent
    metadata_dir = project_root / "data" / "metadata" / kb_id
    metadata_dir.mkdir(parents=True, exist_ok=True)
    return metadata_dir / "documents.json"


def load_documents_metadata(kb_id: str) -> dict:
    """Load document metadata from JSON file."""
    metadata_path = get_metadata_path(kb_id)
    lock = FileLock(str(metadata_path) + ".lock")
    with lock:
        if not metadata_path.exists():
            return {}
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_documents_metadata(kb_id: str, metadata: dict) -> None:
    """Save document metadata to JSON file."""
    metadata_path = get_metadata_path(kb_id)
    lock = FileLock(str(metadata_path) + ".lock")
    with lock:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
) -> DocumentResponse:
    """
    Upload a document to a knowledge base.
    Automatically triggers vectorization processing after upload.

    - **kb_id**: Knowledge base ID (path parameter)
    - **file**: File to upload (.txt or .md, max 5MB)
    """
    if not file.filename or not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Only {', '.join(ALLOWED_EXTENSIONS)} files are supported."
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."
        )

    doc_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    file_path, stored_filename = get_upload_path(kb_id, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    metadata = {
        "id": doc_id,
        "kb_id": kb_id,
        "filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_size": file_size,
        "status": DocumentStatus.PENDING.value,
        "created_at": timestamp.isoformat(),
        "updated_at": None
    }

    all_metadata = load_documents_metadata(kb_id)
    all_metadata[doc_id] = metadata
    save_documents_metadata(kb_id, all_metadata)

    chroma_client = get_chroma_client()
    chroma_client.get_or_create_collection(kb_id)

    processing_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": timestamp.isoformat()
    }

    # Auto-trigger vectorization processing in background
    background_tasks.add_task(process_document_task, kb_id, doc_id, task_id)

    return DocumentResponse(
        id=doc_id,
        kb_id=kb_id,
        filename=file.filename,
        status=DocumentStatus.PROCESSING,
        file_size=file_size,
        created_at=timestamp,
        task_id=task_id
    )


@router.get("/{kb_id}/documents")
async def list_documents(kb_id: str, user: User = Depends(get_current_user)) -> DocumentListResponse:
    """
    List all documents in a knowledge base.

    - **kb_id**: Knowledge base ID
    """
    all_metadata = load_documents_metadata(kb_id)

    documents = []
    for doc_id, doc_data in all_metadata.items():
        created_at = datetime.fromisoformat(doc_data["created_at"])

        documents.append(DocumentResponse(
            id=doc_data["id"],
            kb_id=doc_data["kb_id"],
            filename=doc_data["filename"],
            status=DocumentStatus(doc_data["status"]),
            file_size=doc_data["file_size"],
            created_at=created_at
        ))

    documents.sort(key=lambda x: x.created_at, reverse=True)

    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(kb_id: str, doc_id: str, user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Delete a document from a knowledge base.

    - **kb_id**: Knowledge base ID
    - **doc_id**: Document ID to delete
    """
    all_metadata = load_documents_metadata(kb_id)

    if doc_id not in all_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    doc_data = all_metadata[doc_id]

    file_path = Path(doc_data["file_path"])
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass

    del all_metadata[doc_id]
    save_documents_metadata(kb_id, all_metadata)

    chroma_client = get_chroma_client()
    chroma_client.delete_document(kb_id, doc_id)

    return JSONResponse(
        content={"message": "Document deleted successfully.", "doc_id": doc_id},
        status_code=status.HTTP_200_OK
    )


def update_document_status(kb_id: str, doc_id: str, status: DocumentStatus, error_message: str | None = None):
    """Update document status in metadata."""
    all_metadata = load_documents_metadata(kb_id)
    if doc_id in all_metadata:
        all_metadata[doc_id]["status"] = status.value
        all_metadata[doc_id]["updated_at"] = datetime.utcnow().isoformat()
        if error_message:
            all_metadata[doc_id]["error_message"] = error_message
        save_documents_metadata(kb_id, all_metadata)


def process_document_task(kb_id: str, doc_id: str, task_id: str | None = None):
    """Background task to process a document."""
    all_metadata = load_documents_metadata(kb_id)
    if doc_id not in all_metadata:
        return

    doc_data = all_metadata[doc_id]
    file_path = doc_data["file_path"]

    update_document_status(kb_id, doc_id, DocumentStatus.PROCESSING)
    if task_id and task_id in processing_tasks:
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["progress"] = 10

    try:
        rag_pipeline = get_rag_pipeline()
        result = rag_pipeline.process_document(kb_id, doc_id, file_path)

        if result["status"] == "completed":
            update_document_status(kb_id, doc_id, DocumentStatus.COMPLETED)
            if task_id and task_id in processing_tasks:
                processing_tasks[task_id]["status"] = "completed"
                processing_tasks[task_id]["progress"] = 100
        else:
            update_document_status(
                kb_id,
                doc_id,
                DocumentStatus.FAILED,
                result.get("message", "Unknown error")
            )
            if task_id and task_id in processing_tasks:
                processing_tasks[task_id]["status"] = "failed"
                processing_tasks[task_id]["error"] = result.get("message", "Unknown error")
    except Exception as e:
        update_document_status(kb_id, doc_id, DocumentStatus.FAILED, str(e))
        if task_id and task_id in processing_tasks:
            processing_tasks[task_id]["status"] = "failed"
            processing_tasks[task_id]["error"] = str(e)


@router.post("/{kb_id}/process/{doc_id}")
async def process_document(
    kb_id: str,
    doc_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Process a document: parse, chunk, embed, and store to ChromaDB.
    
    - **kb_id**: Knowledge base ID
    - **doc_id**: Document ID to process
    """
    all_metadata = load_documents_metadata(kb_id)
    
    if doc_id not in all_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
    
    doc_data = all_metadata[doc_id]

    current_status = DocumentStatus(doc_data["status"])
    if current_status == DocumentStatus.PROCESSING:
        return JSONResponse(
            content={"message": "Document is already being processed.", "doc_id": doc_id},
            status_code=status.HTTP_200_OK
        )

    if current_status == DocumentStatus.COMPLETED:
        return JSONResponse(
            content={"message": "Document has already been processed.", "doc_id": doc_id},
            status_code=status.HTTP_200_OK
        )

    task_id = str(uuid.uuid4())
    processing_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": datetime.utcnow().isoformat()
    }
    background_tasks.add_task(process_document_task, kb_id, doc_id, task_id)
    
    return JSONResponse(
        content={
            "message": "Document processing started.",
            "doc_id": doc_id,
            "task_id": task_id
        },
        status_code=status.HTTP_202_ACCEPTED
    )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, user: User = Depends(get_current_user)) -> dict:
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return processing_tasks[task_id]


@router.get("/{kb_id}/search")
async def search_documents(
    kb_id: str,
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of top results to return", ge=1, le=20),
    user: User = Depends(get_current_user)
) -> dict:
    """
    Search for relevant chunks in a knowledge base.
    
    - **kb_id**: Knowledge base ID
    - **query**: Search query string
    - **top_k**: Number of top results to return (default: 5, max: 20)
    """
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )
    
    try:
        rag_pipeline = get_rag_pipeline()
        results = rag_pipeline.search(kb_id, query, top_k=top_k)
        
        return {
            "kb_id": kb_id,
            "query": query,
            "top_k": top_k,
            "results": results,
            "total": len(results)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/{kb_id}/info")
async def get_knowledge_base_info(kb_id: str, user: User = Depends(get_current_user)) -> dict:
    chroma_client = get_chroma_client()
    collection_info = chroma_client.get_collection_info(kb_id)
    all_metadata = load_documents_metadata(kb_id)
    doc_count = len(all_metadata)
    return {
        "kb_id": kb_id,
        "collection_name": collection_info["name"],
        "document_count": doc_count,
        "vector_count": collection_info["count"],
        "collection_exists": collection_info["count"] >= 0
    }


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(user: User = Depends(get_current_user)) -> KnowledgeBaseListResponse:
    metadata = load_kb_metadata()
    items = []
    for kb_id, kb_data in metadata.items():
        created_at = datetime.fromisoformat(kb_data.get("created_at", datetime.utcnow().isoformat()))
        document_count = get_kb_document_count(kb_id)
        items.append(KnowledgeBase(
            id=kb_id,
            name=kb_data.get("name", kb_id),
            document_count=document_count,
            created_at=created_at
        ))
    items.sort(key=lambda x: x.created_at, reverse=True)
    return KnowledgeBaseListResponse(items=items, total=len(items))


@router.post("", response_model=KnowledgeBase, status_code=201)
async def create_knowledge_base(data: KnowledgeBaseCreate, user: User = Depends(get_current_user)) -> KnowledgeBase:
    kb_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    metadata = load_kb_metadata()
    metadata[kb_id] = {
        "id": kb_id,
        "name": data.name,
        "created_at": timestamp.isoformat()
    }
    save_kb_metadata(metadata)
    chroma_client = get_chroma_client()
    chroma_client.get_or_create_collection(kb_id)
    return KnowledgeBase(
        id=kb_id,
        name=data.name,
        document_count=0,
        created_at=timestamp
    )




@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: str, user: User = Depends(get_current_user)) -> None:
    metadata = load_kb_metadata()
    if kb_id not in metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{kb_id}' not found"
        )

    chroma_client = get_chroma_client()
    chroma_client.delete_collection(kb_id)

    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / kb_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    metadata_dir = project_root / "data" / "metadata" / kb_id
    if metadata_dir.exists():
        shutil.rmtree(metadata_dir)

    del metadata[kb_id]
    save_kb_metadata(metadata)
