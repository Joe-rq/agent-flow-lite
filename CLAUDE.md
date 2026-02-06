# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Working Rules（必须遵守）

以下规则优先级最高，覆盖所有默认行为：

### 行为约束

1. **修 bug 优先于一切。** 用户报了 bug，在 bug 确认修复前不做任何其他事（包括写文档、重构、优化、添加注释）。
2. **改代码前先读代码。** 不要基于猜测修改文件。先 Read 相关文件，理解现有逻辑后再提出方案。
3. **每次改动都要验证。** 后端改动后运行 `uv run pytest`；前端改动后运行 `npx tsc --noEmit && npm run test`。验证不通过不算完成。
4. **单任务原则。** 每轮只做一件事，做完确认后再接下一件。不要在一轮里同时改 auth、chat、workflow 等不相关模块。
5. **大改动先列清单。** 涉及 3 个以上文件的改动，先列出要改哪些文件、每个文件改什么，用户确认后再动手。

### 代码质量

6. **TypeScript 文件改完必须通过类型检查。** 编辑 `.ts` 或 `.vue` 文件后，确保 `npx tsc --noEmit` 通过。
7. **Python 文件改完必须通过语法检查。** 编辑 `.py` 文件后，确保 `python -m py_compile <file>` 通过。
8. **不要做没被要求的事。** 不要主动添加注释、文档、类型标注、重构、优化。只做用户明确要求的事。
9. **新功能先写测试。** 添加新功能时，先写一个失败测试来定义预期行为，再实现功能让测试通过。

### 禁止事项

10. **不要在修 bug 时写文档或优化计划。** 这是最常见的跑偏模式。
11. **不要一次改太多文件。** 除非用户明确要求，否则每次改动控制在 1-3 个文件内。
12. **不要吞掉错误。** 遇到测试失败或编译错误时，报告给用户而不是绕过。

---

## Project Overview

**Agent Flow Lite** is a full-stack AI agent orchestration platform with visual workflow editing, RAG knowledge retrieval, intelligent chat, skill system, and user management capabilities.

**Tech Stack:**
- **Backend**: FastAPI + Python 3.11+ + LlamaIndex + ChromaDB + SQLAlchemy (SQLite)
- **Frontend**: Vue 3 + Vite + TypeScript + Vue Flow + Pinia + Vue Router
- **AI Services**:
  - DeepSeek API (LLM)
  - SiliconFlow API (embeddings)
  - Zep Cloud (optional session memory)
- **Vector DB**: ChromaDB (persistent storage)

**Key Features:**
1. Visual workflow editor with node-based graph (start, llm, knowledge, condition, end, skill nodes)
2. RAG knowledge base with document upload/processing
3. SSE streaming chat with skill execution (@skill syntax)
4. User authentication with role-based access control (admin/user)
5. Skill system compatible with Agent Skills specification
6. Session memory with Zep Cloud integration
7. File-based storage for workflows, sessions, and skills

---

## Development Commands

### Frontend (`frontend/`)

```bash
cd frontend

# Install dependencies
npm install

# Development server (http://localhost:5173)
npm run dev

# Type checking
npm run type-check

# Linting (oxlint + eslint with auto-fix)
npm run lint

# Format code (prettier)
npm run format

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Production build
npm run build
```

### Backend (`backend/`)

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
./start.sh    # or start.bat on Windows

