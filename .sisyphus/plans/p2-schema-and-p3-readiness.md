# Phase 2 Delivery + Phase 3 Exit Readiness Plan (Agent Flow Lite)

## TL;DR

> **目标**：按 `docs/long-term-optimization-plan.md` 的依赖顺序推进 Phase 2（先 2.1 Schema 统一），同时把 Phase 3 → Phase 4 出口闸门（覆盖率 >=70% + Alembic）做成可机器验收。
>
> **关键交付物**：
> - Workflow Schema：后端 Pydantic discriminated union + 前端 TS union（向后兼容现有 `workflows.json`）。
> - Hybrid Retrieval：Chroma cosine + SQLite FTS5 合并 + 可选 Rerank（可降级）。
> - Workflow Import/Export：JSON schema 校验 + 原子导入。
> - Publish MVP：默认走 iframe embed（更轻、更安全），可后续扩展 OpenAI compat。
> - Phase 3→4 Gate：`pytest --cov-fail-under=70` 通过 + Alembic 集成完成。
>
> **Estimated Effort**：Large
> **Parallel Execution**：YES（2 waves + integration wave）
> **Critical Path**：2.1 Schema → 2.5 Import/Export → Template flows → Publish MVP

---

## Context

### Repo Root (Authoritative)

本计划的所有相对路径都以此目录为准（注意：目录名含前导空格）：

- `/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite`

### 原始依据
- `docs/long-term-optimization-plan.md`
- `gates.yaml`
- `scripts/verify_gates.py`

### 当前已验证状态（机器证据）
- `cd "/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite/backend" && uv run --group dev python ../scripts/verify_gates.py --all`：
  - `p1_to_p2`：PASS
  - `p2_to_p3`：PASS
  - `p3_to_p4`：FAIL（覆盖率 + Alembic）
- 覆盖率快照：`cd "/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite/backend" && uv run pytest --cov=app --cov-report=term -q` → TOTAL 64%

### 重要现实（别自欺欺人）
- 机器 gate 目前对 `p2_to_p3` 只做“代码存在性/grep”检查，不会验证“真实用户完成端到端”。如果你想严肃做增长漏斗，必须补一个可机器核验的数据口径（见 TODO 9）。
- 目录名包含前导空格：`/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite`。执行命令时不要偷懒写错目录。

### Metis Review（已吸收）
- 纠偏：当前机器 gate 显示 `p2_to_p3 PASS`，意味着“允许启动 Phase 3 工作”，但 Phase 2 的功能交付（2.1/2.4/2.5/2.6）仍然大量未完成；计划将以“完成 Phase 2 核心交付”为主线，并并行准备 Phase 3→4 出口 gate（覆盖率/Alembic）。
- 风险提示：2.1 是基础契约改动，强依赖排序；必须定义向后兼容与迁移策略。

---

## Work Objectives

### Core Objective
在不破坏现有工作流存量数据的前提下，把 Phase 2 的工作流能力做成“可扩展、可分发、可熔断”的可验收版本，并把 Phase 3 出口门禁变成可持续通过的工程基线。

### Concrete Deliverables
- 后端：workflow node schema 明确化（类型约束 + 校验），导入导出接口，混合检索 pipeline，Alembic。
- 前端：workflow editor 的 node 类型与配置表单类型化，导入导出 UI（最小），模板落地。
- 质量：覆盖率 >=70%（后端），CI gate `p3_to_p4` 通过。

### Definition of Done
- `cd "/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite/backend" && uv run --group dev python ../scripts/verify_gates.py --all` → PASS
- `cd "/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite/backend" && uv run pytest --cov=app --cov-fail-under=70 -q` → PASS
- `cd "/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite/frontend" && npm run build` → PASS
- `cd "/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite/frontend" && npm run test` → PASS

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**：YES（backend: pytest + pytest-cov；frontend: vitest + vue-tsc）
- **Automated tests**：YES（Tests-after + 针对高风险点补单测/集成测试）
- **Agent-Executed QA**：ALWAYS

