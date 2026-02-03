# 数据库架构设计 (Database Schema / PostgreSQL)

基于 **Python (SQLAlchemy / Tortoise-ORM) + PostgreSQL** 的设计方案。
> **注:** 由于 Python 具有强大的 ORM 能力，我们将使用 Code-First 模式生成表结构。

## 1. 实体关系图 (ER Diagram)
*结构保持不变，主要变化在于 ORM 映射层的实现差异。*

```mermaid
erDiagram
    %% 用户与鉴权 (简化)
    User {
        string id PK
        string username
        datetime created_at
    }

    %% 工作流域
    Workflow {
        string id PK
        string name
        string description
        jsonb graph_data "Pydantic Model Dump"
        boolean is_published
        datetime created_at
    }

    %% 知识库域 (RAG Core)
    KnowledgeBase {
        string id PK
        string name
    }

    Document {
        string id PK
        string kb_id FK
        string filename
        string status "parsing, ready, error"
    }

    DocumentChunk {
        string id PK
        string doc_id FK
        text content
        vector embedding "vector(1536) using pgvector"
        jsonb metadata "页码, 来源等元数据"
    }

    %% 会话域
    ChatSession {
        string id PK
        string workflow_id FK
    }

    ChatMessage {
        string id PK
        string session_id FK
        string role
        text content
        jsonb citations
    }
```

## 2. 关键技术点 (Python Specifics)

### A. Vector Extension
在 FastAPI 启动时，使用 Alembic 迁移脚本自动开启插件：
```python
op.execute("CREATE EXTENSION IF NOT EXISTS vector")
```

### B. ORM Selection
建议使用 **SQLModel** (FastAPI 作者开发，完美结合 Pydantic 和 SQLAlchemy)。
```python
class DocumentChunk(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))
```

## 3. 索引优化
为 `DocumentChunk.embedding` 创建 `hnsw` 索引：
```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```
