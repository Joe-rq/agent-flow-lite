# Testing Strategy

## 根级推荐入口

- `npm run lint`
- `npm run build`
- `npm run test`
- `npm run verify`

## Frontend

- 类型检查：`npm run frontend:type-check`
- 构建：`npm run frontend:build`
- Lint：`npm run frontend:lint`
- 关键测试：`npm run frontend:test:critical`

说明：
- 关键测试复用现有 Vitest 关键用例，并带 `--isolate`
- 前端最终验证仍以 `frontend/package.json` 中的真实脚本为准

## Backend

- 全量测试：`npm run backend:test`
- 关键测试：`npm run backend:test:critical`

说明：
- 后端使用 `uv run pytest`
- 关键测试复用当前 Quality Gate 的 P0 测试集

## Governance

- `npm run docs:impact`：查看本次改动触发了哪些治理文档义务
- `npm run docs:verify`：验证核心文档链接、命令引用和 diff-aware 同步关系
- `npm run check:governance`：检查治理结构、索引、进度和文档一致性