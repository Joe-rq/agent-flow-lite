# REQ-2026-003: P1 任务实施

## 状态
- 当前状态：completed
- 当前阶段：ship

## 背景
根据 `reviews/agent-flow-lite-review-r2.md` 审查文档执行 P1 任务，提升系统稳定性和可观测性。

## 目标
- ChromaDB 维度变更警告：防止用户误改嵌入模型配置导致知识库不可用
- SSE 重连机制：提升网络不稳定情况下的用户体验
- 可观测性仪表盘：提供 LLM 成本监控能力
- SDK 生成：为外部开发者提供 Python/JS SDK

## 非目标
- P2/P3 任务（不在本次范围）
- 复杂图表库集成

## 范围
- 涉及目录 / 模块：
  - `frontend/src/views/SettingsView.vue`
  - `frontend/src/composables/useSSEStream.ts`
  - `frontend/src/composables/chat/useChatSSE.ts`
  - `frontend/src/composables/workflow/useWorkflowExecution.ts`
  - `backend/app/api/observability.py` (新增)
  - `backend/app/api/settings.py`
  - `frontend/src/views/AdminDashboardView.vue` (新增)
  - `frontend/src/composables/useDashboard.ts` (新增)
  - `scripts/generate-sdk.sh` (新增)
  - `sdks/` (新增目录)

- 影响接口 / 页面：
  - `GET /api/v1/settings/embedding`
  - `GET /api/v1/observability/token-usage`
  - `/settings` 页面
  - `/admin/dashboard` 页面

## 验收标准
- [x] 设置页显示嵌入模型配置，知识库存在时显示风险提示
- [x] SSE 连接失败时自动重试（指数退避）
- [x] 管理仪表盘显示 token 使用统计
- [x] SDK 生成脚本可用

## 设计与实现链接
- 设计稿：基于 `reviews/agent-flow-lite-review-r2.md` P1 计划
- 相关规范：无

## 报告链接
- Code Review：`requirements/reports/REQ-2026-003-code-review.md`
- QA：`requirements/reports/REQ-2026-003-qa.md`
- Ship：`requirements/reports/REQ-2026-003-ship.md`

## 验证计划
- 前端：`cd frontend && npm run build`
- 后端：`cd backend && uv run python -m py_compile app/api/observability.py`

## 风险与回滚
- 风险：SSE 重连可能导致重复请求
- 回滚方式：git revert

## 关键决策
- 2026-03-29：SSE 重连使用指数退避，最大 3 次重试
- 2026-03-29：可观测性仪表盘不引入图表库，保持简洁
- 2026-03-29：SDK 使用手写客户端（OpenAPI Generator 环境问题）
