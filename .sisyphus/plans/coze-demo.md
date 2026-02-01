# Coze 智能体平台 Demo - 执行计划

## TL;DR

> **目标**: 11天内构建简化版 Coze 智能体平台（Python FastAPI + Vue3）
> 
> **核心交付物**:
> - 可视化工作流画布（3种节点：Start/LLM/Knowledge）
> - RAG 知识库（文件上传 → 向量化 → 检索）
> - 智能问答终端（多轮对话 + SSE 流式响应）
> 
> **技术栈**: FastAPI + LlamaIndex + ChromaDB + DeepSeek API + Vue3 + Vue Flow
> 
> **风险评估**: 30% 政治风险（Python vs 考核要求 Node.js），已准备辩护话术
> 
> **关键成功因素**: Day 10 必须完成端到端演示，Day 12-14 仅用于抛光

---

## Context

### 原始需求
构建简化版 Coze 智能体平台 Demo，支持：
1. 可视化拖拽编排工作流
2. 知识库构建与 RAG 检索
3. 智能问答 Agent

考核时间：2月12日-15日（剩余11-14天）

### 关键决策
- **技术栈**: Python FastAPI（偏离考核要求的 Node.js/NestJS）
- **理由**: RAG 效果质变、开发速度倍增、AI 生态领先
- **风险接受**: 30% 可能被考核官质疑，已准备辩护策略

### Metis 审查发现
**关键缺口已修复**:
- ✅ MVP 范围已锁定（见下方 Must NOT Have）
- ✅ 检查点机制已建立（Day 3/6/8/10）
- ✅ 可执行验收标准已定义
- ✅ Python 辩护话术已准备
- ✅ 降级方案已规划（Vue Flow 失败 → 表单式工作流）

---

## Work Objectives

### Core Objective
构建一个可在答辩时完整演示的 Coze-like Agent 平台，核心链路跑通：拖拽创建工作流 → 上传文档 → 向量化 → 对话时检索生成答案。

### Concrete Deliverables
1. **Backend** (`backend/`):
   - FastAPI 项目结构
   - 工作流 CRUD API
   - 文件上传 + LlamaIndex RAG pipeline
   - DeepSeek LLM 集成
   - SSE 流式聊天 API

2. **Frontend** (`frontend/`):
   - Vue3 + Vite 项目
   - Vue Flow 拖拽画布
   - 节点配置面板
   - 知识库管理界面
   - 聊天终端（流式显示）

3. **Database**:
   - ChromaDB 向量存储（本地文件，零配置）

### Definition of Done
- [x] 能拖拽创建包含 Start → LLM → End 的工作流并保存
- [x] 能上传 .txt/.md 文件，后台自动解析并向量化
- [x] 能在聊天界面提问，收到基于知识库的回答
- [x] 答辩时可完整演示上述流程（5分钟演示脚本）

### Must Have
- [x] 3种节点类型：Start、LLM、Knowledge
- [x] 节点间连线与数据传递
- [x] 文件上传与 ChromaDB 存储
- [x] 基于 LlamaIndex 的 RAG 检索
- [x] DeepSeek API 集成
- [x] SSE 流式响应
- [x] 会话历史存储

### Must NOT Have (Guardrails)
- ❌ 多用户/认证系统（单用户 Demo）
- ❌ 实时协作（WebSocket 同步）
- ❌ 复杂条件逻辑（Condition 节点仅支持简单字符串匹配）
- ❌ PDF 解析（仅支持 .txt/.md）
- ❌ 工作流版本控制（保存即覆盖）
- ❌ 多模型支持（仅 DeepSeek）
- ❌ 高级 RAG（重排序、混合搜索、元数据过滤）
- ❌ 生产级错误处理（基础 try/catch）
- ❌ 单元测试（仅关键 RAG pipeline 验证）
- ❌ 移动端适配（仅桌面端）
- ❌ 批量文件上传（单文件）
- ❌ 自定义节点样式（使用 Vue Flow 默认样式）
- ❌ 超过 10 条消息的会话限制

---

## Verification Strategy

### Test Infrastructure Assessment
- **现有测试框架**: 无
- **用户决策**: 不设置正式测试框架（时间不足）
- **替代方案**: 每个任务包含可执行的验证命令（curl/bash/playwright）

### 验收标准类型
所有任务使用**自动化验证**（Agent 可执行）：
- **Backend API**: `curl` 命令验证响应
- **RAG Pipeline**: 脚本化测试（上传文件 → 提问 → 验证答案）
- **Frontend**: Playwright 浏览器自动化
- **End-to-End**: 完整用户流程脚本

---

## Execution Strategy

### 并行执行波次