# Stop all servers
./stop.sh
```

---

## Directory Structure

```
agent-flow-lite/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   │   ├── auth.py       # Login/logout/user info
│   │   │   ├── chat.py       # SSE streaming chat
│   │   │   ├── knowledge.py  # KB CRUD, doc upload
│   │   │   ├── workflow.py   # Workflow CRUD/execution
│   │   │   ├── skill.py     # Skill CRUD/execution
│   │   │   └── admin.py     # User management
│   │   ├── core/             # Business logic
│   │   │   ├── auth.py       # Token validation, user retrieval
│   │   │   ├── config.py     # Pydantic settings
│   │   │   ├── database.py   # SQLAlchemy async session
│   │   │   ├── llm.py       # DeepSeek API client
│   │   │   ├── rag.py        # RAG pipeline (load/chunk/embed)
│   │   │   ├── chroma_client.py  # ChromaDB wrapper
│   │   │   ├── workflow_engine.py  # Graph traversal executor
│   │   │   ├── workflow_nodes.py    # Node executors
│   │   │   ├── workflow_context.py  # Variable resolution
│   │   │   ├── skill_loader.py  # SKILL.md parsing/validation
│   │   │   ├── skill_executor.py # Skill execution
│   │   │   └── zep.py        # Session memory client
│   │   └── models/           # Pydantic/SQLAlchemy models
│   │       ├── chat.py       # ChatMessage, ChatRequest
│   │       ├── workflow.py   # Workflow, GraphData
│   │       ├── document.py   # Document, KnowledgeBase
│   │       ├── skill.py      # SkillDetail, SkillSummary
│   │       └── user.py      # User, AuthToken
│   ├── data/                 # Runtime data
│   │   ├── sessions/{session_id}.json  # Chat history
│   │   ├── workflows.json             # Workflow storage
│   │   ├── kb_metadata.json          # KB metadata
│   │   ├── uploads/{kb_id}/          # Uploaded docs
│   │   ├── chromadb/                 # Vector DB persistence
│   │   └── skills/{skill_name}/      # Skill folders
│   ├── .venv/                # Python virtual environment
│   ├── main.py               # FastAPI entry point
│   └── pyproject.toml        # uv project config
├── frontend/
│   ├── src/
│   │   ├── views/            # Page components
│   │   │   ├── HomeView.vue
│   │   │   ├── LoginView.vue
│   │   │   ├── WorkflowView.vue
│   │   │   ├── WorkflowEditor.vue
│   │   │   ├── KnowledgeView.vue
│   │   │   ├── ChatTerminal.vue
│   │   │   ├── SkillsView.vue
│   │   │   ├── SkillEditor.vue
│   │   │   └── AdminUsersView.vue
│   │   ├── components/
│   │   │   ├── nodes/     # Workflow node components
│   │   │   │   ├── StartNode.vue
│   │   │   │   ├── LLMNode.vue
│   │   │   │   ├── KnowledgeNode.vue
│   │   │   │   ├── ConditionNode.vue
│   │   │   │   ├── EndNode.vue
│   │   │   │   └── SkillNode.vue
│   │   │   ├── ui/        # UI components
│   │   │   └── NodeConfigPanel.vue
│   │   ├── stores/           # Pinia state
│   │   │   └── auth.ts     # Auth state
│   │   ├── router/
│   │   │   └── index.ts     # Vue Router config
│   │   ├── utils/
│   │   │   └── axios.ts     # Axios instance
│   │   └── __tests__/        # Vitest tests
│   ├── node_modules/
│   ├── package.json
│   ├── vite.config.ts        # Vite proxy to backend
│   ├── tsconfig.json
│   └── .prettierrc.json
├── docs/                    # Documentation
│   ├── design/
│   └── testing/
├── install.sh               # Setup script
├── start.sh / start.bat     # Server startup
├── stop.sh                 # Server shutdown
└── README.md
```

---

## Key Architecture Patterns

### 1. SSE (Server-Sent Events) Streaming

**Location**: `backend/app/api/chat.py`, `skill.py`, `workflow.py`

The application uses SSE for real-time streaming of AI responses. Events include:

**Chat/Workflow/Skill Execution Events:**
- `thought` - RAG retrieval status, node execution progress
- `token` - LLM-generated content chunks
- `citation` - Source metadata from retrieved documents
- `done` - Completion marker with status
- `error` - Error messages

**Key SSE Function:**
```python
def format_sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
```

**Response Headers** (for nginx compatibility):
```python
headers={
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # Disable nginx buffering
}
```

### 2. File-Based Storage with FileLock

**Locations**: `backend/app/api/chat.py`, `workflow.py`, `skill_loader.py`

The application uses file-based storage for workflows, sessions, and skills with `filelock` for concurrent access safety:

**Session Storage** (`data/sessions/{session_id}.json`):
```python
def save_session(session: SessionHistory) -> None:
    session_path = get_session_path(session.session_id)
    session.updated_at = datetime.utcnow()
    lock = FileLock(str(session_path) + ".lock")
    with lock:
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
```

**Workflow Storage** (`data/workflows.json`):
- Single JSON file with all workflows
- FileLock protects concurrent writes

**Skill Storage** (`data/skills/{skill_name}/SKILL.md`):
- Each skill in its own folder
- FileLock per skill file

### 3. Authentication & Authorization

**Location**: `backend/app/core/auth.py`, `app/api/auth.py`, `app/api/admin.py`

**Auth Flow:**
1. Demo email authentication (no password required)
2. Token-based session management (UUID tokens, 7-day expiry)
3. Role-based access control (admin/user)
4. Auto-assign admin role based on `ADMIN_EMAIL` env var

**Key Components:**

```python
# User model with soft delete
class User(Base):
    id: Mapped[int]
    email: Mapped[str]  # Unique
    role: Mapped[UserRole]  # USER or ADMIN
    is_active: Mapped[bool]
    created_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]  # Soft delete

# Auth token with expiration
class AuthToken(Base):
    token: Mapped[str]  # UUID
    user_id: Mapped[int]  # FK to users
    expires_at: Mapped[datetime]  # 7 days

