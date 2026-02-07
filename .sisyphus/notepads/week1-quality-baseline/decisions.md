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

---

## 2025-02-07: 分支保护与 Required Checks 配置

### 决策背景
将 Week 1 完成的 CI workflow 中的 critical jobs 绑定到 `main` 分支保护规则，确保 PR 必须通过所有 critical checks 才能合并。

### 核心决策

#### 不在 Week 1 自动启用保护
- **原因**: 团队需要适应新的 CI 流程，避免因配置问题阻断正常开发
- **方案**: 创建配置文档，由管理员在 D3 后手动启用
- **风险**: Week 1 期间代码可直推 main，需依赖团队自律

#### 4 个 Required Checks
与 CI workflow 中的 critical layer 一致：
1. `frontend-type-check` - TypeScript 类型检查
2. `frontend-build` - 前端构建验证
3. `frontend-critical-tests` - 前端 P0 测试
4. `backend-critical-tests` - 后端 P0 测试

#### 分支保护规则
```yaml
enforce_admins: true          # 管理员也需遵守
strict: true                   # 必须同步最新 base 才可合并
required_approving_review_count: 1  # 至少 1 个批准
bypass: disabled              # 不允许任何人绕过
```

### 紧急例外流程
仅限生产严重故障、安全漏洞、紧急热修复场景：
1. 在应急渠道发布紧急例外请求
2. 至少 1 名维护者审批
3. 创建 Issue 记录例外详情（模板已提供）
4. 24 小时内补充遗漏测试
5. 周会复盘

### 配置方式
- **推荐**: GitHub CLI 命令
- **备选**: GitHub Web UI 手动配置
- **IaC**: Terraform 配置（可选）

### 验证清单
- [ ] PR 未通过检查时合并按钮禁用
- [ ] PR 缺少批准时无法合并
- [ ] PR 未同步最新 base 时提示

### 相关文档
- 证据文档: `.sisyphus/evidence/week1-branch-protection-setup.md`
- CI 配置: `.github/workflows/quality-gate.yml`

---

## 2026-02-07: Week 1 验收决策

### 验收结论

**状态**: ✅ Week 1 达标

**判定依据**:
1. P0 测试通过率: 100% (291/291 通过)
2. 构建成功率: 100% (Day0 FAIL → Day7 PASS)
3. Type Check: 0 errors
4. Lint 预算: 11 errors (<= 40 预算) 
5. Task 完成率: 100% (7/7)

### 关键指标变化 (Day0 → Day7)

| 指标 | Day0 | Day7 | 变化 |
|------|------|------|------|
| Frontend Tests | 28/30 | 164/164 | +136, 修复2失败 |
| Frontend Build | FAIL | PASS | 完全修复 |
| Lint Errors | 74 | 11 | -85% |
| Backend Tests | 100 | 159 | +59 |

### Week 2 承接项

**P1 Issue 清零** (2026-02-14 前):
- P1-001: Vue Router 路径未匹配警告 (21次)
- P1-002: 控制台错误输出污染 (7处)

**Week 2 新目标**:
1. E2E 测试启用 (优先级: 高)
2. 测试覆盖率可视化 (优先级: 中)
3. 性能基准测试 (优先级: 中)
4. Lint 债务清零 (优先级: 低)

### 风险记录

- 分支保护待启用 (配置就绪，需管理员手动执行)
- 2个 P1 Issue 遗留 (已分配 Owner 和 Deadline)

### 产出物

- `.sisyphus/evidence/week1-acceptance-report.md` - 完整验收报告

