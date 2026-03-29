# REQ-2026-001 Design

## Background

`agent-flow-lite` 已经具备清晰的前后端结构和开发规范，但这些规则主要分散在 `AGENTS.md`、`CLAUDE.md`、`README.md` 和零散文档中。
仓库缺少一层统一的治理协议来承接：

- 当前活跃需求是什么
- 设计、评审、QA 的固定落盘位置
- 新会话如何快速恢复上下文
- agent 修改后如何判断治理文档是否同步

因此本次引入 Harness Lab，但只作为治理层套在现有项目外部，不改动业务运行时结构。

## Goal

- 为项目增加 REQ 生命周期、context、reports 和 skills 导航目录
- 为根目录补一个统一的治理入口和命令入口
- 保留现有前后端架构、质量门和业务命令

## Scope

### In scope

- 新增 `context/`、`requirements/`、`skills/`、`docs/plans/`
- 新增根级 `package.json`，挂接真实 `lint / build / test / verify`
- 引入 `docs:impact`、`docs:verify`、`check:governance`、`req:*`
- 把项目现有事实沉淀到 `context/tech/*.md`
- 更新 `AGENTS.md`、`CLAUDE.md`、`README.md`、`docs/README.md`

### Out of scope

- 调整前后端业务架构
- 改写现有 CI 工作流
- 迁移所有历史设计和测试文档到新目录
- 为旧需求补齐完整 REQ 历史

## Product Review

### User Value

- 解决的问题：让人和 agent 能按同一套索引、状态和交付物接手项目
- 目标用户：维护 `agent-flow-lite` 的开发者和协作 agent
- 预期收益：减少需求推进依赖口头上下文，降低治理入口漂移

### Recommendation

- Proceed

## Engineering Review

### Architecture Impact

- 影响模块：
  - 根级治理目录与脚本入口
  - `AGENTS.md` / `CLAUDE.md` / `README.md` / `docs/README.md`
  - 根级 `package.json`
- 依赖方向：
  - 治理层读取现有项目事实，但不侵入前后端运行时代码
  - `verify` 继续复用项目已有前后端关键检查
- 需要新增或修改的边界：
  - 新会话默认先读治理索引，再深入代码
  - 根级 `npm run verify` 负责统一调度关键检查

### Verification

- 自动验证：
  - `npm run docs:impact`
  - `npm run docs:verify`
  - `npm run check:governance`
  - `npm run verify`
- 人工验证：
  - 检查 AGENTS / CLAUDE / README 是否指向同一套启动顺序
  - 检查 context 文档是否反映真实项目结构与命令
- 回滚：
  - 回退新增治理目录、根级脚本和入口文档变更