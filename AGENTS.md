# AGENTS.md

This file guides agentic coding assistants working in this repository.
Follow it strictly to avoid style drift and broken workflows.

## Repository Overview

- frontend/ : Vue 3 + Vite app
- backend/  : FastAPI service (RAG + chat + workflow APIs)
- backend/data/ : runtime data (uploads, metadata, sessions, chromadb)

## Environment Requirements

- Node: ^20.19.0 or >=22.12.0 (see frontend/package.json)
- Python: >=3.11 (see backend/pyproject.toml)
- Backend uses uv for execution (not pip as primary workflow)

## Build / Lint / Test Commands

### Frontend (frontend/)

- Install deps:
  - `cd frontend && npm install`
- Dev server:
  - `npm run dev`
- Production build (type-check + build):
  - `npm run build`
- Build only:
  - `npm run build-only`
- Preview build:
  - `npm run preview`
- Type-check:
  - `npm run type-check`
- Lint (all):
  - `npm run lint`
- Lint (oxlint only):
  - `npm run lint:oxlint`
- Lint (eslint only):
  - `npm run lint:eslint`
- Format (prettier):
  - `npm run format`
- Run all tests:
  - `npm run test`
- Run tests with UI:
  - `npm run test:ui`
- Run single test file:
  - `npx vitest run src/components/__tests__/MyComponent.spec.ts`
- Run single test in watch mode:
  - `npx vitest src/components/__tests__/MyComponent.spec.ts`

### Backend (backend/)

- Install deps (uv):
  - `cd backend && uv pip install -e .`
- Run dev server:
  - `uv run uvicorn main:app --reload`
- Run all tests:
  - `uv run pytest -q`
- Run single test file:
  - `uv run pytest tests/test_zep_client.py -q`
- Run single test in watch mode:
  - `uv run pytest tests backend/tests/test_chat_zep.py -q --watch`
- Run manual test scripts:
  - `uv run python test_chat_api.py`
  - `uv run python test_deepseek.py`

### Single Test Execution

**Frontend (Vitest):**
```bash
cd frontend
# Run specific test file
npx vitest run src/__tests__/views/ChatTerminal.spec.ts

# Run specific test in watch mode
npx vitest src/__tests__/views/ChatTerminal.spec.ts

# Run tests matching pattern
npx vitest run --reporter=verbose MyComponent
```

**Backend (pytest):**
```bash
cd backend
# Run specific test file
uv run pytest tests/test_zep_client.py -q

# Run with verbose output
uv run pytest tests/test_chat_zep.py -v

# Run matching pattern
uv run pytest -k "zep" -q
```

## Code Style Guidelines

### General (all files)

- Indent: 2 spaces
- Line endings: LF
- Max line length: 100
- Trim trailing whitespace
- Always add final newline
- See frontend/.editorconfig for source of truth

### Frontend (Vue 3 + TypeScript)

- Formatting uses Prettier:
  - No semicolons
  - Single quotes
  - Print width 100
  - Source: frontend/.prettierrc.json
- Linting uses ESLint + OXLint (essential + recommended configs)
  - Source: frontend/eslint.config.ts and frontend/.oxlintrc.json
- Prefer `<script setup lang="ts">` in .vue files
- Keep Vue SFC order: `<template>`, `<script setup>`, `<style scoped>`
- Use @/ alias for src imports (see frontend/tsconfig.app.json)
- Keep components small and cohesive; avoid large monolithic views
- Avoid adding new UI libraries without explicit requirement
- Prefer scoped styles in SFCs unless global styling is intentional
- Use Composition API patterns (ref/computed/watch) consistently

### Backend (FastAPI + Pydantic)

- Use docstrings for modules and public functions
- Use type hints everywhere (see existing code)
- Keep imports ordered: stdlib → third-party → local
- Use APIRouter with versioned prefix (/api/v1/...) and tags
- Prefer Path from pathlib for filesystem paths
- Use Pydantic models in app/models for request/response schemas
- Use settings from app/core/config.py (do not hardcode secrets)
- Use HTTPException with proper status codes for API errors
- When returning custom JSON, use JSONResponse
- Keep API routers thin; put logic in app/core helpers when possible
- Store runtime state under backend/data (uploads/metadata/sessions)
- Preserve existing API prefixes and tags for new routes

### Error Handling

- Raise HTTPException for client errors (400/404)
- Catch narrow exceptions; do not swallow errors silently
- For background tasks, update status metadata on failure
- Include human-readable error messages in API responses

### Naming Conventions

- Python: snake_case for functions/variables, PascalCase for classes
- TS/JS: camelCase for variables/functions, PascalCase for components
- Files: lowercase with underscores for Python, kebab/camel for TS as used

## Data and Runtime Files

- backend/data/ is runtime state (uploads, metadata, sessions, chromadb)
- Do not depend on existing data for logic
- Avoid committing large or sensitive files in backend/data/

## Cursor / Copilot Rules

- No Cursor rules found (.cursor/rules/ or .cursorrules)
- No GitHub Copilot instructions found (.github/copilot-instructions.md)

## Repository-Specific Notes

- Backend entrypoint is main.py (FastAPI app instance: app)
- Chat streaming endpoint uses SSE (see backend/app/api/chat.py)
- RAG pipeline uses LlamaIndex + ChromaDB (backend/app/core/rag.py)
- DeepSeek API client wrapper is in backend/app/core/llm.py

## When in Doubt

- Match existing patterns in backend/app/api and backend/app/core
- Prefer explicit, readable code over clever shortcuts
- Update this file if you add new workflows or commands

---

## Auth & Bootstrap Lessons (2026-02-06)

**Incident**: Refresh causes logout → Three cascading bugs.

### Root Causes & Fixes

| # | Bug | Symptom | Fix |
|---|-----|---------|-----|
| 1 | Axios interceptor registered AFTER auth init | `/api/v1/auth/me` returns 401 (no Authorization header) | Register interceptors BEFORE `authStore.init()` |
| 2 | Router initialized BEFORE auth hydration | Route guard redirects to `/login` before `isAuthenticated` restored | Initialize router AFTER `authStore.init()`, add public→home校正 |
| 3 | `const { meta } = useRoute()` destructuring | Non-reactive meta causes UI tearing (sidebar shows + login page) | Use `route.meta` directly, NOT destructured |

### Correct Bootstrap Order

```typescript
// main.ts
app.use(pinia)

const authStore = useAuthStore()
setupAxiosInterceptors()        // 1. 拦截器先注册
await authStore.init()          // 2. 再水合 auth（token 恢复 + /me 校验）

app.use(router)                 // 3. 路由最后挂载

// 4. 防止首屏落在 public 路由
if (router.currentRoute.value.meta.public && authStore.isAuthenticated) {
  await router.replace('/')
}

app.mount('#app')
```

### Vue Router Anti-Patterns

**WRONG** (non-reactive):
```typescript
const { meta } = useRoute()
if (meta.hideChrome) { ... }  // ❌ stale, doesn't update
```

**RIGHT** (reactive):
```typescript
const route = useRoute()
if (route.meta.hideChrome) { ... }  // ✅ updates on navigation
```

### Debugging Checklist

When "refresh logs out" or "401 on auth endpoints":
- [ ] Check Network: Does `/api/v1/auth/me` have `Authorization` header?
- [ ] Check Timing: Is axios interceptor registered before init()?
- [ ] Check Navigation: Does router guard fire BEFORE or AFTER auth hydration?
- [ ] Check Reactivity: Are route meta accessed reactively?
