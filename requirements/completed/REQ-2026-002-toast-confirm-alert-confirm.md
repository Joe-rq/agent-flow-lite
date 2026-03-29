# REQ-2026-002: Toast/Confirm 通知系统替换 alert/confirm

## 状态
- 当前状态：completed
- 当前阶段：done
- 完成日期：2026-03-29
- 完成提交：`b56f3d2`

## 背景

根据自适应多智能体评审报告（`reviews/agent-flow-lite-review.md`），前端存在 9 处 `alert()` 和 7 处 `confirm()` 调用，这些浏览器原生弹窗破坏产品专业感，阻塞 UI 线程，且无法自定义样式。

**问题分析：**
- `alert()` 无法访问错误详情，一旦关闭信息消失
- `confirm()` 样式与项目主题不统一
- 在 SSE 流式响应场景中，模态弹窗打断用户体验
- 不符合现代 Web 应用的交互预期

## 目标
- 创建统一的 Toast 通知组件，替换所有 `alert()` 调用
- 创建统一的 ConfirmDialog 组件，替换所有 `confirm()` 调用
- 支持非阻塞式通知、可堆叠、可关闭
- 支持无障碍访问（aria-live）

## 非目标
- 不做国际化支持（本次仅中文）
- 不做主题切换支持
- 不做通知历史持久化

## 范围
- 涉及目录 / 模块：
  - `frontend/src/components/ui/` — 新增 Toast.vue、ToastContainer.vue、ConfirmDialog.vue
  - `frontend/src/composables/` — 新增 useToast.ts、useConfirm.ts
  - `frontend/src/App.vue` — 挂载全局容器
  - `frontend/src/composables/**/*.ts` — 替换 alert/confirm 调用
  - `frontend/src/views/**/*.vue` — 替换 alert/confirm 调用

- 影响接口 / 页面 / 脚本：
  - 工作流模块：useWorkflowExecution、useWorkflowCrud、useEditorActions
  - 知识库模块：useKnowledgeApi
  - 聊天模块：useChatSSE、useChatSession
  - 技能模块：useSkillRunner、useSkillForm、SkillsView
  - 用户管理：useUserAdmin

### 约束（Scope Control）

**允许（CAN）**：
- 可修改的文件：`frontend/src/components/ui/*.vue`、`frontend/src/composables/**/*.ts`、`frontend/src/views/**/*.vue`、`frontend/src/App.vue`
- 可新增的测试：`frontend/src/__tests__/components/ui/Toast.spec.ts`、`ConfirmDialog.spec.ts`

**禁止（CANNOT）**：
- 不可修改后端代码
- 不可引入新的第三方依赖（如 vue-toastification）

**边界条件**：
- 改动规模：预计 6-10 小时
- 使用原生 Vue 3 + TypeScript 实现，零额外依赖

## 验收标准
- [x] 所有 9 处 `alert()` 替换为 `toast.success/error/warning/info()`
- [x] 所有 7 处 `confirm()` 替换为 `await confirm.show()`
- [x] Toast 支持自动消失、手动关闭、堆叠显示
- [x] ConfirmDialog 支持 ESC 取消、Enter 确认
- [x] `npm run build` 通过
- [x] `npm run test -- --run --isolate` 通过

## 设计与实现链接
- 设计稿：`docs/plans/REQ-2026-002-design.md`
- 相关规范：评审报告 `reviews/agent-flow-lite-review.md`
- 完成提交：`b56f3d2` feat(frontend): 用 Toast/Confirm 组件替换 alert/confirm

## 报告链接
- Code Review：`requirements/reports/REQ-2026-002-code-review.md`
- QA：`requirements/reports/REQ-2026-002-qa.md`
- Ship：N/A（无发布流程）

## 验证计划
- 计划执行的命令：
  - `cd frontend && npm run build`
  - `cd frontend && npm run test -- --run --isolate`
- 需要的环境：Node.js 20.x
- 需要的人工验证：
  - 手动测试删除操作确认弹窗
  - 手动测试错误提示 Toast 显示

## 阻塞 / 搁置说明（可选）
- 无

## 风险与回滚
- 风险：替换过程中可能遗漏某些调用点
- 回滚方式：`git revert` 本次提交

## 关键决策
- 2026-03-29：由 `req:create` 自动生成骨架
- 2026-03-29：补充具体内容，基于评审报告分析
- 2026-03-29：决定使用原生 Vue 3 实现，不引入第三方库
- 2026-03-29：完成实现，所有验收标准通过