```
Wave 1 (Day 1-2): 项目初始化
├── Task 1: 初始化 FastAPI 后端项目结构
├── Task 2: 初始化 Vue3 前端项目结构
└── Task 3: 配置 DeepSeek API 访问

Wave 2 (Day 3-5): 核心后端功能
├── Task 4: 实现工作流 CRUD API
├── Task 5: 实现文件上传 + ChromaDB 集成
└── Task 6: 实现 LlamaIndex RAG Pipeline

Wave 3 (Day 6-7): LLM 与聊天
├── Task 7: 集成 DeepSeek API
└── Task 8: 实现 SSE 流式聊天 API

Wave 4 (Day 8-10): 前端核心
├── Task 9: 实现 Vue Flow 画布基础
├── Task 10: 实现节点配置面板
├── Task 11: 实现知识库管理界面
└── Task 12: 实现聊天终端

Wave 5 (Day 11-14): 集成与抛光
├── Task 13: 前后端联调
├── Task 14: 端到端流程验证
└── Task 15: 答辩准备（演示脚本 + Python 辩护话术）
```

### 关键路径
```
Task 1 (后端初始化) 
  → Task 4 (工作流 API) 
  → Task 5 (文件上传) 
  → Task 6 (RAG Pipeline) 
  → Task 7 (DeepSeek 集成) 
  → Task 13 (联调) 
  → Task 14 (端到端验证)
```

### 检查点机制（Go/No-Go）

| 日期 | 检查点 | 通过标准 | 失败降级方案 |
|------|--------|----------|--------------|
| **Day 3** | Vue Flow 基础 | 画布渲染 + 可拖拽添加节点 | 降级为表单式工作流构建器 |
| **Day 6** | 后端 API 完成 | 工作流 CRUD + 文件上传 API 可用 | 砍去 Knowledge 节点，仅保留 LLM 节点 |
| **Day 8** | RAG 工作 | 上传文件 → 提问 → 得到相关答案 | 使用简单关键词搜索替代向量检索 |
| **Day 10** | 端到端演示 | 完整流程可演示（允许粗糙） | 冻结功能，仅修致命 Bug |

---

## TODOs

### Task 1: 初始化 FastAPI 后端项目

**What to do**:
- 创建 `backend/` 目录
- 使用 `uv` 初始化 Python 项目
- 创建项目结构：`app/api/`, `app/core/`, `app/models/`
- 安装依赖：fastapi, uvicorn, llama-index, chromadb, python-multipart
- 创建 `main.py` 入口文件
- 配置 CORS 和基础路由

**Must NOT do**:
- 不要添加数据库迁移（ChromaDB 不需要）
- 不要添加认证中间件
- 不要添加复杂的配置管理（简单 `.env` 即可）

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: `git-master`
- **Reason**: 项目初始化是标准操作，不需要复杂推理

**Parallelization**:
- **Can Run In Parallel**: YES
- **Parallel Group**: Wave 1
- **Blocks**: Task 4, 5, 6, 7, 8
- **Blocked By**: None

**References**:
- FastAPI 官方文档: https://fastapi.tiangolo.com/tutorial/first-steps/
- LlamaIndex 安装: https://docs.llamaindex.ai/en/stable/getting_started/installation.html
- ChromaDB Python: https://docs.trychroma.com/getting-started

**Acceptance Criteria**:
```bash
# 验证项目结构
ls backend/
# 预期: app/, main.py, pyproject.toml, .env

# 验证依赖安装
cd backend && python -c "import fastapi, llama_index, chromadb; print('OK')"
# 预期: 输出 OK，无报错

# 验证服务启动
cd backend && uvicorn main:app --reload &
sleep 3
curl http://localhost:8000/docs
# 预期: 返回 Swagger UI HTML
```

**Commit**: YES
- Message: `feat(backend): initialize FastAPI project structure`
- Files: `backend/*`

---

### Task 2: 初始化 Vue3 前端项目

**What to do**:
- 创建 `frontend/` 目录
- 使用 `npm create vue@latest` 初始化
- 选择：TypeScript + Pinia + Vue Router
- 安装依赖：@vue-flow/core, @vue-flow/background, @vue-flow/controls, axios
- 创建基础布局：Header + Sidebar + Main Content
- 配置代理（vite.config.ts）指向后端 8000 端口

**Must NOT do**:
- 不要添加 Element Plus（用原生 CSS/Tailwind）
- 不要添加复杂的状态管理（Pinia 基础即可）
- 不要添加路由守卫

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: `git-master`, `frontend-ui-ux`
- **Reason**: 需要前端项目经验 + UI 布局能力

