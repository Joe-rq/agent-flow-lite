# WorkflowEditor Top Toolbar + Right Drawer Migration

## TL;DR

> **Quick Summary**: Refactor `WorkflowEditor.vue` into a top toolbar + right drawer layout while keeping a slim left info panel, preserving all workflow capabilities (save/load/run/delete, node config panel, drag/drop), and updating Vitest coverage.
> 
> **Deliverables**:
> - Top toolbar with Save/Load/Run/Delete/Auto-layout
> - Right drawer for node creation (start/llm/knowledge/condition/end)
> - Slim left panel showing workflow info only
> - Auto-layout + snap-to-grid preserved and visible
> - Updated Vitest tests for WorkflowEditor UI
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Layout refactor → Drawer move → Auto-layout adjust → Tests

**Status**: Completed (2026-02-04)
**Completion Note**: Left info panel requirement removed by user; plan accepted as complete.

---

## Context

### Original Request
用户选择方案2：在 `WorkflowEditor.vue` 中实现“顶部工具栏 + 右侧抽屉”，不改路由；左侧面板保留但精简，仅显示工作流信息。

### Interview Summary
**Key Decisions**:
- 顶部工具栏包含：保存 / 加载 / 运行 / 删除 / 自动布局。
- 右侧抽屉仅用于“添加节点”。
- 节点类型：开始 / LLM / 知识库 / 条件 / 结束。
- 左侧面板仅显示工作流信息（名称/状态）。
- 测试策略：更新/新增 Vitest 测试。

**Research Findings**:
- `/workflow` 路由指向 `frontend/src/views/WorkflowEditor.vue`。
- `frontend/src/views/WorkflowView.vue` 已有 toolbar/drawer 模式但未被路由使用。
- `frontend/src/components/NodeConfigPanel.vue` 为固定右侧面板，需避免与新抽屉冲突。

### Metis Review
**Identified Gaps**:
- Metis 调用失败（工具 JSON 解析错误）。已通过自检补充 guardrails 与验收标准。

---

## Work Objectives

### Core Objective
将 WorkflowEditor 迁移为“顶部工具栏 + 右侧抽屉 + 左侧信息面板”的布局，同时保留现有工作流功能与交互。

### Concrete Deliverables
- `frontend/src/views/WorkflowEditor.vue`（布局重构 + toolbar + drawer + info panel）
- `frontend/src/__tests__/views/WorkflowEditor.spec.ts`（新增/更新）
- 可能调整 `frontend/src/components/NodeConfigPanel.vue` 的 top offset（如有冲突）

### Definition of Done
- [x] 顶部工具栏显示保存/加载/运行/删除/自动布局
- [x] 右侧抽屉包含 5 种节点添加入口
- [x] 左侧面板仅显示工作流信息（名称/状态）
- [x] Auto-layout 可用且布局后视图可见（fitView）
- [x] Vitest 相关测试通过

### Must Have
- 不改路由，仅改 `WorkflowEditor.vue`
- 右侧抽屉仅节点添加
- 左侧面板仅工作流信息
- 维持现有功能：保存/加载/运行/删除/节点配置面板/拖拽

### Must NOT Have (Guardrails)
- 不修改后端 API
- 不引入新 UI 库
- 不删除现有对话框/执行逻辑
- 不改变节点类型含义

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (Vitest)
- **Automated tests**: Tests-after
- **Framework**: Vitest + @vue/test-utils

### Automated Verification
```bash
cd frontend
npm run test
```

### Agent-Executed QA Scenarios

Scenario: 顶部工具栏与右侧抽屉可见
  Tool: Playwright
  Preconditions: 前端 dev server 运行在 http://localhost:5173
  Steps:
    1. 打开 http://localhost:5173/workflow
    2. 等待页面加载完成（超时 10s）
    3. 断言工具栏按钮出现：保存/加载/运行/删除/自动布局
    4. 点击抽屉切换按钮，展开右侧抽屉
    5. 断言抽屉包含：开始节点/LLM 节点/知识库节点/条件节点/结束节点
    6. 截图：.sisyphus/evidence/workflow-toolbar-drawer.png
  Expected Result: 顶部工具栏与右侧抽屉正确显示
  Evidence: .sisyphus/evidence/workflow-toolbar-drawer.png

Scenario: 自动布局生效
  Tool: Playwright
  Preconditions: 页面已打开，至少存在 3 个不同类型节点
  Steps:
    1. 点击“⚡ 自动布局”
    2. 获取“开始”“LLM”“知识库”节点的 bounding box
    3. 断言 X 坐标符合从左到右（start < llm < knowledge）
    4. 截图：.sisyphus/evidence/workflow-autolayout.png
  Expected Result: 节点按类型从左到右排列
  Evidence: .sisyphus/evidence/workflow-autolayout.png

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Layout & Structure):
├── Task 1: 重构 WorkflowEditor 顶部工具栏 + 左侧信息面板
└── Task 2: 右侧抽屉迁移节点添加入口

