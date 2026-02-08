# Post-Gate Stability Quick Pass

## TL;DR

> **Quick Summary**: 修复两个非阻塞 CI 作业的失败：(1) E2E 缺少前端服务器启动；(2) 全量测试因 `isolate: false` 导致状态污染。不变更合并阻塞策略。
>
> **Deliverables**:
> - E2E job 在 Playwright 执行前启动前端服务并等待就绪。
> - 全量测试命令加 `--isolate`，消除跨文件状态污染。
> - Critical Layer 保持绿色。
>
> **Parallel Execution**: NO - 串行
> **Critical Path**: Task 1 -> Task 2 -> Task 3

---

## Context

### 当前状态
- **Critical Layer**: 全绿（4/4 通过）
- **E2E Tests (Playwright)**: 失败 - `ERR_CONNECTION_REFUSED localhost:5173`
- **Frontend Full Tests (All)**: 失败 - 34/164 测试不稳定失败

### 根因分析

**E2E 失败根因**：CI 工作流（`.github/workflows/quality-gate.yml:256-276`）只启动了后端服务器，没有启动前端服务器。Playwright 测试（`login-verification.spec.ts:9`）访问 `http://localhost:5173/login` 时连接被拒绝。

**全量测试失败根因**：`vitest.config.ts` 设置了 `isolate: false`（资源约束），测试进程间共享全局状态（localStorage、Pinia store、Vue Router 实例），导致文件间状态污染。同一命令连续两次运行，失败的文件不同——证明不是个别测试的 bug，是运行环境问题。

| 运行次数 | 失败文件 |
|---------|---------|
| 第1次 | login (9), users (5), App (3), SkillsView (16), WorkflowView (1) |
| 第2次 | SkillsView (16), WorkflowView (1), App (3), SkillEditor (30), ChatTerminal (2) |

P0 测试已经用 `--isolate` 覆盖了全局配置，所以稳定通过。全量测试缺少这个标志。

### Guardrails
- 不升级 E2E/Full 为阻塞检查（本轮不变更 gate 策略）。
- 不做依赖升级、性能优化、代码重构。
- 不改动 `vitest.config.ts` 中的资源约束。

---

## TODOs

- [x] 1. 修复 E2E 前端服务器启动

  **根因**：E2E job 缺少前端服务器启动步骤。

  **修改文件**：`.github/workflows/quality-gate.yml`

  **具体改动**：在 `Start backend server` 和 `Run E2E tests` 之间插入前端服务启动步骤：

  ```yaml
  - name: Build and serve frontend
    working-directory: frontend
    run: |
      npm run build
      npx vite preview --port 5173 &
      echo $! > /tmp/vite-preview.pid
      # Wait for frontend to be ready
      curl --retry 10 --retry-delay 2 --retry-all-errors http://localhost:5173 || exit 1

  # ... (Run E2E tests step stays here) ...

  - name: Cleanup frontend server
    if: always()
    run: |
      if [ -f /tmp/vite-preview.pid ]; then
        kill "$(cat /tmp/vite-preview.pid)" 2>/dev/null || true
      fi
  ```

  **选型理由**：
  - 用 `vite preview`（静态文件服务）而非 `npm run dev`（开发服务器），因为 CI 环境不需要 HMR，静态服务启动更快、资源占用更低。
  - 用 `curl --retry` 做就绪探测，复用后端启动已有的模式，不引入新依赖。
  - E2E job 已 `needs: [frontend-build]`，但 GitHub Actions 各 job 独立 runner，构建产物不共享，所以仍需在本 job 中执行 `npm run build`。

  **Acceptance Criteria**：
  - [x] E2E job 状态为 **success**（绿色）。
  - [x] 2 个 Playwright 用例全部通过（`login-verification.spec.ts` 中的 login 页面验证 + logout 重定向验证）。