### Universal Rules
- 所有验收必须是“agent 可执行命令”或自动化脚本，不允许“你手动点一下看看”。
- 任何涉及高风险能力（HTTP/Code node / embed / openai compat）默认必须可通过 feature flag 熔断。

### Common QA Setup (用于 curl 场景)

> 如果某个 TODO 的 QA 场景需要真实跑 API，请按以下方式拿 token（避免手动复制）。

```bash
export API_BASE="http://127.0.0.1:8000"
export EMAIL="admin@test.com"
export PASS="password123"

# register (如果已存在可忽略失败)
curl -s -X POST "$API_BASE/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" >/dev/null || true

# login -> token
TOKEN=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | python -c 'import sys, json; print(json.load(sys.stdin)["token"])')
echo "TOKEN=${TOKEN:0:8}..."
```

---

## Execution Strategy

### Parallel Execution Waves

Wave 1（基础契约 + 质量门禁，阻塞后续）：
- TODO 1：2.1 Workflow Schema 统一（后端）
- TODO 2：2.1 Workflow Schema 统一（前端）
- TODO 3：Phase 3 gate：Alembic 集成
- TODO 4：Phase 3 gate：覆盖率提升到 >=70%（优先补低覆盖模块）

Wave 2（功能交付，基于 schema）：
- TODO 5：2.4 Hybrid Retrieval（cosine + FTS5 合并 + 可选 rerank + 降级）
- TODO 6：2.5 Workflow Import/Export（后端 API + 校验 + 原子性）
- TODO 7：2.5 前端导入/导出 UI（最小）
- TODO 8：2.6 Publish MVP（默认 iframe embed）

Wave 3（模板与漏斗闭环，避免“做完没人用”）：
- TODO 9：两个模板（知识库问答、SOP 助手）+ 机器可核验的漏斗计数口径

---

## TODOs

> 说明：每个 TODO 都包含 References + Acceptance Criteria + Agent-Executed QA Scenarios。

- [x] 1. Phase 2.1 — 后端 Workflow NodeSchema（Pydantic union + 向后兼容）

  **What to do**:
  - 设计 `NodeSchema`（discriminated union），并采用“渐进收紧”策略：
    - 持久化层（`workflows.json`）继续存储为 dict（避免一次性迁移）。
    - API 层与执行层增加强校验：把 dict 解析/校验为 `NodeSchema`，失败则 4xx。
  - 必须提供向后兼容：旧工作流（nodes/edges 是任意 dict）仍可加载/执行；不合法节点要给出可读错误。
  - 为新节点类型补齐 schema：`http`、`code`（对应 Phase 2.2/2.3）。
  - API 入口处做 schema 校验：创建/更新/导入 workflow 时拒绝不合法 payload。

  **Must NOT do**:
  - 不允许一次性破坏所有存量 `workflows.json`。
  - 不允许把“校验失败”变成 500（必须 4xx + 清晰 detail）。

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: （无）

  **References**:
  - `backend/app/models/workflow.py` - 当前 `GraphData` 是 `Dict[str, Any]`，这是要收紧的起点。
  - `backend/app/api/workflow.py` - Workflow CRUD 的 API 入口与持久化（`workflows.json`）。
  - `backend/app/core/workflow/workflow_engine.py` - engine 依赖 node.type 分发，schema 变更必须保持执行路径稳定。
  - `backend/app/core/workflow/workflow_nodes.py` - node data 字段实际使用情况（是 schema 的“事实来源”。）

  **Acceptance Criteria**:
  - [ ] `uv run pytest -q` → PASS
  - [ ] `uv run --group dev python ../scripts/verify_gates.py --phase p2_to_p3` → PASS
  - [ ] 新增测试文件：`backend/tests/test_workflow_schema_validation.py`（至少覆盖：legacy payload 可用、非法节点 400、未知 node.type 400）。
  - [ ] `uv run pytest -q backend/tests/test_workflow_schema_validation.py` → PASS

  **Agent-Executed QA Scenarios**:
  - Scenario: 旧 workflow 仍可执行
    - Tool: Bash (curl)
    - Preconditions: backend 服务已启动（监听 127.0.0.1:8000），并已获取 `$TOKEN`（见 Common QA Setup）
    - Steps:
      1. 创建 workflow：
         - `WF_ID=$(curl -s -X POST "$API_BASE/api/v1/workflows" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"name":"schema-legacy","description":null,"graph_data":{"nodes":[{"id":"start-1","type":"start","data":{}},{"id":"end-1","type":"end","data":{}}],"edges":[{"id":"e1","source":"start-1","target":"end-1"}]}}' | python -c 'import sys, json; print(json.load(sys.stdin)["id"])')`
      2. 执行 workflow（SSE）：
         - `curl -s -N -X POST "$API_BASE/api/v1/workflows/$WF_ID/execute" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"input":"ping"}' | head -n 50`
      3. Assert: 输出中包含 `event: workflow_complete` 或 `workflow_complete` 字样。

  - Scenario: 非法 node 被拒绝（4xx，不是 500）
    - Tool: Bash (curl)
    - Preconditions: backend 服务已启动 + `$TOKEN` 已就绪
    - Steps:
      1. POST 创建 workflow（带未知 type）：
         - `curl -s -w "\n%{http_code}\n" -X POST "$API_BASE/api/v1/workflows" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"name":"bad","description":null,"graph_data":{"nodes":[{"id":"x","type":"__unknown__","data":{}}],"edges":[]}}'`
      2. Assert: HTTP code 是 400/422（任何 4xx 均可，但禁止 5xx）。