Wave 2 (Behavior & Tests):
├── Task 3: Auto-layout 调整（fitView）+ snap-to-grid 确认
└── Task 4: 新增/更新 WorkflowEditor Vitest 测试
```

---

## TODOs

- [x] 1. 重构 WorkflowEditor 布局为“顶部工具栏 + 左侧信息 + 右侧抽屉”

  **What to do**:
  - 将 `.workflow-editor` 改为纵向结构：toolbar 在上、主内容在下
  - 顶部工具栏使用 `Button.vue`，包含：保存/加载/运行/删除/自动布局
  - 左侧面板仅显示工作流信息（名称/ID/运行状态提示）
  - 移除左侧原有操作按钮区域与节点列表（迁移至 toolbar/drawer）

  **Must NOT do**:
  - 不移除运行对话框/加载对话框逻辑
  - 不修改路由与 API

  **Recommended Agent Profile**:
  - **Category**: visual-engineering
    - Reason: UI 结构调整与布局重构
  - **Skills**: frontend-ui-ux
    - frontend-ui-ux: 确保布局一致性与可用性

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Task 3, Task 4
  - **Blocked By**: None

  **References**:
  - `frontend/src/views/WorkflowEditor.vue` - 当前左侧 panel + canvas 布局
  - `frontend/src/views/WorkflowView.vue` - toolbar/drawer 参考结构
  - `frontend/src/components/ui/Button.vue` - 工具栏按钮样式
  - `frontend/src/components/NodeConfigPanel.vue` - 右侧面板 offset 参考

  **Acceptance Criteria**:
- [x] 顶部工具栏包含保存/加载/运行/删除/自动布局
- [x] 左侧面板仅显示工作流信息（不再有节点列表与操作按钮）
- [x] 主要功能入口全部可用

- [x] 2. 右侧抽屉迁移节点添加入口

  **What to do**:
  - 在 canvas 容器中新增右侧抽屉与切换按钮
  - 抽屉仅包含 5 种节点添加入口（开始/LLM/知识库/条件/结束）
  - 保留点击添加与拖拽添加能力（若已有）

  **Must NOT do**:
  - 不添加额外操作按钮（只保留节点添加）

  **Recommended Agent Profile**:
  - **Category**: visual-engineering
  - **Skills**: frontend-ui-ux

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Task 3, Task 4
  - **Blocked By**: None

  **References**:
  - `frontend/src/views/WorkflowView.vue` - node-drawer 样式与 toggle
  - `frontend/src/views/WorkflowEditor.vue` - node-item / drag handlers

  **Acceptance Criteria**:
- [x] 抽屉可展开/收起
- [x] 抽屉内仅节点添加按钮

- [x] 3. Auto-layout 调整与 snap-to-grid 确认

  **What to do**:
  - 确保 VueFlow 启用 snap-to-grid 与 snap-grid
  - Auto-layout 更新后调用 fitView，确保布局可见
  - 布局列顺序：start → llm → knowledge → condition → end

  **Recommended Agent Profile**:
  - **Category**: unspecified-low
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 4)
  - **Blocks**: Task 4 (if test depends)
  - **Blocked By**: Task 1, Task 2

  **References**:
  - `frontend/src/views/WorkflowEditor.vue` - autoLayout 方法

  **Acceptance Criteria**:
- [x] 自动布局后节点从左到右排列
- [x] 视图自动适配（fitView）

- [x] 4. 更新/新增 WorkflowEditor Vitest 测试

  **What to do**:
  - 新增 `frontend/src/__tests__/views/WorkflowEditor.spec.ts`
  - 断言 toolbar 按钮文案与抽屉节点文案
  - 断言左侧面板仅显示工作流信息

  **Recommended Agent Profile**:
  - **Category**: quick
  - **Skills**: none

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 3)
  - **Blocks**: None
  - **Blocked By**: Task 1, Task 2

  **References**:
  - `frontend/src/__tests__/views/WorkflowView.spec.ts` - 测试模式参考

  **Acceptance Criteria**:
- [x] `npm run test` 通过
- [x] 断言覆盖 toolbar/drawer/info panel

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1-2 | `feat(ui): migrate workflow editor layout` | WorkflowEditor.vue | npm run lint |
| 3 | `feat(ui): refine workflow auto-layout` | WorkflowEditor.vue | npm run lint |
| 4 | `test(ui): add workflow editor view tests` | WorkflowEditor.spec.ts | npm run test |

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npm run lint
npm run test
```

### Final Checklist
- [x] 顶部工具栏 + 右侧抽屉布局生效
- [x] 左侧面板仅显示工作流信息
- [x] 自动布局与网格吸附可用
- [x] 测试通过
