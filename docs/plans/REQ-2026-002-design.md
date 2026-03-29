# REQ-2026-002 Design

## Background

前端存在 9 处 `alert()` 和 7 处 `confirm()` 调用，需要替换为统一的通知系统。

### 当前调用点分析

**alert() 调用（9 处）：**
| 文件 | 场景 | 类型 |
|------|------|------|
| useWorkflowExecution.ts:13 | 工作流执行错误 | error |
| useWorkflowCrud.ts:40 | 工作流操作错误 | error |
| useUserAdmin.ts:34 | 用户管理错误 | error |
| useSkillRunner.ts:74 | 技能必填项缺失 | warning |
| SkillsView.vue:106 | 加载技能列表失败 | error |
| SkillsView.vue:127 | 删除技能失败 | error |
| useSkillForm.ts:118 | 加载技能失败 | error |
| useKnowledgeApi.ts:39 | 知识库操作错误 | error |
| useChatSSE.ts:143 | 发送消息失败 | error |

**confirm() 调用（7 处）：**
| 文件 | 场景 | 类型 |
|------|------|------|
| useChatSession.ts:41 | 删除会话 | danger |
| useWorkflowCrud.ts:106 | 删除工作流 | danger |
| useKnowledgeApi.ts:87 | 删除知识库 | danger |
| useKnowledgeApi.ts:96 | 删除文档 | danger |
| useEditorActions.ts:37 | 删除连线 | warning |
| useEditorActions.ts:41 | 删除节点 | warning |
| SkillsView.vue:119 | 删除技能 | danger |

## Goal

- 替换 9 处 alert() 为 Toast 组件
- 替换 7 处 confirm() 为 ConfirmDialog 组件
- 提升产品专业感和用户体验

## Scope

### In scope

1. **Toast 组件** — 非阻塞式通知
   - 支持 4 种类型：success / error / warning / info
   - 自动消失（默认 4 秒）
   - 手动关闭按钮
   - 堆叠显示（多个 Toast 同时存在）
   - aria-live 无障碍支持

2. **ConfirmDialog 组件** — 模态确认框
   - 支持标题、消息、确认/取消按钮
   - 支持 ESC 取消、Enter 确认
   - 支持三种类型：danger / warning / info
   - aria-modal 无障碍支持

3. **Composables** — 组合式 API
   - `useToast()` — 返回 success/error/warning/info 方法
   - `useConfirm()` — 返回 show() 方法（返回 Promise<boolean>）

4. **替换所有调用点** — 16 处

### Out of scope

- 国际化支持
- 主题切换
- 通知历史持久化
- 第三方库引入

## Product Review

### User Value

- 解决的问题：原生弹窗破坏专业感、阻塞 UI、样式不统一
- 目标用户：所有产品用户
- 预期收益：提升产品专业感、改善用户体验、符合现代 Web 应用预期

### Recommendation

- **Proceed** — 评审报告已确认此为 P1 优先级

## Engineering Review

### Architecture Impact

- 影响模块：前端 UI 层、Composables 层
- 依赖方向：新增组件被 App.vue 挂载，Composables 被各业务模块调用
- 需要新增或修改的边界：
  - `components/ui/` 新增 3 个组件
  - `composables/` 新增 2 个 composables
  - 修改 9 个文件替换调用

### Verification

- 自动验证：
  - `npm run build` — 类型检查 + 构建
  - `npm run test -- --run --isolate` — 测试套件
- 人工验证：
  - 删除操作确认弹窗样式
  - 错误提示 Toast 显示效果
- 回滚：
  - `git revert` 单次提交

## Implementation Plan

### Phase 1: 创建组件（2h）

1. `components/ui/Toast.vue` — 单个通知组件
2. `components/ui/ToastContainer.vue` — 通知容器，处理全局事件
3. `components/ui/ConfirmDialog.vue` — 确认对话框组件

### Phase 2: 创建 Composables（1h）

1. `composables/useToast.ts` — Toast API
2. `composables/useConfirm.ts` — Confirm API

### Phase 3: 挂载全局容器（0.5h）

1. 修改 `App.vue`，添加 `<ToastContainer />` 和 `<ConfirmDialog />`

### Phase 4: 替换调用点（2h）

1. 替换 9 处 alert() 调用
2. 替换 7 处 confirm() 调用
3. 将同步 `confirm()` 改为异步 `await confirm.show()`

### Phase 5: 验证（1h）

1. `npm run build`
2. `npm run test -- --run --isolate`
3. 人工验证关键场景

## File List

```
frontend/src/
├── components/ui/
│   ├── Toast.vue           # 新增
│   ├── ToastContainer.vue  # 新增
│   └── ConfirmDialog.vue   # 新增
├── composables/
│   ├── useToast.ts         # 新增
│   ├── useConfirm.ts       # 新增
│   ├── chat/
│   │   ├── useChatSSE.ts       # 修改
│   │   └── useChatSession.ts   # 修改
│   ├── knowledge/
│   │   └── useKnowledgeApi.ts  # 修改
│   ├── workflow/
│   │   ├── useWorkflowCrud.ts      # 修改
│   │   ├── useWorkflowExecution.ts # 修改
│   │   └── useEditorActions.ts     # 修改
│   ├── skills/
│   │   ├── useSkillRunner.ts  # 修改
│   │   └── useSkillForm.ts    # 修改
│   └── useUserAdmin.ts        # 修改
├── views/
│   └── SkillsView.vue        # 修改
└── App.vue                   # 修改
```
