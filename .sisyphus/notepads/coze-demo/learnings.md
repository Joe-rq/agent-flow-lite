# DeepSeek API 配置学习笔记

## 完成的工作
- 创建了 `backend/.env.example` 模板文件，包含 DeepSeek API 配置说明
- 创建了 `backend/app/core/config.py`，使用 pydantic-settings 加载环境变量
- 创建了 `backend/.env` 示例配置文件
- 更新了 `.gitignore` 确保 `.env` 文件不被提交
- 添加了必要的依赖：pydantic-settings, httpx
- 创建了 `test_deepseek.py` 测试脚本

## 关键配置
```python
# config.py 使用 pydantic-settings
class Settings(BaseSettings):
    deepseek_api_key: str = Field(default="")
    deepseek_model: str = Field(default="deepseek-chat")
    deepseek_api_base: str = Field(default="https://api.deepseek.com")
```

## API 端点验证
- API Base URL: `https://api.deepseek.com/chat/completions`
- 使用的模型: `deepseek-chat`
- API 格式兼容 OpenAI 标准

## 注意事项
1. API Key 从环境变量加载，不会硬编码在代码中
2. .env 文件被正确添加到 .gitignore
3. 测试脚本会检查 key 是否为示例值并给出提示

## 待办
- 用户需要从 https://platform.deepseek.com/api_keys 获取真实的 API Key
- 配置完成后可解锁 Task 7

---

# Vue3 前端项目初始化学习笔记

## 完成的工作
- 创建 `frontend/` 目录
- 使用 `npm create vue@latest` 初始化项目（TypeScript + Pinia + Vue Router）
- 安装 Vue Flow 依赖：`@vue-flow/core`, `@vue-flow/background`, `@vue-flow/controls`
- 安装 axios
- 配置 vite.config.ts 代理到后端 8000 端口
- 创建基础布局组件：App.vue（Header + Sidebar + Main Content）
- 创建路由：`/`, `/workflow`, `/knowledge`, `/chat`
- 验证开发服务器能正常启动

## 项目结构
```
frontend/
├── src/
│   ├── App.vue          # 基础布局组件
│   ├── router/index.ts  # 路由配置
│   ├── views/           # 页面视图
│   │   ├── HomeView.vue
│   │   ├── WorkflowView.vue
│   │   ├── KnowledgeView.vue
│   │   └── ChatView.vue
│   └── ...
├── vite.config.ts       # Vite 配置（含代理）
└── package.json         # 依赖（含 Vue Flow）
```

## 关键配置
```typescript
// vite.config.ts 代理配置
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

## 依赖版本
- Vue Flow: 1.48.2
- Axios: 1.13.4
- Vite: 内置于 create-vue 模板

## 待办
- Task 9: 集成 Vue Flow 可视化工作流编辑器
- Task 10: 创建 API 服务层（axios 封装）
- Task 11: 实现知识库页面（KnowledgeView）
- Task 12: 实现对话页面（ChatView）

---

# FastAPI 后端项目初始化学习笔记

## 完成的工作
- 创建 `backend/` 目录
- 使用 `uv init` 初始化 Python 项目（Python 3.11）
- 创建 FastAPI 标准项目结构：`app/api/`, `app/core/`, `app/models/`
- 安装依赖：fastapi, uvicorn, llama-index, chromadb, python-multipart, python-dotenv
- 创建 `main.py` 入口文件，配置 CORS 和基础路由（/, /health）
- 创建 `.env.example` 配置文件模板
- 创建 `.gitignore` 排除 .env, __pycache__, .venv 等
- 验证服务能启动并访问 `/docs`

## 项目结构
```
backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   └── __init__.py
│   └── models/
│       └── __init__.py
├── main.py              # FastAPI 应用入口
├── .env.example         # 环境变量模板
├── .gitignore
├── pyproject.toml       # uv 项目配置
├── uv.lock
└── README.md
```

## 关键配置
```python
# main.py - FastAPI 应用配置
def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent Flow Lite API",
        description="Backend API for Agent Flow Lite",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS 配置
    origins = os.getenv("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app
```

## 依赖版本
- FastAPI: 0.128.0
- Uvicorn: 0.40.0
- Llama-Index: 0.14.13
- ChromaDB: 1.4.1
- Python: 3.11.11

## 验证结果
- ✅ 依赖导入成功
- ✅ 服务启动成功（http://127.0.0.1:8000）
- ✅ /docs 端点可访问（Swagger UI）

## 启动方式
```bash
cd backend
uv run uvicorn main:app --reload
# 访问 http://localhost:8000/docs 查看 API 文档
```

## 待办
- Task 4: 集成 DeepSeek API（已存在，可跳过）
- Task 5: 集成 LlamaIndex RAG
- Task 6: 集成 ChromaDB 向量存储
- Task 7: 实现对话 API
- Task 8: 实现知识库 API

---

# Task 4: 工作流 CRUD API 学习笔记

## 完成的工作
- 创建 `backend/app/models/workflow.py`：Workflow Pydantic 模型
  - Workflow, WorkflowCreate, WorkflowUpdate, GraphData 模型
  - 包含 id, name, description, graph_data, created_at, updated_at 字段
  - graph_data 存储 Vue Flow 的节点和边数据
- 创建 `backend/app/api/workflow.py`：CRUD 端点
  - GET /api/v1/workflows - 列表
  - POST /api/v1/workflows - 创建
  - GET /api/v1/workflows/{id} - 详情
  - PUT /api/v1/workflows/{id} - 更新
  - DELETE /api/v1/workflows/{id} - 删除
- 修改 `backend/main.py`：注册 workflow 路由
- 使用 JSON 文件存储（data/workflows.json）
- 添加适当的错误处理（404, 400）

## API 端点验证结果
```bash
# 创建工作流 - 201 Created
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"A test","graph_data":{"nodes":[],"edges":[]}}'

