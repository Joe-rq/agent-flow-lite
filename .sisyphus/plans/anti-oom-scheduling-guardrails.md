# 防止并行执行内存爆炸的调度护栏计划

## TL;DR

> **Quick Summary**: 这不是机器性能问题，而是调度规则缺失问题。此计划通过“并发预算 + 任务互斥 + 禁止 watch 误用 + 内存熔断”四层护栏，避免后续计划执行再出现 OOM。
>
> **Deliverables**:
> - `AGENTS.md` 新增“资源预算与调度护栏”章节
> - `.sisyphus` 计划模板/执行规范新增“资源约束必填项”
> - `/start-work` 执行规范加入并发与熔断规则
> - 一份可复核的验证记录（命令输出 + 阈值触发演练）
>
> **Estimated Effort**: Short (0.5-1 day)
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Task 1 -> Task 3 -> Task 5

---

## Context

### Original Request
用户反馈：执行 `.sisyphus/plans/week1-quality-baseline.md` 时，因并行执行导致内存爆掉；要求后续计划制定时系统性避免此类问题，并优化调度规则，规则需覆盖两处（仓库级与 .sisyphus 级）。

### Interview Summary
**Key Discussions**:
- 事故发生于并行执行场景，不是单任务偶发。
- 截图显示多条 `node (vitest N)` 高内存进程并发驻留，触发 swap 压力。
- 目标不是临时止血，而是“以后每次计划都能规避”。
- 规则落点确认：`AGENTS.md` + `.sisyphus` 双处同步。

**Research Findings**:
- `frontend/package.json` 的 `test` 脚本为 `vitest`（易进入驻留/观察语义）。
- `frontend/vitest.config.ts` 未设置并发上限（无 maxForks / 等价限制）。
- `.sisyphus/plans/week1-quality-baseline.md` 存在 wave 并行执行策略，易与高内存测试任务叠加。
- `.sisyphus/scripts/start-work.sh` 存在测试调用样式不安全示例，可诱发长驻进程。

### Metis Review
**Identified Gaps (addressed)**:
- 补齐“具体数值”而非原则口号（并发上限、熔断阈值、恢复条件）。
- 补齐“范围边界”，防止一次计划扩展成通用调度器重写。
- 补齐“可执行验收”，每条规则都有可跑命令验证。
- 补齐“边界场景”，覆盖僵尸进程、嵌套并发、外部内存占用。

---

## Work Objectives

### Core Objective
建立一套默认保守且可验证的执行护栏，让未来计划在并行执行时保持可控内存占用，避免 OOM 与系统抖动。

### Concrete Deliverables
- `AGENTS.md`：新增资源预算、任务分级、互斥规则、熔断规则、恢复流程。
- `.sisyphus` 计划规范：新增“资源约束”与“禁止 watch 误用”强制项。
- `/start-work` 执行规范：新增波次并发上限和内存压力处理流程。
- `.sisyphus/evidence/anti-oom-guardrails-verification.md`：验证证据。

### Definition of Done
- [ ] 任意新计划包含“并发预算、互斥组、熔断阈值、恢复条件”四项。
- [ ] 测试类任务默认使用一次性运行语义（非 watch）。
- [ ] 本地 16GB 机器上，执行并行波次时无 swap 持续上升。
- [ ] 熔断演练可触发且能自动进入降级执行。

### Must Have
- 规则可被执行者直接照做，不依赖口头解释。
- 验收命令能自动判定 pass/fail。

### Must NOT Have (Guardrails)
- 不做“全平台智能调度器”重构（本次只做防 OOM 护栏）。
- 不把规则写成抽象口号（必须有数值和命令）。
- 不允许用“机器不够强”替代调度治理。

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> 所有验收由执行代理通过命令与日志完成；不依赖人工目测判断。

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: None（本次以规范/流程验证为主）
- **Framework**: Bash command assertions + file checks

### Agent-Executed QA Scenarios (GLOBAL)

