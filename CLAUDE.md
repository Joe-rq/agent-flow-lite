# CLAUDE.md

<!-- HARNESS-LAB:BEGIN -->
## Harness Lab 治理入口

本仓库采用 Harness Lab 作为研发治理层。**每次会话必须先按治理入口恢复上下文，再执行具体任务。**

### 会话启动顺序

每次会话开始时，**必须**按下面顺序读取：
1. `AGENTS.md`
2. `requirements/INDEX.md`
3. `.claude/progress.txt`
4. 与当前任务相关的 `context/*/README.md`
5. 当前 REQ、设计稿、已有报告和必要代码

**禁止跳过启动顺序直接进入实现。**

### 开工前检查

开始实现前，**必须**确认：
- 当前活跃 REQ 是什么
- 该 REQ 的设计稿是否存在
- 目标项目是否已经绑定真实 `lint / test / build / verify` 命令
- 本次工作需要落哪些报告

如果项目还没绑定真实命令，先补命令或明确记录缺口，不要假装已经验证。

### 默认工作方式

- **理解任务**：从 REQ 和设计稿理解范围、非目标和验收标准，只加载必要的 context
- **实现任务**：遵循 `plan -> build -> verify -> fix -> record` 闭环，及时更新 `.claude/progress.txt`
- **验证任务**：review / QA / ship 的结论必须落到 `requirements/reports/`
- **完成任务**：更新 REQ 状态和 `.claude/progress.txt`，有复用价值的结论写入 `context/experience/`

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
<!-- HARNESS-LAB:END -->

---

## 项目约束（补充规则）

以下规则在治理框架内执行，作为项目特定的补充约束。

### 行为约束

1. **修 bug 优先于一切。** 用户报了 bug，在 bug 确认修复前不做任何其他事（包括写文档、重构、优化、添加注释）。
2. **改代码前先读代码。** 不要基于猜测修改文件。先 Read 相关文件，理解现有逻辑后再提出方案。
3. **每次改动都要验证。** 后端改动后运行 `cd backend && uv run pytest`；前端改动后运行 `cd frontend && npm run build`（含 vue-tsc + vite 构建）。验证不通过不算完成。
4. **单任务原则。** 每轮只做一件事，做完确认后再接下一件。不要在一轮里同时改 auth、chat、workflow 等不相关模块。
5. **大改动先列清单。** 涉及 3 个以上文件的改动，先列出要改哪些文件、每个文件改什么，用户确认后再动手。

### 代码质量

6. **TypeScript 文件改完必须通过类型检查。** 编辑 `.ts` 或 `.vue` 文件后，确保 `npm run build` 通过。注意：`npm run build` 使用 `vue-tsc --build` 而非 `tsc --noEmit`，vue-tsc 对 `.vue` 模板中的类型检查更严格。
7. **Python 文件改完必须通过语法检查。** 编辑 `.py` 文件后，确保 `python -m py_compile <file>` 通过。
8. **不要做没被要求的事。** 不要主动添加注释、文档、类型标注、重构、优化。只做用户明确要求的事。
9. **新功能先写测试。** 添加新功能时，先写一个失败测试来定义预期行为，再实现功能让测试通过。

### 禁止事项

10. **不要在修 bug 时写文档或优化计划。** 这是最常见的跑偏模式。
11. **不要一次改太多文件。** 除非用户明确要求，否则每次改动控制在 1-3 个文件内。
12. **不要吞掉错误。** 遇到测试失败或编译错误时，报告给用户而不是绕过。
13. **捕获第三方异常前必须用真实环境验证异常类型。** 不要凭类名猜测——ChromaDB 维度不匹配抛的是 `InvalidArgumentError` 而非 `InvalidDimensionException`。写 `except` 前先用真实调用确认 `type(e).__name__`。
14. **正则匹配第三方错误消息前必须拿真实消息验证。** 不要凭文档或猜测写 pattern。先触发真实错误，拿到实际消息字符串，再写正则。
15. **只改数据不改代码不算修 bug。** 重建数据（如 ChromaDB 重索引）能临时恢复功能，但如果根因在代码层（异常类型错误、缺少防御），必须同时修代码。数据修复 ≠ 代码修复。