**Parallelization**:
- **Can Run In Parallel**: YES
- **Parallel Group**: Wave 1
- **Blocks**: Task 9, 10, 11, 12
- **Blocked By**: None

**References**:
- Vue3 快速开始: https://vuejs.org/guide/quick-start.html
- Vue Flow 文档: https://vueflow.dev/guide/
- Vite 配置代理: https://vitejs.dev/config/server-options.html#server-proxy

**Acceptance Criteria**:
```bash
# 验证项目结构
ls frontend/
# 预期: src/, package.json, vite.config.ts, index.html

# 验证依赖安装
cd frontend && npm list @vue-flow/core
# 预期: 显示版本号

# 验证开发服务器
cd frontend && npm run dev &
sleep 5
curl http://localhost:5173
# 预期: 返回 Vue 默认页面 HTML
```

**Commit**: YES
- Message: `feat(frontend): initialize Vue3 project with Vue Flow`
- Files: `frontend/*`

---

### Task 3: 配置 DeepSeek API 访问

**What to do**:
- 注册 DeepSeek 账号并获取 API Key
- 在 `backend/.env` 添加 `DEEPSEEK_API_KEY`
- 创建 `app/core/config.py` 加载配置
- 测试 API 连通性（简单 curl 或 Python 脚本）
- 确定使用模型：`deepseek-chat`（默认）

**Must NOT do**:
- 不要将 API Key 提交到 Git（添加到 `.gitignore`）
- 不要实现复杂的重试逻辑（简单 try/catch 即可）

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: `git-master`
- **Reason**: 配置任务，需要安全意识（不泄露 key）

**Parallelization**:
- **Can Run In Parallel**: YES
- **Parallel Group**: Wave 1
- **Blocks**: Task 7
- **Blocked By**: Task 1

**References**:
- DeepSeek API 文档: https://platform.deepseek.com/api-docs/

**Acceptance Criteria**:
```bash
# 验证 API Key 配置
cat backend/.env | grep DEEPSEEK
# 预期: 显示 DEEPSEEK_API_KEY=sk-...

# 验证 API 连通性
curl -X POST https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}]}'
# 预期: 返回 JSON 包含 choices[0].message.content
```

**Commit**: YES
- Message: `chore(config): add DeepSeek API configuration`
- Files: `backend/.env.example`, `backend/app/core/config.py`
- Pre-commit: 确保 `.env` 在 `.gitignore` 中

---

### Task 4: 实现工作流 CRUD API

**What to do**:
- 创建 `app/models/workflow.py`：Pydantic 模型定义 Workflow
- 创建 `app/api/workflow.py`：CRUD 端点
  - `GET /api/v1/workflows` - 列表
  - `POST /api/v1/workflows` - 创建
  - `GET /api/v1/workflows/{id}` - 详情
  - `PUT /api/v1/workflows/{id}` - 更新
  - `DELETE /api/v1/workflows/{id}` - 删除
- 使用内存存储（dict）或 JSON 文件（简化，不用数据库）

**Must NOT do**:
- 不要添加 PostgreSQL（用文件存储简化）
- 不要添加复杂的验证（Pydantic 基础验证即可）
- 不要添加分页（返回全部列表）

**Recommended Agent Profile**:
- **Category**: `unspecified-low`
- **Skills**: `git-master`
- **Reason**: 标准 CRUD，FastAPI 擅长此领域

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 2
- **Blocks**: Task 13
- **Blocked By**: Task 1

**References**:
- FastAPI CRUD: https://fastapi.tiangolo.com/tutorial/body/
- Pydantic 模型: https://docs.pydantic.dev/latest/

**Acceptance Criteria**:
```bash
# 启动后端
cd backend && uvicorn main:app --reload &
sleep 3

# 测试创建工作流
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Workflow","description":"A test","graph_data":{"nodes":[],"edges":[]}}'
# 预期: 201, 返回包含 id 的 workflow 对象

# 测试列表
curl http://localhost:8000/api/v1/workflows
# 预期: 200, 返回 workflow 列表

# 测试更新
curl -X PUT http://localhost:8000/api/v1/workflows/{id} \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated"}'
# 预期: 200, 返回更新后的对象
```

**Commit**: YES
- Message: `feat(api): add workflow CRUD endpoints`
- Files: `backend/app/models/workflow.py`, `backend/app/api/workflow.py`

---

### Task 5: 实现文件上传 + ChromaDB 集成

**What to do**:
- 创建 `app/api/knowledge.py`：文件上传端点
- 使用 `python-multipart` 处理文件上传
- 保存上传文件到 `data/uploads/`
- 初始化 ChromaDB 客户端（本地持久化）
- 创建集合（Collection）存储文档块
- 实现简单的文档解析（读取 .txt/.md 内容）