Scenario: 规则完整性扫描
  Tool: Bash
  Preconditions: 规范文件已更新
  Steps:
    1. 扫描 `AGENTS.md` 是否包含 `max_parallel`、`memory-heavy mutex`、`circuit breaker`、`recovery` 关键段
    2. 扫描 `.sisyphus` 规范是否包含 `no-watch` 与 `resource budget required`
    3. 输出命中结果到 `.sisyphus/evidence/anti-oom-rule-scan.txt`
  Expected Result: 必需关键段全部命中
  Failure Indicators: 任一关键段缺失
  Evidence: `.sisyphus/evidence/anti-oom-rule-scan.txt`

Scenario: 熔断策略演练（负向场景）
  Tool: Bash
  Preconditions: 已定义熔断阈值与降级动作
  Steps:
    1. 构造模拟高压条件（读取系统内存/交换区占用）
    2. 执行规则检查脚本，断言命中“停止新并发任务 + 降级串行”路径
    3. 记录动作与恢复条件判断
  Expected Result: 熔断触发后不再启动新并发任务
  Failure Indicators: 高压状态下仍继续并发派发
  Evidence: `.sisyphus/evidence/anti-oom-circuit-breaker.txt`

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
- Task 1 定义统一资源预算基线
- Task 2 定义任务分级与互斥矩阵

Wave 2 (After Wave 1):
- Task 3 更新 `AGENTS.md` 护栏章节
- Task 4 更新 `.sisyphus` 计划/执行规范
- Task 5 增加 `/start-work` 调度规则与熔断流程
- Task 6 完成验证与证据归档

Critical Path: Task 1 -> Task 3 -> Task 5

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 3,4,5 | 2 |
| 2 | None | 4,5 | 1 |
| 3 | 1 | 6 | 4 |
| 4 | 1,2 | 6 | 3 |
| 5 | 1,2 | 6 | 3,4 |
| 6 | 3,4,5 | None | None |

---

## TODOs

- [ ] 1. 定义默认资源预算与并发上限（本次基线）

  **What to do**:
  - 明确默认机器画像：16GB RAM 本地开发机
  - 定义并发预算：`max_parallel=2`
  - 定义高内存任务互斥：同一时刻仅 1 个 `memory-heavy` 任务

  **Must NOT do**:
  - 不做动态自适应调优（后续迭代再做）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 3,4,5
  - **Blocked By**: None

  **References**:
  - `.sisyphus/plans/week1-quality-baseline.md` - 并行波次与任务编排现状
  - `frontend/package.json` - 测试命令入口语义
  - `frontend/vitest.config.ts` - 当前无并发上限设置

  **Acceptance Criteria**:
  - [ ] 预算定义文档化：`max_parallel=2`
  - [ ] `memory-heavy` 任务集合有清单（vitest/playwright/build 等）

- [ ] 2. 定义任务分级与互斥矩阵

  **What to do**:
  - 建立任务类别：`memory-heavy` / `cpu-heavy` / `lightweight`
  - 定义互斥规则：`memory-heavy` 互斥，`lightweight` 可并发
  - 定义降级规则：触发熔断后自动切串行

  **Must NOT do**:
  - 不把所有任务一刀切串行（避免过度保守）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 4,5
  - **Blocked By**: None

  **References**:
  - `.sisyphus/plans/week1-quality-baseline.md` - 任务类型样本
  - `.sisyphus/scripts/start-work.sh` - 执行入口参考

  **Acceptance Criteria**:
  - [ ] 互斥矩阵包含“可并发/不可并发/条件并发”三态
  - [ ] 每类至少有 2 个示例任务

