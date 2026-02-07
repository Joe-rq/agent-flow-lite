# Chat Composer Desktop Scale Rebalance Plan (Revised)

## TL;DR

> **Quick Summary**: Keep the original direction (single-file CSS-only, no logic changes), but remove over-engineered E2E dependency and lock exact desktop scale numbers before implementation.
>
> **Deliverables**:
> - Exact desktop-only (`min-width: 1200px`) value map for composer-related styles
> - `frontend/src/views/ChatTerminal.vue` media-query override only
> - Lightweight, executable verification (`type-check` + targeted `vitest` + CSS rule assertions)
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO
> **Critical Path**: Task 1 -> Task 2 -> Task 3

---

## Context

### Original Request
对话下方输入区和配置区太小，和页面整体比例不协调；仅做桌面端。

### Interview Summary
- Scale target chosen: `+25%` (中等放大)
- Scope: desktop only
- Constraint: no interaction logic change

### Metis + User Feedback Consolidation
已吸收并修复以下问题：
- 缺少具体数值映射 -> **已补齐完整现值->目标值表**
- 按钮 specificity 策略不明 -> **明确使用同元素类叠加选择器**
- Playwright 前置条件重（登录态/后端）-> **降级为轻量可执行验证主线**
- Citation panel 自动化路径不清 -> **移出必选验收，改为可选扩展**
- `max-width` 目标不明确 -> **固定具体目标值**

---

## Work Objectives

### Core Objective
在不改任何业务逻辑的前提下，提升桌面端聊天 Composer（配置条 + 输入区 + 发送按钮）的视觉权重与比例协调性。

### Concrete Deliverables
- 更新 `frontend/src/views/ChatTerminal.vue` 的桌面媒体查询样式。
- 产出可执行验证结果（命令输出 + 规则断言）。

### Definition of Done
- [x] `>=1200px` 下，Composer 样式按映射值生效。
- [x] `<1200px` 下，原样保持。
- [x] 输入、发送、下拉功能无回退（通过现有测试覆盖）。
- [x] 无 script/template 逻辑变更。

### Must Have
- 单文件 CSS 改造（`ChatTerminal.vue`）
- 精确数值映射先行
- 明确 specificity 覆盖策略

### Must NOT Have (Guardrails)
- 不改 `script setup`、不改 API、不改路由守卫
- 不改主题色、动画、阴影、其他页面样式
- 不引入登录态依赖的 E2E 作为“必须通过”项

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> 本计划采用“轻量可执行验证主线”：静态样式断言 + 现有自动化回归。

### Test Decision
- **Infrastructure exists**: YES (Vitest)
- **Automated tests**: Tests-after
- **Framework**: Vitest + Bash-level CSS rule assertions

### Validation Baseline (No Playwright as mandatory)
- Mandatory:
  - `cd frontend && npm run type-check`
  - `cd frontend && npx vitest run src/__tests__/views/ChatTerminal.spec.ts`
  - CSS rule existence/value assertions against `ChatTerminal.vue`
- Optional extension (not blocking): Playwright visual snapshots if auth+backend are already prepared.

---

## Execution Strategy

### Parallel Execution Waves
Wave 1: Task 1
Wave 2: Task 2
Wave 3: Task 3

Critical Path: 1 -> 2 -> 3

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2 | None |
| 2 | 1 | 3 | None |
| 3 | 2 | None | None |

---

## TODOs

- [ ] 1. 产出完整数值映射（现值 -> 目标值）并冻结

  **What to do**:
  - 确认桌面断点：`@media (min-width: 1200px)`。
  - 固化以下映射（仅桌面生效）：

  | Selector / Property | Baseline | Target |
  |---|---:|---:|
  | `.config-bar` `padding` | `12px 20px` | `15px 25px` |
  | `.config-bar` `gap` | `16px` | `20px` |
  | `.config-item` `gap` | `8px` | `10px` |
  | `.config-item label` `font-size` | `12px` | `14px` |
  | `.config-item select` `padding` | `6px 10px` | `8px 12px` |
  | `.config-item select` `font-size` | `12px` | `14px` |
  | `.config-item select` `min-width` | `150px` | `190px` |
  | `.input-area` `padding` | `16px 20px` | `20px 25px` |
  | `.input-wrapper` `gap` | `12px` | `15px` |
  | `.input-wrapper` `max-width` | `800px` | `1000px` |
  | `.input-wrapper input` `padding` | `12px 16px` | `15px 20px` |
  | `.input-wrapper input` `font-size` | `14px` | `16px` (readability cap) |
  | `.send-btn.btn.btn--md` `height` | `2.5rem` | `3rem` |
  | `.send-btn.btn.btn--md` `padding` | `0.5rem 1rem` | `0.625rem 1.25rem` |
  | `.send-btn.btn.btn--md` `font-size` | `0.9375rem` | `1rem` |

  **Must NOT do**:
  - 不在映射阶段做实现。

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: None

  **References**:
  - `frontend/src/views/ChatTerminal.vue:810`
  - `frontend/src/views/ChatTerminal.vue:1041`
  - `frontend/src/views/ChatTerminal.vue:1054`
  - `frontend/src/views/ChatTerminal.vue:1074`
  - `frontend/src/components/ui/Button.vue:64`

  **Acceptance Criteria**:
  - [ ] 上表字段完整且无 TBD。
  - [ ] 每个目标值可直接写入 CSS，无二义性。

  **Agent-Executed QA Scenarios**:
  Scenario: Mapping completeness check
    Tool: Bash
    Preconditions: Repo readable
    Steps:
      1. Parse this plan table
      2. Ensure each target selector has baseline + target
      3. Ensure no “约/大概/视情况”字样
    Expected Result: Mapping is deterministic
    Evidence: Task log text output

  **Commit**: NO