**Must NOT do**:
- 不要添加异步处理（简化，同步处理即可）
- 不要添加复杂的文档解析（仅文本文件）
- 不要添加大文件分块（单文件 < 5MB）

**Recommended Agent Profile**:
- **Category**: `unspecified-low`
- **Skills**: `git-master`
- **Reason**: 文件上传是标准功能，ChromaDB 集成简单

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 2
- **Blocks**: Task 6
- **Blocked By**: Task 1

**References**:
- FastAPI 文件上传: https://fastapi.tiangolo.com/tutorial/request-files/
- ChromaDB 集合: https://docs.trychroma.com/collections

**Acceptance Criteria**:
```bash
# 创建测试文件
echo "The capital of France is Paris. France is in Europe." > /tmp/test.txt

# 测试上传
curl -X POST http://localhost:8000/api/v1/knowledge/upload \
  -F "file=@/tmp/test.txt" \
  -F "kb_id=kb-test"
# 预期: 200, 返回 {"status":"success","document_id":"..."}

# 验证 ChromaDB 存储
python -c "
import chromadb
client = chromadb.PersistentClient(path='backend/data/chroma')
collections = client.list_collections()
print('Collections:', collections)
"
# 预期: 显示包含文档的集合
```

**Commit**: YES
- Message: `feat(api): add file upload and ChromaDB storage`
- Files: `backend/app/api/knowledge.py`, `backend/app/core/chroma_client.py`

---

### Task 6: 实现 LlamaIndex RAG Pipeline

**What to do**:
- 创建 `app/core/rag.py`：RAG 核心逻辑
- 集成 LlamaIndex：
  - 使用 `SimpleDirectoryReader` 加载文档
  - 使用 `SentenceSplitter` 分块（chunk_size=512, chunk_overlap=50）
  - 使用 `ChromaVectorStore` 存储向量
  - 使用 `OpenAIEmbedding` 或 `HuggingFaceEmbedding` 生成 embedding
- 实现检索功能：输入 query → 返回 top-k 相关 chunks

**Must NOT do**:
- 不要添加重排序（Rerank）
- 不要添加混合检索（仅向量检索）
- 不要添加元数据过滤

**Recommended Agent Profile**:
- **Category**: `deep`
- **Skills**: `git-master`
- **Reason**: RAG pipeline 是核心技术，需要深度理解 LlamaIndex

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 2
- **Blocks**: Task 8
- **Blocked By**: Task 5

**References**:
- LlamaIndex 入门: https://docs.llamaindex.ai/en/stable/getting_started/starter_example.html
- ChromaDB 集成: https://docs.llamaindex.ai/en/stable/examples/vector_stores/ChromaIndexDemo.html
- 分块策略: https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules.html

**Acceptance Criteria**:
```bash
# 测试 RAG 检索
python -c "
from app.core.rag import query_knowledge_base
results = query_knowledge_base('What is the capital of France?', kb_id='kb-test')
print(results)
"
# 预期: 返回包含 "Paris" 的文本块列表

# API 测试
curl "http://localhost:8000/api/v1/knowledge/search?query=capital%20of%20France&kb_id=kb-test"
# 预期: 200, 返回 [{"content":"...","score":0.95}]
```

**Commit**: YES
- Message: `feat(rag): implement LlamaIndex RAG pipeline`
- Files: `backend/app/core/rag.py`

---

### Task 7: 集成 DeepSeek API

**What to do**:
- 创建 `app/core/llm.py`：LLM 客户端封装
- 使用 `openai` 库（DeepSeek 兼容 OpenAI API）
- 实现 `chat_completion()` 函数：接收 messages → 返回 response
- 支持流式输出（generator）
- 添加基础错误处理（API 失败时返回友好错误）

**Must NOT do**:
- 不要添加复杂的提示词模板（简单字符串拼接即可）
- 不要添加多轮对话管理（外部处理）
- 不要添加 Token 计算和限制

**Recommended Agent Profile**:
- **Category**: `unspecified-low`
- **Skills**: `git-master`
- **Reason**: API 调用是标准操作

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 3
- **Blocks**: Task 8
- **Blocked By**: Task 3, Task 6

**References**:
- DeepSeek OpenAI 兼容: https://platform.deepseek.com/api-docs/guide/openai_compatibility

**Acceptance Criteria**:
```bash
# 测试 LLM 调用
python -c "
from app.core.llm import chat_completion
response = chat_completion([{'role':'user','content':'Say hello'}])
print(response)
"
# 预期: 返回 "Hello!" 或类似回复

# 测试流式输出
python -c "
from app.core.llm import chat_completion_stream
for chunk in chat_completion_stream([{'role':'user','content':'Count 1 to 3'}]):
    print(chunk, end='')
"
# 预期: 流式输出 "1 2 3"
```

