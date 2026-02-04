# Agent Flow Lite

一个轻量级、高还原度的智能体编排平台，支持可视化工作流编排、RAG 知识检索和智能对话。

![Vue 3](https://img.shields.io/badge/Vue%203-4FC08D?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## ✨ 核心特性

- 🎨 **可视化工作流** - 拖拽式节点编排，支持 LLM、知识库、条件分支
- 📚 **RAG 知识管理** - 文档上传、智能分块、向量检索
- 💬 **智能对话终端** - SSE 流式响应、多轮会话、引用溯源
- 🧠 **长期记忆** - 集成 Zep 云服务，跨会话记忆持久化
- ⚡ **现代化技术栈** - Vue 3 + FastAPI + LlamaIndex + ChromaDB

---

## 🚀 快速开始

### 1. 环境准备

确保已安装以下工具：

| 工具 | 版本要求 | 安装指南 |
|------|---------|---------|
| Node.js | ^20.19.0 或 >=22.12.0 | [nodejs.org](https://nodejs.org/) |
| Python | >=3.11 | [python.org](https://www.python.org/) |
| uv | 最新版 | [astral.sh/uv](https://github.com/astral-sh/uv) |

### 2. 获取 API Keys

本项目需要以下 API 服务：

- **DeepSeek API** - 用于 LLM 对话 → [注册获取](https://platform.deepseek.com/)
- **SiliconFlow API** - 用于文本向量化 → [注册获取](https://siliconflow.cn/)
- **Zep Cloud** - 长期记忆存储（可选）→ [注册获取](https://www.getzep.com/)

### 3. 安装与配置

#### 方式一：一键脚本（推荐）

```bash
# 克隆仓库
git clone https://github.com/Joe-rq/agent-flow-lite.git
cd agent-flow-lite

# 安装依赖
./install.sh

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Keys

# 启动服务
./start.sh
```

#### 方式二：手动安装

```bash
# 前端
cd frontend
npm install

# 后端
cd backend
uv venv
uv pip install -e .
cp .env.example .env
# 编辑 .env 文件
```

**环境变量配置** (`backend/.env`)：

```env
# DeepSeek API（必需）
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# SiliconFlow API（必需）
SILICONFLOW_API_KEY=sk-xxxxx
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

# Zep Cloud（可选 - 长期记忆）
ZEP_API_KEY=sk-xxxxx
ZEP_URL=https://api.getzep.com

# 服务器配置（可选）
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

### 4. 启动应用

```bash
# 启动前端（终端 1）
cd frontend
npm run dev

# 启动后端（终端 2）
cd backend
uv run uvicorn main:app --reload
```

### 5. 访问应用

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:5173 | 主界面 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 服务状态 |

---

## 📖 使用指南

### 工作流编排

1. 进入「工作流」页面
2. 点击「新建工作流」
3. 从左侧拖拽节点到画布
4. 连接节点，配置参数
5. 保存并测试工作流

**支持的节点类型**：
- **Start** - 工作流入口
- **LLM** - 调用大语言模型
- **Knowledge** - 检索知识库
- **Condition** - 条件分支
- **End** - 工作流出口

### 知识库管理

1. 进入「知识库」页面
2. 创建新知识库
3. 上传文档（支持 .txt、.md）
4. 系统自动分块和向量化
5. 在对话中引用知识库

### 智能对话

1. 进入「对话」页面
2. 选择知识库或工作流（可选）
3. 输入问题，实时获取回复
4. 查看思维链和引用来源
5. 点击「引用」按钮查看详细来源信息和文本摘录

---

## 🏗️ 技术架构

### 技术栈

**前端**
- Vue 3 + Vite + TypeScript
- Vue Flow（工作流画布）
- Pinia（状态管理）
- Axios（HTTP 客户端）

**后端**
- FastAPI + Python 3.11+
- LlamaIndex（RAG 框架）
- ChromaDB（向量数据库）
- DeepSeek API（LLM）
- SiliconFlow API（Embedding）

### 项目结构

```
agent-flow-lite/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── stores/       # 状态管理
│   │   └── assets/       # 静态资源
│   └── package.json
│
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   │   ├── chat.py           # 对话接口
│   │   │   ├── knowledge.py      # 知识库接口
│   │   │   └── workflow.py       # 工作流接口
│   │   ├── core/         # 核心逻辑
│   │   │   ├── rag.py            # RAG 管道
│   │   │   ├── llm.py            # LLM 客户端
│   │   │   ├── workflow_engine.py # 工作流引擎
│   │   │   ├── zep.py            # Zep 记忆客户端
│   │   │   └── config.py         # 配置管理
│   │   └── models/       # 数据模型
│   ├── tests/              # 测试套件
│   │   ├── test_smoke.py          # 健康检查
│   │   ├── test_zep_client.py     # Zep 客户端测试
│   │   ├── test_chat_zep.py       # 聊天集成测试
│   │   └── test_chat_citation.py  # 引用功能测试
│   ├── data/             # 运行时数据
│   │   ├── uploads/      # 上传文档
│   │   ├── metadata/     # 知识库元数据
│   │   ├── sessions/     # 会话历史
│   │   └── chromadb/     # 向量数据
│   └── main.py           # 应用入口
│
├── CLAUDE.md             # Claude Code 指南
├── AGENTS.md             # 开发规范
└── prd.md                # 产品需求文档
```

### 核心模块

#### 1. RAG 管道

```
文档上传 → 文本分块 → 向量化 → 存储 → 检索
         (512 tokens)  (BGE-M3)  (ChromaDB)
```

- **分块策略**: LlamaIndex SentenceSplitter（512 tokens，50 overlap）
- **向量模型**: SiliconFlow BGE-M3
- **存储引擎**: ChromaDB 持久化
- **检索方式**: Top-K 相似度搜索

#### 2. 工作流引擎

```
图结构解析 → BFS 遍历 → 节点执行 → 数据流转
```

- **执行模式**: 异步生成器 + 事件流
- **数据传递**: 变量引用（`{{step1.output}}`）
- **分支控制**: 条件节点 + sourceHandle 路由
- **持久化**: JSON 文件存储

#### 3. SSE 流式对话

```
用户输入 → RAG 检索 → Zep 记忆 → LLM 生成 → SSE 推送 → 前端渲染
```

- **协议**: Server-Sent Events
- **事件类型**: thought（思维链）、token（内容）、citation（引用）、done（完成）
- **会话管理**: JSON 文件 + FileLock 并发控制

#### 4. Zep 长期记忆

```
消息同步 → 记忆存储 → 上下文检索 → 跨会话记忆
      (Zep Cloud)  (Semantic Search)  (Embedding)
```

- **记忆存储**: Zep Cloud 服务
- **检索策略**: 语义相似度搜索
- **会话持久化**: 用户级别的跨会话记忆
- **配置**: 通过 `.env` 文件配置 `ZEP_API_KEY` 和 `ZEP_URL`

---

## 💻 开发指南

### 前端开发

```bash
cd frontend

npm run dev          # 开发服务器
npm run test         # 运行测试
npm run test:ui      # 测试 UI
npm run type-check   # 类型检查
npm run lint         # 代码检查
npm run format       # 代码格式化
npm run build        # 生产构建
```

### 后端开发

```bash
cd backend

uv pip install -e .              # 安装依赖
uv run uvicorn main:app --reload # 开发服务器
uv run python test_chat_api.py   # 测试 API
```

### 代码规范

- **前端**: Prettier + ESLint + OXLint
- **后端**: PEP 8 + 类型提示 + 文档字符串
- **提交**: Conventional Commits（`feat:`, `fix:`, `docs:`）

### 添加新功能

**添加工作流节点类型**：
1. 在 `backend/app/core/workflow_nodes.py` 添加执行函数
2. 在 `backend/app/core/workflow_engine.py` 注册节点类型
3. 在 `frontend/src/views/WorkflowEditor.vue` 添加节点配置

**扩展 RAG 管道**：
1. 修改 `backend/app/core/rag.py` 中的分块或检索逻辑
2. 更新 `backend/app/api/knowledge.py` 中的接口
3. 调整前端 `KnowledgeView.vue` 的 UI

---

## ❓ 常见问题

<details>
<summary><strong>ChromaDB 初始化失败</strong></summary>

**错误**: `chromadb.errors.InvalidDimensionException`

**原因**: 向量维度不匹配或数据损坏

**解决**:
```bash
rm -rf backend/data/chromadb/
# 重新上传文档建立索引
```
</details>

<details>
<summary><strong>SSE 流式响应不工作</strong></summary>

**症状**: 前端收不到流式数据

**排查步骤**:
1. 检查后端服务: `curl http://localhost:8000/health`
2. 检查 CORS 配置: `backend/.env` 中的 `CORS_ORIGINS`
3. 如使用 Nginx: 添加 `proxy_buffering off;`
</details>

<details>
<summary><strong>API Key 错误</strong></summary>

**错误**: `401 Unauthorized` 或 `Invalid API Key`

**解决**:
1. 确认 `backend/.env` 文件存在
2. 检查 API Key 格式（通常以 `sk-` 开头）
3. 访问对应平台确认 Key 有效
4. 重启后端服务
</details>

<details>
<summary><strong>前端代理错误</strong></summary>

**错误**: `ECONNREFUSED` 或 `502 Bad Gateway`

**原因**: 后端服务未启动或端口不匹配

**解决**:
1. 确保后端运行在 8000 端口
2. 检查 `frontend/vite.config.ts` 中的 proxy 配置
3. 查看后端日志排查错误
</details>

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献流程

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- ✅ 遵循现有代码风格
- ✅ 添加必要的注释和文档
- ✅ 提交前运行测试和检查
- ✅ 使用语义化提交信息

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🔗 相关资源

### 官方文档
- [Vue Flow](https://vueflow.dev/) - 工作流画布组件
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
- [LlamaIndex](https://docs.llamaindex.ai/) - RAG 框架
- [ChromaDB](https://docs.trychroma.com/) - 向量数据库

### API 服务
- [DeepSeek API](https://platform.deepseek.com/docs) - LLM 服务
- [SiliconFlow API](https://docs.siliconflow.cn/) - Embedding 服务

### 项目文档
- [CLAUDE.md](./CLAUDE.md) - Claude Code 使用指南
- [AGENTS.md](./AGENTS.md) - 开发规范与指南
- [prd.md](./prd.md) - 产品需求文档

---

<div align="center">

**⭐ 如果这个项目对你有帮助，欢迎 Star！**

Made with ❤️ by the Agent Flow Lite Team

</div>
