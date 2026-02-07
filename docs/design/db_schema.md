# 数据库架构设计

> **技术栈:** SQLite (aiosqlite) + ChromaDB + 文件存储
> **ORM:** SQLAlchemy 2.0 (异步)
> **最后更新:** 2026-02-07

## 1. 数据存储概览

本项目采用混合存储架构：

| 数据类型 | 存储方案 | 说明 |
|----------|----------|------|
| 关系数据 | SQLite | 用户、认证令牌、会话元数据 |
| 向量数据 | ChromaDB | 文档块向量、相似度检索 |
| 文件数据 | 本地文件系统 | Skill 定义、上传文档、工作流配置、会话消息 |

## 2. SQLite 数据库表结构

### 2.1 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- 'user' | 'admin'
    is_active BOOLEAN DEFAULT 1,
    deleted_at TIMESTAMP NULL,        -- 软删除标记
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 认证令牌表 (auth_tokens)
```sql
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(36) UNIQUE NOT NULL,  -- UUID
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 3. ChromaDB 集合结构

### 3.1 知识库集合
每个知识库对应一个 ChromaDB Collection：

```python
# Collection 名称: 知识库 ID (如 "kb-uuid")
collection = chroma_client.get_or_create_collection("kb-uuid")

# 存储的 Document 结构:
{
    "ids": ["doc-id_chunk_0", "doc-id_chunk_1", ...],
    "documents": ["文本片段1", "文本片段2", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],  # 1024 维向量
    "metadatas": [
        {"doc_id": "doc-uuid", "chunk_index": 0, "chunk_size": 512},
        {"doc_id": "doc-uuid", "chunk_index": 1, "chunk_size": 498}
    ]
}
```

### 3.2 向量维度
- **模型:** BAAI/bge-m3 (SiliconFlow)
- **维度:** 1024
- **距离度量:** L2 (Euclidean)

## 4. 文件存储结构

### 4.1 目录布局
```
backend/data/
├── app.db                      # SQLite 数据库
├── workflows.json              # 工作流配置
├── kb_metadata.json            # 知识库元数据
├── chromadb/                   # ChromaDB 持久化数据
│   └── {kb-id}/
│       ├── data_level0.bin
│       ├── header.bin
│       └── ...
├── skills/                     # Skill 定义文件
│   └── {skill-name}/
│       └── SKILL.md
├── uploads/                    # 上传的原始文档
│   └── {kb-id}/
│       └── {filename}.txt
├── metadata/                   # 文档元数据
│   └── {kb-id}/
│       └── documents.json
└── sessions/                   # 会话历史
    └── {session-id}.json
```

### 4.2 Skill 文件格式
```yaml
# backend/data/skills/{skill-name}/SKILL.md
---
name: skill-name
description: Skill 描述
inputs:
  - name: input1
    type: string
    required: true
knowledge_base: null  # 可选：关联知识库 ID
model:
  temperature: 0.3
  max_tokens: 2000
---

Prompt 模板内容，支持 {{variable}} 变量替换...
```

### 4.3 会话消息格式
```json
{
  "id": "session-uuid",
  "title": "会话标题",
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
      "citations": [
        {
          "doc_id": "doc-uuid",
          "chunk_index": 0,
          "score": 0.85,
          "text": "引用文本..."
        }
      ]
    }
  ],
  "created_at": "2026-02-01T10:00:00Z",
  "updated_at": "2026-02-01T11:00:00Z"
}
```

## 5. 并发控制

### 5.1 文件锁 (filelock)
使用 `filelock` 库保护并发文件访问：

```python
from filelock import FileLock

# 锁定文件进行读写
with FileLock(f"{filepath}.lock"):
    with open(filepath, 'w') as f:
        json.dump(data, f)
```

### 5.2 锁文件位置
- SQLite 写入: 依赖 SQLite 内置锁机制
- JSON 文件: `{filepath}.lock`
- Skill 文件: `{skill_path}.lock`

## 6. 数据备份与迁移

### 6.1 备份策略
```bash
# 备份 SQLite
cp backend/data/app.db backend/data/app.db.backup

# 备份 ChromaDB
cp -r backend/data/chromadb/ backend/data/chromadb.backup/

# 备份配置文件
cp backend/data/workflows.json backend/data/workflows.json.backup
```

### 6.2 维度变更处理
更换嵌入模型（导致维度变化）时：
```bash
# 1. 删除旧向量数据
rm -rf backend/data/chromadb/

# 2. 重新上传文档建立索引
# 3. 系统会自动返回 409 错误提示重建
```

## 7. 与原始设计的差异

| 方面 | 原始设计 (PostgreSQL + pgvector) | 实际实现 (SQLite + ChromaDB) | 原因 |
|------|----------------------------------|------------------------------|------|
| 关系数据库 | PostgreSQL | SQLite | 简化部署，单文件存储 |
| 向量存储 | pgvector | ChromaDB | 专用向量库，更好的 RAG 支持 |
| ORM | SQLModel | SQLAlchemy 2.0 | 更成熟，异步支持完善 |
| 部署复杂度 | 需要 PostgreSQL 服务 | 零配置 | 便于演示和开发 |
