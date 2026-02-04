# User Management + Email Demo Auth + User-Scoped Zep Memory

## TL;DR

> **Quick Summary**: Add demo email-only login with admin/user roles, protect all APIs, and enforce user-scoped data + Zep memory using SQLite-backed auth tokens.
>
> **Deliverables**:
> - Auth + admin APIs with SQLite storage and bearer token auth
> - Frontend login + admin user management page with route guards
> - User-scoped chat sessions + Zep memory (server-side user_id)
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Backend auth/data model → API protection → Frontend auth/admin UI

---

## Context

### Original Request
“添加用户管理，不同用户通过邮箱登录区分。demo，不依赖真实邮箱。管理员可管理用户，普通用户只能看自己的数据。Zep 记忆按用户隔离。”

### Interview Summary
**Key Discussions**:
- Demo-only auth: email input logs in without verification.
- Storage: SQLite with create_all (no Alembic).
- Roles: admin + user; admin manages users (view/delete/disable/enable).
- Normal users can only see their own data (auth info + chats + Zep memory).
- Admin account is fixed email: `admin@mail.com`.
- Auth session: Bearer token stored client-side.
- Admin needs a frontend management page.

**Research Findings**:
- No existing auth system; all APIs are open.
- Zep client exists at `backend/app/core/zep.py`, chat uses session-level memory and accepts client `user_id`.
- Chat sessions are stored as JSON files under `backend/data/sessions/` and currently list all sessions without user filtering.
- Frontend chat currently reads `user_id` from `localStorage` (`ChatTerminal.vue`) and passes it in requests.
- Frontend list/table/dialog patterns exist in `frontend/src/views/KnowledgeView.vue` and toolbar patterns in `frontend/src/views/WorkflowView.vue`.
- Zep docs indicate memory is user-level across sessions; per-user isolation must be enforced via server-side `user_id` naming (no client trust).

### Metis Review
**Identified Gaps (addressed)**:
- Define data retention: disable keeps data; delete is soft delete.
- Admin bootstrap and email normalization; prevent self-disable; token revocation for disabled users.
- Clarify Zep scoping: implement server-side user_id and namespace session IDs by user.

---

## Work Objectives

### Core Objective
Implement a demo email-based user system (admin/user), protect APIs, and enforce user-scoped memory/data including Zep.

### Concrete Deliverables
- Backend auth + admin endpoints with SQLite models and bearer token auth.
- Frontend login + admin management UI with route guards and token attachment.
- Chat sessions and Zep memory scoped to authenticated user.

### Definition of Done
- [ ] Unauthenticated API calls return 401 for protected endpoints.
- [ ] Login with `admin@mail.com` returns admin role and exposes admin UI.
- [ ] Normal user can only view their own chat sessions; admin can view all users.
- [ ] Zep memory operations use server-side user_id and cannot be spoofed by client.

### Must Have
- Email-only demo login (no real email delivery)
- Admin user management (view/delete/disable/enable)
- Soft delete + data retention on delete
- User-scoped sessions + Zep memory

### Must NOT Have (Guardrails)
- No password auth, email verification, or OAuth
- No profile editing, role changes, or password reset
- No hard delete of user data
- No Alembic migrations
- Do not rely on client-provided `user_id` for any Zep operations

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> This applies to EVERY task, regardless of test strategy.

### Test Decision
- **Infrastructure exists**: YES (frontend Vitest, backend Pytest)
- **Automated tests**: TDD
- **Framework**: Vitest (frontend), Pytest (backend)

### If TDD Enabled

Each TODO follows RED-GREEN-REFACTOR.

**Backend** (Pytest):
1. RED: Write failing test in `backend/tests/test_auth.py`
2. GREEN: Implement endpoint/model
3. REFACTOR: Clean up; tests still pass

**Frontend** (Vitest):
1. RED: Write failing test in `frontend/src/__tests__/auth/*.spec.ts`
2. GREEN: Implement component/store
3. REFACTOR: Clean up; tests still pass

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Each scenario includes tool + steps + evidence path.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
├── Task 1: Backend auth + SQLite models + token middleware
└── Task 2: Zep scoping + session access control updates

Wave 2 (After Wave 1):
├── Task 3: Frontend login + auth store + route guards
└── Task 4: Admin management UI + admin API wiring

Critical Path: Task 1 → Task 3 → Task 4

---

## TODOs

### 1) Backend auth + SQLite models + token middleware

