# Agent Flow Lite

一个轻量级、高还原度的智能体编排平台，支持可视化工作流编排、RAG 知识检索和智能对话。

![Vue 3](https://img.shields.io/badge/Vue%203-4FC08D?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)

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
- **LLM 集成**: DeepSeek API / OpenAI API
- **包管理**: uv

## 快速开始

### 环境要求

- Node.js: ^20.19.0 或 >=22.12.0
- Python: >=3.11
- uv: Python 包管理工具

### 安装与启动

```bash
# 方式1: 使用一键脚本（推荐）
./install.sh  # 安装依赖
./start.sh    # 启动服务

# 方式2: 手动安装
# 前端
cd frontend
npm install
npm run dev

# 后端
cd backend
uv venv
uv pip install -e .
uv run uvicorn main:app --reload
```

访问 http://localhost:5173 查看前端应用。

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

# 开发服务器
npm run dev

# 类型检查
npm run type-check

# 代码格式化
npm run format

# 代码检查
npm run lint

# 生产构建
npm run build
```

### 后端开发

```bash
cd backend

# 安装依赖
uv pip install -e .

# 开发服务器
uv run uvicorn main:app --reload

# 测试 API
uv run python test_chat_api.py
uv run python test_deepseek.py
```

## 配置说明

### 后端环境变量

复制 `backend/.env.example` 为 `backend/.env`，并配置：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 其他配置
...
```

## API 文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心功能模块

### 1. 可视化工作流引擎
- 无限画布拖拽、缩放
- SVG/HTML 节点渲染
- 贝塞尔曲线连接线
- 节点类型：Start/End、LLM、Knowledge、Condition
- 变量引用数据流转

### 2. RAG 知识管理系统
- 支持 .txt, .md 文件上传
- 自动文本解析与清洗
- 语义分块与向量索引
- 检索测试窗口

### 3. 智能对话终端
- 自动会话管理
- SSE 流式响应
- 思维链展示
- 引用溯源高亮

## 文档

- [产品需求文档](./prd.md) - 详细功能规格说明
- [API 文档](./api_docs.md) - 接口详细说明
- [数据库设计](./db_schema.md) - 数据模型设计
- [技术栈分析](./tech_stack_analysis.md) - 技术选型说明
- [AGENTS.md](./AGENTS.md) - 开发规范与指南

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License

## 相关链接

- [Vue Flow 文档](https://vueflow.dev/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)
