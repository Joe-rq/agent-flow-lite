# Requirements Index

> 本文件是仓库内需求状态的单一事实源。
> 任何 REQ 的创建、切换、完成、搁置，都要同步更新这里。

## 读取顺序

1. 查看当前活跃 REQ
2. 查看 `.claude/progress.txt`
3. 打开对应的 `requirements/in-progress/` 或 `requirements/completed/` 文件
4. 按需打开 `docs/plans/` 和 `requirements/reports/` 中的关联文档

## 当前活跃 REQ

- 无

## 最近完成 REQ

- `REQ-2026-003-p1-implementation.md`（P1 任务：ChromaDB警告、SSE重连、可观测性仪表盘、SDK生成）
- `REQ-2026-002-toast-confirm-alert-confirm.md`（Toast/Confirm 通知系统替换 alert/confirm）
- `REQ-2026-001-harness-lab-integration.md`（Harness Lab integration）

## 当前搁置 REQ

- 无

## 目录约定

- `requirements/REQ_TEMPLATE.md`
  新建 REQ 时复制此模板，或使用 `npm run req:create`
- `requirements/in-progress/`
  正在推进的需求。
- `requirements/completed/`
  已完成需求。
- `requirements/reports/`
  `code-review`、`qa`、`ship` 等执行报告。

## 生命周期约定

### 新建
- 在 `requirements/in-progress/` 创建 `REQ-YYYY-NNN-*.md`
- 中大改动在 `docs/plans/` 创建对应 `REQ-YYYY-NNN-design.md`
- 小改动可把设计摘要直接写在 REQ 文件中
- 如果任务需要明确 agent / 协作者的行为边界，可在 REQ 的"范围"下补 `Scope Control`

### 推进
- 设计、实现、评审、验证都围绕同一个 REQ 编号展开
- 相关报告落到 `requirements/reports/`

### 完成
- 将 REQ 文件移入 `requirements/completed/`
- 更新"当前活跃 REQ"和"最近完成 REQ"
- 如有复用价值，补 `context/experience/` 经验文档

### 搁置
- 在 REQ 文件中写明原因、恢复条件和下一步
- `blocked / suspended` 的 REQ 仍保留在 `requirements/in-progress/`
- 在本索引里标明搁置状态

## 报告约定

建议至少有这些报告：
- `REQ-YYYY-NNN-code-review.md`
- `REQ-YYYY-NNN-qa.md`
- `REQ-YYYY-NNN-ship.md`

如果某类报告不适用，也要在 REQ 中明确说明原因，而不是默认省略。
