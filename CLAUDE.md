# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Flow Lite is a lightweight AI agent orchestration platform with visual workflow editing, RAG knowledge retrieval, and intelligent chat capabilities. It's a full-stack application demonstrating modern AI integration patterns.

**Tech Stack:**
- Frontend: Vue 3 + Vite + TypeScript + Vue Flow
- Backend: FastAPI + Python 3.11+ + LlamaIndex + ChromaDB
- AI: DeepSeek API (LLM) + SiliconFlow API (embeddings)

## Development Commands

### Frontend (frontend/)

```bash
cd frontend

# Install dependencies
npm install

# Development server (http://localhost:5173)
npm run dev

# Type checking
npm run type-check

# Linting (runs oxlint + eslint)
npm run lint

# Format code
npm run format

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Production build
npm run build
```

### Backend (backend/)

```bash
cd backend

# Create virtual environment (first time only)
uv venv

# Install dependencies
uv pip install -e .

# Development server (http://localhost:8000)
uv run uvicorn main:app --reload

# Manual API tests
uv run python test_chat_api.py
uv run python test_deepseek.py
```

### Quick Start Scripts

```bash
# Install all dependencies (frontend + backend)
./install.sh

# Start both servers
./start.sh

# Stop all servers
./stop.sh
```

## Architecture Overview

### Backend Architecture

**Entry Point:** `backend/main.py` - FastAPI app with CORS middleware and router registration

**API Routers** (`backend/app/api/`):
- `chat.py` - SSE streaming chat with RAG integration and workflow execution
- `knowledge.py` - Knowledge base and document management
- `workflow.py` - Workflow CRUD and execution

**Core Logic** (`backend/app/core/`):
- `rag.py` - RAG pipeline: document loading, chunking (LlamaIndex SentenceSplitter), embedding (SiliconFlow BGE-M3), and retrieval (ChromaDB)
- `llm.py` - DeepSeek API client wrapper for streaming chat completions
- `workflow_engine.py` - Graph-based workflow executor with BFS traversal
- `workflow_nodes.py` - Node execution handlers (start, llm, knowledge, condition, end)
- `workflow_context.py` - Execution context with variable resolution and template interpolation
- `chroma_client.py` - ChromaDB client singleton with collection management
- `config.py` - Pydantic settings with .env loading

**Data Models** (`backend/app/models/`):
- `chat.py` - Chat messages, requests, and session history
- `workflow.py` - Workflow graph structure (nodes, edges, metadata)
- `document.py` - Document and knowledge base schemas

**Runtime Data** (`backend/data/`):
- `uploads/{kb_id}/` - Uploaded documents
- `metadata/{kb_id}/` - Knowledge base metadata (JSON)
- `sessions/{session_id}.json` - Chat session history
- `chromadb/` - Vector database persistence

### Frontend Architecture

**Entry Point:** `frontend/src/main.ts` - Vue app with Pinia and router

**Views** (`frontend/src/views/`):
- `HomeView.vue` - Landing page
- `WorkflowView.vue` - Workflow list and management
- `WorkflowEditor.vue` - Visual workflow editor (Vue Flow canvas with top toolbar + right drawer + left info panel)
- `KnowledgeView.vue` - Knowledge base management with document upload
- `ChatView.vue` - Chat interface selector
- `ChatTerminal.vue` - SSE streaming chat terminal with thought process display

**Node Components** (`frontend/src/components/nodes/`):
- `StartNode.vue`, `LLMNode.vue`, `KnowledgeNode.vue`, `ConditionNode.vue`, `EndNode.vue`

**State Management** (`frontend/src/stores/`):
- Uses Pinia for global state (minimal usage, mostly component-local state)

**API Proxy:** Vite dev server proxies `/api` to `http://localhost:8000`

### Key Integration Points

**SSE Streaming Chat** (`backend/app/api/chat.py`):
- Endpoint: `POST /api/v1/chat/completions`
- Events: `thought` (RAG retrieval), `token` (LLM output), `citation` (sources), `done` (completion)
- Supports three modes: simple chat, RAG-enhanced chat, workflow execution
- Session persistence via `data/sessions/{session_id}.json` with FileLock for concurrency

**Workflow Execution** (`backend/app/core/workflow_engine.py`):
- BFS graph traversal with execution context
- Supports conditional branching via `sourceHandle` (true/false)
- Streams events: `workflow_start`, `node_start`, `token`, `node_complete`, `workflow_complete`
- Node executors mapped in `_execute_node`: start, llm, knowledge, condition, end
- Variable resolution via `{{step1.output}}` interpolation in `ExecutionContext`

