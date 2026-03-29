# REQ-2026-001: Harness Lab integration

## 状态
- 当前状态：completed
- 当前阶段：qa

## 背景
`agent-flow-lite` 已经有清晰的前后端架构和项目约束，但缺少统一的治理协议来串起需求、设计、评审、QA、进度交接和文档同步。
为了让后续维护者和 agent 不再依赖口头上下文，需要把 Harness Lab 作为研发治理层引入仓库。

## 目标
- 新增 REQ 生命周期、context、skills 和报告目录
- 为仓库补一个统一的根级治理入口和命令入口
- 保留项目现有前后端结构、测试链路和质量门

## 非目标
- 不改写业务运行时架构
- 不迁移全部历史文档到新治理目录
- 不在本轮改变现有 CI 工作流定义

## 范围
- 涉及目录 / 模块：
  - `context/`
  - `requirements/`
  - `skills/`
  - `docs/plans/`
  - `scripts/docs-verify.mjs`
  - `scripts/check-governance.mjs`
  - `scripts/req-cli.mjs`
  - `package.json`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `docs/README.md`
- 影响接口 / 页面 / 脚本：
  - `npm run lint`
  - `npm run build`
  - `npm run test`
  - `npm run verify`
  - `npm run docs:impact`
  - `npm run docs:verify`
  - `npm run check:governance`
  - `npm run req:*`

### 约束（Scope Control，可选）
> 本次只引入治理层，不顺手改业务代码。

**允许（CAN）**：
- 新增治理目录、模板、技能导航和根级治理脚本
- 更新入口文档以反映新的会话启动顺序和命令入口
- 复用现有前后端真实命令作为根级脚本的底座

**禁止（CANNOT）**：
- 修改 `frontend/`、`backend/` 运行时业务逻辑
- 重构现有工作流、RAG、Chat 或 Auth 代码
- 更改已有 CI 工作流的业务验收语义

**边界条件**：
- 治理层必须包裹现有项目，而不是替换现有架构
- `verify` 必须调用真实项目命令，不能写成假脚本
- 新会话的默认读取顺序必须落到仓库文档中

## 验收标准
- [x] 仓库新增 `context/`、`requirements/`、`skills/` 和 `docs/plans/` 治理目录
- [x] 根级 `package.json` 提供真实 `lint / build / test / verify` 以及 `docs:* / check:governance / req:*` 入口
- [x] `AGENTS.md`、`CLAUDE.md`、`README.md` 和 `docs/README.md` 说明新的治理入口和读取顺序
- [x] `context/tech/` 文档沉淀了本项目真实的架构、测试、环境和部署事实
- [x] 真实执行 `npm run docs:impact`、`npm run docs:verify`、`npm run check:governance` 和 `npm run verify`

## 设计与实现链接
- 设计稿：`docs/plans/REQ-2026-001-design.md`
- 相关规范：`package.json`、`scripts/check-governance.mjs`

## 报告链接
- Code Review：`requirements/reports/REQ-2026-001-code-review.md`
- QA：`requirements/reports/REQ-2026-001-qa.md`
- Ship：`requirements/reports/REQ-2026-001-ship.md`（本次不适用；治理接入不单独发布）

## 验证计划
- 计划执行的命令：
  - `npm run docs:impact`
  - `npm run docs:verify`
  - `npm run check:governance`
  - `npm run verify`
- 需要的环境：
  - Node.js
  - Python 3.11+
  - uv
  - frontend 依赖与 backend `.venv`
- 需要的人工验证：
  - 核对会话启动顺序和治理入口是否一致
  - 核对 root scripts 是否映射到项目真实命令

## 阻塞 / 搁置说明（可选）
- 原因：无
- 恢复条件：无
- 下一步：无

## 风险与回滚
- 风险：
  - 如果治理入口与原有项目规范不一致，会引入第二套事实源
  - 如果 root scripts 不调用真实命令，会把治理层变成假入口
- 回滚方式：
  - 回退新增治理目录、根级 `package.json` 和相关入口文档

## 关键决策
- 2026-03-28：Harness Lab 只作为治理层引入，不替换业务架构
- 2026-03-28：根级 `verify` 复用现有前后端关键检查，而不是新造一套业务验证
- 2026-03-28：历史设计与测试文档保留原目录，后续新变更通过 `requirements/` 与 `docs/plans/` 接管

<!-- Source file: REQ-2026-001-harness-lab-integration.md -->