- [x] 2. 修复全量测试状态污染

  **根因**：`vitest.config.ts` 的 `isolate: false` 导致测试文件间共享进程状态。

  **修改文件**：`.github/workflows/quality-gate.yml`

  **具体改动**：第172行，全量测试命令加 `--isolate`：

  ```yaml
  # Before
  run: npm run test -- --run

  # After
  run: npm run test -- --run --isolate
  ```

  **选型理由**：
  - `--isolate` 在命令行层面覆盖 `vitest.config.ts` 的 `isolate: false`，强制每个测试文件独立进程。
  - P0 测试已经用了这个方案（`.github/workflows/quality-gate.yml:107`），验证过可行。
  - 不修改 `vitest.config.ts` 全局配置，避免影响本地开发体验（本地可能需要 `isolate: false` 节省资源）。
  - 不逐个修复 34 个测试的隔离问题——根因在运行环境配置，不在测试代码。

  **验证数据**（本地确认）：
  - `npm run test -- --run --isolate` 本地两次运行均为 **164/164 通过**。
  - 本地环境下状态污染是全量测试失败的主因。若 CI 环境（Ubuntu runner）仍有残余失败，按残余失败清单继续最小修复。

  **Acceptance Criteria**：
  - [x] `npm run test -- --run --isolate` 本地运行 **164/164 通过**。（已在本地验证）
  - [x] P0 测试不受影响（52/52 通过）。（已在本地验证）

- [x] 3. CI 验证 + 关闭报告

  **What to do**：
  - 推送改动，触发 Quality Gate 工作流。
  - 验证 E2E 和 Full Tests 作业状态。
  - Critical Layer 仍然全绿。
  - 保存证据到 `.sisyphus/evidence/`。

  **Acceptance Criteria**：
  - [x] E2E Tests 不再因连接拒绝失败。（CI 已验证）
  - [x] Frontend Full Tests **164/164 通过**（CI 环境）。（CI 已验证）
  - [x] Critical Layer 4/4 绿色，Summary 显示 PASS。（CI 已验证）
  - [x] 证据报告已保存。（已保存到 .sisyphus/evidence/post-gate-stability-quick-pass-verification-20260208.md）

---

## Commit Strategy

| After Task | Message | Files |
|------------|---------|-------|
| 1-2 | `fix(ci): add frontend server to e2e and isolate to full tests` | `.github/workflows/quality-gate.yml` |

一次提交，改动集中在一个文件的两处位置。

---

## Verification Commands

```bash
# 本地验证全量测试（加 --isolate）
cd frontend && npm run test -- --run --isolate

# 本地验证 P0 不受影响
cd frontend && npm run test -- --run --isolate \
  src/__tests__/App.spec.ts \
  src/__tests__/views/ChatTerminal.spec.ts \
  src/__tests__/auth/login.spec.ts

# 后端 P0 不受影响
cd backend && uv run pytest -q \
  tests/test_auth.py \
  tests/test_chat_citation.py \
  tests/test_chat_scoped.py \
  tests/test_workflow_api.py \
  tests/test_knowledge_dimension_mismatch.py
```

---

## Final Checklist

- [x] E2E 连接拒绝问题解决（CI 已验证）
- [x] 全量测试状态污染问题解决（CI 已验证）
- [x] Critical Layer 保持绿色（CI 已验证）
- [x] 非阻塞策略本轮不变更

---

## CI 验证任务

- [x] 4. 验证 GitHub Actions CI 执行结果

  **说明**：由于 CI 执行需要 GitHub Actions 环境，无法在本地自动等待。需要手动验证。

  **验证步骤**：
  1. 访问 https://github.com/Joe-rq/agent-flow-lite/actions/workflows/quality-gate.yml
  2. 找到最新的工作流运行（提交 `27bfb20`）
  3. 检查所有 job 状态是否为 `success`
  4. 特别关注以下修复目标：
     - `e2e-tests` - 应不再因连接拒绝失败
     - `frontend-full-tests` - 应显示 164/164 通过
  5. 查看 `quality-gate-summary` 是否显示 "PASS - All critical checks passed"

  **验收标准**：
  - [x] E2E job 状态为 **success**（绿色） — Run #21794582261, 2 passed
  - [x] 2 个 Playwright 用例全部通过 — `login-verification.spec.ts`: 2 passed (4.0s)
  - [x] Frontend Full Tests **164/164 通过**（CI 环境） — 12 files, 164 passed
  - [x] Critical Layer 4/4 绿色，Summary 显示 PASS — 8/8 jobs success
  - [x] 所有 Final Checklist 项目已勾选 — 连续 4 次运行全绿

  **参考文档**：
  - 详见 `.sisyphus/evidence/ci-verification-guide.md`
  - 证据报告：`.sisyphus/evidence/post-gate-stability-quick-pass-verification-20260208.md`

  **如果 CI 失败**：
  - 记录失败详情到 `.sisyphus/notepads/post-gate-stability-quick-pass/issues.md`
  - 分析失败原因
  - 创建新的修复计划
