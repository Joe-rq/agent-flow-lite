# Frontend UI Style Unification (Light Theme + CN)

## TL;DR

> **Quick Summary**: Unify all frontend pages under a Clean Tech Light theme, translate all visible UI text to Chinese, and reduce visual fragmentation across home/workflow/knowledge/chat. Add Vitest test infrastructure with a few key UI smoke tests.
> 
> **Deliverables**:
> - Light theme tokens in `frontend/src/styles/theme.css`
> - Unified light styles across App/Home/Workflow/Knowledge/Chat
> - Chinese copy for all visible UI strings
> - Vitest setup + core smoke tests
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Theme tokens → UI components → Page refactors → Tests

---

## Context

### Original Request
用户反馈：首页仍是英文，工作流画布/知识库/对话界面风格与主页割裂；要求全站中文化，并改为浅色布局风格。

### Interview Summary
**Key Discussions**:
- 全站可见文案全部中文化（包含工作流/知识库/对话界面）。
- 仅浅色主题，替换现有深色方案。
- 视觉方向：Clean Tech Light（冷灰底 + 青色强调 + 轻微渐变/阴影）。
- 需要搭建测试框架并补充关键测试。

**Research Findings**:
- `frontend/package.json` 仅有 lint/type-check/build，无测试框架脚本。
- 未发现 jest/vitest/pytest 配置或测试目录。

### Metis Review
**Identified Gaps**:
- Metis 调用失败（工具错误）。已在计划中补充自检与明确验收标准。

---

## Work Objectives

### Core Objective
将前端统一为浅色科技风格，并完成全站可见文案中文化，消除页面风格割裂。

### Concrete Deliverables
- `frontend/src/styles/theme.css`（浅色主题变量）
- `frontend/src/styles/animations.css`（沿用/微调）
- `frontend/src/components/ui/*`（浅色风格适配）
- `frontend/src/App.vue`（浅色布局统一）
- `frontend/src/views/HomeView.vue`（中文化 + 轻科技浅色）
- `frontend/src/views/WorkflowView.vue`（画布/工具栏浅色统一）
- `frontend/src/views/KnowledgeView.vue`（浅色卡片与表格）
- `frontend/src/views/ChatTerminal.vue`（浅色对话界面）
- `frontend/src/components/nodes/*.vue`（节点样式统一）
- `frontend/vitest.config.ts` + `frontend/src/__tests__/*`

### Definition of Done
- [ ] 全站可见文案均为中文
- [ ] 主页/工作流/知识库/对话视觉一致且为浅色风格
- [ ] UI 组件与页面均使用浅色主题变量
- [ ] Vitest 可运行且关键页面有基础测试
- [ ] `npm run lint` 和 `npm run type-check` 通过

### Must Have
- 仅浅色主题（替换深色）
- 全站中文文案
- 样式统一（减少割裂感）
- 测试框架搭建（Vitest）

### Must NOT Have (Guardrails)
- 不引入大型 UI 库
- 不修改后端 API
- 不引入国际化框架（i18n）除非必要
- 不添加深色主题切换

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO
- **User wants tests**: YES (tests-after)
- **Framework**: Vitest + @vue/test-utils

### Test Setup Task (required)
- [ ] 安装 Vitest + @vue/test-utils + jsdom
- [ ] 新增 `vitest.config.ts`
- [ ] 在 `package.json` 增加 `test` 脚本
- [ ] 创建示例测试，确保 `npm run test` 可执行

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation):
├── Task 1: Update light theme tokens
├── Task 2: Update UI components for light style
└── Task 3: Set up Vitest infrastructure

Wave 2 (Pages):
├── Task 4: App.vue layout + nav labels CN
├── Task 5: HomeView CN + light visuals
├── Task 6: WorkflowView light canvas + toolbar
└── Task 7: Node components light style

