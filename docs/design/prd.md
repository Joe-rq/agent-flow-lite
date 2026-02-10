# 产品需求文档 (PRD) - 简化版 Coze 智能体平台 Demo

## 1. 项目概述 (Overview)
本项目旨在构建一个轻量级、高还原度的智能体编排平台。通过可视化的工作流引擎、RAG 知识检索系统以及智能对话终端，让用户（开发者/考核官）能够通过“拖拽+配置”的方式快速搭建具备领域知识的 AI Agent。

**核心愿景：**
- **可视化 (Visual):** 所见即所得的逻辑编排。
- **智能化 (Intelligent):** 基于 RAG 和 LLM 的深度问答。
- **全栈化 (Full-Stack):** 完整的前后端流式交互与数据闭环。

## 2. 用户角色 (User Roles)

- **管理员 (Admin):** 用户管理、系统配置、所有资源的完全访问权限。
- **Agent 编排者 (Builder):** 创建工作流、上传知识库、配置节点逻辑、创建 Skill。
- **Agent 用户 (End-User):** 在对话终端与 Agent 进行交互，获取答案。

## 3. 核心功能模块 (Functional Concepts)

### 3.1 可视化工作流引擎 (Visual Workflow Engine)
*这是系统的“大脑”，负责逻辑的构建与流转。*

**功能点：**
- **画布操作 (Canvas):**
  - 支持无限画布拖拽、缩放。
  - 支持 SVG/HTML 节点渲染，视觉效果需现代化（建议使用 `Vue Flow` 或 `LogicFlow`）。
  - 连接线支持贝塞尔曲线，自动吸附。
- **节点类型 (Nodes):**
  - **Start/End 节点:** 流程的开始与结束。
  - **LLM 节点:** 配置模型参数（Temperature, System Prompt），输入 Prompt 模板。
  - **Knowledge 节点:** 关联已上传的知识库，进行检索配置。
  - **Skill 节点:** 调用预定义的 Skill 技能，支持变量输入。
  - **Condition 节点 (If/Else):** 简单的 JS 表达式判断分支。
- **数据流转:**
  - 节点间通过“变量引用”传递数据（例如 `{{step1.output}}`）。
  - 前端将图结构序列化为 JSON 发送至后端。

### 3.2 RAG 知识管理系统 (RAG Knowledge Base)
*这是系统的“海马体”，负责存储和检索长期记忆。*

**功能点：**
- **数据摄入:**
  - 支持 `.txt`, `.md` 文件拖拽上传。
  - 文件解析与文本清洗（去除乱码、标准化格式）。
- **分块与索引 (Chunking & Indexing):**
  - 按固定长度或语义段落进行切片 (Chunking)。
  - 调用 Embedding API 将文本转为向量。
- **检索测试:**
  - 提供后台测试窗口，输入 Query，实时查看召回的文本片段及其相似度分数。

### 3.3 智能多轮对话终端 (Intelligent Chat Terminal)
*这是系统的"嘴巴"，负责与用户交互。*

**功能点：**
- **会话管理:**
  - 自动创建 Session ID。
  - 历史记录回显（存储于后端 JSON 文件）。
  - 用户隔离：每个用户只能访问自己的会话。
- **交互体验:**
  - **流式响应 (Streaming):** 打字机效果显示 AI 回复，降低等待焦虑。
  - **思维链展示 (Chain of Thought):** (可选) 展示工作流当前的执行节点（如："正在检索知识库..."、"正在思考..."）。
  - **引用溯源:** 点击角标可高亮显示引用的知识库段落。
  - **引用详情面板:** 点击「引用」按钮显示来源信息、相似度分数和文本摘录。
  - **@Skill 调用:** 在对话中通过 `@skill-name` 语法直接调用 Skill 技能。

### 3.4 Skill 技能系统 (Skill System)
*这是系统的"技能库"，提供可复用的 AI 能力。*

**功能点：**
- **Skill 定义:**
  - 基于 YAML frontmatter + Markdown 格式。
  - 支持定义输入变量（名称、类型、是否必需）。
  - 支持关联知识库。
  - 可配置模型参数（temperature, max_tokens）。
- **Skill 管理:**
  - 创建、编辑、删除 Skill。
  - Skill 列表展示和搜索。
  - 独立测试运行 Skill。
- **Skill 使用:**
  - 在工作流中作为节点使用。
  - 在对话中通过 `@skill-name` 语法调用。

### 3.5 用户管理 (User Management)
*系统的"权限中心"。*

**功能点：**
- **认证授权:**
  - 基于邮箱的 Token 认证。
  - 首次登录自动创建用户。
  - 管理员角色区分。
- **管理员功能:**
  - 查看所有用户列表。
  - 启用/禁用用户账号。
  - 删除用户账号。

## 4. 技术架构 (Technical Architecture)

### 4.1 前端 (Frontend)
- **框架:** Vue 3 + Vite + TypeScript (强类型约束)。
- **UI 方案:** Vue Flow (工作流画布) + 项目内自定义组件与样式。
- **架构模式:**
  - **Composable 架构** - 业务逻辑抽取至可复用 composables，按域组织（knowledge/workflow/chat/skills）
  - **组件拆分** - 页面组件控制在 <=200 行，细粒度子组件按功能域分组
- **核心逻辑:**
  - 使用 Pinia 管理全局状态。
  - 使用 `EventSource` 处理 SSE 流式响应。

### 4.2 后端 (Backend)
- **框架:** **Python (FastAPI)**。
  - *决策:* AI 领域标准栈，异步高性能。
- **存储:**
  - **SQLite:** 用户、会话等关系数据 (aiosqlite + SQLAlchemy)。
  - **ChromaDB:** 向量数据本地持久化存储。
  - **文件系统:** Skill 定义、上传文档、工作流配置。
- **AI 集成:**
  - **LlamaIndex:** RAG 检索框架。
  - **DeepSeek API:** LLM 大语言模型。
  - **SiliconFlow API:** Embedding 向量模型 (BGE-M3)。

### 4.3 接口规范 (API Design)
- 遵循 RESTful 规范，使用 Python `Pydantic` 定义数据模型，自动生成 Swagger 文档。

## 5. 考核与优化重点 (Success Metrics)
- **架构清晰:** 代码分层 (Controller -> Service -> Data Access)。
- **闭环完整:** 从“上传文档”到“对话引用文档”必须完全跑通，不能有 Mock 数据。
- **代码可读:** 核心逻辑（如调度器）需要有详细注释。

## 6. 风险与规避 (Risks)
- **LLM 响应慢:** 必须实现流式传输 (Stream) 以优化体验。
- **Prompt 注入不可控:** 在后端对 System Prompt 进行预置保护。
- **Token 消耗过大:** 在 Dev 模式下限制上下文长度。
