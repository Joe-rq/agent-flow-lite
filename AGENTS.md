# AGENTS.md

Guidelines for agentic coding assistants working in this repository.

## Repository Overview

- **frontend/**: Vue 3 + Vite + TypeScript (views, components, composables)
- **backend/**: FastAPI + Pydantic + Python 3.11+ (RAG, chat, workflow APIs)
- **backend/data/**: Runtime state - do not commit

## Environment Requirements

- **Node**: ^20.19.0 or >=22.12.0
- **Python**: >=3.11
- **Backend uses `uv`** (not pip) for dependency management

## Commands

### Frontend (`cd frontend`)

```bash
npm install              # Install dependencies
npm run dev              # Dev server (port 5173)
npm run build            # Type-check + production build
npm run type-check       # TypeScript check only
npm run lint             # ESLint + OXLint with auto-fix
npm run format           # Prettier format
npm run test             # Run all tests (one-shot)
npx vitest run src/__tests__/App.spec.ts    # Single test file
npx vitest run -t "test name"               # Run by pattern
```

### Backend (`cd backend`)

```bash
uv venv                  # Create virtual environment (first time)
uv pip install -e .      # Install dependencies
uv run uvicorn main:app --reload    # Dev server (port 8000)
uv run pytest -q         # Run all tests
uv run pytest tests/test_smoke.py -q    # Single test file
uv run pytest -k "citation" -q          # Run tests matching pattern
```

## Code Style

### General (All Files)

- **Indent**: 2 spaces
- **Line endings**: LF
- **Max line length**: 100
- **Trim trailing whitespace**, always add final newline
- See `frontend/.editorconfig` for source of truth

### Frontend (Vue 3 + TypeScript)

**Formatting**: Prettier with no semicolons, single quotes, print width 100

**Conventions**:
- Prefer `<script setup lang="ts">`
- SFC order: `<template>` → `<script setup>` → `<style scoped>`
- Use `@/` alias for src imports
- Use Composition API (ref/computed/watch) consistently
- File names: kebab-case.ts or PascalCase.ts
- Functions/variables: camelCase, Classes: PascalCase

### Backend (FastAPI + Pydantic)

**Python Style**:
- Use docstrings for modules and public functions
- Use type hints everywhere
- Import order: stdlib → third-party → local
- Functions/variables: snake_case, Classes: PascalCase

**API Conventions**:
- Use `APIRouter` with versioned prefix (`/api/v1/...`) and tags
- Use Pydantic models in `app/models` for request/response schemas
- Use settings from `app/core/config.py` (never hardcode secrets)
- Raise `HTTPException` with proper status codes
- Keep API routers thin; put logic in `app/core` helpers

## Test Resource Constraints (CRITICAL)

Vitest spawns multiple workers (2-3GB each) - **must limit concurrency to avoid OOM**.

Required config (`frontend/vitest.config.ts`):
```typescript
test: {
  pool: 'forks',
  poolOptions: { forks: { maxForks: 2, minForks: 1 } },
  maxConcurrency: 5,
  isolate: true,
}
```

**Forbidden**:
- ❌ `npm run test` in parallel with memory-heavy tasks (build, lint)
- ❌ `vitest` (watch mode) in automated scripts - use `vitest run` instead
- ❌ Removing `maxForks` limit

## CI Post-Push Checks

After `git push`, verify Quality Gate status:

```bash
gh run list --workflow="Quality Gate" --limit 3
gh run view <run-id> --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```

Key jobs: `frontend-type-check`, `frontend-build`, `frontend-critical-tests`, `backend-critical-tests`

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
const { meta } = useRoute()  // Stale
// RIGHT
const route = useRoute()     // Reactive
```

### Embedding Model Change Protocol

When changing `EMBEDDING_MODEL` in `.env`:
1. **Dimension mismatch will occur** for existing knowledge bases
2. **Search returns 409 Conflict** - delete `backend/data/chromadb/` and re-upload

## Repository-Specific Notes

- Backend entrypoint: `main.py` (FastAPI app instance: `app`)
- Chat streaming uses SSE (see `backend/app/api/chat.py`)
- RAG pipeline: LlamaIndex + ChromaDB (`backend/app/core/rag.py`)
- Runtime data stored under `backend/data/` - do not depend on existing data

## When in Doubt

- Match existing patterns in `backend/app/api` and `backend/app/core`
- Match existing patterns in `frontend/src/views` and `frontend/src/components`
- Prefer explicit, readable code over clever shortcuts
- Update this file if you add new workflows or commands

---

*Last updated: 2026-02-12*