- [x] 2. 实施桌面媒体查询覆盖（单文件 CSS）

  **What to do**:
  - 在 `frontend/src/views/ChatTerminal.vue` 中新增桌面媒体查询，按 Task 1 数值逐项覆盖。
  - specificity 策略：
    - 发送按钮覆盖使用同元素类叠加：`.send-btn.btn.btn--md`（避免跨组件 deep 误用）
    - 不修改 `Button.vue`。

  **Must NOT do**:
  - 不改 template/script
  - 不改全局组件 `Button.vue`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 1

  **References**:
  - `frontend/src/views/ChatTerminal.vue:810`
  - `frontend/src/views/ChatTerminal.vue:1041`
  - `frontend/src/views/ChatTerminal.vue:1074`
  - `frontend/src/components/ui/Button.vue:64`

  **Acceptance Criteria**:
  - [ ] 存在 `@media (min-width: 1200px)`。
  - [ ] 目标选择器与目标值全部落地。
  - [ ] 无 script/template diff。

  **Agent-Executed QA Scenarios**:
  Scenario: CSS patch integrity
    Tool: Bash
    Preconditions: Patch applied
    Steps:
      1. Read `frontend/src/views/ChatTerminal.vue`
      2. Assert presence of `@media (min-width: 1200px)`
      3. Assert presence of `.send-btn.btn.btn--md` and mapped values
    Expected Result: Selector and values exactly match mapping table
    Failure Indicators: missing selector / value drift
    Evidence: assertion output log

  **Commit**: YES
  - Message: `fix(chat): scale desktop composer controls with explicit mapping`
  - Files: `frontend/src/views/ChatTerminal.vue`
  - Pre-commit: `cd frontend && npm run type-check`

- [x] 3. 轻量回归验证（去 E2E 强依赖）

  **What to do**:
  - 执行类型检查与现有 ChatTerminal 测试。
  - 执行 CSS 规则断言，确认桌面断点和值存在。

  **Must NOT do**:
  - 不把 Playwright 登录态场景作为阻塞条件。
  - 不引入人工目检作为验收前置。

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 2

  **References**:
  - `frontend/package.json:11`
  - `frontend/package.json:16`
  - `frontend/src/__tests__/views/ChatTerminal.spec.ts:25`
  - `frontend/src/router/index.ts:53`

  **Acceptance Criteria**:
  - [ ] `cd frontend && npm run type-check` PASS
  - [ ] `cd frontend && npx vitest run src/__tests__/views/ChatTerminal.spec.ts` PASS
  - [ ] CSS 断点与关键值断言 PASS

  **Agent-Executed QA Scenarios**:
  Scenario: Type and unit regression
    Tool: Bash
    Preconditions: deps installed
    Steps:
      1. Run `cd frontend && npm run type-check`
      2. Run `cd frontend && npx vitest run src/__tests__/views/ChatTerminal.spec.ts`
      3. Assert both exit code = 0
    Expected Result: no regression in typed build or chat tests
    Evidence: command outputs

  Scenario: Desktop-only rule assertion
    Tool: Bash
    Preconditions: Task 2 complete
    Steps:
      1. Read `frontend/src/views/ChatTerminal.vue`
      2. Assert `@media (min-width: 1200px)` exists
      3. Assert mapped key values exist under the media block
    Expected Result: desktop-only constraints are encoded
    Evidence: assertion output log

  **Commit**: NO

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2 | `fix(chat): scale desktop composer controls with explicit mapping` | `frontend/src/views/ChatTerminal.vue` | `cd frontend && npm run type-check` |

---

## Success Criteria

### Verification Commands
```bash
cd frontend && npm run type-check
cd frontend && npx vitest run src/__tests__/views/ChatTerminal.spec.ts
```

### Final Checklist
- [ ] 映射完整、无二义性
- [ ] 单文件 CSS 媒体查询实现完成
- [ ] specificity 策略明确且可复现
- [ ] 轻量自动化回归通过
