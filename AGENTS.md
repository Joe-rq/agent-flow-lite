# AGENTS.md

<!-- HARNESS-LAB:BEGIN -->
## Harness Lab 治理层

本仓库已接入 Harness Lab 作为研发治理层，但它不会替换现有业务结构。

### 默认读取顺序

每次会话开始时，默认按下面顺序读取：
1. `AGENTS.md`
2. `requirements/INDEX.md`
3. `.claude/progress.txt`
4. 与当前任务相关的 `context/*/README.md`
5. 当前 REQ、设计稿、已有报告和必要代码

不要默认读取整个仓库。

### 治理命令

```bash
npm run docs:impact      # 文档影响分析
npm run docs:verify      # 文档一致性验证
npm run check:governance # 治理状态检查
npm run req:create       # 创建新 REQ
npm run req:start        # 开始 REQ
npm run req:complete     # 完成 REQ
npm run verify           # 运行质量门
```

后面的项目约束和实现细节仍然有效，治理层只是在它们外面补一层统一入口。
<!-- HARNESS-LAB:END -->

---

## Repository Overview

- **frontend/**: Vue 3 + Vite + TypeScript (views, components, composables)
- **backend/**: FastAPI + Pydantic + Python 3.11+ (RAG, chat, workflow APIs)
- **backend/data/**: Runtime state - do not commit

## Environment Requirements

- **Node**: ^20.19.0 or >=22.12.0
- **Python**: >=3.11
- **Backend uses `uv`** (not pip) for dependency management

## Quick Commands

| Layer | Command | Description |
|-------|---------|-------------|
| Frontend | `cd frontend && npm run dev` | Dev server (port 5173) |
| Frontend | `cd frontend && npm run build` | Type-check + build |
| Frontend | `cd frontend && npm run test` | Run tests |
| Backend | `cd backend && uv run uvicorn main:app --reload` | Dev server (port 8000) |
| Backend | `cd backend && uv run pytest -q` | Run tests |

## Key Patterns

- **SSE protocol**: Backend streams `thought/token/citation/done/error` events; frontend parses via `createSSEParser()`
- **File-based storage**: Workflows, sessions, skills use `filelock` for concurrent safety
- **Skill invocation**: Chat via `@skill-name content` syntax
- **Workflow execution**: BFS graph traversal with `{{step_id.output}}` variable interpolation

## Critical Notes

- **Auth bootstrap order**: `pinia → setupAxiosInterceptors → authStore.init → router → mount`
- **Do not destructure `useRoute()`**: It's non-reactive
- **CI critical tests**: Require `--isolate` flag for process isolation

---

*详细开发规范见 `CLAUDE.md`，技术架构见 `context/tech/`，业务背景见 `context/business/`。*
