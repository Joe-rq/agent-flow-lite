# Agent Flow Lite

一个轻量级、高还原度的智能体编排平台，支持可视化工作流编排、RAG 知识检索和智能对话。

![Vue 3](https://img.shields.io/badge/Vue%203-4FC08D?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

> 🚀 一个展示现代 AI 应用开发模式的全栈项目，集成了 LLM、RAG、工作流编排等核心能力。

## 核心特性

- **可视化工作流引擎** - 基于 Vue Flow 的拖拽式节点编排，支持 LLM、知识库、条件分支等多种节点类型
- **RAG 知识管理** - 支持文档上传、自动分块、向量索引和语义检索
- **智能对话终端** - 流式响应 (SSE)、多轮会话、引用溯源
- **全栈架构** - Vue 3 + FastAPI 的现代化技术栈

## 技术栈

### 前端
- **框架**: Vue 3 + Vite + TypeScript
- **状态管理**: Pinia
- **工作流引擎**: Vue Flow (@vue-flow/core)
- **HTTP 客户端**: Axios
- **代码规范**: ESLint + OXLint + Prettier

### 后端
- **框架**: FastAPI + Python 3.11+
- **AI/RAG**: LlamaIndex + ChromaDB
- **LLM**: DeepSeek API (chat completions)
- **Embedding**: SiliconFlow API (BGE-M3)
- **包管理**: uv

## 快速开始

### 环境要求

- **Node.js**: ^20.19.0 或 >=22.12.0
- **Python**: >=3.11
- **uv**: Python 包管理工具 ([安装指南](https://github.com/astral-sh/uv))

### 安装与启动

#### 方式 1: 一键脚本（推荐）

```bash
# 1. 安装所有依赖
./install.sh

# 2. 配置环境变量（首次运行必须）
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Keys

# 3. 启动服务
./start.sh
```

#### 方式 2: 手动启动

```bash
# 前端（终端 1）
cd frontend
npm install
npm run dev

# 后端（终端 2）
cd backend
uv venv                    # 创建虚拟环境
uv pip install -e .        # 安装依赖
cp .env.example .env       # 配置环境变量
uv run uvicorn main:app --reload
```

#### 访问应用

- **前端**: http://localhost:5173
- **后端 API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 项目结构

```
agent-flow-lite/
├── frontend/          # Vue 3 前端应用
│   ├── src/
│   │   ├── views/     # 页面视图
│   │   ├── stores/    # Pinia 状态管理
│   │   └── assets/    # 静态资源
│   └── package.json
├── backend/           # FastAPI 后端服务
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── core/      # 核心逻辑 (RAG, LLM)
│   │   └── models/    # Pydantic 模型
│   ├── data/          # 运行时数据
│   └── pyproject.toml
├── prd.md             # 产品需求文档
└── AGENTS.md          # 开发规范
```

## 开发指南

### 前端开发

```bash
cd frontend

# 开发服务器（热重载）
npm run dev

# 运行测试
npm run test

# 测试 UI 界面
npm run test:ui

# 类型检查
npm run type-check

# 代码检查和自动修复
npm run lint

# 代码格式化
npm run format

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

### 后端开发

```bash
cd backend

# 安装依赖（开发模式）
uv pip install -e .

# 开发服务器（热重载）
uv run uvicorn main:app --reload

# 手动测试 API
uv run python test_chat_api.py
uv run python test_deepseek.py
```

### 代码规范

- **前端**: 使用 Prettier + ESLint + OXLint，运行 `npm run lint` 自动修复
- **后端**: 遵循 PEP 8，使用类型提示，添加文档字符串
- **提交**: 遵循 Conventional Commits 规范（如 `feat:`, `fix:`, `docs:`）

## 配置说明

### 后端环境变量

复制 `backend/.env.example` 为 `backend/.env`，并配置以下必需项：

```env
# DeepSeek API 配置（必需 - 用于 LLM 对话）
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# SiliconFlow API 配置（必需 - 用于文本向量化）
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

# 服务器配置（可选）
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

### 获取 API Keys

- **DeepSeek API**: 访问 [DeepSeek 平台](https://platform.deepseek.com/) 注册并获取 API Key
- **SiliconFlow API**: 访问 [SiliconFlow 平台](https://siliconflow.cn/) 注册并获取 API Key

## API 文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心功能模块

### 1. 可视化工作流引擎

基于 Vue Flow 的拖拽式节点编排系统：

- ✨ **无限画布**: 支持拖拽、缩放、平移操作
- 🎨 **节点类型**: Start/End、LLM、Knowledge、Condition
- 🔗 **数据流转**: 通过变量引用（如 `{{step1.output}}`）传递数据
- 🌊 **流式执行**: BFS 图遍历，支持条件分支
- 💾 **持久化**: 工作流定义存储为 JSON

### 2. RAG 知识管理系统

完整的文档处理和检索流程：

- 📄 **文档上传**: 支持 .txt、.md 格式
- ✂️ **智能分块**: 使用 LlamaIndex SentenceSplitter（512 tokens，50 overlap）
- 🧮 **向量化**: SiliconFlow BGE-M3 embedding 模型
- 🗄️ **向量存储**: ChromaDB 持久化存储
- 🔍 **语义检索**: Top-K 相似度搜索，返回相关文档片段

### 3. 智能对话终端

流式 AI 对话体验：

- 💬 **多轮对话**: 自动会话管理，历史记录持久化
- ⚡ **SSE 流式**: 打字机效果，实时显示 AI 回复
- 🧠 **思维链**: 展示 RAG 检索过程和工作流执行状态
- 📚 **引用溯源**: 显示知识库来源，支持点击查看原文
- 🔄 **三种模式**: 简单对话、RAG 增强对话、工作流执行

## 技术架构

### 后端架构

```
backend/
├── main.py                    # FastAPI 应用入口
├── app/
│   ├── api/                   # API 路由层
│   │   ├── chat.py           # SSE 流式对话接口
│   │   ├── knowledge.py      # 知识库管理接口
│   │   └── workflow.py       # 工作流 CRUD 接口
│   ├── core/                  # 核心业务逻辑
│   │   ├── rag.py            # RAG 管道（分块、向量化、检索）
│   │   ├── llm.py            # DeepSeek API 客户端
│   │   ├── workflow_engine.py # 工作流执行引擎
│   │   ├── workflow_nodes.py  # 节点执行器
│   │   ├── chroma_client.py   # ChromaDB 客户端
│   │   └── config.py          # 配置管理
│   └── models/                # Pydantic 数据模型
└── data/                      # 运行时数据
    ├── uploads/              # 上传的文档
    ├── metadata/             # 知识库元数据
    ├── sessions/             # 对话会话历史
    └── chromadb/             # 向量数据库
```

### 关键技术点

- **SSE 流式传输**: 使用 FastAPI `StreamingResponse` + EventSource 实现实时响应
- **工作流引擎**: BFS 图遍历 + 异步生成器，支持条件分支和变量传递
- **RAG 管道**: LlamaIndex 分块 → SiliconFlow 向量化 → ChromaDB 检索
- **会话管理**: JSON 文件持久化 + FileLock 并发控制

## 文档

- 📋 [产品需求文档](./prd.md) - 详细功能规格说明
- 🤖 [AGENTS.md](./AGENTS.md) - 开发规范与指南
- 🧑‍💻 [CLAUDE.md](./CLAUDE.md) - Claude Code 使用指南

## 常见问题

### 1. ChromaDB 初始化失败

**问题**: `chromadb.errors.InvalidDimensionException`

**解决**: 删除 `backend/data/chromadb/` 目录，重新上传文档建立索引。

### 2. SSE 流式响应不工作

**问题**: 前端收不到流式数据

**解决**:
- 检查后端是否正常运行（http://localhost:8000/health）
- 确保 CORS 配置正确
- 如果使用 Nginx，添加 `X-Accel-Buffering: no` 头

### 3. API Key 错误

**问题**: `401 Unauthorized` 或 `Invalid API Key`

**解决**:
- 确认 `backend/.env` 文件存在且配置正确
- 检查 API Key 是否有效（访问对应平台确认）
- 重启后端服务使配置生效

### 4. 前端代理错误

**问题**: `ECONNREFUSED` 或 `502 Bad Gateway`

**解决**: 确保后端服务运行在 8000 端口，前端 Vite 配置了正确的代理。

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- 遵循现有代码风格（前端: Prettier + ESLint，后端: PEP 8）
- 添加必要的注释和文档字符串
- 提交前运行测试和代码检查
- 使用 Conventional Commits 规范编写提交信息

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 相关链接

- [Vue Flow 文档](https://vueflow.dev/) - 工作流画布组件
- [FastAPI 文档](https://fastapi.tiangolo.com/) - 后端框架
- [LlamaIndex 文档](https://docs.llamaindex.ai/) - RAG 框架
- [ChromaDB 文档](https://docs.trychroma.com/) - 向量数据库
- [DeepSeek API](https://platform.deepseek.com/docs) - LLM API
- [SiliconFlow API](https://docs.siliconflow.cn/) - Embedding API

## 致谢

感谢以下开源项目：

- Vue.js 团队和社区
- FastAPI 和 Starlette
- LlamaIndex 和 ChromaDB
- 所有依赖库的维护者

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