- [x] 2. Phase 2.1 — 前端 GraphData/NodeConfig 类型化（TS union + 表单对齐）

  **What to do**:
  - 为 workflow nodes 定义 TS union（按 node.type 区分 data 结构）。
  - `NodeConfigPanel` 保存时对 HTTP/Code 节点做 JSON 解析与最小校验（避免把字符串塞回后端导致 500）。
  - 确保前端保存的数据形状与后端 NodeSchema 一致。

  **Must NOT do**:
  - 不允许把“后端 feature flag 关闭”变成“前端仍能创建并运行”。（可创建，但运行必须明确报错；或直接在 UI 隐藏创建入口。）

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `frontend-ui-ux`

  **References**:
  - `frontend/src/views/WorkflowEditor.vue` - workflow editor 入口与 node slot。
  - `frontend/src/components/NodeConfigPanel.vue` - 节点配置保存路径。
  - `frontend/src/composables/workflow/useNodeConfig.ts` - 节点配置的字段集合与同步逻辑。

  **Acceptance Criteria**:
  - [ ] `cd frontend && npm run build` → PASS
  - [ ] `cd frontend && npm run test` → PASS

  **Agent-Executed QA Scenarios**:
  - Scenario: TS 类型检查拦截非法 config
    - Tool: Bash
    - Steps:
      1. `cd frontend && npm run build`
      2. Assert: exit code 0

- [x] 3. Phase 3 Gate — 引入 Alembic（不改变业务行为）

  **What to do**:
  - 集成 Alembic 到 `backend/`：生成 `backend/alembic.ini` 与 `backend/alembic/`。
  - 建立“现有模型的初始迁移”并可在本地/CI 执行。
  - 将 `init_db()` 中的手写迁移策略逐步迁移到 Alembic（先并存，后替换）。

  **Must NOT do**:
  - 不允许引入需要额外服务的数据库（守住轻量边界）。

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: （无）

  **References**:
  - `backend/app/core/database.py` - 当前 `init_db()` 使用 `Base.metadata.create_all` + 手写 ALTER。
  - `gates.yaml` - `p3_to_p4.alembic` 明确要求 `backend/alembic.ini` 与 `backend/alembic/`。

  **Acceptance Criteria**:
  - [ ] `uv run --group dev python ../scripts/verify_gates.py --phase p3_to_p4` 中 alembic check → PASS
  - [ ] `uv run pytest -q` → PASS

  **Agent-Executed QA Scenarios**:
  - Scenario: Alembic 初始化可用
    - Tool: Bash
    - Steps:
      1. `cd backend && uv run alembic --help`
      2. Assert: exit code 0

