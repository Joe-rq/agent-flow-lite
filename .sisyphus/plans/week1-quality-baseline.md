# Week 1 质量基线落地计划（开源教学版）

## TL;DR

> **Quick Summary**: 本周只做质量基线治理，不做新功能。目标是把“可演示”升级成“可审计”，用可执行门禁替代口头承诺。
>
> **Deliverables**:
> - D3 起启用 GitHub Actions + Branch Protection（P0 阻断）
> - 关键链路测试与后端关键测试全部稳定通过
> - Vitest 与 Playwright 测试体系分层，避免收集污染
> - Week1 lint 历史存量压到 `<=40`，新改文件 `0 error`
>
> **Estimated Effort**: 1人 x 7天 x 6小时/天 ~= 42人时
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 5 -> Task 8

---

## Context

### Original Request
用户要求制定第一周详细优化方案，用于把项目从“能跑”提升到“可开源教学”，并要求可量化、可追责、可防口径漂移。

### Interview Summary
**Key Discussions**:
- Week1 仅做质量基线，禁止新增功能
- 采用 B 分层达标
- P0 测试阻断；P1 测试非阻断但必须 issue 化并 7 天清零
- D3 开始强制 CI 与分支保护
- Lint 目标：历史存量 `<=40`，改动文件 `0 error`

**Research Findings**:
- 前端测试拓扑共 13 个 spec，其中 `frontend/src/__tests__/login-verification.spec.ts` 为 Playwright 风格，混在 Vitest 收集路径内
- 存在 flaky 风险点：魔法 `setTimeout`、悬空 Promise
- CI 需拆为 critical/full/e2e 分层，并明确 required checks

### Metis Review
**Identified Gaps（已纳入）**:
- 增补 Day0 基线采集（通过率、lint 分布、耗时）
- 增补“修改文件”定义（以 PR diff 为准）
- 增补 flaky 处置与紧急绕过预案
- 增补“不得放宽 lint 规则/不得顺手重构”硬护栏

---

## Work Objectives

### Core Objective
在 7 天内建立可执行质量门禁，使 `main` 分支从 D3 开始被自动化检查保护，并用明确指标证明项目达到“教学型开源可维护基线”。

### Concrete Deliverables
- `.github/workflows/quality-gate.yml`（分层 CI）
- `frontend` 测试分层规则（Vitest 与 Playwright 分离）
- Week1 基线报告文档（Day0 vs Day7）
- P1 失败 issue 清单（owner + deadline）

### Definition of Done
- [ ] D3 起 `main` 启用分支保护，required checks 生效
- [ ] P0 前端测试与后端关键测试 100% 通过
- [ ] 新改动文件 lint 0 error，历史存量 <=40
- [ ] P1 失败全部有 issue，且 7 天内清零计划明确

### Must Have
- 不允许“口头通过”，必须有命令输出和 CI 记录
- CI 结果作为唯一标准

### Must NOT Have (Guardrails)
- 不新增功能代码
- 不放宽 lint 规则、不加 `eslint-disable` 逃逸
- 不在修测试时顺手重构业务
- 不把 Playwright 测试混入 Vitest 主流水

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> 所有验收均由执行代理自动完成：命令运行、断言、日志/截图留证。

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after（本周以稳定化为主）
- **Framework**: Vitest + Pytest + Playwright(独立E2E)

### Agent-Executed QA Scenarios (GLOBAL)

Scenario: Day0 基线采集
  Tool: Bash
  Preconditions: 依赖已安装
  Steps:
    1. 容错采集 frontend（允许失败并记录退出码）:
       - `npm run type-check > .sisyphus/evidence/day0-typecheck.txt 2>&1; echo $? > .sisyphus/evidence/day0-typecheck.rc`
       - `npm run build > .sisyphus/evidence/day0-build.txt 2>&1; echo $? > .sisyphus/evidence/day0-build.rc`
       - `npm run test -- --run > .sisyphus/evidence/day0-test.txt 2>&1; echo $? > .sisyphus/evidence/day0-test.rc`
       - `npm run lint > .sisyphus/evidence/day0-lint.txt 2>&1; echo $? > .sisyphus/evidence/day0-lint.rc`
    2. 容错采集 backend:
       - `uv run pytest -q > .sisyphus/evidence/day0-pytest.txt 2>&1; echo $? > .sisyphus/evidence/day0-pytest.rc`
    3. 汇总失败项、退出码、lint error 数量、耗时
  Expected Result: 生成可比较的 Day0 数据表
  Failure Indicators: 结果缺失任一维度（退出码/失败项/错误数/耗时）
  Evidence: `.sisyphus/evidence/week1-day0-baseline.txt`
  Failure Recovery: 若任一命令无法执行，记录为 `infra-blocker` 并转 Task 1 子问题，不阻断基线采集

