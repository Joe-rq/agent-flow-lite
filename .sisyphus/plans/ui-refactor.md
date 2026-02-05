# UI 重构：侧边栏抽屉化 + 对话框风格统一

## TL;DR

> **Quick Summary**: 将 App.vue 左侧导航栏改为可折叠抽屉（图标模式），并统一所有页面的对话框风格以匹配主题系统
> 
> **Deliverables**: 
> - App.vue 可折叠侧边栏（60px 折叠态，支持 localStorage 持久化）
> - WorkflowEditor.vue 两个对话框使用主题变量和 Button 组件
> - KnowledgeView.vue 对话框风格统一
> - ChatTerminal.vue 对话框风格统一
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: NO - 顺序执行（先 App.vue，再各页面）
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4

---

## Context

### Original Request
用户希望：
1. 左侧导航栏改为抽屉式（可折叠，仅显示图标）
2. 工作流运行对话框与整体前端风格不一致，需要统一

### Interview Summary
**Key Discussions**:
- 折叠后显示方式：仅显示图标（60px 宽度），支持 tooltip
- 状态持久化：使用 localStorage 记住折叠状态
- 对话框范围：WorkflowEditor.vue 的两个对话框（加载、运行）都要修改
- 其他页面：KnowledgeView.vue 和 ChatTerminal.vue 的对话框也需要统一风格

### Research Findings
- App.vue 当前使用固定 240px 侧边栏，使用 theme.css 变量
- WorkflowEditor.vue 对话框使用硬编码颜色（#2c3e50, #3498db 等）
- Button.vue 组件已存在，有 primary/secondary/danger 三种变体
- 其他页面（KnowledgeView.vue, ChatTerminal.vue）也有相同的硬编码颜色问题

### Metis Review
**Identified Gaps** (addressed):
- 明确了折叠宽度（60px）和状态持久化需求
- 确认了所有需要修改的对话框范围
- 确定了其他页面也需要统一风格

---

## Work Objectives

### Core Objective
将左侧导航栏改为可折叠抽屉，并统一所有页面的对话框风格以匹配主题系统

### Concrete Deliverables
- App.vue 可折叠侧边栏（展开 240px / 折叠 60px）
- WorkflowEditor.vue 加载对话框风格统一
- WorkflowEditor.vue 运行对话框风格统一
- KnowledgeView.vue 对话框风格统一
- ChatTerminal.vue 对话框风格统一

### Definition of Done
- [x] 侧边栏可以折叠/展开，动画流畅
- [x] 折叠状态保存到 localStorage
- [x] 所有对话框使用 theme.css 变量
- [x] 所有对话框按钮使用 Button.vue 组件
- [x] 无硬编码颜色残留

### Must Have
- 侧边栏折叠/展开功能
- localStorage 状态持久化
- 所有对话框风格统一

### Must NOT Have (Guardrails)
- 不添加新的依赖库（如 GSAP、图标库）
- 不修改 Button.vue 的 props 接口
- 不改变对话框的结构或行为逻辑
- 不添加新的对话框功能

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: NO（纯 UI 修改，无需测试框架）
- **Automated tests**: None
- **Agent-Executed QA**: Playwright 视觉验证

### Agent-Executed QA Scenarios (MANDATORY)

**Verification Tool by Deliverable Type:**
| Type | Tool | How Agent Verifies |
|------|------|-------------------|
| **Frontend/UI** | Playwright | Navigate, interact, assert DOM, screenshot |

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
└── Task 1: App.vue 侧边栏折叠功能

Wave 2 (After Wave 1):
└── Task 2: WorkflowEditor.vue 对话框风格统一

Wave 3 (After Wave 2):
└── Task 3: KnowledgeView.vue 对话框风格统一

Wave 4 (After Wave 3):
└── Task 4: ChatTerminal.vue 对话框风格统一

Critical Path: Task 1 → Task 2 → Task 3 → Task 4
Parallel Speedup: N/A (sequential dependencies)
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2, 3, 4 | None |
| 2 | 1 | 3, 4 | None |
| 3 | 1, 2 | 4 | None |
| 4 | 1, 2, 3 | None | None |

---

## TODOs