**RAG Pipeline** (`backend/app/core/rag.py`):
- Document processing: load → chunk (512 tokens, 50 overlap) → embed → store
- Retrieval: query embedding → ChromaDB similarity search → top-k results
- Embedding model: SiliconFlow BGE-M3 via OpenAI-compatible API
- Chunking: LlamaIndex SentenceSplitter with configurable chunk_size/overlap

**ChromaDB Client** (`backend/app/core/chroma_client.py`):
- Singleton pattern: `get_chroma_client()`
- One collection per knowledge base (kb_id)
- PersistentClient storage at `backend/data/chromadb/`

## Configuration

### Backend Environment Variables

Copy `backend/.env.example` to `backend/.env`:

```env
# DeepSeek API (required for LLM)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# SiliconFlow API (required for embeddings)
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

# Server config
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

## Code Style and Conventions

### General
- Indentation: 2 spaces
- Line endings: LF
- Max line length: 100
- See `frontend/.editorconfig` for details

### Frontend (Vue 3 + TypeScript)
- Formatting: Prettier (no semicolons, single quotes, print width 100)
- Linting: ESLint + OXLint
- SFC order: `<template>`, `<script setup lang="ts">`, `<style scoped>`
- Use `@/` alias for src imports
- Prefer Composition API (`ref`, `computed`, `watch`)

### Backend (FastAPI + Python)
- Type hints required everywhere
- Docstrings for modules and public functions
- Import order: stdlib, third-party, local
- Use `APIRouter` with `/api/v1/` prefix and tags
- Use `Path` from pathlib for filesystem operations
- Use Pydantic models for request/response schemas
- Use `HTTPException` for API errors
- Settings from `app.core.config.settings()` (no hardcoded secrets)

### Naming Conventions
- Python: `snake_case` (functions/variables), `PascalCase` (classes)
- TypeScript: `camelCase` (variables/functions), `PascalCase` (components)

## Testing

**Frontend:**
- Test runner: Vitest with jsdom
- Run: `npm run test` or `npm run test:ui`
- Test files: `frontend/src/__tests__/**/*.spec.ts`
- Mock Vue Flow components in tests (see `WorkflowView.spec.ts`)

**Backend:**
- No pytest configured (manual test scripts only)
- Manual tests: `test_chat_api.py`, `test_deepseek.py`

## Important Notes

- **Python package management:** Use `uv` exclusively (not pip directly)
- **Virtual environment:** Always create `.venv` in project folder with `uv venv`
- **API documentation:** Available at http://localhost:8000/docs (Swagger) and http://localhost:8000/redoc
- **Session persistence:** Chat sessions stored as JSON files in `backend/data/sessions/` with FileLock
- **ChromaDB collections:** One collection per knowledge base (kb_id)
- **Workflow execution:** Stateless (no persistence of execution state)
- **SSE streaming:** Requires `X-Accel-Buffering: no` header for nginx compatibility
- **WorkflowEditor layout:** Top toolbar (save/load/run/delete/auto-layout) + Right drawer (node addition) + Left info panel (workflow info only)

## Common Patterns

### Adding a New API Endpoint

1. Define Pydantic models in `backend/app/models/`
2. Create route handler in appropriate router (`backend/app/api/`)
3. Use `APIRouter` with prefix `/api/v1/{resource}` and tags
4. Add business logic to `backend/app/core/` if complex
5. Return proper HTTP status codes and error messages

### Adding a New Workflow Node Type

1. Add `execute_{type}_node` async generator function to `backend/app/core/workflow_nodes.py`
2. Register executor in `WorkflowEngine._execute_node` (workflow_engine.py) with mapping
3. Add node component to `frontend/src/components/nodes/{Type}Node.vue`
4. Update frontend node palette in `WorkflowEditor.vue` drawer
5. Define node data schema in `backend/app/models/workflow.py` if needed

### Extending RAG Pipeline

- Embedding logic: `backend/app/core/rag.py` → `SiliconFlowEmbedding`
- Chunking strategy: `backend/app/core/rag.py` → `RAGPipeline.__init__` (SentenceSplitter params: CHUNK_SIZE=512, CHUNK_OVERLAP=50)
- Retrieval logic: `backend/app/core/rag.py` → `RAGPipeline.search`
- ChromaDB operations: `backend/app/core/chroma_client.py`

## Troubleshooting

- **ChromaDB errors:** Check `backend/data/chromadb/` permissions and disk space. Delete directory to reset.
- **SSE not streaming:** Verify `X-Accel-Buffering: no` header and CORS settings in `.env`
- **API key errors:** Ensure `.env` file exists in `backend/` with valid keys
- **Frontend proxy errors:** Backend must be running on port 8000
- **Import errors:** Run `uv pip install -e .` in backend directory
