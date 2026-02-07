# Fix Refresh Logout in Frontend Auth Flow

## TL;DR

> **Quick Summary**: Refresh logout is caused by inconsistent auth state recovery: token is restored, user is not, but route access requires both.
>
> **Deliverables**:
> - Implement hybrid restore + revalidation auth startup flow in frontend auth store
> - Add/adjust route-guard-safe initialization state handling
> - Add TDD coverage for refresh persistence + 401/failed revalidation behavior
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential (state logic has direct dependencies)
> **Critical Path**: Task 1 -> Task 2 -> Task 3 -> Task 4

---

## Context

### Original Request
Refresh currently logs users out.

### Interview Summary
**Key Discussions**:
- Repro scope is all browsers.
- User selected hybrid strategy: optimistic local restore, then `/api/v1/auth/me` revalidation.
- User selected TDD workflow.

**Research Findings**:
- `frontend/src/stores/auth.ts`: `isAuthenticated` is `!!token && !!user`; `init()` restores token only.
- `frontend/src/main.ts`: `authStore.init()` runs at boot.
- `frontend/src/router/index.ts`: unauthenticated users are redirected to `/login`.
- `frontend/src/utils/axios.ts`: global 401 handler clears auth + redirects.
- `backend/app/core/auth.py`: bearer token DB model with 7-day expiry, so this bug is frontend-side state mismatch first.

### Metis Review
**Identified Gaps (addressed in this plan)**:
- Revalidation behavior ambiguity -> defaulted to "cache first, revalidate in background, hard-fail on 401".
- Missing edge-case coverage -> explicit scenarios added for success/401/network failure/no-token.
- Potential scope creep -> strict guardrails added (no backend auth redesign, no refresh-token work).

---

## Work Objectives

### Core Objective
Make refresh preserve valid login sessions by aligning auth restoration with route guard expectations and server truth.

### Concrete Deliverables
- Frontend auth store supports hybrid restore + `/api/v1/auth/me` reconciliation.
- Router guard behavior remains secure and deterministic during startup hydration.
- Vitest tests cover refresh and failure-path regressions.

### Definition of Done
- [x] With valid token + cached user, refresh stays logged in and protected route remains accessible.
- [x] With valid token but stale/missing user, app restores, revalidates via `/me`, then remains logged in.
- [x] With invalid/expired token, refresh redirects to `/login` and clears auth state.
- [x] `npm run test -- auth` (or equivalent targeted vitest command) passes for added scenarios.

### Must Have
- Keep existing bearer-token architecture.
- Keep global 401 safety behavior.
- Add deterministic startup auth hydration state.

### Must NOT Have (Guardrails)
- No backend auth protocol changes (no refresh token feature in this task).
- No auth system rewrite outside affected frontend auth paths.
- No unrelated login UI redesign.
- No manual-only verification acceptance criteria.

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> Every task is verified by agent-executable checks only.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: TDD
- **Framework**: Vitest

### If TDD Enabled

Each coding task follows RED-GREEN-REFACTOR.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1:
- Task 1

Wave 2:
- Task 2 (depends on 1)

Wave 3:
- Task 3 (depends on 2)

Wave 4:
- Task 4 (depends on 3)

Critical Path: 1 -> 2 -> 3 -> 4

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2 | None |
| 2 | 1 | 3 | None |
| 3 | 2 | 4 | None |
| 4 | 3 | None | None |

---

## TODOs

- [x] 1. Add failing tests for refresh-session persistence and hydration

  **What to do**:
  - Create/extend auth store tests covering refresh with token-only, token+user, invalid token, and `/me` network failure.
  - Add route-guard behavior assertions tied to startup hydration outcomes.

  **Must NOT do**:
  - Do not assert implementation internals; assert externally visible auth state/navigation behavior.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: focused single-feature bugfix with local tests.
  - **Skills**: `git-master`
    - `git-master`: keep changes atomic and reviewable.
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: no UI design work required.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References**:
  - `frontend/src/stores/auth.ts`: current auth state shape and `init()` behavior.
  - `frontend/src/router/index.ts`: route guard expectations on `isAuthenticated`.
  - `frontend/src/main.ts`: startup timing for `authStore.init()`.
  - `frontend/src/__tests__/auth/login.spec.ts`: existing auth test style and test harness.
  - `frontend/src/utils/axios.ts`: current 401 side effects relevant to assertions.

  **Acceptance Criteria**:
  - [ ] RED: new test cases fail before implementation.
  - [ ] Added tests explicitly verify refresh does not force logout for valid sessions.
  - [ ] Added tests verify invalid token path clears state and redirects.

  **Agent-Executed QA Scenarios**:

  ```text
  Scenario: RED phase detects refresh regression
    Tool: Bash (Vitest)
    Preconditions: frontend dependencies installed
    Steps:
      1. Run: cd frontend && npx vitest run src/__tests__/auth/login.spec.ts
      2. Assert: newly added refresh-hydration tests fail
      3. Save output to: .sisyphus/evidence/task-1-red-vitest.txt
    Expected Result: Failing tests confirm bug captured
    Failure Indicators: All tests pass before code change
    Evidence: .sisyphus/evidence/task-1-red-vitest.txt
  ```