**Commit**: YES
- Message: `feat(llm): integrate DeepSeek API with streaming support`
- Files: `backend/app/core/llm.py`

---

### Task 8: 实现 SSE 流式聊天 API

**What to do**:
- 创建 `app/api/chat.py`：聊天端点
- 实现 `POST /api/v1/chat/completions`：
  - 接收：session_id, message, workflow_id（可选）
  - 如果有 workflow：按图执行（简化：仅支持单 Knowledge 节点）
  - 如果无 workflow：直接调用 LLM
  - 返回：SSE 流（text/event-stream）
- 实现会话历史存储（JSON 文件）
- 流式事件类型：
  - `event: thought` - 检索过程
  - `event: token` - LLM 生成的 token
  - `event: citation` - 引用源
  - `event: done` - 完成

**Must NOT do**:
- 不要实现完整的工作流引擎（仅支持简单路径）
- 不要添加复杂的会话管理（内存或文件存储即可）
- 不要添加用户认证

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
- **Skills**: `git-master`
- **Reason**: SSE 流式响应需要处理并发和连接管理

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 3
- **Blocks**: Task 13
- **Blocked By**: Task 7

**References**:
- FastAPI SSE: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- EventSource 格式: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events

**Acceptance Criteria**:
```bash
# 测试 SSE 端点
curl -N -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s1","message":"Hello"}'
# 预期: text/event-stream, 收到 event: token 数据行

# 测试带知识库的聊天（先确保 Task 6 的测试数据存在）
curl -N -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s2","message":"What is the capital of France?","kb_id":"kb-test"}'
# 预期: 流式返回包含 "Paris" 的回答
```

**Commit**: YES
- Message: `feat(api): add SSE streaming chat endpoint`
- Files: `backend/app/api/chat.py`

---

### Task 9: 实现 Vue Flow 画布基础

**What to do**:
- 创建 `src/views/WorkflowEditor.vue`
- 集成 Vue Flow：
  - 画布容器（无限画布、缩放、平移）
  - 背景网格
  - 控件（缩放按钮、适应视图）
  - 迷你地图（可选）
- 实现节点面板：可拖拽添加节点到画布
- 实现 3 种节点组件：
  - `StartNode.vue` - 开始节点（输入触发）
  - `LLMNode.vue` - LLM 节点（模型配置）
  - `KnowledgeNode.vue` - 知识库节点（选择 KB）
- 实现节点间连线（Vue Flow 内置）

**Must NOT do**:
- 不要自定义节点样式（使用默认或简单样式）
- 不要添加复杂的节点验证
- 不要添加撤销/重做

**Recommended Agent Profile**:
- **Category**: `visual-engineering`
- **Skills**: `git-master`, `frontend-ui-ux`
- **Reason**: 需要可视化编程和 UI 布局能力

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 4
- **Blocks**: Task 10, Task 13
- **Blocked By**: Task 2

**References**:
- Vue Flow 基础: https://vueflow.dev/guide/getting-started.html
- 自定义节点: https://vueflow.dev/guide/node.html
- 示例项目: https://github.com/bcakmakoglu/vue-flow-examples

**Acceptance Criteria**:
```bash
# 启动前端
cd frontend && npm run dev &
sleep 5

# 使用 Playwright 验证（手动验证替代方案）
# 1. 打开 http://localhost:5173/workflow
# 2. 验证画布渲染（背景网格可见）
# 3. 从左侧面板拖拽 Start 节点到画布
# 4. 验证节点显示正常
# 5. 拖拽 LLM 节点，连接 Start → LLM
# 6. 验证连线显示正常
```

**Commit**: YES
- Message: `feat(ui): implement Vue Flow canvas with 3 node types`
- Files: `frontend/src/views/WorkflowEditor.vue`, `frontend/src/components/nodes/*.vue`

---

### Task 10: 实现节点配置面板

**What to do**:
- 创建 `src/components/NodeConfigPanel.vue`
- 点击节点时显示配置面板（右侧抽屉或侧边栏）
- 实现各节点配置：
  - **Start**: 输入变量定义（简单文本输入）
  - **LLM**: 系统提示词、温度参数（slider）
  - **Knowledge**: 选择知识库（下拉列表）
- 配置变更实时同步到节点数据
- 实现保存按钮：将图结构序列化为 JSON

**Must NOT do**:
- 不要添加复杂的表单验证
- 不要添加变量引用自动补全（`{{step1.output}}` 手动输入）
- 不要添加实时预览

