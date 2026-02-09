"""
Knowledge base API endpoints for document management.
"""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.chroma_client import get_chroma_client
from app.core.knowledge_store import (
    add_task,
    allowed_file,
    ALLOWED_EXTENSIONS,
    cleanup_old_tasks,
    get_kb_document_count,
    get_kb_directories,
    get_upload_path,
    load_documents_metadata,
    load_kb_metadata,
    MAX_FILE_SIZE,
    processing_tasks,
    remove_kb_directories,
    save_documents_metadata,
    save_kb_metadata,
    update_document_status,
    update_task,
    validate_kb_id,
)
from app.core.rag import EmbeddingDimensionMismatchError, get_rag_pipeline
from app.models.document import (
    DocumentResponse,
    DocumentStatus,
    DocumentListResponse,
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
)
from app.core.auth import User, get_current_user
import uuid


router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


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
    timestamp = datetime.now(timezone.utc)

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

    add_task(task_id, {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": timestamp.isoformat()
    })

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


async def process_document_task(kb_id: str, doc_id: str, task_id: str | None = None):
    """Background task to process a document."""
    all_metadata = load_documents_metadata(kb_id)
    if doc_id not in all_metadata:
        return

    doc_data = all_metadata[doc_id]
    file_path = doc_data["file_path"]

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
            update_document_status(
                kb_id,
                doc_id,
                DocumentStatus.FAILED,
                error_msg
            )
            if task_id and task_id in processing_tasks:
                update_task(task_id, {"status": "failed", "error": error_msg})
    except Exception as e:
        update_document_status(kb_id, doc_id, DocumentStatus.FAILED, str(e))
        if task_id and task_id in processing_tasks:
            update_task(task_id, {"status": "failed", "error": str(e)})


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
    add_task(task_id, {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": datetime.now(timezone.utc).isoformat()
    })
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
    cleanup_old_tasks()
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
        results = await rag_pipeline.search(kb_id, query, top_k=top_k)
        
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
    except EmbeddingDimensionMismatchError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Knowledge base index is incompatible with current embedding model. "
                "Rebuild the knowledge base index and re-upload documents."
            )
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
        created_at = datetime.fromisoformat(kb_data.get("created_at", datetime.now(timezone.utc).isoformat()))
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
    timestamp = datetime.now(timezone.utc)
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
    # Validate kb_id format (fail-closed)
    if not validate_kb_id(kb_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid kb_id format: {kb_id}"
        )

    metadata = load_kb_metadata()
    if kb_id not in metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{kb_id}' not found"
        )

    chroma_client = get_chroma_client()
    chroma_client.delete_collection(kb_id)

    project_root = Path(__file__).parent.parent.parent
    upload_dir, metadata_dir = get_kb_directories(kb_id)

    # Containment check: ensure paths are within project_root
    try:
        upload_dir.resolve().relative_to(project_root.resolve())
        metadata_dir.resolve().relative_to(project_root.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid kb_id: path outside allowed directory"
        )

    remove_kb_directories(kb_id)

    del metadata[kb_id]
    save_kb_metadata(metadata)
