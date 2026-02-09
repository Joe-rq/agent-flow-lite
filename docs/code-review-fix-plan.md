# Agent Flow Lite 代码审查修复计划（v3 — 经二次核查修订）

## Context

代码审查发现多项安全漏洞和运行时崩溃问题。经两轮可行性审核（`.sisyphus/drafts/code-review-fix-plan-feasibility.md`），修正了原计划中的范围混淆、遗漏攻击面、行号过期等问题。本版本为最终执行版。

## 修订历史

**v1 → v2:**
1. 拆分为 Track A/B/C，不再混合热修复和重构
2. 移除 `extract_token_content`（v1 中引用了不存在的函数）
3. `WorkflowView.vue` 删除降级：发现专用测试 `WorkflowView.spec.ts` 引用它
4. `set` 无序问题降级为 Track B
5. Phase 3/4 大规模重构全部移入 Track C

**v2 → v3（本次）：**
1. **A1 扩大防护面**：`GET/DELETE /sessions/{session_id}` 路径参数绕过了 `ChatRequest` 模型校验，需在 `get_session_path` 层做 containment 防护
2. **A2 改用 fail-closed**：无效 `kb_id` 应直接拒绝（400），而非静默规范化后可能产生 ID 碰撞
3. **A3 明确 fallback 行为契约**：`safe_eval` 在 simpleeval 不可用时的语义需文档化
4. **B4 改用模式匹配**：调试日志清理改为 `console.log` 全量搜索，不依赖固定行号
5. **Track C 爆炸半径补充**：记录已知的测试依赖链

---

## Track A: 合并阻塞项 — 安全 + 运行时修复

> 每项改动 1-2 个文件，局部性强，回归风险低。完成后提交一次 commit。

### A1. session_id 路径遍历防护
- **文件**: `backend/app/models/chat.py` + `backend/app/api/chat.py`
- **攻击面**:
  - `ChatRequest.session_id`（请求体） — 用于 `POST /chat`
  - `GET /sessions/{session_id}`（路径参数，第 639 行） — 绕过 ChatRequest 模型校验
  - `DELETE /sessions/{session_id}`（路径参数，第 683 行） — 同上
- **改动**:
  - `ChatRequest.session_id` 加正则约束 `Field(..., pattern=r"^[a-zA-Z0-9_-]{1,128}$")`
  - `get_session_path` 函数（第 43 行）增加 `resolve().relative_to(SESSIONS_DIR.resolve())` containment 检查，覆盖所有调用路径（包括路径参数入口）
  - containment 检查失败时抛出 `HTTPException(400)`，fail-closed
- **验证**: `uv run pytest`

### A2. kb_id 删除接口路径遍历防护
- **文件**: `backend/app/api/knowledge.py`
- **改动**: `delete_knowledge_base`（第 514 行）中：
  - 对 `kb_id` 做格式校验：不符合 `r"^[\w-]+$"` 的直接返回 `HTTPException(400, "Invalid kb_id")`，**fail-closed**，不做静默规范化（避免 ID 碰撞风险）
  - 对 `upload_dir` 和 `metadata_dir` 追加 `resolve().relative_to()` containment 检查作为二重防线
- **验证**: `uv run pytest`

### A3. safe_eval 表达式注入加固
- **文件**: `backend/app/core/workflow_context.py`
- **改动**:
  - `except Exception` → `except ImportError`（simpleeval 未安装）+ `except (TypeError, ValueError, NameError)`（合法计算错误），其他异常向上传播
  - 对 `simple_eval` 配置显式 `names={}` 和 `functions={}` 白名单
  - **fallback 行为契约**：当 simpleeval 不可用时，仅接受字面布尔值（`"true"/"yes"/"1"` → True，其他一律 False），并记录 warning 日志说明 fallback 被触发
- **验证**: `uv run pytest`

### A4. SKILLS_DIR 路径修正
- **文件**: `backend/app/api/chat.py`
- **改动**: `Path(__file__).parent.parent.parent.parent.parent / "skills"` → `Path(__file__).parent.parent.parent / "data" / "skills"`（与 `skill.py` 一致）
- **验证**: `uv run pytest`

### A5. SkillExecutor dict/Pydantic 接口统一
- **文件**: `backend/app/core/skill_executor.py`
- **改动**: `validate_inputs` 和 `substitute_variables` 中将 `input_def.get("name")` → `input_def.name`，`input_def.get("required", False)` → `input_def.required` 等，类型签名从 `List[Dict[str, Any]]` 改为 `List[SkillInput]`
- **验证**: `uv run pytest`

### A6. SkillDetail.description 默认值冲突修复
- **文件**: `backend/app/core/skill_loader.py`
- **改动**: `_build_skill_detail` 中 `description=frontmatter.get("description", "")` → `description=frontmatter.get("description") or name`，避免触发 `min_length=1` 校验
- **验证**: `uv run pytest`

---

## Track B: 稳定性改进 — 非阻塞但建议尽快修复

> 不影响安全和核心功能，但改善可调试性和健壮性。可与 Track A 同期或紧随其后执行。

### B1. llm.py 异常链丢失修复
- **文件**: `backend/app/core/llm.py`
- **改动**: 两处 `raise Exception(f"DeepSeek API call failed: {str(e)}")` → `raise RuntimeError(f"DeepSeek API call failed: {e}") from e`
- **验证**: `uv run pytest`

### B2. NodeConfigPanel 移除模拟数据
- **文件**: `frontend/src/components/NodeConfigPanel.vue`
- **改动**: catch 块中移除硬编码模拟数据（`kb1`, `kb2`, `kb3`），`knowledgeBases.value` 保持空数组，保留 `console.error` 日志
- **验证**: `npx tsc --noEmit && npm run test`

