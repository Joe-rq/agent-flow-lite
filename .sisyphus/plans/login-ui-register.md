# Login Page Minimal Layout + Register CTA

## TL;DR

> **Quick Summary**: Hide all app chrome (header + sidebar) on `/login`, show only the login form, and add a register CTA that uses the existing demo email login flow.
>
> **Deliverables**:
> - App chrome hidden on `/login` via layout condition or route meta
> - Login UI includes a register action wired to existing login behavior
> - Frontend tests updated/added (TDD) and passing
>
> **Estimated Effort**: Short
> **Parallel Execution**: YES - 1 wave
> **Critical Path**: App layout guard → Login UI register CTA → Tests

---

## Context

### Original Request
"登录界面应该只有用户输入，左侧菜单栏不应该显示；同时应该有注册功能。"

### Interview Summary
**Key Discussions**:
- Login page should show only the form (no sidebar or top header chrome).
- Registration behavior: same as login (demo email auto-creates user and logs in).
- Tests: TDD with Vitest (frontend).

**Research Findings**:
- Login view: `frontend/src/views/LoginView.vue`.
- App chrome (header + sidebar) in `frontend/src/App.vue` and currently always visible.
- Router: `/login` route in `frontend/src/router/index.ts` with `meta.public`.
- No existing register/signup flow found.

### Metis Review
No additional feedback returned by Metis during consultation.

---

## Work Objectives

### Core Objective
Ensure `/login` renders a clean, standalone form-only view and provide a register CTA that uses the existing demo email login flow without backend changes.

### Concrete Deliverables
- `frontend/src/App.vue` conditionally hides header + sidebar on `/login`.
- `frontend/src/views/LoginView.vue` adds a register CTA wired to the same login action.
- Vitest updates for layout visibility and register CTA behavior.

### Definition of Done
- [x] On `/login`, sidebar and header are not rendered; only the login card is visible.
- [x] Register CTA exists and triggers the same login flow as the login button.
- [x] All updated/added Vitest tests pass.

### Must Have
- No app chrome on `/login` (header + sidebar hidden).
- Register action uses existing `/api/v1/auth/login` behavior.

### Must NOT Have (Guardrails)
- No new backend auth endpoints.
- No password fields or verification flows.
- No layout changes on non-login pages.

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: YES (Vitest)
- **Automated tests**: TDD

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Scenario: Login page shows only form (no chrome)
  Tool: Bash (Vitest)
  Preconditions: frontend tests configured
  Steps:
    1. Run: `npx vitest run src/__tests__/auth/login.spec.ts`
    2. Assert: exit code 0
  Expected Result: Tests confirm `.app-header` and `.app-sidebar` are absent on `/login`
  Evidence: Vitest stdout

Scenario: Register CTA triggers login flow
  Tool: Bash (Vitest)
  Preconditions: frontend tests configured
  Steps:
    1. Run: `npx vitest run src/__tests__/auth/login.spec.ts`
    2. Assert: exit code 0
  Expected Result: Tests confirm register CTA calls same login action
  Evidence: Vitest stdout

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
├── Task 1: Hide app chrome on `/login` (App layout condition + tests)
└── Task 2: Add register CTA to login view (UI + tests)

Critical Path: Task 1 → Task 2 (tests)

---

## TODOs

### 1) Hide app chrome on `/login`

**What to do**:
- RED: add test to verify header/sidebar hidden on `/login`.
- GREEN: conditionally render header + sidebar in `frontend/src/App.vue` based on route (e.g., route meta `hideChrome`).
- Update `frontend/src/router/index.ts` to mark `/login` with `meta.hideChrome = true` (or equivalent).

**Must NOT do**:
- Do not change chrome visibility for non-login routes.

**Recommended Agent Profile**:
- **Category**: `quick`
  - Reason: small, localized layout change
- **Skills**: `frontend-ui-ux`
  - `frontend-ui-ux`: ensure layout remains clean and intentional
- **Skills Evaluated but Omitted**:
  - `typescript-pro`: change is minor and UI-focused

**Parallelization**:
- **Can Run In Parallel**: YES (with Task 2)
- **Parallel Group**: Wave 1
- **Blocks**: None
- **Blocked By**: None

**References**:
- `frontend/src/App.vue` - contains header + sidebar rendering
- `frontend/src/router/index.ts` - `/login` route meta for layout logic
- `frontend/src/__tests__/auth/login.spec.ts` - existing login-related test patterns

**Acceptance Criteria (TDD)**:
- [x] Test added that asserts chrome hidden on `/login`
- [x] `npx vitest run src/__tests__/auth/login.spec.ts` → PASS

**Agent-Executed QA Scenarios**:

Scenario: Login page shows only form (no chrome)
  Tool: Bash (Vitest)
  Preconditions: frontend tests configured
  Steps:
    1. Run: `npx vitest run src/__tests__/auth/login.spec.ts`
    2. Assert: exit code 0
  Expected Result: Tests confirm `.app-header` and `.app-sidebar` are absent on `/login`
  Evidence: Vitest stdout

---

### 2) Add register CTA on login view (same flow as login)

**What to do**:
- RED: add test ensuring register CTA calls the same login action (auth store login).
- GREEN: add register CTA button/link in `frontend/src/views/LoginView.vue` that reuses the existing submit handler.
- Keep copy minimal (e.g., "注册" / "注册并登录").

**Must NOT do**:
- No new backend endpoints or password inputs.

**Recommended Agent Profile**:
- **Category**: `visual-engineering`
  - Reason: UI changes on login view
- **Skills**: `frontend-ui-ux`
  - `frontend-ui-ux`: preserve consistent styling and spacing
- **Skills Evaluated but Omitted**:
  - `typescript-pro`: logic change is minimal

**Parallelization**:
- **Can Run In Parallel**: YES (with Task 1)
- **Parallel Group**: Wave 1
- **Blocks**: None
- **Blocked By**: None

**References**:
- `frontend/src/views/LoginView.vue` - login form and submit handler
- `frontend/src/stores/auth.ts` - login action implementation
- `frontend/src/__tests__/auth/login.spec.ts` - existing login tests

**Acceptance Criteria (TDD)**:
- [x] Test confirms register CTA triggers login action
- [x] `npx vitest run src/__tests__/auth/login.spec.ts` → PASS

**Agent-Executed QA Scenarios**:

Scenario: Register CTA triggers login flow
  Tool: Bash (Vitest)
  Preconditions: frontend tests configured
  Steps:
    1. Run: `npx vitest run src/__tests__/auth/login.spec.ts`
    2. Assert: exit code 0
  Expected Result: Tests confirm register CTA behavior
  Evidence: Vitest stdout

---

## Commit Strategy

| After Task | Message | Files | Verification |
|---|---|---|---|
| 1+2 | `feat(ui): simplify login layout and add register CTA` | `frontend/src/App.vue`, `frontend/src/views/LoginView.vue`, tests | `npx vitest run src/__tests__/auth/login.spec.ts` |

---

## Success Criteria

### Verification Commands
```bash
cd frontend && npx vitest run src/__tests__/auth/login.spec.ts
```

### Final Checklist
- [x] Login page shows only form (no sidebar/header)
- [x] Register CTA logs in using existing demo flow
- [x] Tests pass
