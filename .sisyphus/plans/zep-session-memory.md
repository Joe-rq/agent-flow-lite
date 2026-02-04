# Zep Session Memory (Enhancement Only)

## TL;DR

> **Quick Summary**: Add Zep session memory as a read+write enhancement layer for chat. Frontend sends real `user_id` from localStorage; backend stores messages to Zep and injects memory context into the system prompt.
>
> **Deliverables**:
> - Zep client + config in backend (API key, URL, enable flag)
> - Chat API accepts `user_id` and syncs messages to Zep
> - System prompt includes Zep memory context
> - Frontend passes `user_id` from localStorage in chat requests
> - TDD tests for Zep integration and chat behavior
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Backend Zep integration → Frontend user_id → Tests/QA

---

## Context

### Original Request
Enhance the product by integrating https://app.getzep.com/ knowledge graph as session memory, without changing the existing RAG pipeline.

### Interview Summary
**Key Discussions**:
- Scope: session memory only (no KB documents).
- Zep usage: read + write; inject memory context into system prompt.
- user_id: real user id from frontend localStorage (no new UI).
- Test strategy: TDD with pytest.

**Research Findings**:
- Session lifecycle and persistence: `backend/app/api/chat.py` (save_session + stream_with_save)
- Chat models: `backend/app/models/chat.py`
- Zep API: `memory.add_session`, `memory.add`, `memory.get`

### Metis Review
No additional feedback returned by Metis during consultation.

---

## Work Objectives

### Core Objective
Persist session memory to Zep and inject Zep memory context into the chat system prompt, while preserving existing RAG behavior.

### Concrete Deliverables
- Backend Zep client wrapper and config
- Chat API accepts `user_id` and syncs messages to Zep
- System prompt includes Zep memory context
- Frontend passes `user_id` from localStorage
- Pytest coverage for Zep integration

### Definition of Done
- [x] Chat requests include `user_id`
- [x] Zep sessions are created and messages are synced for both user and assistant
- [x] Zep memory context is injected into system prompt
- [x] All new tests pass via `uv run pytest -q`

### Must Have
- Non-breaking integration; existing RAG pipeline unchanged
- Zep integration is optional and degrades gracefully if disabled

### Must NOT Have (Guardrails)
- No KB document ingestion into Zep
- No UI redesign or new UI libraries
- No DB migration

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: Backend pytest configured
- **Automated tests**: TDD

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

**Tools by deliverable**:
- API: Bash (`curl`)
- Tests: Bash (`uv run pytest -q`)

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
- Task 1: Add Zep config + client wrapper
- Task 2: Update backend chat flow to use Zep (TDD)

Wave 2 (After Wave 1):
- Task 3: Update frontend to pass `user_id` from localStorage
- Task 4: End-to-end verification + tests

Critical Path: Task 1 → Task 2 → Task 3 → Task 4

---

## TODOs

- [x] 1. Add Zep config + client wrapper (TDD)

  **What to do**:
  - RED: add tests for config defaults and Zep client init behavior
  - GREEN: add Zep config fields in `backend/app/core/config.py` (API key, URL, enabled flag)
  - GREEN: create `backend/app/core/zep.py` client wrapper with:
    - `ensure_user_session(user_id, session_id)`
    - `add_messages(session_id, messages)`
    - `get_memory(session_id)`
  - REFACTOR: make client lazy and safe when disabled

  **Must NOT do**:
  - Do not hardcode secrets; read from env

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: backend config + integration wrapper
  - **Skills**: `python-pro`
    - `python-pro`: FastAPI + async client patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References**:
  - `backend/app/core/config.py` - settings pattern
  - `backend/pyproject.toml` - dependencies (add `zep-cloud`)
  - Zep docs: https://help.getzep.com/v2/sessions

  **Acceptance Criteria**:
- [x] Config includes `ZEP_API_KEY`, `ZEP_API_URL`, `ZEP_ENABLED`
- [x] Zep client wrapper handles disabled mode without raising
- [x] `uv run pytest -q` passes new config tests

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Config defaults and disabled mode
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run: uv run pytest -q
      2. Assert: exit code 0
    Expected Result: Tests validate config defaults and disabled mode
    Evidence: pytest stdout
  ```

- [x] 2. Integrate Zep into chat flow (TDD)

  **What to do**:
  - RED: tests for chat_completions requiring user_id and injecting memory
  - GREEN:
    - Extend `ChatRequest` with `user_id`
    - In `chat_completions`, ensure Zep user+session exists
    - Call `get_memory(session_id)` and inject into system prompt
    - On user message append, call `add_messages` (role_type=user)
    - On assistant message append, call `add_messages` (role_type=assistant)
  - REFACTOR: isolate Zep calls to avoid affecting SSE streaming

  **Must NOT do**:
  - Do not change RAG retrieval logic or citation formatting

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: API + streaming flow integration
  - **Skills**: `python-pro`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3, Task 4
  - **Blocked By**: Task 1

  **References**:
  - `backend/app/api/chat.py` - session save + streaming
  - `backend/app/models/chat.py` - `ChatRequest`, `ChatMessage`
  - `backend/app/api/chat.py` - `build_system_prompt` usage

  **Acceptance Criteria**:
- [x] Requests without user_id return 400
- [x] System prompt includes Zep memory context when enabled
- [x] Zep receives both user and assistant messages
- [x] `uv run pytest -q` passes

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Chat request requires user_id
    Tool: Bash (curl)
    Preconditions: Backend running on localhost:8000
    Steps:
      1. POST /api/v1/chat/completions without user_id
      2. Assert: HTTP 400
    Expected Result: Backend rejects missing user_id
    Evidence: curl output
  ```

- [x] 3. Frontend: pass user_id from localStorage (TDD)

  **What to do**:
  - RED: add unit test ensuring request payload includes user_id
  - GREEN: in `ChatTerminal.vue`, read `localStorage.getItem('user_id')` and include in chat POST
  - REFACTOR: centralize request payload creation

  **Must NOT do**:
  - Do not add new UI input fields

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: small front-end change
  - **Skills**: `typescript-pro`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 4
  - **Blocked By**: Task 2

  **References**:
  - `frontend/src/views/ChatTerminal.vue` - chat request payload
  - `frontend/src/__tests__/views/ChatTerminal.spec.ts` - test pattern

  **Acceptance Criteria**:
- [x] user_id included in chat POST payload
- [x] `npx vitest run src/__tests__/views/ChatTerminal.spec.ts` passes

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Chat payload includes user_id
    Tool: Bash
    Preconditions: Frontend test env
    Steps:
      1. Run: npx vitest run src/__tests__/views/ChatTerminal.spec.ts
      2. Assert: exit code 0
    Expected Result: Tests validate payload includes user_id
    Evidence: vitest stdout
  ```

- [x] 4. End-to-end verification

  **What to do**:
  - Run pytest and verify chat endpoint handles user_id

  **Must NOT do**:
  - Do not require Zep network access for QA (use disabled mode)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: verification only
  - **Skills**: `python-pro`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: Task 2, Task 3

  **References**:
  - `backend/app/api/chat.py` - 400 validation for user_id
  - `backend/app/core/zep.py` - disabled mode guard

  **Acceptance Criteria**:
- [x] `uv run pytest -q` passes
- [x] curl request without user_id returns 400

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Backend validation and tests
    Tool: Bash (curl)
    Preconditions: Backend running on localhost:8000
    Steps:
      1. Run: uv run pytest -q
      2. POST /api/v1/chat/completions without user_id
      3. Assert: HTTP 400
    Expected Result: Tests pass and validation enforced
    Evidence: pytest stdout + curl output
  ```

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(zep): add config and client wrapper` | `backend/app/core/config.py`, `backend/app/core/zep.py`, tests | `uv run pytest -q` |
| 2 | `feat(chat): integrate zep memory` | `backend/app/api/chat.py`, `backend/app/models/chat.py`, tests | `uv run pytest -q` |
| 3 | `feat(chat-ui): send user_id` | `frontend/src/views/ChatTerminal.vue`, tests | `npx vitest run src/__tests__/views/ChatTerminal.spec.ts` |

---

## Success Criteria

### Verification Commands
```bash
uv run pytest -q
npx vitest run src/__tests__/views/ChatTerminal.spec.ts
```

### Final Checklist
- [x] Zep session memory read+write integrated
- [x] user_id passed from frontend localStorage
- [x] All tests pass
