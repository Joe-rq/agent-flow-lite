# Backend - FastAPI 后端服务

Agent Flow Lite 的 FastAPI 后端服务，提供工作流编排、知识库管理和智能对话 API。

## 🏗️ 技术架构

### 核心框架
- **FastAPI** - 现代化 Python Web 框架
- **Pydantic** - 数据验证和序列化
- **Uvicorn** - ASGI 服务器

### AI 能力
- **LlamaIndex** - RAG 框架和文档索引
- **ChromaDB** - 向量数据库（本地持久化）
- **DeepSeek API** - LLM 对话服务
- **SiliconFlow API** - 文本向量化服务

### 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── chat.py           # 智能对话接口（SSE 流式）
│   │   ├── knowledge.py      # 知识库管理接口
│   │   └── workflow.py       # 工作流编排接口
│   ├── core/             # 核心逻辑
│   │   ├── config.py         # 配置管理
│   │   ├── llm.py            # LLM 客户端封装
│   │   ├── rag.py            # RAG 管道实现
│   │   ├── workflow_engine.py # 工作流执行引擎
│   ├── models/           # Pydantic 数据模型
│   └── main.py           # 应用入口
│
├── tests/                 # 测试套件
│   ├── test_smoke.py          # 健康检查
│   └── test_chat_citation.py  # 引用功能测试
│
├── data/                  # 运行时数据（不提交）
│   ├── uploads/              # 上传文档
│   ├── metadata/             # 知识库元数据
│   ├── sessions/             # 会话历史
│   └── chromadb/             # ChromaDB 向量存储
│
├── .env.example           # 环境变量模板
├── pyproject.toml         # 项目配置和依赖
└── uv.lock               # 依赖锁定文件
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python >= 3.11 和 uv：

```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv
```

### 2. 安装依赖

```bash
# 安装项目依赖（开发模式）
uv pip install -e .
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入 API Keys
```

**必需配置：**
```env
# DeepSeek API（LLM）
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# SiliconFlow API（Embedding）
SILICONFLOW_API_KEY=sk-xxxxx
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
```

**可选配置：**
```env
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

### 4. 启动服务

```bash
# 开发模式（热重载）
uv run uvicorn main:app --reload

# 生产模式
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 访问服务

| 服务 | 地址 |
|------|------|
| Swagger UI (API 文档) | http://localhost:8000/docs |
| ReDoc (替代文档) | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| 健康检查 | http://localhost:8000/health |

## 🧪 测试

### 运行所有测试

```bash
uv run pytest -q
```

### 运行单个测试文件

```bash
uv run pytest tests/test_chat_citation.py -q

### Watch 模式（自动重新运行）

```bash
uv run pytest tests/test_chat_citation.py -q --watch
```

### 测试覆盖率

```bash
uv run pytest
uv run pytest --cov=app --cov-report=html
```

## 📝 API 说明

### 1. 智能对话 (`/api/v1/chat/completions`)

支持 RAG 检索、工作流执行和长期记忆的流式对话接口。

**请求示例：**
```json
{
  "message": "用户问题",
  "session_id": "session-123",
  "kb_id": "kb-456",
  "workflow_id": "workflow-789",
  "user_id": "user-001"
}
```

**SSE 事件流：**
- `thought` - 思维链信息
- `token` - LLM 生成的字符
- `citation` - 引用源信息
- `done` - 完成状态

### 2. 知识库管理 (`/api/v1/knowledge/*`)

- POST `/upload` - 上传文档到知识库
- GET `/` - 获取所有知识库
- DELETE `/{kb_id}` - 删除知识库

### 3. 工作流编排 (`/api/v1/workflows/*`)

- GET `/` - 获取所有工作流
- POST `/` - 创建/保存工作流
- DELETE `/{workflow_id}` - 删除工作流
- POST `/{workflow_id}/run` - 运行工作流

## 🔧 核心模块说明

### RAG 管道 (`app/core/rag.py`)

处理文档分块、向量化和检索。

**流程：**
```
文档上传 → 文本解析 → 分块处理 → 向量化 → ChromaDB 存储
```

**特点：**
- LlamaIndex SentenceSplitter（512 tokens，50 overlap）
- SiliconFlow BGE-M3 向量模型
- Top-K 相似度检索

### 工作流引擎 (`app/core/workflow_engine.py`)

执行可视化工作流逻辑。

**执行流程：**
```
图结构解析 → BFS 遍历 → 节点执行 → 数据流转
```

**支持节点：**
- Start - 工作流入口
- LLM - 调用大语言模型
- Knowledge - 检索知识库
- Condition - 条件分支
- End - 工作流出口

## 🐛 常见问题

<details>
<summary>ChromaDB 初始化失败</summary>

**错误**: `chromadb.errors.InvalidDimensionException`

**解决**:
```bash
rm -rf backend/data/chromadb/
# 重新上传文档建立索引
```
</details>

<details>
<summary>API Key 错误</summary>

**错误**: `401 Unauthorized` 或 `Invalid API Key`

**解决**:
1. 检查 `.env` 文件是否正确配置
2. 确认 API Key 格式（通常以 `sk-` 开头）
3. 访问对应平台确认 Key 有效
4. 重启后端服务
</details>

</details>

## 📚 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [DeepSeek API](https://platform.deepseek.com/docs)
- [SiliconFlow API](https://docs.siliconflow.cn/)