**What to do**:
- Add SQLite engine/session + create_all initialization.
- Create user + auth token models with soft delete support.
- Implement `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/logout`.
- Implement auth dependency to validate bearer tokens and user status.
- Enforce admin-only actions via role checks.

**Must NOT do**:
- No password fields, verification, or OAuth.
- No hard delete.

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: multi-file backend auth + DB plumbing
- **Skills**: `git-master` (omit), `frontend-ui-ux` (omit)
  - Omitted: `frontend-ui-ux` not needed; `git-master` only if committing

**Parallelization**:
- **Can Run In Parallel**: YES (with Task 2)
- **Parallel Group**: Wave 1 (with Task 2)
- **Blocks**: Task 3, Task 4
- **Blocked By**: None

**References**:
- `backend/main.py:27` - app creation and lifespan; add DB init here
- `backend/app/core/config.py:13` - add admin email + auth settings
- `backend/app/api/chat.py:444` - sessions list endpoint to protect and scope
- `backend/app/models/chat.py:20` - request model; remove reliance on client user_id
- `backend/pyproject.toml:7` - add SQLAlchemy dependency if needed

**Acceptance Criteria (TDD)**:
- [ ] `backend/tests/test_auth.py` includes login + me + logout tests
- [ ] `uv run pytest tests/test_auth.py -q` → PASS

**Agent-Executed QA Scenarios**:

Scenario: Login creates user and returns token
  Tool: Bash (curl)
  Preconditions: Backend running on localhost:8000
  Steps:
    1. POST `http://localhost:8000/api/v1/auth/login` with JSON `{ "email": "user1@mail.com" }`
    2. Assert HTTP 200
    3. Assert response has `token` and `user.role == "user"`
  Expected Result: User created, token returned
  Evidence: `.sisyphus/evidence/task-1-login.json`

Scenario: Disabled user token rejected
  Tool: Bash (curl)
  Preconditions: Admin token available, user exists
  Steps:
    1. POST disable user with admin token
    2. Call `/api/v1/auth/me` with disabled user's token
    3. Assert HTTP 403
  Expected Result: Disabled users cannot access APIs
  Evidence: `.sisyphus/evidence/task-1-disable.json`

---

### 2) Zep scoping + session access control updates

**What to do**:
- Ensure Zep operations use server-side user_id from auth token.
- Namespace session IDs by user (e.g., `{user_id}::{session_id}`) to enforce per-user isolation.
- Update session list/detail/delete to filter by user for non-admin.

**Must NOT do**:
- Do not trust client-provided user_id.
- Do not hard delete user data.

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: backend logic touching Zep + sessions
- **Skills**: none

**Parallelization**:
- **Can Run In Parallel**: YES (with Task 1)
- **Parallel Group**: Wave 1 (with Task 1)
- **Blocks**: Task 3 (frontend relies on scoped APIs)
- **Blocked By**: Task 1 for auth dependency

**References**:
- `backend/app/core/zep.py:48` - current Zep user/session methods
- `backend/app/api/chat.py:311` - current client user_id requirement
- `backend/app/api/chat.py:444` - session list endpoint without scoping
- `frontend/src/views/ChatTerminal.vue:389` - client user_id in payload
- Zep docs: `https://help.getzep.com/v2/sessions` - user-level knowledge graph across sessions
- Zep docs: `https://help.getzep.com/v3/ecosystem/livekit-memory` - user_id naming for isolation

**Acceptance Criteria (TDD)**:
- [ ] New tests assert session list returns only current user's sessions
- [ ] Tests assert client user_id spoofing is ignored

**Agent-Executed QA Scenarios**:

Scenario: User cannot read another user's session
  Tool: Bash (curl)
  Preconditions: Two users exist with tokens and sessions
  Steps:
    1. GET `/api/v1/chat/sessions` with user A token
    2. Assert no sessions from user B
  Expected Result: User-scoped sessions
  Evidence: `.sisyphus/evidence/task-2-sessions.json`

Scenario: Zep uses server-side user_id
  Tool: Bash (curl)
  Preconditions: Zep enabled, user token
  Steps:
    1. POST `/api/v1/chat/completions` with body containing `user_id: "spoof"`
    2. Assert backend ignores client user_id (verified via logs/test spy)
  Expected Result: Zep scoped to authenticated user
  Evidence: `.sisyphus/evidence/task-2-zep.json`

---

