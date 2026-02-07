# AGENTS.md

This file guides agentic coding assistants working in this repository.
Follow it strictly to avoid style drift and broken workflows.

## Repository Overview

- **frontend/**: Vue 3 + Vite + TypeScript app
- **backend/**: FastAPI + Pydantic service (RAG + chat + workflow APIs)
- **backend/data/**: Runtime state (uploads, metadata, sessions, chromadb) - do not commit

## Environment Requirements

- **Node**: ^20.19.0 or >=22.12.0 (see frontend/package.json)
- **Python**: >=3.11 (see backend/pyproject.toml)
- **Backend uses `uv`** for dependency management (not pip)

## Build / Lint / Test Commands

### Frontend

```bash
cd frontend
npm install              # Install dependencies
npm run dev              # Dev server
npm run build            # Type-check + production build
npm run type-check       # TypeScript check only
npm run lint             # ESLint + OXLint
npm run format           # Prettier format
npm run test             # Run all tests (one-shot mode)
npm run test:watch       # Run tests in watch mode (dev only)
npx vitest run src/components/__tests__/MyComponent.spec.ts  # Single test file
npx vitest src/components/__tests__/MyComponent.spec.ts      # Single test (watch)
```

### Backend

```bash
cd backend
uv pip install -e .                    # Install dependencies
uv run uvicorn main:app --reload       # Dev server
uv run pytest -q                       # Run all tests
uv run pytest tests/test_smoke.py -q   # Single test file
uv run pytest -k "citation" -q         # Run tests matching pattern
uv run pytest tests/test_chat_citation.py -q --watch  # Watch mode
```

## Code Style Guidelines

### General (All Files)

- **Indent**: 2 spaces
- **Line endings**: LF
- **Max line length**: 100
- **Trim trailing whitespace**
- **Always add final newline**
- See `frontend/.editorconfig` for source of truth

### Frontend (Vue 3 + TypeScript)

**Formatting (Prettier)**:
- No semicolons
- Single quotes
- Print width: 100
- Source: `frontend/.prettierrc.json`

**Linting**: ESLint + OXLint (essential + recommended configs)
- Source: `frontend/eslint.config.ts`, `frontend/.oxlintrc.json`

**Vue Conventions**:
- Prefer `<script setup lang="ts">`
- SFC order: `<template>` → `<script setup>` → `<style scoped>`
- Use `@/` alias for src imports
- Keep components small and cohesive
- Prefer scoped styles unless global is intentional
- Use Composition API (ref/computed/watch) consistently

### Backend (FastAPI + Pydantic)

**Python Style**:
- Use docstrings for modules and public functions
- Use type hints everywhere
- Import order: stdlib → third-party → local
- Use `Path` from pathlib for filesystem paths

**API Conventions**:
- Use `APIRouter` with versioned prefix (`/api/v1/...`) and tags
- Use Pydantic models in `app/models` for request/response schemas
- Use settings from `app/core/config.py` (never hardcode secrets)
- Raise `HTTPException` with proper status codes for API errors
- Keep API routers thin; put logic in `app/core` helpers
- Preserve existing API prefixes and tags for new routes

### Error Handling

- Raise `HTTPException` for client errors (400/404/409)
- Catch narrow exceptions; do not swallow errors silently
- Include human-readable error messages in API responses
- For background tasks, update status metadata on failure

### Naming Conventions

| Language | Functions/Variables | Classes | Files |
|----------|-------------------|---------|-------|
| Python | `snake_case` | `PascalCase` | `lowercase_with_underscores.py` |
| TypeScript | `camelCase` | `PascalCase` | `kebab-case.ts` or `PascalCase.ts` |

## Repository-Specific Notes

- Backend entrypoint: `main.py` (FastAPI app instance: `app`)
- Chat streaming uses SSE (see `backend/app/api/chat.py`)
- RAG pipeline: LlamaIndex + ChromaDB (`backend/app/core/rag.py`)
- DeepSeek API client: `backend/app/core/llm.py`
- Runtime data stored under `backend/data/` - do not depend on existing data for logic

## Test Resource Constraints

### Frontend (Vitest)

**CRITICAL**: Vitest 默认配置会启动多个 worker 进程，每个进程可能占用 2-3GB 内存。
在自动化流程中必须限制并发数，避免 OOM。

**Required Configuration** (`frontend/vitest.config.ts`):
```typescript
test: {
  pool: 'forks',              // Use process isolation (not threads)
  poolOptions: {
    forks: {
      maxForks: 2,            // Limit to 2 worker processes
      minForks: 1,
    }
  },
  maxConcurrency: 5,          // Max 5 tests running simultaneously
  isolate: false,             // Reduce isolation overhead
}
```

**Forbidden Patterns**:
- ❌ `npm run test` in parallel with other memory-heavy tasks (build, lint)
- ❌ `vitest` (watch mode) in automated scripts - use `vitest run` instead
- ❌ Removing `maxForks` limit "to speed up tests"

**Verification**:
```bash
# After running tests, check process count
pgrep -c vitest 2>/dev/null || ps aux | grep "[v]itest" | wc -l  # Should be ≤ 3 (main + 2 workers)
```

### Backend (Pytest)

**Note**: Currently no pytest configured. If adding pytest with `pytest-xdist`:
```bash
# ✅ Correct - limit workers explicitly
uv run pytest -n 2 -q

# ❌ Wrong - uses all CPU cores
uv run pytest -n auto
```

## Cursor / Copilot Rules

- No Cursor rules found (`.cursor/rules/` or `.cursorrules`)
- No GitHub Copilot instructions found (`.github/copilot-instructions.md`)

## Critical Implementation Notes

### Auth Bootstrap Order (Avoid Refresh Logout Bug)

```typescript
// main.ts - REQUIRED ORDER:
app.use(pinia)
const authStore = useAuthStore()
setupAxiosInterceptors()        // 1. Register interceptors FIRST
await authStore.init()          // 2. THEN hydrate auth
app.use(router)                 // 3. Router LAST

// Prevent landing on public route when authenticated
if (router.currentRoute.value.meta.public && authStore.isAuthenticated) {
  await router.replace('/')
}
app.mount('#app')
```

**Anti-pattern**: Never destructure `useRoute()` - it's non-reactive:
```typescript
// WRONG
const { meta } = useRoute()  // Stale, doesn't update

// RIGHT
const route = useRoute()     // Reactive
if (route.meta.hideChrome) { ... }
```

### Embedding Model Change Protocol

When changing `EMBEDDING_MODEL` in `.env`:
1. **Dimension mismatch will occur** for existing knowledge bases
2. **Search will return 409 Conflict** with new error handling
3. **Fix**: Delete `backend/data/chromadb/` and re-upload documents
4. Future improvement: Add per-KB model tracking in metadata

## When in Doubt

- Match existing patterns in `backend/app/api` and `backend/app/core`
- Match existing patterns in `frontend/src/views` and `frontend/src/components`
- Prefer explicit, readable code over clever shortcuts
- Update this file if you add new workflows or commands

---

*Last updated: 2026-02-07*