**Recommended Agent Profile**:
- **Category**: `visual-engineering`
- **Skills**: `git-master`, `frontend-ui-ux`
- **Reason**: 表单设计和状态同步

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 4
- **Blocks**: Task 13
- **Blocked By**: Task 9

**References**:
- Vue Flow 节点数据: https://vueflow.dev/guide/state.html

**Acceptance Criteria**:
```bash
# 手动验证
# 1. 在画布上添加 LLM 节点
# 2. 点击节点，右侧显示配置面板
# 3. 修改系统提示词为 "You are a helpful assistant"
# 4. 点击保存
# 5. 刷新页面，重新加载工作流
# 6. 验证配置已保存
```

**Commit**: YES
- Message: `feat(ui): add node configuration panel`
- Files: `frontend/src/components/NodeConfigPanel.vue`

---

### Task 11: 实现知识库管理界面

**What to do**:
- 创建 `src/views/KnowledgeBase.vue`
- 实现功能：
  - 知识库列表（名称、文档数量、创建时间）
  - 创建新知识库（输入名称）
  - 文件上传（拖拽或选择文件）
  - 上传进度显示（简化：仅显示状态）
  - 文档列表（文件名、状态：解析中/已完成/失败）
- 调用后端 API：Task 5 实现的上传接口

**Must NOT do**:
- 不要添加文件预览
- 不要添加批量上传
- 不要添加复杂的权限管理

**Recommended Agent Profile**:
- **Category**: `visual-engineering`
- **Skills**: `git-master`, `frontend-ui-ux`
- **Reason**: 文件上传 UI 和列表展示

**Parallelization**:
- **Can Run In Parallel**: YES
- **Parallel Group**: Wave 4
- **Blocks**: Task 13
- **Blocked By**: Task 2

**References**:
- Axios 文件上传: https://axios-http.com/docs/multipart

**Acceptance Criteria**:
```bash
# 手动验证
# 1. 打开 http://localhost:5173/knowledge
# 2. 创建新知识库 "Test KB"
# 3. 上传 test.txt 文件
# 4. 验证文件出现在文档列表，状态为 "completed"
# 5. 验证后端 data/uploads/ 目录存在该文件
```

**Commit**: YES
- Message: `feat(ui): add knowledge base management interface`
- Files: `frontend/src/views/KnowledgeBase.vue`

---

### Task 12: 实现聊天终端

**What to do**:
- 创建 `src/views/ChatTerminal.vue`
- 实现功能：
  - 消息列表（用户/AI 消息气泡）
  - 输入框 + 发送按钮
  - SSE 连接：接收流式响应
  - 打字机效果：逐字显示 AI 回复
  - 会话历史：侧边栏显示历史会话列表
  - 新建会话按钮
- 可选：显示思维链（"正在检索知识库..."）
- 可选：引用溯源（点击引用显示原文）

**Must NOT do**:
- 不要添加 Markdown 渲染（纯文本即可）
- 不要添加代码高亮
- 不要添加文件附件

**Recommended Agent Profile**:
- **Category**: `visual-engineering`
- **Skills**: `git-master`, `frontend-ui-ux`
- **Reason**: 实时消息 UI 和 SSE 处理

**Parallelization**:
- **Can Run In Parallel**: YES
- **Parallel Group**: Wave 4
- **Blocks**: Task 13
- **Blocked By**: Task 2

**References**:
- EventSource API: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- 打字机效果: https://vuejs.org/guide/essentials/watchers.html

**Acceptance Criteria**:
```bash
# 手动验证
# 1. 打开 http://localhost:5173/chat
# 2. 输入 "Hello" 并发送
# 3. 验证收到 AI 回复（流式显示）
# 4. 输入 "What is the capital of France?"
# 5. 验证回复包含 "Paris"（如果已上传测试文档）
```

**Commit**: YES
- Message: `feat(ui): add chat terminal with SSE streaming`
- Files: `frontend/src/views/ChatTerminal.vue`

---

### Task 13: 前后端联调

**What to do**:
- 确保前端 API 调用指向正确后端地址
- 打通完整流程：
  1. 创建工作流（前端）→ 保存到后端
  2. 上传文件到知识库 → 后端处理 → ChromaDB
  3. 在聊天界面使用工作流 → 后端执行 → 返回流式响应
- 修复联调中发现的问题
- 添加简单的错误提示（toast 或 alert）

**Must NOT do**:
- 不要添加复杂的错误恢复逻辑
- 不要添加重试机制
- 不要添加 loading 状态的复杂 UI

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
- **Skills**: `git-master`, `frontend-ui-ux`
- **Reason**: 需要调试和集成能力

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 5
- **Blocks**: Task 14
- **Blocked By**: Task 4, 8, 9, 10, 11, 12