### B3. workflow_engine 最终输出健壮性改进
- **文件**: `backend/app/core/workflow_engine.py`
- **改动**: 新增 `last_executed_id: str | None = None`，在执行循环中追踪最后执行的节点 ID，替代 `list(executed)[-1]`
- **说明**: CPython 3.7+ 的 set 迭代顺序接近插入序，此项属健壮性改进而非紧急修复
- **验证**: `uv run pytest`

### B4. 调试日志清理
- **范围**: 基于 `console.log` 模式搜索，覆盖以下已确认位置：
  - `frontend/src/components/NodeConfigPanel.vue`：第 152 行（模板内）、第 374 行（脚本内）
  - `frontend/src/views/WorkflowEditor.vue`：第 369、688、692、695 行
  - `frontend/src/views/WorkflowView.vue`：第 253、259 行（如 C8 尚未执行）
- **不清理**: `login-verification.spec.ts` 中的 `console.log`（测试代码中的条件日志，保留）
- **改动**: 移除所有非测试文件中的遗留 `console.log` 调试输出
- **验证**: `npx tsc --noEmit && npm run test`

### B5. 后端小修合集
- `backend/app/core/auth.py`: `normalize_email` 去掉不必要的 `async`
- `backend/app/core/llm.py`: `get_client()` 加 `@lru_cache(maxsize=1)` 避免重复创建客户端
- `backend/app/core/workflow_nodes.py`: `__import__("json")` → 文件顶部 `import json`
- **验证**: `uv run pytest`

---

## Track C: 结构性重构 — 独立 Epic，单独排期

> 爆炸半径大，需独立分支、充分测试。不在热修复窗口内执行。

### C1. 后端 SSE 工具函数提取
- **新建**: `backend/app/utils/sse.py` — 提取 `format_sse_event`（当前重复 3 处）
- **影响**: `chat.py`、`workflow.py`、`skill_executor.py`
- **复杂度**: 低

### C2. SkillInput 解析逻辑提取
- **文件**: `backend/app/core/skill_loader.py`
- **改动**: 提取 `_parse_inputs()` 方法，替换 3 处重复的列表推导式
- **复杂度**: 低（单文件内部重构）

### C3. 前端 SSE 流解析器提取
- **新建**: `frontend/src/utils/sse-parser.ts` — 带行缓冲的共享解析器
- **影响**: `ChatTerminal.vue`、`WorkflowEditor.vue`、`SkillsView.vue`
- **复杂度**: 中（需验证跨 chunk 缓冲正确性）

### C4. 前端工具函数 / 类型集中化
- **新建**: `frontend/src/utils/format.ts`、`constants.ts`、`fetch-auth.ts`、`types/index.ts`
- **影响**: 多个 view 和 component 的 import 变更
- **复杂度**: 中（广泛但低风险的 import 替换）

### C5. 后端 chat.py 拆分（720 行 → ~3 文件）
- **复杂度**: 高（会话管理 + 流生成 + 路由高度耦合）
- **前置**: 需先完成 C1（SSE 工具提取）
- **已知依赖**: `backend/tests/test_chat_scoped.py` 直接 import `app.api.chat` 内部函数；`backend/tests/test_chat_citation.py` import `chat_stream_generator`

### C6. 后端 knowledge.py 拆分（536 行 → ~2 文件）
- **复杂度**: 中高
- **已知依赖**: `backend/tests/test_knowledge_dimension_mismatch.py` 依赖 `app.api.knowledge` 符号

### C7. 后端 core/ 目录重组（11 → 6 + 2 子目录）
- **复杂度**: 非常高（全量 import 路径变更 + 测试路径变更）
- **前置**: 需先完成 C5、C6
- **已知依赖**: `backend/main.py` 直接 import chat/knowledge router；所有 `backend/tests/` 文件依赖 `app.core.*` 路径

### C8. 前端死代码清理
- **删除**: `WorkflowView.vue`、`App.vue.bak`
- **前置**: 需先处理 `frontend/src/__tests__/views/WorkflowView.spec.ts` 测试耦合（删除或迁移测试）
- **复杂度**: 低（但有测试依赖）

### C9. 前端大组件拆分（可选）
- `ChatTerminal.vue`（1164 行）、`KnowledgeView.vue`（1132 行）、`WorkflowEditor.vue`（1036 行）
- 提取 composables + 子组件
- **复杂度**: 高

### C10. 后端性能优化
- `rag.py`: `SiliconFlowEmbedding` 异步化
- `knowledge.py`: `processing_tasks` 持久化
- `core/auth.py`: 过期 token 定期清理
- **复杂度**: 中

---

## 执行策略

```
Track A（安全+崩溃）──→ 验证通过 ──→ commit + 合并
       ↓
Track B（稳定性）────→ 验证通过 ──→ commit + 合并
       ↓
Track C（重构 epic）──→ 独立分支 ──→ 逐项 PR + review
```

- **Track A**: 6 项，改动范围 6 个文件，必须全部通过后才能合并
- **Track B**: 5 项，改动范围 5 个文件，建议紧随 Track A 执行
- **Track C**: 10 项，独立排期，按 C1→C2→…→C9→C10 顺序执行，每项独立 PR
- 每项改动后运行对应验证命令（后端 `uv run pytest`，前端 `npx tsc --noEmit && npm run test`）
- 执行前刷新行号引用（审核中已指出部分行号可能过期）