- [x] 1. App.vue 侧边栏折叠功能

  **What to do**:
  - 添加 `sidebarCollapsed` ref 状态（默认 false）
  - 添加折叠/展开切换按钮（放在 header 或 sidebar 顶部）
  - 修改侧边栏样式：展开时 240px，折叠时 60px
  - 折叠时只显示图标，隐藏文字
  - 添加 CSS transition 动画（300ms ease）
  - 使用 localStorage 保存/恢复折叠状态
  - 折叠状态下添加 tooltip（使用 title 属性或自定义 tooltip）

  **Must NOT do**:
  - 不改变导航链接的路由逻辑
  - 不添加新的依赖库
  - 不影响 main 内容区域的布局逻辑

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 纯 UI 布局修改，需要精确的 CSS 控制
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: 处理侧边栏折叠动画和响应式布局

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Task 2, 3, 4
  - **Blocked By**: None

  **References**:
  - `frontend/src/App.vue:12-24` - 当前侧边栏结构
  - `frontend/src/styles/theme.css` - 主题变量
  - `frontend/src/App.vue:86-106` - RouterLink 样式

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Sidebar collapse and expand
    Tool: Playwright
    Preconditions: Dev server running on localhost:5173
    Steps:
      1. Navigate to: http://localhost:5173
      2. Wait for: .app-sidebar visible (timeout: 5s)
      3. Assert: .app-sidebar width is 240px
      4. Click: sidebar toggle button
      5. Wait for: 350ms (animation duration)
      6. Assert: .app-sidebar width is 60px
      7. Assert: nav link text is hidden or has opacity 0
      8. Click: sidebar toggle button again
      9. Wait for: 350ms
      10. Assert: .app-sidebar width is 240px
      11. Screenshot: .sisyphus/evidence/task-1-sidebar-toggle.png
    Expected Result: Sidebar toggles between 240px and 60px smoothly
    Evidence: .sisyphus/evidence/task-1-sidebar-toggle.png
  
  Scenario: Sidebar state persists in localStorage
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Navigate to: http://localhost:5173
      2. Click: sidebar toggle button
      3. Reload page
      4. Wait for: page loaded (timeout: 5s)
      5. Assert: .app-sidebar width is 60px (still collapsed)
      6. Click: sidebar toggle button
      7. Reload page
      8. Assert: .app-sidebar width is 240px (expanded)
    Expected Result: Sidebar state persists across page reloads
    Evidence: localStorage content captured
  ```

  **Evidence to Capture**:
  - [x] Screenshots in .sisyphus/evidence/ for sidebar states
  - [x] localStorage state verification

  **Commit**: YES
  - Message: `feat(ui): add collapsible sidebar with localStorage persistence`
  - Files: `frontend/src/App.vue`

- [x] 2. WorkflowEditor.vue 对话框风格统一

  **What to do**:
  - 替换所有硬编码颜色为 theme.css 变量
  - 将原生按钮替换为 Button.vue 组件
  - 修改的对话框：
    - 加载工作流对话框（showLoadDialog）
    - 运行工作流对话框（showRunDialog）
  - 颜色映射：
    - `#2c3e50` → `var(--text-primary)`
    - `#3498db` → `var(--accent-cyan)`
    - `#7f8c8d` → `var(--text-muted)`
    - `#e9ecef`, `#f8f9fa` → `var(--bg-secondary)` 或 `var(--surface-secondary)`
    - `#ecf0f1`, `#bdc3c7`, `#d5dbdb` → `var(--border-primary)` 或 `var(--bg-tertiary)`
  - 按钮替换：
    - `.btn-secondary` → `<Button variant="secondary">`
    - `.btn-run` → `<Button variant="primary">`

  **Must NOT do**:
  - 不改变对话框的结构或内容
  - 不修改对话框的打开/关闭逻辑
  - 不影响 z-index 或定位

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI 样式统一，需要精确的颜色替换
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: 确保对话框风格与整体主题一致

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Task 3, 4
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/views/WorkflowEditor.vue:162-217` - 两个对话框的模板
  - `frontend/src/views/WorkflowEditor.vue:941-1086` - 对话框样式
  - `frontend/src/components/ui/Button.vue` - Button 组件
  - `frontend/src/styles/theme.css` - 主题变量

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: No hardcoded colors in WorkflowEditor dialogs
    Tool: Bash (grep)
    Preconditions: None
    Steps:
      1. Run: cd frontend && grep -n "#2c3e50\|#3498db\|#7f8c8d\|#e9ecef\|#f8f9fa\|#ecf0f1\|#bdc3c7\|#d5dbdb" src/views/WorkflowEditor.vue
      2. Assert: Command returns no matches (exit code 1 or empty output)
    Expected Result: No hardcoded colors remain in WorkflowEditor.vue
    Evidence: grep output captured
  
  Scenario: Dialog buttons use Button component
    Tool: Bash (grep)
    Preconditions: None
    Steps:
      1. Run: grep -n "<Button" frontend/src/views/WorkflowEditor.vue
      2. Assert: Output contains buttons for both dialogs
      3. Run: grep -n "btn-secondary\|btn-run" frontend/src/views/WorkflowEditor.vue
      4. Assert: No native button class usage in dialog sections
    Expected Result: All dialog buttons use Button.vue component
    Evidence: grep output captured
  
  Scenario: Run dialog visual verification
    Tool: Playwright
    Preconditions: Dev server running, workflow exists
    Steps:
      1. Navigate to: http://localhost:5173/workflow
      2. Click: 运行工作流 button
      3. Wait for: .dialog.run-dialog visible (timeout: 5s)
      4. Assert: Dialog background uses --bg-secondary
      5. Assert: Dialog buttons use Button component styles
      6. Screenshot: .sisyphus/evidence/task-2-run-dialog.png
      7. Click: 关闭 button
      8. Click: 加载工作流 button
      9. Wait for: .dialog visible
      10. Screenshot: .sisyphus/evidence/task-2-load-dialog.png
    Expected Result: Both dialogs use theme colors and Button component
    Evidence: Screenshots in .sisyphus/evidence/
  ```

  **Evidence to Capture**:
  - [x] grep 输出验证无硬编码颜色
  - [x] Screenshots 验证对话框外观

  **Commit**: YES
  - Message: `style(ui): unify WorkflowEditor dialog styles with theme`
  - Files: `frontend/src/views/WorkflowEditor.vue`