### CI 验证规则

16. **推送后必须验证 CI。** 代码推送到远程后，用以下命令检查 Quality Gate 状态：
    ```bash
    gh run list --workflow="Quality Gate" --limit 3
    gh run view <run-id> --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
    ```
17. **CI 验收标准。** Quality Gate 通过的条件是 Critical Layer 4/4 绿色：
    - `frontend-type-check`: success（vue-tsc --build）
    - `frontend-build`: success（vite build）
    - `frontend-critical-tests`: success（需 `--isolate` 标志）
    - `backend-critical-tests`: success
18. **非阻塞 job 也要关注。** E2E Tests 和 Frontend/Backend Full Tests 是 informational，不阻塞合并，但失败时应记录原因并评估是否需要修复。
19. **CI 失败时不继续下一个任务。** 先定位失败 job 的日志，分析根因，修复后再继续。

---

## Development Commands

### Frontend (`frontend/`)

```bash
cd frontend
npm install                    # Install dependencies
npm run dev                    # Dev server (http://localhost:5173, proxies /api -> localhost:8000)
npm run build                  # Type check (vue-tsc) + production build (vite)
npm run test                   # Run all tests (vitest)
npm run test -- --run src/__tests__/views/ChatTerminal.spec.ts  # Run single test file
npm run test -- --run --isolate # Run all tests with process isolation (CI mode)
npm run lint                   # oxlint + eslint with auto-fix
npm run format                 # Prettier
```

**Important**: `npm run build` uses `vue-tsc --build` which is stricter than `npx tsc --noEmit` for `.vue` files. Always use `npm run build` as the final verification, not `tsc --noEmit` alone.

### Backend (`backend/`)

```bash
cd backend
uv venv                        # Create virtual environment (first time)
uv sync --group dev            # Install all dependencies including test deps
uv run uvicorn main:app --reload  # Dev server (http://localhost:8000)
uv run pytest                  # Run all tests
uv run pytest tests/test_auth.py  # Run single test file
uv run pytest -k "test_login"  # Run tests matching pattern
```

---

## Project Overview

**Agent Flow Lite** — Full-stack AI agent orchestration platform with visual workflow editing, RAG knowledge retrieval, SSE streaming chat, skill system, and user management.

**Tech Stack:**
- **Backend**: FastAPI + Python 3.11+ + LlamaIndex + ChromaDB + SQLAlchemy (async SQLite)
- **Frontend**: Vue 3 + Vite + TypeScript + Vue Flow + Pinia + Vue Router
- **AI**: DeepSeek API (LLM) + SiliconFlow API (embeddings, BGE-M3)

---

## Architecture

### Backend (`backend/`)

Three-layer structure under `app/`:

- **`app/api/`** — FastAPI route handlers. All routes under `/api/v1/` prefix. Each file corresponds to a feature domain (auth, chat, knowledge, workflow, skill, admin).
- **`app/core/`** — Business logic. Key modules:
  - `workflow_engine.py` + `workflow_nodes.py` + `workflow_context.py` — BFS graph traversal executor with `{{variable}}` interpolation
  - `rag.py` + `chroma_client.py` — RAG pipeline: load → chunk (SentenceSplitter) → embed (SiliconFlow) → store/retrieve (ChromaDB)
  - `skill_loader.py` + `skill_executor.py` — SKILL.md frontmatter parsing, validation, and execution
  - `llm.py` — DeepSeek API client
  - `auth.py` — Token validation with `get_current_user` / `require_admin` FastAPI dependencies
- **`app/models/`** — Pydantic schemas and SQLAlchemy ORM models (user, chat, workflow, document, skill)
- **`data/`** — Runtime file storage (sessions JSON, workflows JSON, skills SKILL.md, ChromaDB, uploads). All file writes use `filelock`.
- **`tests/`** — pytest + pytest-asyncio tests (11 files, ~45 tests)

