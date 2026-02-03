
# Python (FastAPI) Implementation Plan

## User Review Required
> [!WARNING]
> This plan deviates from the original assessment requirement of using Node.js/NestJS.
> We are choosing Python (FastAPI) to deliver a higher quality RAG experience and efficiency.

## Proposed Changes

### Backend (Python/FastAPI)
#### [NEW] `backend/pyproject.toml`
- Dependency management using `uv`.
- Key dependencies: `fastapi`, `uvicorn`, `langchain`, `langgraph`, `asyncpg`, `pgvector`.

#### [NEW] `backend/app/main.py`
- Application entry point.
- Global exception handlers.

#### [NEW] `backend/app/api/`
- `v1/endpoints/chat.py`: Chat endpoints (SSE streaming).
- `v1/endpoints/workflow.py`: Workflow CRUD.
- `v1/endpoints/knowledge.py`: File upload & processing.

#### [NEW] `backend/app/core/rag.py`
- Document loading (`unstructured`).
- Text splitting (`SimpleDirectoryReader` or `RecursiveCharacterTextSplitter`).
- Vector store integration (`pgvector`).

### Frontend (Vue 3)
- Standard Vue 3 + Vite setup.
- `axios` for API requests.
- `EventSource` for SSE chat streaming.

## Verification Plan

### Automated Tests
- Run `pytest` for backend logic (RAG pipeline, API endpoints).
- Run `npm run test` for frontend components if needed.

### Manual Verification
1.  **Workflow**: Create a simple workflow in the UI -> Save -> Verify in DB.
2.  **RAG**: Upload a unique PDF -> Ask a question about its content -> Verify accurate answer & citation.
3.  **Chat**: engage in multi-turn conversation -> Verify context retention.
