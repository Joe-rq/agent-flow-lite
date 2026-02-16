# Agent Flow Lite 代码审查修复计划（v3 — 全部完成）

> **状态：全部完成** — 2026-02-16 CI Quality Gate 8/8 通过

## Context

代码审查发现多项安全漏洞和运行时崩溃问题。经两轮可行性审核（`.sisyphus/drafts/code-review-fix-plan-feasibility.md`），修正了原计划中的范围混淆、遗漏攻击面、行号过期等问题。

## 修订历史

**v1 → v2:**
1. 拆分为 Track A/B/C，不再混合热修复和重构
2. 移除 `extract_token_content`（v1 中引用了不存在的函数）
3. `WorkflowView.vue` 删除降级：发现专用测试 `WorkflowView.spec.ts` 引用它
4. `set` 无序问题降级为 Track B
5. Phase 3/4 大规模重构全部移入 Track C

**v2 → v3：**
1. **A1 扩大防护面**：`GET/DELETE /sessions/{session_id}` 路径参数绕过了 `ChatRequest` 模型校验，需在 `get_session_path` 层做 containment 防护
2. **A2 改用 fail-closed**：无效 `kb_id` 应直接拒绝（400），而非静默规范化后可能产生 ID 碰撞
3. **A3 明确 fallback 行为契约**：`safe_eval` 在 simpleeval 不可用时的语义需文档化
4. **B4 改用模式匹配**：调试日志清理改为 `console.log` 全量搜索，不依赖固定行号
5. **Track C 爆炸半径补充**：记录已知的测试依赖链

---

## Track A: 合并阻塞项 — 安全 + 运行时修复 ✅ 6/6

> 每项改动 1-2 个文件，局部性强，回归风险低。完成后提交一次 commit。

### ✅ A1. session_id 路径遍历防护
- **文件**: `backend/app/models/chat.py` + `backend/app/api/chat_session.py`
- **完成方式**: `ChatRequest.session_id` 加正则约束；`get_session_path` 加 `resolve().relative_to()` containment 检查，失败抛 `HTTPException(400)`

### ✅ A2. kb_id 删除接口路径遍历防护
- **文件**: `backend/app/api/knowledge.py` + `backend/app/core/knowledge/processor.py`
- **完成方式**: `_check_kb_id()` 格式校验 + `delete_kb()` 内 `resolve().relative_to()` 双重防线

### ✅ A3. safe_eval 表达式注入加固
- **文件**: `backend/app/core/workflow/workflow_context.py`
- **完成方式**: 异常收窄为 `(TypeError, ValueError, NameError, InvalidExpression)`；`simple_eval` 配置 `names=_SAFE_NAMES, functions={}`；fallback 仅接受字面布尔值

### ✅ A4. SKILLS_DIR 路径修正
- **完成方式**: 路径集中化到 `backend/app/core/paths.py`，所有消费方统一从 `paths.py` 导入（比原计划更彻底）

### ✅ A5. SkillExecutor dict/Pydantic 接口统一
- **文件**: `backend/app/core/skill/skill_executor.py` + `backend/tests/test_skill_executor.py`
- **完成方式**: 移除 dict 兼容分支，测试全部迁移为 `SkillInput` 对象

### ✅ A6. SkillDetail.description 默认值冲突修复
- **文件**: `backend/app/core/skill/skill_loader.py`
- **完成方式**: `description=frontmatter.get("description") or name`

---

## Track B: 稳定性改进 — 非阻塞但建议尽快修复 ✅ 5/5

> 不影响安全和核心功能，但改善可调试性和健壮性。

### ✅ B1. llm.py 异常链丢失修复
- **完成方式**: `raise RuntimeError(...) from exc`，保留异常链

### ✅ B2. NodeConfigPanel 移除模拟数据
- **完成方式**: 逻辑已迁移到 `useNodeConfig.ts` composable，catch 中无 mock 数据

### ✅ B3. workflow_engine 最终输出健壮性改进
- **完成方式**: `self.last_executed_id` 追踪最后执行节点，替代 `list(executed)[-1]`

### ✅ B4. 调试日志清理
- **完成方式**: `NodeConfigPanel.vue`、`WorkflowEditor.vue`、`WorkflowView.vue` 中的 `console.log` 全部清除

### ✅ B5. 后端小修合集
- `normalize_email` 去掉 `async` ✅
- `get_client()` 缓存：通过 `_create_client()` 的 `@lru_cache(maxsize=8)` 等效实现 ✅
- `workflow_nodes.py` 顶层 `import json` ✅

---

## Track C: 结构性重构 ✅ 10/10

> 原计划为独立 Epic，实际已在多轮迭代中逐步完成。

### ✅ C1. 后端 SSE 工具函数提取
- `backend/app/utils/sse.py` 已存在，`chat_stream.py`、`workflow.py`、`skill_executor.py` 统一导入

### ✅ C2. SkillInput 解析逻辑提取
- `skill_loader.py` 中已有 `_parse_inputs()` 方法

### ✅ C3. 前端 SSE 流解析器提取
- `frontend/src/utils/sse-parser.ts` 已存在，被 `useChatSSE`、`useSSEStream`、`useSkillRunner` 使用

### ✅ C4. 前端工具函数 / 类型集中化
- `format.ts`、`constants.ts`、`fetch-auth.ts`、`types/index.ts` 全部存在

### ✅ C5. 后端 chat.py 拆分
- 已拆为 `chat.py`（409 行）+ `chat_session.py`（104 行）+ `chat_stream.py`（457 行）

### ✅ C6. 后端 knowledge.py 拆分
- API 层 `knowledge.py`（291 行）+ 核心逻辑 `core/knowledge/`（processor.py、store.py、fts.py）

### ✅ C7. 后端 core/ 目录重组
- 已重组为 `core/knowledge/`、`core/skill/`、`core/workflow/` 子目录

### ✅ C8. 前端死代码清理
- `WorkflowView.vue` 和 `App.vue.bak` 均已删除

### ✅ C9. 前端大组件拆分
- `ChatTerminal.vue` 179 行、`KnowledgeView.vue` 130 行、`WorkflowEditor.vue` 181 行（提取 `useFeatureFlags` composable）

### ✅ C10. 后端性能优化
- `SiliconFlowEmbedding` 已 async 化
- `processing_tasks` 模块级持久化
- `cleanup_expired_tokens` 后台定期执行
