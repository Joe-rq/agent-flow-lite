# Contributing

Thanks for improving Agent Flow Lite.

## Scope

本仓库已经接入 Harness Lab 作为治理层，但业务实现仍然以现有 `frontend/`、`backend/`、`docs/` 和 `scripts/` 为准。
提交改动时，优先保持：

- 业务架构与运行命令的真实性
- REQ / design / review / QA 的证据链
- 入口文档与治理索引的一致性

## Before Opening a PR

提交前请尽量说明：

1. 你解决的是哪个 REQ，或为什么这次改动不需要新 REQ
2. 改动影响哪些入口或治理文件
3. 是否需要更新 `context/`、`docs/plans/` 或 `requirements/reports/`
4. 是否影响 root scripts 或质量门

## Files To Update Together

如果改动影响这些区域，通常要联动更新：

- 接入说明：
  `README.md`
- 会话入口：
  `AGENTS.md`
  `CLAUDE.md`
- 需求流程：
  `requirements/INDEX.md`
  `requirements/REQ_TEMPLATE.md`
- 业务 / 技术上下文：
  `context/*/README.md`
  `context/tech/*.md`
- 执行协议：
  `skills/**`

`npm run docs:impact` 会先列出当前 git status 触发的治理文档义务，`npm run docs:verify` 再对这些联动关系做最小自动检查，`npm run check:governance` 负责校验治理结构和索引一致性。
如果你新增或修改了治理脚本、入口文档或同步约束，请同时更新 `scripts/docs-sync-rules.json`，不要只改脚本或只改文档。

## Pull Request Checklist

- [ ] 改动仍然符合“治理层包裹业务项目”的定位
- [ ] 没有把业务项目事实写成模板空话
- [ ] 相关入口文档已同步
- [ ] 相关 REQ / 设计 / 报告已同步
- [ ] 已运行 `npm run docs:impact`
- [ ] 已运行 `npm run docs:verify`
- [ ] 已运行 `npm run check:governance`
- [ ] 涉及代码改动时，已运行 `npm run verify`