**SSE streaming** is used across chat, workflow execution, and skill execution. All three emit the same event protocol: `thought`, `token`, `citation`, `done`, `error`. Events formatted via `format_sse_event()` in each API module.

### Frontend (`frontend/src/`)

Follows a **View → Composable → Component** decomposition pattern:

- **`views/`** — Page-level components (one per route). Each view is an orchestrator that wires composables and child components together. All views ≤200 lines, with CSS extracted to co-located `.css` files using `<style scoped src="./ViewName.css">`.
- **`composables/`** — Reusable stateful logic extracted from views, organized by domain:
  - `chat/` — `useChatSession` (session CRUD), `useChatSSE` (SSE streaming), `sseEventHandlers` (event dispatch), `types` (shared interfaces)
  - `workflow/` — `useWorkflowCrud`, `useWorkflowExecution`, `useNodeDragDrop`, `useEditorActions`, `useNodeConfig`
  - `knowledge/` — `useKnowledgeApi`
  - `skills/` — `useSkillRunner`, `useSkillForm`
  - Root: `useSSEStream` (shared fetch+SSE pattern), `useSkillAutocomplete`, `useUserAdmin`
- **`components/`** — UI components organized by domain (`chat/`, `workflow/`, `knowledge/`, `skills/`, `config/`, `nodes/`, `ui/`). Each component has a co-located `.css` file.
- **`stores/auth.ts`** — Pinia store for auth state (token, user, isAuthenticated, isAdmin) with localStorage persistence.
- **`router/index.ts`** — Vue Router with `beforeEach` auth guard. Routes use `meta.public` and `meta.requiresAdmin`.
- **`utils/`** — `axios.ts` (interceptor with 401 redirect), `sse-parser.ts` (SSE stream parser), `fetch-auth.ts`, `format.ts`, `constants.ts`.

### Key Cross-Cutting Patterns

1. **SSE protocol** — Backend streams events via `StreamingResponse`; frontend parses via `createSSEParser()` from `utils/sse-parser.ts`. The `useSSEStream` composable provides a reusable `fetchSSE()` wrapper.

2. **File-based storage with FileLock** — Workflows (`data/workflows.json`), sessions (`data/sessions/{id}.json`), and skills (`data/skills/{name}/SKILL.md`) all use `filelock` for concurrent write safety.

3. **Skill invocation** — Skills are invoked in chat via `@skill-name content` syntax. The chat API parses this, calls `skill_executor`, which loads SKILL.md, resolves `{{variable}}` placeholders, and streams LLM output.

4. **Workflow execution** — BFS traversal of node graph. Conditional nodes branch via `sourceHandle` (true/false). `ExecutionContext` provides `{{step_id.output}}` variable resolution between nodes.

### Frontend Testing Caveats

- Tests in `__tests__/` use `@vue/test-utils` with jsdom environment.
- **ChatTerminal tests access `wrapper.vm.$.setupState.*`** to directly call composable functions. This means all composable return values must be destructured at the top level of `<script setup>` — wrapping them in a local object will break tests.
- CI critical tests require the `--isolate` flag for process isolation.

---

## Configuration

### Backend Environment Variables (`backend/.env`)

Copy from `.env.example`. Required keys:
- `DEEPSEEK_API_KEY` / `DEEPSEEK_API_BASE` / `DEEPSEEK_MODEL` — LLM
- `SILICONFLOW_API_KEY` / `SILICONFLOW_API_BASE` / `EMBEDDING_MODEL` — Embeddings
- `ADMIN_EMAIL` — Auto-assigns admin role to this email on login
- `CORS_ORIGINS` — Default `http://localhost:5173`

### Frontend

- Vite dev server proxies `/api` → `http://localhost:8000`
- `@/` alias maps to `src/`
- Node version: `^20.19.0 || >=22.12.0`
