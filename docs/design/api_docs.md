# API 接口定义文档 (RESTful / FastAPI)

> 本文档描述了前后端交互的核心接口。
> **Base URL:** `/api/v1`
> **Docs:** `/docs` (Swagger UI)
> **最后更新:** 2026-02-07

## 1. 认证 (Auth)

### 1.1 用户登录
- **POST** `/auth/login`
- **Request Body:**
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response:**
  ```json
  {
    "token": "uuid-token-string",
    "expires_at": "2026-02-14T10:00:00Z"
  }
  ```
- **说明:** 基于邮箱的简化的 Token 认证，首次登录自动创建用户

### 1.2 获取当前用户信息
- **GET** `/auth/me`
- **Headers:** `Authorization: Bearer {token}`
- **Response:**
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "is_active": true
  }
  ```

### 1.3 用户登出
- **POST** `/auth/logout`
- **Headers:** `Authorization: Bearer {token}`
- **Response:** `{ "message": "Logged out successfully" }`

---

## 2. 工作流 (Workflow)

### 2.1 获取工作流列表
- **GET** `/workflows`
- **Headers:** `Authorization: Bearer {token}`
- **Response:**
  ```json
  {
    "workflows": [
      {
        "id": "workflow-uuid",
        "name": "我的工作流",
        "description": "描述",
        "node_count": 5,
        "edge_count": 4,
        "created_at": "2026-02-01T10:00:00Z"
      }
    ]
  }
  ```

### 2.2 获取单个工作流
- **GET** `/workflows/{workflow_id}`
- **Response:** 完整的工作流定义（包含 nodes 和 edges）

### 2.3 创建/保存工作流
- **POST** `/workflows`
- **Request Body:**
  ```json
  {
    "name": "新工作流",
    "description": "可选描述",
    "nodes": [...],
    "edges": [...]
  }
  ```

### 2.4 更新工作流
- **PUT** `/workflows/{workflow_id}`
- **Request Body:** 同创建工作流

### 2.5 删除工作流
- **DELETE** `/workflows/{workflow_id}`
- **Response:** 204 No Content

### 2.6 运行工作流
- **POST** `/workflows/{workflow_id}/execute`
- **Request Body:**
  ```json
  {
    "inputs": { "query": "用户输入" }
  }
  ```
- **Response:** SSE 流式响应
  - `event: workflow_start`
  - `event: node_start`
  - `event: node_end`
  - `event: workflow_end`

---

## 3. 知识库 (Knowledge Base)

### 3.1 获取知识库列表
- **GET** `/knowledge`
- **Response:**
  ```json
  {
    "knowledge_bases": [
      {
        "id": "kb-uuid",
        "name": "我的知识库",
        "description": "描述",
        "document_count": 5,
        "created_at": "2026-02-01T10:00:00Z"
      }
    ]
  }
  ```

### 3.2 创建知识库
- **POST** `/knowledge`
- **Request Body:**
  ```json
  {
    "name": "新知识库",
    "description": "可选描述"
  }
  ```

### 3.3 上传文档
- **POST** `/knowledge/{kb_id}/upload`
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: UploadFile (.txt, .md)
- **Response:**
  ```json
  {
    "id": "doc-uuid",
    "status": "processing",
    "task_id": "task-uuid"
  }
  ```

### 3.4 获取文档列表
- **GET** `/knowledge/{kb_id}/documents`
- **Response:**
  ```json
  {
    "documents": [
      {
        "id": "doc-uuid",
        "filename": "document.txt",
        "status": "completed",
        "file_size": 1024,
        "created_at": "2026-02-01T10:00:00Z"
      }
    ]
  }
  ```

### 3.5 删除文档
- **DELETE** `/knowledge/{kb_id}/documents/{doc_id}`

### 3.6 搜索知识库
- **GET** `/knowledge/{kb_id}/search?query={query}&top_k=5`
- **Response:**
  ```json
  {
    "kb_id": "kb-uuid",
    "query": "搜索内容",
    "results": [
      {
        "text": "匹配的文本片段",
        "metadata": { "doc_id": "doc-uuid", "chunk_index": 0 },
        "score": 0.85
      }
    ]
  }
  ```
- **错误处理:** 如果嵌入模型维度不匹配，返回 409 Conflict

---

## 4. Skill 技能

### 4.1 获取 Skill 列表
- **GET** `/skills`
- **Response:**
  ```json
  {
    "skills": [
      {
        "name": "article-summary",
        "description": "文章总结",
        "has_inputs": true,
        "has_knowledge_base": false
      }
    ]
  }
  ```

### 4.2 获取单个 Skill
- **GET** `/skills/{name}`
- **Response:** 完整的 Skill 定义（包含 frontmatter 和 prompt 模板）

### 4.3 创建 Skill
- **POST** `/skills`
- **Request Body:**
  ```json
  {
    "name": "new-skill",
    "content": "---\nname: new-skill\ndescription: 描述\n---\n\nPrompt 内容..."
  }
  ```

### 4.4 更新 Skill
- **PUT** `/skills/{name}`
- **Request Body:** 同创建 Skill

### 4.5 删除 Skill
- **DELETE** `/skills/{name}`

### 4.6 执行 Skill
- **POST** `/skills/{name}/run`
- **Request Body:**
  ```json
  {
    "inputs": { "article": "文章内容..." }
  }
  ```
- **Response:** SSE 流式响应
  - `event: token` - LLM 生成的内容
  - `event: done` - 完成标记

---

## 5. 对话 (Chat)

### 5.1 发送消息 (SSE 流式)
- **POST** `/chat/completions`
- **Request Body:**
  ```json
  {
    "message": "用户消息",
    "session_id": "session-uuid（可选，不传则创建新会话）",
    "kb_id": "知识库ID（可选）",
    "workflow_id": "工作流ID（可选）"
  }
  ```
- **Response:** SSE 流
  - `event: thought` - 思考过程/检索信息
  - `event: token` - LLM 生成的字符
  - `event: citation` - 引用来源
  - `event: done` - 完成

### 5.2 @Skill 调用
在 `message` 中使用 `@skill-name` 语法调用 Skill：
```json
{
  "message": "@article-summary 这是一篇很长的文章..."
}
```

### 5.3 获取会话列表
- **GET** `/chat/sessions`
- **Response:**
  ```json
  {
    "sessions": [
      {
        "id": "session-uuid",
        "title": "会话标题",
        "created_at": "2026-02-01T10:00:00Z",
        "updated_at": "2026-02-01T11:00:00Z"
      }
    ]
  }
  ```

### 5.4 获取会话历史
- **GET** `/chat/sessions/{session_id}`
- **Response:**
  ```json
  {
    "id": "session-uuid",
    "messages": [
      {
        "id": "msg-uuid",
        "role": "user",
        "content": "用户消息",
        "created_at": "2026-02-01T10:00:00Z"
      },
      {
        "id": "msg-uuid",
        "role": "assistant",
        "content": "AI回复",
        "citations": [...]
      }
    ]
  }
  ```

### 5.5 删除会话
- **DELETE** `/chat/sessions/{session_id}`

---

## 6. 管理员 (Admin)

### 6.1 获取用户列表
- **GET** `/admin/users`
- **Headers:** `Authorization: Bearer {admin_token}`
- **Response:**
  ```json
  {
    "users": [
      {
        "id": 1,
        "email": "user@example.com",
        "role": "user",
        "is_active": true,
        "created_at": "2026-02-01T10:00:00Z"
      }
    ],
    "total": 100
  }
  ```

### 6.2 禁用用户
- **POST** `/admin/users/{user_id}/disable`

### 6.3 启用用户
- **POST** `/admin/users/{user_id}/enable`

### 6.4 删除用户
- **DELETE** `/admin/users/{user_id}`

---

## 7. 错误处理

### 7.1 标准错误格式
```json
{
  "detail": "错误信息"
}
```

### 7.2 常见 HTTP 状态码

| 状态码 | 含义 | 场景 |
|--------|------|------|
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未提供认证或 Token 无效 |
| 403 | Forbidden | 权限不足（非管理员） |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如知识库维度不匹配） |
| 422 | Validation Error | 请求体验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

### 7.3 知识库维度不匹配 (409)
当更换嵌入模型后，现有知识库维度不匹配时返回：
```json
{
  "detail": "Knowledge base index is incompatible with current embedding model. Rebuild the knowledge base index and re-upload documents."
}
```

---

## 8. 技术栈说明

### 8.1 存储
- **向量存储:** ChromaDB（本地持久化）
- **关系数据:** SQLite (aiosqlite + SQLAlchemy)
- **文件存储:** 本地文件系统 (`backend/data/`)

### 8.2 AI 服务
- **LLM:** DeepSeek API
- **Embedding:** SiliconFlow API (BAAI/bge-m3)
- **RAG 框架:** LlamaIndex

### 8.3 并发控制
- 使用 `filelock` 保护文件读写
- 会话数据使用文件锁避免并发冲突