- [x] 4. Phase 3 Gate — 覆盖率从 64% 提升到 >= 70%

  **What to do**:
  - 优先补低覆盖模块的“有意义测试”，避免为了数字写无用测试：
    - `backend/app/api/chat_stream.py`
    - `backend/app/core/knowledge/processor.py`
    - `backend/app/core/knowledge/store.py`
    - `backend/app/core/chroma_client.py`
    - `backend/app/utils/ssrf_guard.py`
    - `backend/app/utils/code_sandbox.py`
  - 对 SSRF 与 code sandbox：覆盖“拒绝路径”与“安全默认值”。

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: （无）

  **References**:
  - 覆盖率报告输出（执行时生成）：`uv run pytest --cov=app --cov-report=term-missing`
  - `gates.yaml` - `p3_to_p4.test_coverage` 命令与阈值。

  **Acceptance Criteria**:
  - [ ] `cd backend && uv run pytest --cov=app --cov-fail-under=70 -q` → PASS
  - [ ] `uv run --group dev python ../scripts/verify_gates.py --phase p3_to_p4` 中 coverage check → PASS

  **Agent-Executed QA Scenarios**:
  - Scenario: Gate command passes
    - Tool: Bash
    - Steps:
      1. `cd backend && uv run pytest --cov=app --cov-fail-under=70 -q`
      2. Assert: exit code 0

- [x] 5. Phase 2.4 — Hybrid Retrieval（cosine + SQLite FTS5 + 可选 Rerank + 降级）

  **What to do**:
  - Step 1：Chroma 改用 cosine（不破坏现有数据或提供重建路径）。
  - Step 2：SQLite FTS5 建索引 + 与向量召回合并排序（可配置权重）。
  - Step 3：可选 Rerank（调用 SiliconFlow 或兼容 API），不可用时自动降级。

  **Must NOT do**:
  - 不引入新服务（守住轻量边界）。

  **References**:
  - `backend/app/core/rag.py` - RAG pipeline 主实现。
  - `backend/app/core/chroma_client.py` - 向量存储与检索。
  - `frontend/src/views/KnowledgeView.vue` - 知识库 UI 入口（用于回归验证）。

  **Acceptance Criteria**:
  - [ ] `uv run pytest -q` → PASS
  - [ ] 新增至少 1 个集成测试文件：`backend/tests/test_hybrid_retrieval.py`（覆盖：FTS 命中、向量命中、合并去重、rerank 降级）。
  - [ ] `uv run pytest -q backend/tests/test_hybrid_retrieval.py` → PASS

- [x] 6. Phase 2.5 — Workflow Export/Import 后端（原子导入 + schema 校验）

  **What to do**:
  - 导出：按 NodeSchema 序列化为 JSON（含版本字段）。
  - 导入：上传 JSON → schema 校验 → 原子写入（失败不落脏数据）。
  - 冲突策略：默认生成新 workflow_id（避免覆盖）。

  **References**:
  - `backend/app/api/workflow.py` - 现有 CRUD 与执行接口。
  - `backend/app/models/workflow.py` - schema 定义位置。

  **Acceptance Criteria**:
  - [ ] `uv run pytest -q` → PASS
  - [ ] 新增测试文件：`backend/tests/test_workflow_import_export.py`（覆盖：export→import roundtrip、非法 payload 4xx、导入失败不落脏数据）。
  - [ ] `uv run pytest -q backend/tests/test_workflow_import_export.py` → PASS

  **Agent-Executed QA Scenarios**:
  - Scenario: Export → Import roundtrip（新 ID）
    - Tool: Bash (curl)
    - Preconditions: backend 服务已启动 + `$TOKEN` 已就绪
    - Steps:
      1. 创建 workflow：
         - `WF_ID=$(curl -s -X POST "$API_BASE/api/v1/workflows" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"name":"export-1","description":null,"graph_data":{"nodes":[{"id":"start-1","type":"start","data":{}},{"id":"end-1","type":"end","data":{}}],"edges":[{"id":"e1","source":"start-1","target":"end-1"}]}}' | python -c 'import sys, json; print(json.load(sys.stdin)["id"])')`
      2. 导出（定义为 plan 约定接口）：
         - `EXPORT_JSON=$(curl -s -X GET "$API_BASE/api/v1/workflows/$WF_ID/export" -H "Authorization: Bearer $TOKEN")`
      3. 导入（定义为 plan 约定接口）：
         - `NEW_WF_ID=$(printf '%s' "$EXPORT_JSON" | curl -s -X POST "$API_BASE/api/v1/workflows/import" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' --data-binary @- | python -c 'import sys, json; print(json.load(sys.stdin)["id"])')`
      4. Assert: `NEW_WF_ID` 非空且不等于 `WF_ID`
      5. 执行新 workflow：
         - `curl -s -N -X POST "$API_BASE/api/v1/workflows/$NEW_WF_ID/execute" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"input":"ping"}' | head -n 50`
      6. Assert: 输出中包含 `workflow_complete`