- [x] 3. KnowledgeView.vue 对话框风格统一

  **What to do**:
  - 与 Task 2 相同：替换硬编码颜色，使用 Button 组件
  - 查找 KnowledgeView.vue 中的所有对话框
  - 应用相同的颜色映射规则

  **Must NOT do**:
  - 不改变对话框功能逻辑

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Task 4
  - **Blocked By**: Task 1, 2

  **References**:
  - `frontend/src/views/KnowledgeView.vue` - 需要检查文件内容

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: No hardcoded colors in KnowledgeView
    Tool: Bash (grep)
    Steps:
      1. Run: cd frontend && grep -n "#2c3e50\|#3498db\|#7f8c8d\|#e9ecef\|#f8f9fa\|#ecf0f1\|#bdc3c7\|#d5dbdb" src/views/KnowledgeView.vue
      2. Assert: Command returns no matches
    Expected Result: No hardcoded colors remain
  
  Scenario: KnowledgeView dialogs use Button component
    Tool: Bash (grep)
    Steps:
      1. Run: grep -n "<Button" frontend/src/views/KnowledgeView.vue
      2. Assert: Output shows Button component usage
    Expected Result: All buttons use Button.vue
  ```

  **Commit**: YES
  - Message: `style(ui): unify KnowledgeView dialog styles with theme`
  - Files: `frontend/src/views/KnowledgeView.vue`

- [x] 4. ChatTerminal.vue 对话框风格统一

  **What to do**:
  - 与 Task 2、3 相同：替换硬编码颜色，使用 Button 组件
  - 查找 ChatTerminal.vue 中的所有对话框
  - 应用相同的颜色映射规则

  **Must NOT do**:
  - 不改变对话框功能逻辑

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: Task 1, 2, 3

  **References**:
  - `frontend/src/views/ChatTerminal.vue` - 需要检查文件内容

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: No hardcoded colors in ChatTerminal
    Tool: Bash (grep)
    Steps:
      1. Run: cd frontend && grep -n "#2c3e50\|#3498db\|#7f8c8d\|#e9ecef\|#f8f9fa\|#ecf0f1\|#bdc3c7\|#d5dbdb" src/views/ChatTerminal.vue
      2. Assert: Command returns no matches
    Expected Result: No hardcoded colors remain
  
  Scenario: ChatTerminal dialogs use Button component
    Tool: Bash (grep)
    Steps:
      1. Run: grep -n "<Button" frontend/src/views/ChatTerminal.vue
      2. Assert: Output shows Button component usage
    Expected Result: All buttons use Button.vue
  ```

  **Commit**: YES
  - Message: `style(ui): unify ChatTerminal dialog styles with theme`
  - Files: `frontend/src/views/ChatTerminal.vue`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(ui): add collapsible sidebar with localStorage persistence` | App.vue | Playwright screenshot |
| 2 | `style(ui): unify WorkflowEditor dialog styles with theme` | WorkflowEditor.vue | grep + Playwright |
| 3 | `style(ui): unify KnowledgeView dialog styles with theme` | KnowledgeView.vue | grep |
| 4 | `style(ui): unify ChatTerminal dialog styles with theme` | ChatTerminal.vue | grep |

---

## Success Criteria

### Verification Commands
```bash
# 1. Verify no hardcoded colors in all view files
cd frontend
grep -n "#2c3e50\|#3498db\|#7f8c8d\|#e9ecef\|#f8f9fa\|#ecf0f1\|#bdc3c7\|#d5dbdb" src/views/*.vue
# Expected: No matches

# 2. Verify Button component usage in dialogs
grep -n "<Button" src/views/WorkflowEditor.vue src/views/KnowledgeView.vue src/views/ChatTerminal.vue
# Expected: Multiple matches showing Button usage

# 3. Verify sidebar localStorage
curl -s http://localhost:5173 | head -20
# Then check localStorage in browser dev tools
```

### Final Checklist
- [x] 侧边栏可以折叠/展开，动画流畅（300ms）
- [x] 折叠状态保存到 localStorage
- [x] 折叠时仅显示图标（60px 宽度）
- [x] WorkflowEditor.vue 无硬编码颜色
- [x] KnowledgeView.vue 无硬编码颜色
- [x] ChatTerminal.vue 无硬编码颜色
- [x] 所有对话框按钮使用 Button.vue 组件
- [x] 所有对话框使用 theme.css 变量
