"""Knowledge base API endpoints for document management."""
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse

from app.core.auth import User, get_current_user
from app.core.chroma_client import get_chroma_client
from app.core.knowledge.processor import (
    InvalidKBIdError,
    KBNotFoundError,
    build_document_responses,
    build_kb_list,
    create_document_record,
    create_kb,
    delete_document_files,
    delete_kb,
    process_document_task,
    start_document_processing,
)
from app.core.knowledge.store import (
    ALLOWED_EXTENSIONS,
    allowed_file,
    cleanup_old_tasks,
    load_documents_metadata,
    MAX_FILE_SIZE,
    processing_tasks,
)
from app.core.rag import EmbeddingDimensionMismatchError, get_rag_pipeline
from app.models.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatus,
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Upload a document and automatically trigger vectorization."""
    if not file.filename or not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Only {', '.join(ALLOWED_EXTENSIONS)} files are supported.",
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.",
        )

    doc_id, task_id, _path, metadata = create_document_record(kb_id, file.filename, content)
    background_tasks.add_task(process_document_task, kb_id, doc_id, task_id)

    return DocumentResponse(
        id=doc_id, kb_id=kb_id, filename=file.filename,
        status=DocumentStatus.PROCESSING, file_size=len(content),
        created_at=datetime.fromisoformat(metadata["created_at"]), task_id=task_id,
    )


@router.get("/{kb_id}/documents")
async def list_documents(
    kb_id: str, user: User = Depends(get_current_user)
) -> DocumentListResponse:
    """List all documents in a knowledge base."""
    documents = build_document_responses(kb_id)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str, doc_id: str, user: User = Depends(get_current_user)
) -> JSONResponse:
    """Delete a document from a knowledge base."""
    try:
        delete_document_files(kb_id, doc_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return JSONResponse(
        content={"message": "Document deleted successfully.", "doc_id": doc_id},
        status_code=status.HTTP_200_OK,
    )


@router.post("/{kb_id}/process/{doc_id}")
async def process_document(
    kb_id: str, doc_id: str, background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Process a document: parse, chunk, embed, and store to ChromaDB."""
    task_id, message, code = start_document_processing(kb_id, doc_id)
    if task_id is None:
        if code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        return JSONResponse(content={"message": message, "doc_id": doc_id}, status_code=code)

    background_tasks.add_task(process_document_task, kb_id, doc_id, task_id)
    return JSONResponse(
        content={"message": message, "doc_id": doc_id, "task_id": task_id},
        status_code=status.HTTP_202_ACCEPTED,
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
    user: User = Depends(get_current_user),
) -> dict:
    """Search for relevant chunks in a knowledge base."""
    if not query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")
    try:
        rag_pipeline = get_rag_pipeline()
        results = await rag_pipeline.search(kb_id, query, top_k=top_k)
        return {"kb_id": kb_id, "query": query, "top_k": top_k, "results": results, "total": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmbeddingDimensionMismatchError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Knowledge base index is incompatible with current embedding model. "
            "Rebuild the knowledge base index and re-upload documents.",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.get("/{kb_id}/info")
async def get_knowledge_base_info(kb_id: str, user: User = Depends(get_current_user)) -> dict:
    chroma_client = get_chroma_client()
    info = chroma_client.get_collection_info(kb_id)
    doc_count = len(load_documents_metadata(kb_id))
    return {
        "kb_id": kb_id, "collection_name": info["name"],
        "document_count": doc_count, "vector_count": info["count"],
        "collection_exists": info["count"] >= 0,
    }


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(user: User = Depends(get_current_user)) -> KnowledgeBaseListResponse:
    items = build_kb_list()
    return KnowledgeBaseListResponse(items=items, total=len(items))


@router.post("", response_model=KnowledgeBase, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate, user: User = Depends(get_current_user)
) -> KnowledgeBase:
    return create_kb(data.name)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: str, user: User = Depends(get_current_user)) -> None:
    project_root = Path(__file__).parent.parent.parent
    try:
        delete_kb(kb_id, project_root)
    except InvalidKBIdError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except KBNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
