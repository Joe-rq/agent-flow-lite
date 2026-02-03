# Agent Flow Lite - 5分钟演示脚本

## 演示概述

这是一个完整的5分钟演示脚本，展示 Agent Flow Lite 的核心功能：工作流编排、知识库管理和 RAG 智能问答。

---

## [0:00-0:30] 开场：项目介绍

### 演讲要点

> "大家好，今天我要演示的是 Agent Flow Lite - 一个轻量级的 AI Agent 工作流编排平台。它让你可以通过可视化界面创建工作流，上传文档构建知识库，并进行智能问答。"

### 展示内容
1. 项目首页（如已部署）
2. 技术栈：Vue3 + FastAPI + ChromaDB + DeepSeek LLM
3. 核心特性概览

---

## [0:30-1:30] 演示 1：创建工作流

### 操作步骤

1. **导航到工作流页面**
   - 点击侧边栏 "工作流" 菜单
   - 展示工作流编辑器界面

2. **添加节点**
   - 点击 "+ 开始节点"（已有一个默认节点）
   - 点击 "+ LLM 节点" 添加 LLM 处理节点
   - 点击 "+ 知识库节点" 添加知识库检索节点

3. **配置节点**
   - 点击 LLM 节点
   - 在配置面板中设置系统提示词：
     ```
     你是一个 helpful 的 AI 助手，请用中文回答用户问题。
     ```
   - 设置 temperature：0.7
   - 点击保存

4. **连接节点**
   - 从开始节点拖拽连接到 LLM 节点
   - 从 LLM 节点拖拽连接到知识库节点

5. **保存工作流**
   - 点击 "💾 保存" 按钮
   - 确认工作流保存成功

### 预期结果
- 工作流成功创建并保存
- 可以在工作流列表中看到新创建的工作流

---

## [1:30-2:30] 演示 2：上传文档到知识库

### 操作步骤

1. **创建知识库**
   - 点击侧边栏 "知识库" 菜单
   - 点击 "+ 新建知识库" 按钮
   - 输入名称："演示知识库"
   - 点击创建

2. **进入知识库详情**
   - 点击刚创建的知识库卡片
   - 展示知识库详情页面

3. **上传测试文档**
   - 在文件上传区域点击或拖拽上传以下文件：
     - `france.txt` - 关于法国和巴黎的信息
     - `python.txt` - 关于 Python 编程语言
     - `ai.txt` - 关于人工智能

4. **监控处理进度**
   - 展示上传进度条
   - 等待文档处理完成（约 5-10 秒）
   - 确认所有文档状态显示为 "已完成"

### 预期结果
- 3个文档成功上传并处理
- 向量数量：11 个向量块（可在知识库信息中查看）

---

## [2:30-4:00] 演示 3：智能问答（展示 RAG 效果）

### 操作步骤

1. **打开对话页面**
   - 点击侧边栏 "对话" 菜单
   - 展示对话界面

2. **选择知识库**
   - 在知识库选择器中，选择 "演示知识库"

3. **提问测试**

   **问题 1：法国相关**
   ```
   法国的首都是哪里？埃菲尔铁塔有多高？
   ```
   **预期回答**：
   - 首都是巴黎
   - 埃菲尔铁塔高 330 米

   **问题 2：Python 相关**
   ```
   Python 是谁创建的？列举三个 Python 的 Web 框架。
   ```
   **预期回答**：
   - Guido van Rossum
   - Django、Flask、FastAPI

   **问题 3：AI 相关**
   ```
   什么是 RAG？GPT 是由哪家公司开发的？
   ```
   **预期回答**：
   - 检索增强生成（Retrieval-Augmented Generation）
   - OpenAI

4. **展示流式输出**
   - 观察 SSE 流式响应
   - 展示检索过程（thought 事件）
   - 展示引用来源（citation 事件）

### 预期结果
- 所有问题都能得到准确回答
- 回答基于上传的文档内容
- 流式输出正常工作

---

## [4:00-5:00] 代码讲解：核心架构

### 系统架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Vue3 Frontend │────▶│  FastAPI Backend │────▶│   DeepSeek API  │
│                 │     │                  │     │                 │
│ - Workflow UI   │     │ - Workflow CRUD  │     │ - LLM inference │
│ - Knowledge Base│     │ - Document Upload│     │ - Streaming     │
│ - Chat Interface│     │ - RAG Retrieval  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │    ChromaDB      │
                        │                  │
                        │ - Vector Store   │
                        │ - Embeddings     │
                        └──────────────────┘
