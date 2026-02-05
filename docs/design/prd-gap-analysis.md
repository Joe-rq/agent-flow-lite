# PRD 差距分析与优化优先级

> **目标**：对照 `docs/design/prd.md` 逐条评估当前实现，并给出优化优先级。
> **聚焦**：业务闭环（上传 → 检索 → 对话引用高亮）为最高优先级。

---

## Gap Matrix

### 3.1 可视化工作流引擎

| PRD 要求 | 当前实现证据 | 状态 | 差距说明 |
|---|---|---|---|
| 无限画布拖拽、缩放 | `frontend/src/views/WorkflowEditor.vue`（Vue Flow + Controls + Background） | ✅ 达标 | 已支持缩放/拖拽、网格吸附。
| SVG/HTML 节点渲染 | `frontend/src/components/nodes/*.vue` | ✅ 达标 | 自定义节点组件渲染。
| 贝塞尔/平滑连线、自动吸附 | `WorkflowEditor.vue` 使用 `smoothstep` | ✅ 达标 | 连线类型匹配。
| Start/End/LLM/Knowledge/Condition 节点 | `frontend/src/components/nodes/*` | ✅ 达标 | 节点类型齐全。
| 条件分支 If/Else | `backend/app/core/workflow_engine.py` + `workflow_nodes.py` | ⚠️ 部分 | 后端支持分支；前端显示与交互有待验证。
| 变量引用 `{{step.output}}` | `backend/app/core/workflow_context.py` + `NodeConfigPanel.vue` | ✅ 达标 | 已实现变量模板解析。
| 图结构序列化 JSON | `backend/app/api/workflow.py` + `frontend/src/views/WorkflowEditor.vue` | ✅ 达标 | GraphData 序列化已实现。

### 3.2 RAG 知识管理系统

| PRD 要求 | 当前实现证据 | 状态 | 差距说明 |
|---|---|---|---|
| `.txt/.md` 拖拽上传 | `frontend/src/views/KnowledgeView.vue:49` + `backend/app/api/knowledge.py:126` | ✅ 达标 | 支持拖拽/选择文件上传。
| 文本清洗（去乱码/标准化） | `backend/app/api/knowledge.py` | ⚠️ 部分 | 未看到明确清洗逻辑，仅保存原文。
| 分块（固定长度/语义） | `backend/app/core/rag.py` | ✅ 达标 | 使用 SentenceSplitter 分块。
| Embedding API | `backend/app/core/rag.py` | ✅ 达标 | SiliconFlow Embedding。
| 检索测试窗口 | `frontend/src/views/KnowledgeView.vue:101` | ✅ 达标 | 已有检索测试 UI。

### 3.3 智能多轮对话终端

| PRD 要求 | 当前实现证据 | 状态 | 差距说明 |
|---|---|---|---|
| 自动创建 Session ID | `frontend/src/views/ChatTerminal.vue:156` | ✅ 达标 | 使用 `crypto.randomUUID()`。
| 历史记录回显 | `backend/app/api/chat.py` + `ChatTerminal.vue` | ✅ 达标 | JSON 存储+拉取展示。
| SSE 流式响应 | `backend/app/api/chat.py` + `ChatTerminal.vue` | ✅ 达标 | `StreamingResponse` + SSE 事件。
| 思维链展示（可选） | `ChatTerminal.vue:59` + `chat.py` `thought` 事件 | ✅ 达标 | 已实现。
| 引用溯源（可点击高亮） | `ChatTerminal.vue:447` | ❌ 未达标 | 目前仅文本引用，无可点击与高亮。

### 4. 技术架构

| PRD 要求 | 当前实现证据 | 状态 | 差距说明 |
|---|---|---|---|
| Vue 3 + Vite + TS | `frontend/` | ✅ 达标 | 符合。
| Pinia 管理全局状态 | `frontend/src/main.ts` | ⚠️ 部分 | 已引入但核心页面多为组件内状态。
| FastAPI | `backend/` | ✅ 达标 | 符合。
| PostgreSQL + pgvector | 未见配置 | ❌ 未达标 | 目前使用 JSON + ChromaDB。
| LangChain/LangGraph | 未见引用 | ❌ 未达标 | 自研 workflow engine。
| RESTful + Pydantic | `backend/app/api/*` | ✅ 达标 | 符合。

---

## Prioritized Optimizations

### P0（闭环必须完成）
1) **可点击引用 + 高亮展示**
   - 影响：直接完成 PRD 关键闭环（上传 → 检索 → 对话引用）。
   - 建议：后端 citation payload 增加片段文本；前端点击展示高亮面板。

### P1（体验/一致性提升）
1) **知识清洗明确化**
   - 在 `backend/app/api/knowledge.py` 中加入标准化/去乱码策略。
2) **Pinia 状态统一**
   - 将会话/知识库列表等抽离为 store，减少组件内状态耦合。

### P2（架构偏差说明或后续演进）
1) **存储与向量库偏差**
   - PRD 要求 PostgreSQL+pgvector；当前为 JSON+ChromaDB。
   - 建议：在文档中说明差异或规划迁移。
2) **SSE 稳定性提升**
   - FastAPI 原生 `StreamingResponse` 已可用，若生产可考虑 `sse-starlette`。

---

## Closed-Loop Focus

**闭环链路**：
1. 知识库上传（`.txt/.md`） → 2. 分块/Embedding/索引 → 3. 检索测试 → 4. 对话引用 → 5. 引用高亮展示

**当前阻塞点**：
- 引用无法点击、无法高亮展示（仅文本追加）。

**闭环完成标准**：
- 对话引用可点击；点击后显示对应文档片段，并对命中片段高亮。