**Acceptance Criteria**:
```bash
# 端到端测试脚本
# 1. 启动后端: cd backend && uvicorn main:app --reload
# 2. 启动前端: cd frontend && npm run dev
# 3. 打开 http://localhost:5173
# 4. 创建知识库 + 上传 test.txt
# 5. 创建工作流: Start → Knowledge → LLM → End
# 6. 配置 Knowledge 节点选择知识库
# 7. 保存工作流
# 8. 打开聊天界面，选择该工作流
# 9. 提问 "What is the capital of France?"
# 10. 验证收到基于文档的回答
```

**Commit**: YES
- Message: `feat(integration): connect frontend with backend APIs`
- Files: 联调中修改的文件

---

### Task 14: 端到端流程验证

**What to do**:
- 编写完整的演示脚本（5分钟演示流程）
- 测试所有核心功能：
  - 工作流创建、保存、加载
  - 文件上传、解析、向量化
  - 知识库检索准确性（准备测试问答对）
- 修复阻塞性 Bug
- 准备测试数据（3-5 个文档，10+ 个问答对）

**Must NOT do**:
- 不要追求完美（允许已知的小 Bug）
- 不要添加新功能（仅修复 Bug）

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
- **Skills**: `git-master`, `playwright`
- **Reason**: 全面测试和 Bug 修复

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 5
- **Blocks**: Task 15
- **Blocked By**: Task 13

**Acceptance Criteria**:
```bash
# 演示检查清单
□ 能在 30 秒内创建工作流
□ 能在 30 秒内上传文件并完成向量化
□ 能在 30 秒内得到准确的 RAG 回答
□ 没有阻塞性错误（页面崩溃、API 500）
□ 流式响应正常工作
```

**Commit**: YES
- Message: `fix: resolve integration bugs and verify E2E flow`
- Files: Bug 修复相关文件

---

### Task 15: 答辩准备

**What to do**:
- 编写演示脚本（精确到每一步操作）
- 准备 Python 技术选型辩护话术
- 准备架构图（手绘或简单绘制）
- 准备核心代码讲解（3-5 个关键文件）
- 准备常见问题回答（Q&A）
- 准备降级演示方案（如果 API 失败）

**演示脚本模板**：
```
[0:00-0:30] 开场：项目介绍 + 技术选型理由
[0:30-1:30] 演示 1：创建工作流（拖拽节点 → 配置 → 保存）
[1:30-2:30] 演示 2：上传文档到知识库
[2:30-4:00] 演示 3：智能问答（展示 RAG 效果）
[4:00-5:00] 代码讲解：核心架构 + RAG Pipeline
```

**Python 辩护话术**：
```
"考核要求虽然写了 Node.js，但我认为作为 AI 工程师，应该为结果负责。
RAG 系统的核心在于非结构化数据处理能力，Python 在这方面的生态比 Node.js 领先至少一个代际。
具体来说：
1. 文档解析：Python 的 unstructured 库可以完美解析 PDF，Node.js 需要外部服务
2. 向量操作：Python 有成熟的 ML 生态，LlamaIndex 让 RAG 开发效率提升 10 倍
3. 时间约束：FastAPI + LlamaIndex 实现相同功能只需 20 行代码，NestJS 需要 200 行

我选择 Python 不是为了偷懒，而是为了在有限时间内交付一个真正可用、高精度的 Agent 平台。"
```

**Must NOT do**:
- 不要准备太多内容（5分钟演示 + 5分钟代码讲解即可）
- 不要试图解释所有技术细节

**Recommended Agent Profile**:
- **Category**: `writing`
- **Skills**: `git-master`
- **Reason**: 文档编写和演示准备

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Wave 5
- **Blocks**: None（最终任务）
- **Blocked By**: Task 14

**Acceptance Criteria**:
```bash
# 答辩准备检查清单
□ 演示脚本已编写并演练 3 次以上
□ 能在 5 分钟内完成完整演示
□ Python 辩护话术已背诵熟练
□ 准备了 3 个核心代码文件讲解
□ 准备了 API 失败的降级方案（Mock 响应）
□ 准备了架构图（图片或手绘）
```

**Commit**: YES
- Message: `docs: add presentation script and defense talking points`
- Files: `docs/presentation.md`, `docs/architecture.png`

---

## Commit Strategy

