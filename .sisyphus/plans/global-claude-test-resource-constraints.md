# 全局 CLAUDE.md 测试资源约束更新计划

## TL;DR

> **Quick Summary**: 将防 OOM 的测试执行规则沉淀到用户级 `~/.claude/CLAUDE.md`，让所有项目继承同一套硬约束，避免重复踩“无预算并行 + watch 误用”问题。
>
> **Deliverables**:
> - `~/.claude/CLAUDE.md` 新增全局“Test Resource Constraints”章节
> - 明确禁止项（watch 误用、并行重任务叠加、去掉 worker 上限）
> - 明确验证命令（进程计数 + 配置核对）
> - 一份执行证据记录
>
> **Estimated Effort**: Quick (~10-20 min)
> **Parallel Execution**: NO - sequential
> **Critical Path**: Task 1 -> Task 2 -> Task 3

---

## Context

### Original Request
用户要求更新用户层级规则文件（已确认目标：`~/.claude/CLAUDE.md`），让其他项目也不会出现同样的测试并行内存爆炸问题。

### Interview Summary
**Key Discussions**:
- 事故根因：测试并行无预算 + watch 模式进入自动化路径 + worker 无上限。
- 用户目标：跨项目持久化规则，而不是单仓库临时补丁。
- 目标文件明确为：`~/.claude/CLAUDE.md`。

### Metis Review
**Identified Gaps（已纳入）**:
- 先读取现有 `~/.claude/CLAUDE.md`，防止重复章节与冲突覆盖。
- 只做“测试资源约束”最小闭环，避免 scope creep。
- 增加可执行验收命令，杜绝口头“看起来没问题”。

---

## Work Objectives

### Core Objective
建立一套跨项目统一、可执行、可审计的测试资源约束，降低自动化执行 OOM 风险。

### Concrete Deliverables
- `~/.claude/CLAUDE.md` 中的全局测试资源约束章节（新增或无冲突更新）。
- 约束内容包含：Vitest 并发上限、禁止模式、验证命令。
- `.sisyphus/evidence/global-claude-resource-constraints.md` 验证结果。

### Definition of Done
- [ ] `~/.claude/CLAUDE.md` 存在唯一的测试资源约束章节。
- [ ] 章节内包含 one-shot 测试语义与并发限制。
- [ ] 章节内包含禁止模式与进程计数验证命令。
- [ ] 验证证据文件落盘，包含 pass/fail 结论。

### Must Have
- 规则表达为硬约束（MUST / FORBIDDEN），不使用模糊建议语气。
- 命令示例覆盖 macOS/Linux 常见执行环境。

### Must NOT Have (Guardrails)
- 不扩展到代码风格、lint、安全等无关规则。
- 不批量修改各项目仓库文件（本次只改用户级全局规则）。
- 不依赖人工目测作为唯一验收。

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> 所有验收必须由执行代理通过命令输出完成，不能要求人工点击或肉眼判断。

### Test Decision
- **Infrastructure exists**: N/A（文档策略更新任务）
- **Automated tests**: None
- **Primary verification**: Bash assertions + file checks

### Agent-Executed QA Scenarios

Scenario: 全局规则章节存在且唯一
  Tool: Bash
  Preconditions: `~/.claude/CLAUDE.md` 可读
  Steps:
    1. 统计章节标题出现次数（`Test Resource Constraints`）
    2. 断言次数为 1
  Expected Result: 唯一章节，避免重复冲突
  Failure Indicators: 次数为 0 或 >1
  Evidence: `.sisyphus/evidence/global-claude-resource-constraints.md`

Scenario: 关键约束完整性检查
  Tool: Bash
  Preconditions: 同上
  Steps:
    1. grep 检查 `pool: 'forks'`、`maxForks`、`maxConcurrency`、`isolate` 关键字
    2. grep 检查禁止模式：watch in automation / remove maxForks / parallel heavy tasks
    3. grep 检查验证命令：`pgrep -c vitest 2>/dev/null || ps aux | grep "[v]itest" | wc -l`
  Expected Result: 全部命中
  Failure Indicators: 任一关键项缺失
  Evidence: `.sisyphus/evidence/global-claude-resource-constraints.md`

---

## Execution Strategy

### Sequential Flow
1. 读取并分析现有 `~/.claude/CLAUDE.md` 结构。
2. 插入/更新“Test Resource Constraints”章节（保持无重复）。
3. 运行命令验证并生成证据。

---

## TODOs

- [ ] 1. 盘点并读取现有全局文件结构

  **What to do**:
  - 检查 `~/.claude/CLAUDE.md` 是否存在。
  - 若存在，定位最适合插入“Test Resource Constraints”的位置。
  - 若不存在，创建文件骨架并保留后续扩展空间。

  **Must NOT do**:
  - 不覆盖现有用户自定义内容。

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: None

  **References**:
  - `~/.claude/CLAUDE.md` - 目标全局规则文件

  **Acceptance Criteria**:
  - [ ] 目标文件存在状态明确（存在/不存在）
  - [ ] 插入位置方案确定（无重复章节）

- [ ] 2. 写入全局测试资源约束（最小闭环）

  **What to do**:
  - 写入 Vitest 资源约束模板（forks / maxForks=2 / maxConcurrency=5 / isolate=false）。
  - 写入禁止项与说明（watch 自动化禁用、并行重任务禁用、去掉 maxForks 禁用）。
  - 写入进程计数验证命令（带 fallback）。

  **Must NOT do**:
  - 不引入与测试资源无关的全局策略。

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 1

  **References**:
  - `AGENTS.md:116` - 已验证可用的约束章节样式
  - `frontend/vitest.config.ts:13` - 当前项目落地参数参考
  - `frontend/package.json:16` - one-shot 测试语义参考

  **Acceptance Criteria**:
  - [ ] 章节中包含 4 个核心参数与其目的
  - [ ] 章节中包含 3 条禁止项
  - [ ] 章节中包含可复制执行的验证命令

- [ ] 3. 执行验证并产出证据文件

  **What to do**:
  - 运行章节唯一性检查。
  - 运行关键字完整性检查。
  - 将命令输出与结论写入 `.sisyphus/evidence/global-claude-resource-constraints.md`。

  **Must NOT do**:
  - 不仅凭“文件看起来有内容”判定通过。

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 2

  **References**:
  - `~/.claude/CLAUDE.md`
  - `.sisyphus/evidence/`

  **Acceptance Criteria**:
  - [ ] 证据文件存在且含命令输出
  - [ ] 证据文件含明确 pass/fail 结论

---

## Success Criteria

### Verification Commands
```bash
# 1) 唯一章节检查
grep -c "^## Test Resource Constraints" ~/.claude/CLAUDE.md

# 2) 关键项检查
grep -n "maxForks\|maxConcurrency\|isolate\|watch mode\|pgrep -c vitest" ~/.claude/CLAUDE.md

# 3) 证据检查
test -f .sisyphus/evidence/global-claude-resource-constraints.md
```

### Final Checklist
- [ ] 全局规则文件更新完成且无重复章节
- [ ] 核心约束与禁止项齐全
- [ ] 验证命令可执行并有证据产出