### 3) Frontend login + auth store + route guards

**What to do**:
- Add login page for email-only login.
- Add auth store with token + user profile in Pinia.
- Add axios interceptor to attach Bearer token.
- Add router guard to redirect to `/login` when unauthenticated.

**Must NOT do**:
- No password fields or verification flows.

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: multi-file frontend state + routing
- **Skills**: `frontend-ui-ux`
  - `frontend-ui-ux`: build clear demo login UI consistent with app

**Parallelization**:
- **Can Run In Parallel**: YES (after Task 1)
- **Parallel Group**: Wave 2 (with Task 4)
- **Blocks**: Task 4
- **Blocked By**: Task 1

**References**:
- `frontend/src/router/index.ts:1` - add login/admin routes + guards
- `frontend/src/views/ChatTerminal.vue:389` - remove localStorage user_id usage
- `frontend/README.md` - existing view/page structure

**Acceptance Criteria (TDD)**:
- [ ] `frontend/src/__tests__/auth/login.spec.ts` verifies login flow
- [ ] `npx vitest run src/__tests__/auth/login.spec.ts` → PASS

**Agent-Executed QA Scenarios**:

Scenario: Login redirects to home
  Tool: Playwright
  Preconditions: Frontend dev server on localhost:5173, backend running
  Steps:
    1. Open `/login`
    2. Fill `input[type="email"]` with `user1@mail.com`
    3. Click `button[type="submit"]`
    4. Wait for URL `/`
  Expected Result: User logged in and redirected
  Evidence: `.sisyphus/evidence/task-3-login.png`

Scenario: Unauthenticated user redirected to login
  Tool: Playwright
  Preconditions: Clear localStorage token
  Steps:
    1. Open `/chat`
    2. Assert redirected to `/login`
  Expected Result: Route guard enforced
  Evidence: `.sisyphus/evidence/task-3-guard.png`

---

### 4) Admin management UI + admin API wiring

**What to do**:
- Add admin page to list users with status and actions (disable/enable/delete).
- Add admin-only API endpoints and wire frontend calls.
- Ensure admin cannot disable or delete self.

**Must NOT do**:
- No analytics or extra user profile features.

**Recommended Agent Profile**:
- **Category**: `visual-engineering`
  - Reason: admin UI table + action buttons
- **Skills**: `frontend-ui-ux`

**Parallelization**:
- **Can Run In Parallel**: YES (with Task 3)
- **Parallel Group**: Wave 2 (with Task 3)
- **Blocks**: None
- **Blocked By**: Task 1

**References**:
- `backend/app/api/chat.py:444` - pattern for list endpoints
- `frontend/src/views/WorkflowView.vue` - existing list layout patterns
- `frontend/src/views/KnowledgeView.vue` - list + actions UI patterns

**Acceptance Criteria (TDD)**:
- [ ] `backend/tests/test_admin_users.py` covers list/disable/enable/delete
- [ ] `uv run pytest tests/test_admin_users.py -q` → PASS
- [ ] `frontend/src/__tests__/admin/users.spec.ts` covers admin list render

**Agent-Executed QA Scenarios**:

Scenario: Admin can disable user
  Tool: Playwright
  Preconditions: Logged in as `admin@mail.com`
  Steps:
    1. Open `/admin`
    2. Click `button[data-action="disable"]` on a user row
    3. Assert row shows status “已禁用”
  Expected Result: User disabled and status updated
  Evidence: `.sisyphus/evidence/task-4-disable.png`

Scenario: Non-admin cannot access admin page
  Tool: Playwright
  Preconditions: Logged in as non-admin user
  Steps:
    1. Open `/admin`
    2. Assert redirected to `/` or shows 403 UI
  Expected Result: Admin page protected
  Evidence: `.sisyphus/evidence/task-4-admin-guard.png`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|---|---|---|---|
| 1+2 | `feat(auth): add demo email auth and user-scoped sessions` | backend/app/** | `uv run pytest` |
| 3+4 | `feat(ui): add login and admin user management` | frontend/src/** | `npm run test` |

---

## Success Criteria

### Verification Commands
```bash
cd backend && uv run pytest -q
cd frontend && npm run test
```

### Final Checklist
- [ ] All protected APIs require Bearer token
- [ ] Admin can manage users; normal users restricted to own data
- [ ] Zep memory is user-scoped and not spoofable
- [ ] No password/email verification/OAuth added