Scenario: D3 质量门禁阻断验证
  Tool: Bash + GitHub CLI
  Preconditions: CI workflow 已提交，仓库具备分支保护权限
  Steps:
    1. 创建带故意失败检查的测试 PR 分支
    2. 触发 CI，验证 required checks 出现红灯
    3. 尝试合并 PR，断言被平台拒绝
  Expected Result: P0/critical check 未通过时不可合并
  Failure Indicators: 红灯 PR 仍可合并
  Evidence: `.sisyphus/evidence/week1-d3-branch-protection.txt`
  Failure Recovery: 触发紧急预案（见 Task 6），24小时内恢复保护并补审计记录

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
- Task 1 Day0基线采集
- Task 2 测试分层与污染隔离

Wave 2 (After Wave 1):
- Task 3 修复P0失败与flaky模式
- Task 4 建立P1 issue化追踪
- Task 5 CI分层workflow实现

Wave 3 (After Wave 2):
- Task 6 启用分支保护与required checks
- Task 7 lint债务收敛到<=40
- Task 8 Week1验收报告与移交

Critical Path: Task 1 -> Task 2 -> Task 5 -> Task 8

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 3,5,7,8 | 2 |
| 2 | None | 3,5 | 1 |
| 3 | 1,2 | 8 | 4 |
| 4 | 1 | 8 | 3,5 |
| 5 | 1,2 | 6,8 | 4 |
| 6 | 5 | 8 | 7 |
| 7 | 1 | 8 | 6 |
| 8 | 3,4,5,6,7 | None | None |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1,2 | quick + explore |
| 2 | 3,4,5 | unspecified-high + git-master |
| 3 | 6,7,8 | quick + writing |

---

## TODOs

- [x] 1. 采集 Day0 基线并固化指标定义

  **What to do**:
  - 运行并记录前后端基线命令（通过率、失败项、lint error、耗时）
  - 使用容错模式采集（命令失败不终止流程，必须记录退出码与原始输出）
  - 明确“修改文件”定义为 PR diff 文件集

  **Must NOT do**:
  - 不做任何业务逻辑修复

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 纯基线采集与记录任务
  - **Skills**: [`git-master`]
    - `git-master`: 需要稳定输出命令结果与变更边界

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 3,5,7,8
  - **Blocked By**: None

  **References**:
  - `frontend/package.json` - 前端门禁命令来源
  - `backend/pyproject.toml` - pytest 配置与测试路径

  **Acceptance Criteria**:
  - [ ] 产出 Day0 表格含 5 维：退出码/通过率/失败项/lint 错误/耗时
  - [ ] 前后端每个命令均有 `.txt` 输出与 `.rc` 退出码文件
  - [ ] 证据文件生成：`.sisyphus/evidence/week1-day0-baseline.txt`

- [x] 2. 隔离 Playwright 与 Vitest，清理测试收集污染

  **What to do**:
  - 将 E2E 测试从 Vitest 主收集路径剥离
  - 约束 Vitest 仅运行单测/组件测

  **Must NOT do**:
  - 不新增第三种测试框架

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 3,5
  - **Blocked By**: None

  **References**:
  - `frontend/src/__tests__/login-verification.spec.ts` - 当前 E2E 文件位置
  - `frontend/package.json` - `test` script 现状

  **Acceptance Criteria**:
  - [ ] `npm run test -- --run` 不再因 `@playwright/test` 导入失败
  - [ ] E2E 测试有独立入口命令

- [x] 3. 修复 P0 与 flaky 关键失败模式

  **What to do**:
  - 优先清理 P0 失败用例（按下述 P0 清单，禁止临时改口径）
  - 替换 magic `setTimeout` 等非确定性等待模式

  **Must NOT do**:
  - 不为过测而修改业务行为语义

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 8
  - **Blocked By**: 1,2

  **References**:
  - `frontend/src/__tests__/auth/login.spec.ts`
  - `frontend/src/__tests__/App.spec.ts`
  - `frontend/src/__tests__/views/ChatTerminal.spec.ts`
  - **P0 Test List (MUST PASS)**:
    - `frontend/src/__tests__/App.spec.ts`（全部）
    - `frontend/src/__tests__/views/ChatTerminal.spec.ts`（全部）
    - `frontend/src/__tests__/auth/login.spec.ts`（仅关键用例）:
      - `Auth Store > should login successfully and store token`
      - `LoginView > should redirect to home after successful login`
      - `App Chrome Hiding on Login > should hide header on /login route`
      - `App Chrome Hiding on Login > should hide sidebar on /login route`
      - `App Chrome Hiding on Login > should show header on non-login routes`
      - `App Chrome Hiding on Login > should show sidebar on non-login routes`
    - `backend/tests/test_auth.py`（全部）
    - `backend/tests/test_chat_citation.py`（全部）
    - `backend/tests/test_chat_scoped.py`（全部）
    - `backend/tests/test_workflow_api.py`（全部）
    - `backend/tests/test_knowledge_dimension_mismatch.py`（全部）

  **Acceptance Criteria**:
  - [ ] 前端 P0 集合 100% 通过
  - [ ] 连续 3 次执行无随机失败