# Dependency for protected endpoints
async def get_current_user(request: Request, db: AsyncSession) -> User:
    # Extract Bearer token from Authorization header
    # Validate token exists, not expired
    # Check user is_active
    # Return authenticated user
```

**Admin Protection:**
```python
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### 4. RAG Pipeline Architecture

**Location**: `backend/app/core/rag.py`, `chroma_client.py`

**Pipeline Steps:**
1. **Load**: Read document from file (.txt, .md supported)
2. **Chunk**: LlamaIndex SentenceSplitter (512 tokens, 50 overlap)
3. **Embed**: SiliconFlow BGE-M3 via OpenAI-compatible API
4. **Store**: ChromaDB (persistent client, one collection per KB)
5. **Retrieve**: Vector similarity search (top-k by default)

**Key Classes:**
```python
class SiliconFlowEmbedding:
    def get_text_embedding(self, text: str) -> list[float]: ...
    def get_text_embedding_batch(self, texts: list[str]) -> list[list[float]]: ...

class RAGPipeline:
    def load_document(self, file_path: str) -> str: ...
    def chunk_document(self, content: str, doc_id: str) -> list[dict]: ...
    def process_document(self, kb_id: str, doc_id: str, file_path: str) -> dict: ...
    def search(self, kb_id: str, query: str, top_k: int = 5) -> list[dict]: ...
```

**ChromaDB Configuration:**
- Persistent storage at `data/chromadb/`
- One collection per knowledge base: `kb_{kb_id}`
- Anonymized telemetry disabled
- Collection metadata: doc_id, chunk_index, chunk_size

### 5. Workflow Execution Engine

**Location**: `backend/app/core/workflow_engine.py`, `workflow_nodes.py`

**Execution Pattern:**
- BFS (Breadth-First Search) graph traversal
- Supports conditional branching via `sourceHandle` (true/false)
- Streaming events for real-time progress
- Variable resolution via `{{step1.output}}` interpolation

**Node Types:**
1. **start**: Entry point, passes input to next node
2. **llm**: Calls DeepSeek API, streams tokens
3. **knowledge**: RAG retrieval from KB
4. **condition**: Evaluates boolean, branches true/false
5. **skill**: Executes a skill with variable substitution
6. **end**: Terminal node, returns final output

**Execution Context** (`workflow_context.py`):
```python
class ExecutionContext:
    variables: dict[str, str]  # Global variables
    step_outputs: dict[str]  # Per-node outputs
    def resolve_variable(self, template: str) -> str: ...  # {{var}} substitution
```

### 6. Skill System

**Location**: `backend/app/core/skill_loader.py`, `skill_executor.py`

**SKILL.md Format:**
```yaml
---
name: skill-name
description: Short description
license: MIT
inputs:
  - name: variable1
    label: Display Label
    type: text  # or textarea
    required: true
    default: ""
    description: Help text
model:
  temperature: 0.7
  max_tokens: 2000
knowledge_base: kb-id  # Optional
user_id: user-id  # Owner
---

Markdown prompt template with {{variable}} placeholders...
```

**Chat Invocation:** `@skill-name This is the content...`

**Validation Rules:**
- Name: lowercase, alphanumeric + hyphens, max 64 chars
- No leading/trailing/consecutive hyphens
- All `{{placeholders}}` must be declared as inputs
- Max file size: 50KB soft limit
- Path traversal protection via `.resolve().relative_to()`

### 7. Session Memory (Zep Integration)

**Location**: `backend/app/core/zep.py`

**Optional integration** (enabled via `ZEP_ENABLED=true` env var):
- Stores conversation history across sessions
- Provides memory context for LLM
- Session isolation: `{user_id}::{session_id}`

**Key Methods:**
```python
class ZepClient:
    def ensure_user_session(self, user_id: str, session_id: str) -> bool: ...
    def add_messages(self, session_id: str) -> bool: ...
    def get_memory_context(self, session_id: str) -> str: ...
```

---

## Frontend Architecture Patterns

### 1. Vue Router with Auth Guard

**Location**: `frontend/src/router/index.ts`

**Route Protection:**
- `meta.public`: Bypass auth (e.g., `/login`)
- `meta.requiresAdmin`: Requires admin role (e.g., `/admin`)
- Default: Requires authentication

**Guard Logic:**
```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.public && authStore.isAuthenticated) {
    next('/')  // Redirect authenticated users from login
    return
  }

  if (!to.meta.public && !authStore.isAuthenticated) {
    next('/login')  // Redirect to login
    return
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')  // Redirect non-admins
    return
  }

  next()
})
```

### 2. Pinia Auth Store

**Location**: `frontend/src/stores/auth.ts`