- [ ] 3. 在 `AGENTS.md` 增加“资源预算与调度护栏”章节

  **What to do**:
  - 写入强制规则：禁止 watch 语义进入自动执行路径
  - 写入强制规则：测试命令必须一次性退出语义（如 `vitest run`）
  - 写入并发预算、互斥规则、熔断阈值、恢复条件
  - 写入紧急开关：`force_serial=true`

  **Must NOT do**:
  - 不写模糊表达（如“尽量”“建议”）

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 6
  - **Blocked By**: 1

  **References**:
  - `AGENTS.md` - 仓库级统一规范入口
  - `frontend/package.json` - 测试命令规范化依据

  **Acceptance Criteria**:
  - [ ] 存在明确数值：`max_parallel=2`、`mem>85%` 或 `swap>25%` 触发熔断
  - [ ] 存在恢复条件：`mem<70%` 持续 30s 后允许恢复并发
  - [ ] 存在禁止项：自动执行中禁用 watch 模式

- [ ] 4. 在 `.sisyphus` 计划规范加入“资源约束必填项”

  **What to do**:
  - 在计划模板加入必填字段：并发预算、互斥组、熔断、恢复
  - 在执行策略段加入“波次中 memory-heavy 默认串行”
  - 在验收段加入“资源压力证据文件路径”

  **Must NOT do**:
  - 不允许新计划缺失资源约束字段

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 6
  - **Blocked By**: 1,2

  **References**:
  - `.sisyphus/plans/week1-quality-baseline.md` - 现有模板可改进点
  - `.sisyphus/drafts/week1-quality-baseline-memory.md` - 事故上下文

  **Acceptance Criteria**:
  - [ ] 新模板含 `Resource Budget` 小节
  - [ ] 新模板含 `Circuit Breaker` 小节
  - [ ] 缺字段时校验失败（规则可被脚本扫描）

- [ ] 5. 优化 `/start-work` 调度规则（执行规范层）

  **What to do**:
  - 定义 dispatch 前置检查：当前内存压力、正在运行任务类别
  - 定义派发逻辑：优先 lightweight，并限制 memory-heavy 并发为 1
  - 定义熔断动作：停止新任务、保留当前任务、转串行队列
  - 定义恢复动作：满足恢复阈值后按 FIFO 继续

  **Must NOT do**:
  - 不直接 kill 全部任务（除非进入 emergency 模式）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 6
  - **Blocked By**: 1,2

  **References**:
  - `.sisyphus/scripts/start-work.sh` - 执行入口与可改造点
  - `.sisyphus/plans/week1-quality-baseline.md` - 现有并行波次策略

  **Acceptance Criteria**:
  - [ ] 能区分任务类别并应用互斥
  - [ ] 熔断触发时新任务进入等待队列
  - [ ] 恢复后按顺序继续，且有日志证据

- [ ] 6. 端到端验证并产出证据

  **What to do**:
  - 跑规则扫描与演练命令
  - 记录触发与恢复路径日志
  - 输出一页结论：是否达到“并发不再爆内存”

  **Must NOT do**:
  - 不做“看起来没问题”的口头验收

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: 3,4,5

  **References**:
  - `AGENTS.md`
  - `.sisyphus/` 相关计划与规范文件

  **Acceptance Criteria**:
  - [ ] 证据文件输出：`.sisyphus/evidence/anti-oom-guardrails-verification.md`
  - [ ] 至少包含 1 个正向场景 + 1 个负向场景
  - [ ] 有明确 pass/fail 结论

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 3 | `docs(agents): add anti-oom scheduling guardrails` | AGENTS.md | rule scan |
| 4,5 | `chore(sisyphus): enforce resource budget and circuit breaker` | .sisyphus/* | scenario run |

---

## Success Criteria

### Verification Commands
```bash
# 1) 规则完整性
grep -n "max_parallel\|circuit breaker\|force_serial\|watch" AGENTS.md

# 2) 计划规范完整性
grep -R -n "Resource Budget\|Circuit Breaker\|memory-heavy" .sisyphus

# 3) 证据存在性
test -f .sisyphus/evidence/anti-oom-guardrails-verification.md
```

### Final Checklist
- [ ] 两处规范（AGENTS + .sisyphus）均包含同一套护栏原则
- [ ] 新计划模板强制资源约束字段
- [ ] 并发执行在 16GB 基线下可控，无持续 swap 扩张
- [ ] 熔断与恢复流程可复现、可审计