- [x] 4. 建立 P1 非阻断失败的 issue 化闭环

  **What to do**:
  - 将所有 P1 失败映射到 issue（owner + deadline）
  - 统一模板：原因、影响、复现命令、清零日期（7天内）

  **Must NOT do**:
  - 不允许“口头待修”

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 8
  - **Blocked By**: 1

  **References**:
  - `frontend/src/__tests__/views/SkillsView.spec.ts`
  - `frontend/src/__tests__/views/SkillEditor.spec.ts`
  - `frontend/src/__tests__/views/WorkflowEditor.spec.ts`

  **Acceptance Criteria**:
  - [ ] 每个失败用例有唯一 issue
  - [ ] 每个 issue 有 owner 与 7 天截止时间

- [x] 5. 实现分层 CI Workflow（critical/full/e2e）

  **What to do**:
  - 构建 GitHub Actions：前端 critical 阻断、full 非阻断、后端 critical 阻断
  - `frontend-critical-tests` 仅运行 Task 3 的 P0 清单（禁止跑全量）
  - `frontend-full-tests` 运行全量但不设 required
  - 路径触发 + 缓存 + 并行作业

  **Must NOT do**:
  - 不把 full/e2e 设为 required（Week1）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 6,8
  - **Blocked By**: 1,2

  **References**:
  - `.github/workflows/` - CI 配置目录
  - `frontend/package.json` - 前端脚本
  - `backend/pyproject.toml` - 后端测试入口

  **Acceptance Criteria**:
  - [ ] PR 触发时至少 4 个 job：frontend-type-check、frontend-build、frontend-critical-tests、backend-critical-tests
  - [ ] `frontend-critical-tests` 明确只覆盖 P0，不包含 P1/Playwright
  - [ ] full/e2e job 独立可观测但不阻断

- [x] 6. D3 启用分支保护与 required checks

  **What to do**:
  - 将 required checks 绑定到 `main`
  - 开启“分支需同步最新 base 才可合并”

  **Must NOT do**:
  - 不允许手动绕过（紧急例外需记录）
  - **紧急回滚预案**：若 CI 配置缺陷导致开发阻塞，可临时关闭保护，但必须：
    - 在 issue 记录原因、关闭时间、预计恢复时间
    - 24 小时内恢复保护并补发审计记录
    - 在 Week1 报告披露该事件

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: 8
  - **Blocked By**: 5

  **Acceptance Criteria**:
  - [ ] 红灯 PR 无法合并
  - [ ] 保护策略生效截图/日志留证

- [x] 7. Lint 债务收敛到 Week1 预算

  **What to do**:
  - 修改文件 lint 0 error 强执行（修改文件定义：`git diff --name-only`）
  - 每次提交前对 `git diff --name-only` 文件集执行定向 lint
  - 历史存量收敛到 <=40

  **Must NOT do**:
  - 不改 lint 规则逃逸

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: 8
  - **Blocked By**: 1

  **References**:
  - `frontend/eslint.config.ts`
  - `frontend/.oxlintrc.json`

  **Acceptance Criteria**:
  - [ ] `git diff --name-only` 文件集 lint error = 0
  - [ ] 仓库历史 lint error <=40

- [ ] 8. 输出 Week1 验收报告与 Week2 承接清单

  **What to do**:
  - 汇总 Day0 vs Day7 指标变化
  - 列出未清 P1 与下周计划
  - 失败判定：若 D7 时 P0 未 100% 通过，明确标记 `Week1 未达标`，并给出根因与补救（延期 1-2 天或有理降级）

  **Must NOT do**:
  - 不模糊描述，必须有数字

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: 3,4,5,6,7

  **Acceptance Criteria**:
  - [ ] 交付 Week1 报告（指标/风险/决策）
  - [ ] 输出 Week2 明确任务列表

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2 | `test(frontend): isolate e2e from vitest collection` | frontend test config/files | vitest run |
| 5 | `ci: add layered quality gate workflows` | .github/workflows/* | workflow dry run |
| 7 | `chore(frontend): reduce lint debt to week1 budget` | frontend src/config | npm run lint |

---

## Success Criteria

### Verification Commands
```bash
# Frontend blocking checks
cd frontend && npm run type-check
cd frontend && npm run build
cd frontend && npx vitest run src/__tests__/auth/login.spec.ts src/__tests__/App.spec.ts src/__tests__/views/ChatTerminal.spec.ts

# Backend blocking checks
cd backend && uv run pytest -q tests/test_auth.py tests/test_chat_citation.py tests/test_chat_scoped.py tests/test_workflow_api.py tests/test_knowledge_dimension_mismatch.py

# Debt checks
cd frontend && npm run lint
```

> 注：Day0 基线采集使用容错执行并记录退出码；DoD 验收使用严格执行（失败即失败）。

### Final Checklist
- [ ] D3 起 main 分支 required checks 生效
- [ ] P0/critical 全绿
- [ ] P1 失败全部 issue 化并 7 天清零承诺
- [ ] Lint 预算达标（历史<=40，改动=0）
- [ ] Day0/Day7 基线报告可复核