- [x] 2. Implement hybrid auth hydration in auth store

  **What to do**:
  - Ensure startup restoration can recover token + cached user (if present).
  - Add startup revalidation path against `/api/v1/auth/me`.
  - On `/me` success: reconcile user state with server response.
  - On `/me` 401: clear auth and expose unauthenticated state.
  - On transient network failure: keep cached state but mark hydration status for controlled UX/guard behavior.

  **Must NOT do**:
  - Do not change backend endpoints/contracts.
  - Do not add refresh-token feature.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: localized state-management logic update.
  - **Skills**: `git-master`
    - `git-master`: maintain minimal, auditable diffs.
  - **Skills Evaluated but Omitted**:
    - `ultrabrain`: not architecture-heavy.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/stores/auth.ts`: implement core restore/revalidate logic here.
  - `backend/app/api/auth.py`: `/api/v1/auth/me` response shape/requirements.
  - `backend/app/core/auth.py`: token validity semantics and 401 conditions.

  **Acceptance Criteria**:
  - [x] GREEN: tests from Task 1 pass after implementation.
  - [x] Refresh with valid token no longer drops to login solely due to missing in-memory user.
  - [x] Revalidation 401 path reliably clears local auth.

  **Agent-Executed QA Scenarios**:

  ```text
  Scenario: Store init + /me success preserves session
    Tool: Bash (Vitest)
    Preconditions: mocked /api/v1/auth/me returns 200 user payload
    Steps:
      1. Run targeted auth tests
      2. Assert test: token restored + user hydrated + isAuthenticated true
      3. Save output to: .sisyphus/evidence/task-2-hydration-success.txt
    Expected Result: Session persists across refresh path
    Evidence: .sisyphus/evidence/task-2-hydration-success.txt

  Scenario: /me returns 401 clears auth
    Tool: Bash (Vitest)
    Preconditions: mocked /api/v1/auth/me returns 401
    Steps:
      1. Run targeted auth tests
      2. Assert token removed and auth state reset
      3. Save output to: .sisyphus/evidence/task-2-hydration-401.txt
    Expected Result: Secure logout behavior maintained
    Evidence: .sisyphus/evidence/task-2-hydration-401.txt
  ```

- [x] 3. Align router/startup flow with hydration state (no false redirect)

  **What to do**:
  - Ensure router guard does not prematurely redirect during deterministic startup hydration window.
  - Preserve strict redirect after hydration resolves unauthenticated.

  **Must NOT do**:
  - Do not weaken protected-route access checks.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: narrow change in navigation/auth coordination.
  - **Skills**: `git-master`
    - `git-master`: focused commit boundaries.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 4
  - **Blocked By**: Task 2

  **References**:
  - `frontend/src/router/index.ts`: guard logic where false negatives currently route to `/login`.
  - `frontend/src/main.ts`: app boot ordering constraints.
  - `frontend/src/stores/auth.ts`: hydration status source of truth.

  **Acceptance Criteria**:
  - [x] No immediate false redirect during valid-session startup hydration.
  - [x] Unauthenticated users still redirected correctly after hydration completion.

  **Agent-Executed QA Scenarios**:

  ```text
  Scenario: Valid cached session opens protected route after refresh
    Tool: Playwright (playwright skill)
    Preconditions: app running, localStorage seeded with valid token/user test fixture
    Steps:
      1. Navigate to /workflow
      2. Refresh page
      3. Wait for hydration completion signal/state (max 5s)
      4. Assert URL remains /workflow (no /login redirect)
      5. Screenshot: .sisyphus/evidence/task-3-refresh-stay-protected.png
    Expected Result: Protected route remains accessible
    Evidence: .sisyphus/evidence/task-3-refresh-stay-protected.png

  Scenario: Invalid token redirects to login
    Tool: Playwright (playwright skill)
    Preconditions: app running, localStorage seeded with invalid token
    Steps:
      1. Navigate to /workflow
      2. Refresh page
      3. Wait for route transition
      4. Assert URL is /login
      5. Screenshot: .sisyphus/evidence/task-3-refresh-invalid-token.png
    Expected Result: Secure redirect behavior preserved
    Evidence: .sisyphus/evidence/task-3-refresh-invalid-token.png
  ```

- [x] 4. Run focused regression and finalize

  **What to do**:
  - Run targeted auth/store/router test suite.
  - Run broader frontend test sanity check if targeted suite passes.
  - Prepare concise change note with risk and follow-up items.

  **Must NOT do**:
  - Do not skip failing tests.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: validation and wrap-up.
  - **Skills**: `git-master`
    - `git-master`: final verification discipline.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: Task 3

  **References**:
  - `frontend/package.json`: test commands.
  - `frontend/src/__tests__/auth/login.spec.ts`: primary regression coverage.

  **Acceptance Criteria**:
  - [x] Targeted auth tests pass.
  - [x] No refresh-logout regression remains.
  - [x] Evidence artifacts captured under `.sisyphus/evidence/`.

  **Agent-Executed QA Scenarios**:

  ```text
  Scenario: Targeted auth regression suite passes
    Tool: Bash (Vitest)
    Preconditions: implementation complete
    Steps:
      1. Run: cd frontend && npx vitest run src/__tests__/auth/login.spec.ts
      2. Assert: all tests pass
      3. Save output: .sisyphus/evidence/task-4-auth-regression.txt
    Expected Result: 0 failures
    Evidence: .sisyphus/evidence/task-4-auth-regression.txt
  ```

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1-3 | `fix(auth): preserve login across refresh with hybrid hydration` | `frontend/src/stores/auth.ts`, `frontend/src/router/index.ts`, auth tests | targeted vitest auth tests |
| 4 | `test(auth): add refresh logout regression coverage` | `frontend/src/__tests__/auth/login.spec.ts` | vitest pass |

---

## Success Criteria

### Verification Commands
```bash
cd frontend && npx vitest run src/__tests__/auth/login.spec.ts
cd frontend && npm run test
```

### Final Checklist
- [x] Valid sessions survive refresh.
- [x] Invalid sessions are cleared and redirected.
- [x] Route guard remains secure.
- [x] TDD evidence captured.