Wave 3 (Feature Pages + Tests):
├── Task 8: KnowledgeView light + CN
├── Task 9: ChatTerminal light + CN
└── Task 10: Add Vitest smoke tests
```

---

## TODOs

- [x] 1. Update light theme tokens in `theme.css`

  **What to do**:
  - Replace dark tokens with light palette (cool gray base + cyan accents)
  - Define light background, surface, border, text, shadow variables
  - Keep variable names stable to minimize refactors

  **Must NOT do**:
  - Do not introduce dark tokens
  - Do not rename variables unless necessary

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**: Wave 1

  **References**:
  - `frontend/src/styles/theme.css` - current tokens to replace
  - `frontend/src/styles/animations.css` - keep consistent motion

  **Acceptance Criteria**:
  - [ ] `theme.css` defines light backgrounds, borders, and text colors
  - [ ] Accent colors preserved (cyan/purple) with lighter soft variants

---

- [x] 2. Update UI components for light theme

  **What to do**:
  - Adjust Button/Card/Modal/Input styles for light surfaces
  - Ensure subtle shadows and clean borders
  - Maintain current props and API

  **References**:
  - `frontend/src/components/ui/Button.vue`
  - `frontend/src/components/ui/Card.vue`
  - `frontend/src/components/ui/Input.vue`
  - `frontend/src/components/ui/Modal.vue`

  **Acceptance Criteria**:
  - [ ] All UI components render correctly on light background
  - [ ] Hover/focus states visible but subtle

---

- [x] 3. Set up Vitest test infrastructure

  **What to do**:
  - Add Vitest + @vue/test-utils + jsdom
  - Create `vitest.config.ts`
  - Add `test` script in `frontend/package.json`
  - Add a smoke test file

  **References**:
  - `frontend/package.json`

  **Acceptance Criteria**:
  - [ ] `npm run test` executes Vitest successfully
  - [ ] At least one passing test

---

- [x] 4. App layout + navigation labels CN

  **What to do**:
  - Update App layout to light palette
  - Translate nav labels to Chinese
  - Ensure sidebar/header match home visuals

  **References**:
  - `frontend/src/App.vue`

  **Acceptance Criteria**:
  - [ ] Sidebar uses light surfaces and borders
  - [ ] Navigation labels are Chinese

---

- [x] 5. HomeView CN + light visuals

  **What to do**:
  - Translate hero, feature cards, CTA buttons to Chinese
  - Apply light theme styling consistent with App
  - Keep layout structure, adjust spacing/typography

  **References**:
  - `frontend/src/views/HomeView.vue`

  **Acceptance Criteria**:
  - [ ] All visible text on home is Chinese
  - [ ] Page matches light theme palette

---

- [x] 6. WorkflowView light canvas + toolbar

  **What to do**:
  - Update toolbar/background to light colors
  - Adjust Vue Flow background grid for light canvas
  - Translate toolbar labels if needed

  **References**:
  - `frontend/src/views/WorkflowView.vue`
  - `frontend/src/components/NodeConfigPanel.vue`

  **Acceptance Criteria**:
  - [ ] Canvas grid visible on light background
  - [ ] Toolbar visually consistent with home

---

- [x] 7. Node components light style

  **What to do**:
  - Harmonize node colors with light palette
  - Reduce heavy glow; use subtle shadow and border
  - Keep handles and logic unchanged

  **References**:
  - `frontend/src/components/nodes/*.vue`

  **Acceptance Criteria**:
  - [ ] Nodes look cohesive on light canvas
  - [ ] No logic changes to node behavior

---

- [x] 8. KnowledgeView light + CN

  **What to do**:
  - Translate all UI labels and placeholders
  - Update card/table styles to light palette
  - Ensure upload area and progress bars match home

  **References**:
  - `frontend/src/views/KnowledgeView.vue`

  **Acceptance Criteria**:
  - [ ] All visible text is Chinese
  - [ ] Cards and tables use light surfaces

---

- [x] 9. ChatTerminal light + CN

  **What to do**:
  - Translate UI labels, placeholders, button text
  - Unify sidebar and message bubble styles with home
  - Ensure input area uses light palette

  **References**:
  - `frontend/src/views/ChatTerminal.vue`

  **Acceptance Criteria**:
  - [ ] All visible text is Chinese
  - [ ] Chat UI matches light theme

---

- [x] 10. Add Vitest smoke tests

  **What to do**:
  - Add tests that mount Home/Workflow/Knowledge/Chat
  - Assert core Chinese headings exist
  - Run `npm run test`

  **References**:
  - `frontend/src/views/HomeView.vue`
  - `frontend/src/views/WorkflowView.vue`
  - `frontend/src/views/KnowledgeView.vue`
  - `frontend/src/views/ChatTerminal.vue`

  **Acceptance Criteria**:
  - [ ] Tests pass with `npm run test`
  - [ ] Assertions validate Chinese UI labels

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1-2 | `feat(ui): switch to light theme tokens` | theme + ui components | npm run lint |
| 3 | `chore(test): add vitest setup` | vitest config + deps | npm run test |
| 4-9 | `feat(ui): unify light theme styles` | views + nodes | npm run lint |
| 10 | `test(ui): add smoke tests` | __tests__ | npm run test |

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npm run lint
npm run type-check
npm run test
npm run build
```

### Final Checklist
- [x] 全站文案中文化
- [x] 视觉统一且为浅色主题
- [x] 测试框架可运行
- [x] 构建成功