# 列表 - 200 OK
curl http://localhost:8000/api/v1/workflows

# 详情 - 200 OK
curl http://localhost:8000/api/v1/workflows/{id}

# 更新 - 200 OK
curl -X PUT http://localhost:8000/api/v1/workflows/{id} \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated"}'

# 删除 - 204 No Content
curl -X DELETE http://localhost:8000/api/v1/workflows/{id}
```

## 技术要点
1. **Pydantic v2 模型**：使用 Field 定义验证规则
2. **UUID 生成**：使用 uuid.uuid4() 生成唯一 ID
3. **JSON 文件存储**：简单的文件读写操作
4. **FastAPI 路由注册**：使用 APIRouter 和 include_router

## 遇到的问题
1. **uvicorn 路径问题**：
   - 使用 `uv run uvicorn main:app` 时从错误的目录运行
   - 解决方案：确保从 `backend` 目录运行，或使用 `DEBUG=0` 禁用 reload

2. **相对导入问题**：
   - `from app.api.workflow import router` 需要正确的 PYTHONPATH
   - 解决方案：在 backend 目录下运行，并确保 `app/__init__.py` 存在

## Git 提交
- Message: `feat(api): add workflow CRUD endpoints`
- Files: `backend/app/models/workflow.py`, `backend/app/api/workflow.py`, `backend/main.py`

## 待办
- Task 5: 实现文件上传 + ChromaDB 集成（解锁）

---

# Task 6: LlamaIndex RAG Pipeline 实现学习笔记

## 完成的工作
- 创建 `backend/app/core/rag.py`：RAG 核心逻辑
  - 使用 LlamaIndex 的 Document 和 SentenceSplitter 进行文本分块
  - 使用 HuggingFace BAAI/bge-small-zh-v1.5 本地 embedding 模型（避免依赖 OpenAI API）
  - chunk_size=512, chunk_overlap=50
  - 存储到 ChromaDB，metadata 包含 doc_id 和 chunk_index
  - 检索功能返回 top-k 相关 chunks

- 更新 `backend/app/api/knowledge.py`：
  - POST /api/v1/knowledge/{kb_id}/process/{doc_id} - 处理文档（后台任务）
  - GET /api/v1/knowledge/{kb_id}/search?query=xxx - 检索测试
  - 文档状态更新：pending → processing → completed/error

## 技术要点

### 1. HuggingFace Embedding 模型
```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")
```
- BAAI/bge-small-zh-v1.5 是轻量级多语言模型，支持中英文
- 首次使用时会自动下载模型（约 100MB）
- 无需 OpenAI API Key，完全本地运行

### 2. SentenceSplitter 分块
```python
from llama_index.core.node_parser import SentenceSplitter

node_parser = SentenceSplitter(
    chunk_size=512,
    chunk_overlap=50,
)
```
- 按句子边界分块，避免截断句子
- chunk_overlap 保证上下文连贯性

### 3. ChromaDB 集成
- 每个知识库使用独立的 collection（kb_{kb_id}）
- 存储时包含 embedding、文本、metadata
- chunk ID 格式：{doc_id}_chunk_{index}

### 4. 后台任务处理
```python
from fastapi import BackgroundTasks

@router.post("/{kb_id}/process/{doc_id}")
async def process_document(
    kb_id: str,
    doc_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_document_task, kb_id, doc_id)
    return JSONResponse(
        content={"message": "Document processing started.", "doc_id": doc_id},
        status_code=status.HTTP_202_ACCEPTED
    )
```
- 使用 FastAPI BackgroundTasks 异步处理文档
- 避免长时间处理阻塞 HTTP 请求
- 状态实时更新到 metadata JSON 文件

## API 验证结果

```bash
# 处理文档
curl -X POST http://localhost:8000/api/v1/knowledge/kb-test/process/832143e9-4ae9-46f7-91b2-518be7901ede
# Response: {"message": "Document processing started.", "doc_id": "..."}

# 搜索测试
curl "http://localhost:8000/api/v1/knowledge/kb-test/search?query=capital%20of%20France"
# Response: 返回包含 "Paris" 的文本块，score: 0.4697
```

## 依赖安装
```bash
uv pip install llama-index-embeddings-huggingface transformers torch
```

## 注意事项
1. 首次运行需要下载 embedding 模型（约 100MB），耗时约 30-60 秒
2. 模型缓存在本地，后续启动更快
3. 仅支持 .txt 和 .md 文件（按需求）
4. 每个 chunk 独立存储，支持精确删除文档

## 解锁
- Task 8: 聊天 API 可以使用 RAG 检索功能