- [x] 7. Phase 2.5 — Workflow Export/Import 前端（最小 UI）

  **What to do**:
  - WorkflowEditor 加“导出 JSON/导入 JSON”按钮与对话框（最小可用）。
  - 导入失败时给出明确错误，不破坏当前画布状态。

  **References**:
  - `frontend/src/views/WorkflowEditor.vue` - toolbar 区域。
  - `frontend/src/composables/workflow/useWorkflowCrud` - 现有保存/加载逻辑。

  **Acceptance Criteria**:
  - [ ] `npm run build` → PASS
  - [ ] `npm run test` → PASS（补 1-2 个 smoke test 即可）

- [x] 8. Phase 2.6 — Publish MVP（默认 iframe embed）

  **What to do**:
  - 默认实现 iframe embed（生成带 token 的公开页面 URL）。
  - 用 feature flag `ENABLE_PUBLIC_EMBED` 做熔断。
  - 安全：token 有有效期；公开页面不暴露内部错误细节。

  **Defaults Applied**:
  - publish 优先级：iframe embed 优先于 OpenAI compat（更轻、更少安全坑）。

  **References**:
  - `docs/long-term-optimization-plan.md`（2.6 节）
  - `backend/app/core/feature_flags.py` - flag 读取。

  **Acceptance Criteria**:
  - [ ] 新增后端最小发布 API（plan 默认约定）：
    - `POST /api/v1/publish/embed`（body: `{ "workflow_id": "..." }`）→ 返回 `{ "url": "...", "token": "...", "expires_at": "..." }`
    - `GET /api/v1/publish/embed/{token}`（公开访问，用于页面加载/执行）
  - [ ] 新增测试文件：`backend/tests/test_publish_embed_flag.py`（覆盖：flag 关闭时 403、flag 开启时可生成 token、过期 token 401/403）。
  - [x] `uv run pytest -q backend/tests/test_publish_embed_flag.py` → PASS

- [x] 9. 模板 + 漏斗计数（把“真实用户完成端到端”变成可追踪）

  **What to do**:
  - 提供 2 个模板 workflow（知识库问答、SOP 助手），并能一键导入。
  - 为模板路径定义机器可核验计数口径（建议基于 audit log）：
    - `template_import`
    - `template_execute_success`
  - 产出一个脚本：读取最近 N 天 audit log，输出每个模板的完成次数（为后续“>=5 真实用户”提供量化依据）。

  **References**:
  - `backend/app/core/audit.py` - 审计日志写入点。
  - `gates.yaml` - 当前未对真实用户做检查（这是你要补的经营口径）。

  **Acceptance Criteria**:
  - [ ] 脚本可运行并输出 JSON 统计结果（agent 可直接运行验证）。

---

## Commit Strategy

- 建议按 wave 分批提交（每批都能通过：backend pytest + frontend build/test + gates）。

---

## Decisions Needed (if you want to override defaults)

1) Phase 2.6 Publish MVP：你是否坚持先做 OpenAI compat API？
   - 默认（本 plan）：先 iframe embed。