**State Management:**
```typescript
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(email: string): Promise<void>
  async function logout(): Promise<void>
  function init(): boolean  // Restore from localStorage
  // ...
})
```

### 3. Axios Interceptor

**Location**: `frontend/src/utils/axios.ts`

- Base URL via Vite proxy `/api` -> `http://localhost:8000`
- Authorization header injection from auth store
- Response handler: 401 redirects to login

### 4. Vue Flow Integration

**Location**: `frontend/src/views/WorkflowEditor.vue`, `frontend/src/components/nodes/`

**Node Types:**
- Custom components for each node type
- `sourceHandle` for conditional branching (true/false)
- Drag-and-drop node creation from palette
- Auto-layout support (elkjs)

---

## Testing Approach

### Frontend Testing (Vitest)

**Test Files**: `frontend/src/__tests__/**/*.spec.ts`

**Test Categories:**
- Setup tests (`setup.spec.ts`)
- View tests (`views/*.spec.ts`)
- Auth tests (`auth/login.spec.ts`)
- Admin tests (`admin/users.spec.ts`)

**Test Runner**: Vitest with jsdom environment

### Backend Testing

**No pytest configured** - Manual test scripts only:
- `test_chat_api.py` - Manual chat API testing
- `test_deepseek.py` - Manual DeepSeek API testing

---

## Configuration

### Backend Environment Variables

**File**: `backend/.env` (copy from `.env.example`)

```env
# DeepSeek API (required for LLM)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# SiliconFlow API (required for embeddings)
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

# Zep Cloud (optional for session memory)
ZEP_API_KEY=your_zep_api_key
ZEP_API_URL=https://api.getzep.com
ZEP_ENABLED=false

# Admin Configuration
ADMIN_EMAIL=admin@mail.com  # Auto-assign admin role

# Server config
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

### Python Project Configuration

**File**: `backend/pyproject.toml` (uv project structure)

**Dependencies** (from `uv pip list` analysis):
- FastAPI, uvicorn
- SQLAlchemy, aiosqlite
- pydantic, pydantic-settings
- LlamaIndex (llama-index-core)
- ChromaDB
- OpenAI (for SiliconFlow compatibility)
- python-dotenv
- filelock
- zep-cloud (optional)

### Frontend Configuration

**File**: `frontend/vite.config.ts`

- `/api` proxy to `http://localhost:8000`
- `@/` alias for `src/` directory
- Vue DevTools plugin
- Node version: `^20.19.0 || >=22.12.0`

---

## Important Files Summary

**Backend:**
- `backend/main.py` - FastAPI app with CORS, router registration, lifespan
- `backend/app/api/chat.py` - SSE streaming chat, @skill parsing, session management
- `backend/app/api/auth.py` - Login/logout/user info endpoints
- `backend/app/api/skill.py` - Skill CRUD with SSE execution
- `backend/app/core/workflow_engine.py` - Graph-based workflow executor (BFS)
- `backend/app/core/skill_loader.py` - SKILL.md parsing with validation
- `backend/app/core/rag.py` - RAG pipeline with LlamaIndex + ChromaDB
- `backend/app/core/auth.py` - Token validation, user retrieval
- `backend/app/core/database.py` - SQLAlchemy async session setup

**Frontend:**
- `frontend/src/main.ts` - Vue app entry with Pinia + Router
- `frontend/src/router/index.ts` - Route definitions with auth guard
- `frontend/src/stores/auth.ts` - Auth state with localStorage persistence
- `frontend/src/views/ChatTerminal.vue` - SSE streaming chat UI
- `frontend/src/views/SkillsView.vue` - Skill management UI
- `frontend/src/views/SkillEditor.vue` - Skill editor with markdown
- `frontend/src/views/WorkflowEditor.vue` - Vue Flow canvas editor
- `frontend/vite.config.ts` - API proxy configuration

---

## Code Style & Conventions

**Backend (Python):**
- Type hints required everywhere
- Docstrings for modules and public functions
- Import order: stdlib, third-party, local
- `APIRouter` with `/api/v1/` prefix and tags
- Use `HTTPException` for API errors
- Settings from `app.core.config.settings()` (no hardcoded secrets)
- `snake_case` for functions/variables, `PascalCase` for classes

**Frontend (TypeScript/Vue 3):**
- Composition API (`ref`, `computed`, `watch`)
- SFC order: `<template>`, `<script setup lang="ts">`, `<style scoped>`
- Use `@/` alias for src imports
- Prettier formatting (no semicolons, single quotes, 100 char width)
- Linting: oxlint + eslint

**Naming Conventions:**
- Python: `snake_case` (functions/variables), `PascalCase` (classes)
- TypeScript: `camelCase` (variables/functions), `PascalCase` (components)
