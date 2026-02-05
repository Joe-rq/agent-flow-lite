# Skill Run 401 Fix Plan

## TL;DR

> **Quick Summary**: Fix 401 on skill run by keeping `fetch` (SSE streaming) and adding `Authorization: Bearer <token>` from auth store. Add TDD tests to ensure headers include auth.
>
> **Deliverables**:
> - Update `frontend/src/views/SkillsView.vue` runSkill() to add Authorization header
> - Add/extend `frontend/src/__tests__/views/SkillsView.spec.ts` tests for auth header
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential
> **Critical Path**: Task 1 → Task 2

---

## Context

### Original Request
技能运行报 401 Unauthorized。

### Interview Summary
**Key Discussions**:
- 401 原因：runSkill 用 fetch，未携带 Authorization header。
- 决策：保留 fetch（SSE 流式输出），手动加 Authorization header。
- 测试策略：TDD（Vitest）。

**Research Findings**:
- `frontend/src/views/SkillsView.vue` 中 runSkill 使用 fetch 调用 `/api/v1/skills/{name}/run`。
- 认证拦截器只作用于 axios（`frontend/src/utils/axios.ts`）。
- token 存在于 `frontend/src/stores/auth.ts` 的 `authStore.token`。

### Metis Review
**Identified Gaps (addressed)**:
- 不改 fetch 为 axios（避免破坏 SSE）。
- 只修 runSkill，不扩展到其他 fetch 调用。
- 测试只验证 header，不测试 SSE 流解析。

---

## Work Objectives

### Core Objective
runSkill 请求携带有效 Authorization header，消除 401，同时保持 SSE 流式输出。

### Concrete Deliverables
- runSkill() fetch headers 包含 `Authorization: Bearer <token>`。
- SkillsView 测试覆盖 header 注入。

### Definition of Done
- [ ] runSkill fetch 请求包含 Authorization 头。
- [ ] `npx vitest run src/__tests__/views/SkillsView.spec.ts` 通过。
- [ ] SSE 处理逻辑未修改。

### Must Have
- 保留 fetch + 流式读取逻辑。

### Must NOT Have (Guardrails)
- 不改 axios 拦截器。
- 不改后端鉴权逻辑。
- 不修改其他 fetch 调用。

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**

### Test Decision
- **Infrastructure exists**: YES (Vitest)
- **Automated tests**: TDD
- **Framework**: Vitest

### If TDD Enabled

1. **RED**: 添加测试断言 fetch 调用 headers 包含 Authorization。
2. **GREEN**: 在 runSkill fetch headers 注入 `Authorization`。
3. **REFACTOR**: 不需要（保持最小改动）。

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Scenario: Run skill sends Authorization header
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running on http://localhost:5173; user logged in
  Steps:
    1. Navigate to: http://localhost:5173/skills
    2. Click: button.btn-run on a skill card
    3. Click: button.btn-primary (text contains "运行")
    4. Intercept POST /api/v1/skills/{name}/run
    5. Assert: request header Authorization starts with "Bearer "
    6. Screenshot: .sisyphus/evidence/skill-run-auth-header.png
  Expected Result: Request includes Authorization header
  Evidence: .sisyphus/evidence/skill-run-auth-header.png

---

## Execution Strategy

Wave 1: Task 1 (TDD test)
Wave 2: Task 2 (Add Authorization header)

---

## TODOs

- [x] 1. Add TDD test for Authorization header (RED)

  **What to do**:
  - Update `frontend/src/__tests__/views/SkillsView.spec.ts`:
    - Mock auth store token.
    - Assert fetch is called with headers.Authorization = `Bearer <token>`.

  **Must NOT do**:
  - Do not modify production code yet.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **References**:
  - `frontend/src/views/SkillsView.vue` - runSkill fetch call.
  - `frontend/src/stores/auth.ts` - token source.
  - `frontend/src/__tests__/views/SkillsView.spec.ts` - existing test patterns.

  **Acceptance Criteria**:
  - [ ] `npx vitest run src/__tests__/views/SkillsView.spec.ts` → FAIL (missing Authorization).

- [x] 2. Add Authorization header in runSkill (GREEN)

  **What to do**:
  - Import auth store in `SkillsView.vue` (if not already).
  - Add `Authorization: Bearer ${authStore.token}` to fetch headers when token exists.
  - Keep SSE reader logic unchanged.

  **Must NOT do**:
  - Do not switch fetch to axios.
  - Do not change SSE parsing logic.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **References**:
  - `frontend/src/views/SkillsView.vue` - runSkill fetch block.
  - `frontend/src/utils/axios.ts` - Authorization header pattern.
  - `frontend/src/stores/auth.ts` - token storage.

  **Acceptance Criteria**:
  - [ ] `npx vitest run src/__tests__/views/SkillsView.spec.ts` → PASS.
  - [ ] Fetch headers include Authorization when token exists.

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2 | `fix(技能): 运行请求携带认证` | `frontend/src/views/SkillsView.vue`, `frontend/src/__tests__/views/SkillsView.spec.ts` | `npx vitest run src/__tests__/views/SkillsView.spec.ts` |

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npx vitest run src/__tests__/views/SkillsView.spec.ts
```

### Final Checklist
- [ ] runSkill 请求含 Authorization 头
- [ ] SSE 输出仍可正常解析
- [ ] Tests pass