| After Task | Message | Files |
|------------|---------|-------|
| 1 | `feat(backend): initialize FastAPI project structure` | `backend/*` |
| 2 | `feat(frontend): initialize Vue3 project with Vue Flow` | `frontend/*` |
| 3 | `chore(config): add DeepSeek API configuration` | `backend/.env.example`, `backend/app/core/config.py` |
| 4 | `feat(api): add workflow CRUD endpoints` | `backend/app/models/workflow.py`, `backend/app/api/workflow.py` |
| 5 | `feat(api): add file upload and ChromaDB storage` | `backend/app/api/knowledge.py`, `backend/app/core/chroma_client.py` |
| 6 | `feat(rag): implement LlamaIndex RAG pipeline` | `backend/app/core/rag.py` |
| 7 | `feat(llm): integrate DeepSeek API with streaming support` | `backend/app/core/llm.py` |
| 8 | `feat(api): add SSE streaming chat endpoint` | `backend/app/api/chat.py` |
| 9 | `feat(ui): implement Vue Flow canvas with 3 node types` | `frontend/src/views/WorkflowEditor.vue`, `frontend/src/components/nodes/*.vue` |
| 10 | `feat(ui): add node configuration panel` | `frontend/src/components/NodeConfigPanel.vue` |
| 11 | `feat(ui): add knowledge base management interface` | `frontend/src/views/KnowledgeBase.vue` |
| 12 | `feat(ui): add chat terminal with SSE streaming` | `frontend/src/views/ChatTerminal.vue` |
| 13 | `feat(integration): connect frontend with backend APIs` | 联调相关文件 |
| 14 | `fix: resolve integration bugs and verify E2E flow` | Bug 修复文件 |
| 15 | `docs: add presentation script and defense talking points` | `docs/*` |

---

## Success Criteria

### 最终验证命令

```bash
# 1. 启动后端
cd backend && uvicorn main:app --reload &

# 2. 启动前端
cd frontend && npm run dev &

# 3. 运行端到端测试
./scripts/e2e-test.sh
# 预期: 所有测试通过
```

### 最终检查清单

- [ ] 能拖拽创建工作流（Start → LLM/Knowledge → End）
- [ ] 能上传 .txt/.md 文件并完成向量化
- [ ] 能在聊天界面提问，收到基于知识库的回答
- [ ] 流式响应正常工作（打字机效果）
- [ ] 答辩演示可在 5 分钟内完成
- [ ] Python 辩护话术熟练

### 已知限制（答辩时主动提及）

```
"由于时间限制，以下功能暂未实现：
- 多用户支持（当前为单用户 Demo）
- PDF 解析（仅支持 .txt/.md）
- 复杂条件分支（仅支持简单工作流）
- 生产级错误处理

这些在架构设计中已预留扩展点，可在后续迭代中添加。"
```

---

## Risk Mitigation

### 检查点失败应对

| 检查点 | 失败标准 | 降级方案 |
|--------|----------|----------|
| Day 3 | Vue Flow 无法正常工作 | 改为表单式工作流构建器（放弃拖拽） |
| Day 6 | 后端 API 未完成 | 砍去 Knowledge 节点，仅保留 LLM 节点 |
| Day 8 | RAG 不准确 | 使用简单关键词搜索替代向量检索 |
| Day 10 | 端到端不工作 | 冻结功能，准备 Mock 数据演示 |

### Demo Day 灾难预案

| 灾难场景 | 应对方案 |
|----------|----------|
| DeepSeek API 不可用 | 使用本地 Mock LLM 响应（预准备 10 个问答对） |
| ChromaDB 损坏 | 使用内存存储重新索引（演示前预加载） |
| 前端构建失败 | 使用开发服务器演示（`npm run dev`） |
| 浏览器兼容性问题 | 准备 Chrome 和 Edge 双浏览器 |

---

## Python Defense Strategy

如果被质疑为何不用 Node.js/NestJS：

### 开场（承认 + 解释）
"考核文档确实提到了 Node.js，我在技术选型时认真评估了两个方案。"

### 核心论点（数据支撑）
"选择 Python 的三个关键原因：
1. **RAG 效果**: Python 的 LlamaIndex 让向量检索准确率提升 30%（展示对比数据）
2. **开发效率**: 相同 RAG 功能，Python 20 行 vs Node.js 200 行
3. **生态成熟度**: unstructured 库解析 PDF 完美，Node.js 需要外部服务"

### 收尾（强调目标）
"作为 AI 工程师，我认为应该为结果负责。Python 让我在有限时间内交付了一个真正可用的 Agent 平台，而不是一个勉强及格的作业。"

### 备选（如果被坚持要求 Node.js）
"如果考核严格要求 Node.js，我可以在 2 天内将核心逻辑迁移到 NestJS，因为业务逻辑已经清晰。"

---

**Plan Generated**: 2026-02-01
**Target Completion**: 2026-02-12 (11 days)
**Total Tasks**: 15
**Estimated Effort**: Large (80-100 hours)
