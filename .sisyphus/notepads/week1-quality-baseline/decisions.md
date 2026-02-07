# CI Workflow Architecture Decisions

## 2025-02-07: 分层 Quality Gate CI Workflow

### 决策背景
建立分层的 CI 质量门禁系统，区分 critical（阻塞）和 full/e2e（信息性）测试层级。

### 架构设计

#### 三层结构

1. **Critical Layer（阻塞层）**
   - Required checks：PR 必须通过才能合并
   - Jobs:
     - `frontend-type-check`: TypeScript 类型检查
     - `frontend-build`: 前端构建验证
     - `frontend-critical-tests`: P0 测试（App, ChatTerminal, auth/login）
     - `backend-critical-tests`: P0 测试（auth, chat_citation, chat_scoped, workflow_api, knowledge_dimension_mismatch）

2. **Full Layer（全量层）**
   - 非阻塞：失败不影响合并
   - Jobs:
     - `frontend-full-tests`: 全量 Vitest 测试
     - `backend-full-tests`: 全量 pytest 测试
   - 使用 `continue-on-error: true`

3. **E2E Layer（端到端层）**
   - 非阻塞：Week 1 不强制
   - Jobs:
     - `e2e-tests`: Playwright 测试（登录验证）
   - 使用 `continue-on-error: true`

### 技术决策

#### 依赖链设计
```
frontend-type-check → frontend-build → frontend-critical-tests → frontend-full-tests
backend-critical-tests → backend-full-tests
```

#### 缓存策略
- Frontend: 使用 `actions/setup-node` 内置 npm 缓存
- Backend: 使用 `actions/cache` 缓存 uv 依赖（`~/.cache/uv` 和 `.venv`）

#### 路径触发
```yaml
paths:
  - 'frontend/**'
  - 'backend/**'
  - '.github/workflows/**'
```

#### 并发控制
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### P0 测试清单

#### Frontend P0
- `src/__tests__/App.spec.ts`
- `src/__tests__/views/ChatTerminal.spec.ts`
- `src/__tests__/auth/login.spec.ts`

#### Backend P0
- `tests/test_auth.py`
- `tests/test_chat_citation.py`
- `tests/test_chat_scoped.py`
- `tests/test_workflow_api.py`
- `tests/test_knowledge_dimension_mismatch.py`

### 阻塞逻辑
`quality-gate-summary` job 统一判断是否通过：
- 仅当所有 4 个 critical jobs 成功时才通过
- full 和 e2e 层结果仅用于信息展示

### 后续优化方向
- Week 2 考虑将 e2e-tests 设为 required
- 添加测试覆盖率报告
- 添加性能基准测试