```

### 关键技术点

1. **RAG 流程**
   - 文档 → 切片 → Embedding → ChromaDB
   - 查询 → Embedding → 向量检索 → LLM 增强 → 回答

2. **流式响应**
   - SSE (Server-Sent Events)
   - 事件类型：thought → token → citation → done

3. **向量检索**
   - 使用 HuggingFace BAAI/bge-small-zh-v1.5 嵌入模型
   - ChromaDB 持久化存储
   - 语义相似度搜索

### 项目结构

```
agent-flow-lite/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   │   ├── workflow.py
│   │   │   ├── knowledge.py
│   │   │   └── chat.py
│   │   ├── core/          # 核心逻辑
│   │   │   ├── llm.py     # DeepSeek 客户端
│   │   │   ├── rag.py     # RAG 管道
│   │   │   └── chroma_client.py
│   │   └── models/        # 数据模型
│   └── data/              # 数据存储
│       ├── chromadb/      # 向量数据库
│       ├── uploads/       # 上传文件
│       └── test_docs/     # 测试文档
└── frontend/
    └── src/
        ├── views/         # 页面视图
        │   ├── WorkflowView.vue
        │   ├── KnowledgeView.vue
        │   └── ChatView.vue
        └── components/    # 组件
```

---

## 演示检查清单

在演示前，请确认以下检查项：

### ✅ 系统状态检查
- [ ] 后端服务已启动（端口 8000）
- [ ] 前端服务已启动（端口 5173）
- [ ] ChromaDB 连接正常

### ✅ 功能检查
- [ ] 能在 30 秒内创建工作流
- [ ] 能在 30 秒内上传文件并完成向量化
- [ ] 能在 30 秒内得到准确的 RAG 回答
- [ ] 没有阻塞性错误（页面崩溃、API 500）
- [ ] 流式响应正常工作

### ✅ 测试数据检查
- [ ] france.txt 已上传到知识库
- [ ] python.txt 已上传到知识库
- [ ] ai.txt 已上传到知识库
- [ ] 向量数量正确（11 个向量块）

### ⚠️ 已知限制（演示时说明）
- [ ] LLM 需要配置 DeepSeek API Key
- [ ] 工作流运行功能尚未完全实现
- [ ] 对话界面需要进一步完善

---

## 常见问题解答

**Q: 为什么 LLM 回答失败？**
A: 需要在 backend/.env 中配置有效的 DeepSeek API Key。

**Q: 可以上传什么格式的文档？**
A: 目前支持 .txt 和 .md 格式的文本文件。

**Q: 向量检索的准确性如何？**
A: 使用 BAAI/bge-small-zh-v1.5 中文嵌入模型，在中英文混合场景下表现良好。

**Q: 最大支持多大的文件？**
A: 单个文件最大 5MB。

---

## Day 10 检查点总结

### 已完成
- ✅ 工作流 CRUD API
- ✅ 知识库管理（创建、上传、删除）
- ✅ 文档处理（解析、切片、向量化）
- ✅ RAG 检索（向量搜索）
- ✅ 流式对话 API（SSE）
- ✅ 前端工作流编辑器
- ✅ 前端知识库管理界面
- ✅ 测试文档和问答对准备

### 待完善
- ⏳ 完整的对话界面（ChatView.vue 待实现）
- ⏳ 工作流运行功能
- ⏳ LLM API Key 配置文档

### 演示准备
- ✅ 演示脚本（本文档）
- ✅ 测试数据（3 个文档）
- ✅ 测试问答对（24 个问题）

---

## 附录：API 测试命令

### 健康检查
```bash
curl http://localhost:8000/
```

### 创建工作流
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "演示工作流",
    "description": "测试工作流",
    "graph_data": {"nodes": [], "edges": []}
  }'
```

### 创建知识库
```bash
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -d '{"name": "演示知识库"}'
```

### 上传文档
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/{kb_id}/upload" \
  -F "file=@france.txt"
```

### 搜索知识库
```bash
curl "http://localhost:8000/api/v1/knowledge/{kb_id}/search?query=capital+of+France&top_k=3"
```

### 流式对话
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session",
    "message": "What is the capital of France?",
    "kb_id": "{kb_id}"
  }'
```
