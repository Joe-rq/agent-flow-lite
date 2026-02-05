# 删除工作流信息面板

## TL;DR

> **Quick Summary**: 删除 WorkflowEditor.vue 中的"工作流信息"左侧面板，让画布占据更多空间
> 
> **Deliverables**: 
> - 移除左侧 node-panel 区域
> - 画布宽度调整为 100%
> - 可选：在顶部工具栏显示工作流名称
> 
> **Estimated Effort**: Quick (5-10 minutes)
> **Parallel Execution**: NO

---

## Context

### Original Request
用户认为"工作流信息"面板不美观且占用空间，决定删除（方案1）

### Current State
- WorkflowEditor.vue 左侧有固定宽度的 node-panel（25%，200-300px）
- 显示：名称、ID、状态
- 右侧是 Vue Flow 画布（75%）

---

## Work Objectives

### Core Objective
删除左侧"工作流信息"面板，让画布占据整个编辑区域

### Concrete Deliverables
- 移除 node-panel HTML 结构
- 移除相关 CSS 样式
- 调整画布宽度为 100%
- （可选）在顶部工具栏显示工作流名称

### Definition of Done
- [x] 左侧面板已删除
- [x] 画布占据整个宽度
- [x] 无布局错误

---

## TODOs

- [x] 1. 删除工作流信息面板

  **What to do**:
  - 删除 lines 26-44 的 node-panel HTML
  - 删除相关的 CSS 样式（.node-panel, .panel-header, .panel-info, .info-item 等）
  - 调整 .canvas-container 宽度为 100%
  - 可选：在 toolbar-left 显示工作流名称

  **Must NOT do**:
  - 不改变任何功能逻辑
  - 不删除其他部分

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Acceptance Criteria**:
  - 左侧面板消失
  - 画布宽度 100%
  - 布局正常

  **Commit**: YES
  - Message: `refactor(ui): remove workflow info panel for cleaner layout`
  - Files: `frontend/src/views/WorkflowEditor.vue`
