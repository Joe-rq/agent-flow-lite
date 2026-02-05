# Login Page Cleanup Plan

## TL;DR

> **Quick Summary**: Hide all non-login chrome for unauthenticated users and ensure logout immediately redirects to `/login`. Implement via App layout gating + logout navigation, with TDD tests.
>
> **Deliverables**:
> - Update `frontend/src/App.vue` to hide chrome when unauthenticated and redirect on logout
> - Add tests in `frontend/src/__tests__/App.spec.ts`
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential
> **Critical Path**: Task 1 → Task 2

---

## Context

### Original Request
“登录界面应该只有登录相关信息；所有未登录页面都隐藏；点击退出登录后立刻返回此页面。”

### Interview Summary
**Key Discussions**:
- 所有未登录页面隐藏非登录 UI（侧边栏/顶部栏/其他 chrome）。
- 退出登录后立即跳转到登录页。
- 测试策略：TDD（Vitest）。

**Research Findings**:
- 全局布局在 `frontend/src/App.vue`（header + sidebar + RouterView）。
- 当前 `showChrome` 仅依赖 `route.meta.hideChrome`。
- 登录路由 `frontend/src/router/index.ts` 已设置 `meta: { public: true, hideChrome: true }`。
- 认证守卫在 `frontend/src/router/index.ts`，未登录会重定向 `/login`。
- 退出登录逻辑在 `frontend/src/App.vue` 的 `handleLogout()`，但没有导航。

---

## Work Objectives

### Core Objective
未登录时只显示登录相关内容；登出后立刻跳转登录页。

### Concrete Deliverables
- `showChrome` 逻辑结合认证状态（未登录时隐藏）。
- `handleLogout()` 执行后 `router.push('/login')`。
- 新增 App 级别测试覆盖：未登录隐藏 chrome、登出跳转。

### Definition of Done
- [ ] 未登录时 App header/sidebar 不渲染。
- [ ] 点击“退出登录”后路由立即变为 `/login`。
- [ ] `npx vitest run src/__tests__/App.spec.ts` 通过。

### Must Have
- 未登录时只显示登录页面内容。

### Must NOT Have (Guardrails)
- 不修改 LoginView 表单或 UI 文案。
- 不重构路由守卫逻辑。
- 不新增依赖。

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: YES (Vitest)
- **Automated tests**: TDD
- **Framework**: Vitest

### If TDD Enabled

1. **RED**: 添加 App 测试断言：未登录隐藏 chrome、登出后跳转登录。
2. **GREEN**: 修改 App 逻辑满足测试。
3. **REFACTOR**: 仅小幅整理（如需要）。

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Scenario: Login page shows only login content
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running on http://localhost:5173; user not logged in
  Steps:
    1. Navigate to: http://localhost:5173/login
    2. Assert: header `.app-header` not visible
    3. Assert: sidebar `.app-sidebar` not visible
    4. Assert: login form visible (`input#email`)
    5. Screenshot: .sisyphus/evidence/login-clean.png
  Expected Result: Only login card visible
  Evidence: .sisyphus/evidence/login-clean.png

Scenario: Logout redirects to login
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running; user logged in
  Steps:
    1. Navigate to: http://localhost:5173/
    2. Click: button containing text "退出登录"
    3. Wait for URL to be /login
    4. Screenshot: .sisyphus/evidence/logout-redirect.png
  Expected Result: Redirect to login immediately
  Evidence: .sisyphus/evidence/logout-redirect.png

---

## Execution Strategy

Wave 1: Task 1 (TDD test)
Wave 2: Task 2 (App logic changes)

---

## TODOs

- [ ] 1. Add TDD tests for login chrome + logout redirect (RED)

  **What to do**:
  - Create `frontend/src/__tests__/App.spec.ts`.
  - Mock auth store to control `isAuthenticated`.
  - Assert: when unauthenticated and route `/login`, `.app-header` and `.app-sidebar` not rendered.
  - Assert: clicking logout triggers router navigation to `/login`.

  **Must NOT do**:
  - Do not modify production code yet.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **References**:
  - `frontend/src/App.vue` - `showChrome` and `handleLogout()`.
  - `frontend/src/router/index.ts` - login route meta and guard.
  - `frontend/src/stores/auth.ts` - auth state.

  **Acceptance Criteria**:
  - [ ] `npx vitest run src/__tests__/App.spec.ts` → FAIL (before changes).

- [ ] 2. Update App layout gating + logout redirect (GREEN)

  **What to do**:
  - Update `showChrome` to also depend on `authStore.isAuthenticated`.
  - Use `useRouter()` in `App.vue` and navigate to `/login` after `logout()`.

  **Must NOT do**:
  - Do not change LoginView UI.
  - Do not alter router guard logic.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **References**:
  - `frontend/src/App.vue` - layout and logout handler.
  - `frontend/src/stores/auth.ts` - logout clears auth state.

  **Acceptance Criteria**:
  - [ ] `npx vitest run src/__tests__/App.spec.ts` → PASS.
  - [ ] `.app-header`/`.app-sidebar` hidden when unauthenticated.
  - [ ] Logout navigates to `/login` immediately.

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2 | `fix(登录): 未登录隐藏导航并登出跳转` | `frontend/src/App.vue`, `frontend/src/__tests__/App.spec.ts` | `npx vitest run src/__tests__/App.spec.ts` |

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npx vitest run src/__tests__/App.spec.ts
```

### Final Checklist
- [ ] 未登录页面无 header/sidebar
- [ ] 登出后立即跳转 /login
- [ ] Tests pass
