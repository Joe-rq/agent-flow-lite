# 2026-03-28 Harness Lab Integration

## 场景

为一个已经存在明确业务架构和开发规范的全栈项目接入 Harness Lab。

## 关联材料

- REQ：`requirements/completed/REQ-2026-001-harness-lab-integration.md`
- Design：`docs/plans/REQ-2026-001-design.md`
- Code Review：`requirements/reports/REQ-2026-001-code-review.md`
- QA：`requirements/reports/REQ-2026-001-qa.md`

## 问题 / 模式

- 现有项目通常已经有 `AGENTS.md`、`CLAUDE.md`、README 和业务文档
- 直接照抄治理模板容易覆盖已有事实源，形成第二套入口
- 治理层如果没有根级真实命令入口，会停留在“目录接入”而不是“流程接入”

## 解决方案

1. 保留业务运行时结构，只新增治理目录与脚本入口。
2. 把项目现有架构、测试、环境事实沉淀到 `context/tech/`，避免只写模板空话。
3. 为根目录补 `package.json`，把现有前后端真实命令挂成统一的 `lint / build / test / verify`。
4. 用首个真实 REQ 记录接入动作，而不是只复制模板文件。

## 复用建议

- 给已有项目接入治理层时，优先做“统一入口 + 事实沉淀 + 首个真实 REQ”三件事。
- 不要强行迁移所有历史文档；先让新变更进入治理流程，再逐步收敛旧资产。
- 如果项目已经有严格的业务规范，治理层应引用它们，而不是与它们竞争。