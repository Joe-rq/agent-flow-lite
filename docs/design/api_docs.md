# API 接口定义文档 (RESTful / FastAPI)

> 本文档描述了前后端交互的核心接口。
> **Base URL:** `/api/v1`
> **Docs:** `/docs` (Swagger UI)

## 1. 工作流 (Workflow)

### 1.1 获取工作流列表
- **GET** `/workflows`
- **Response Model:** `List[WorkflowRead]`

### 1.2 创建/保存工作流
- **POST** `/workflows`
- **Request Body (Pydantic):**
  ```python
  class WorkflowCreate(BaseModel):
      name: str
      description: Optional[str] = None
      graph_data: Dict[str, Any]  # 前端 Vue Flow 的完整 JSON
  ```

### 1.3 运行工作流 (Run)
- **POST** `/workflows/{workflow_id}/run`
- **Request:**
  ```json
  { "inputs": { "query": "hello" } }
  ```

## 2. 知识库 (Knowledge Base)

### 2.1 上传文件 (RAG Ingestion)
- **POST** `/knowledge/upload`
- **Form Data:**
  - `file`: UploadFile
  - `kb_id`: str
- **Backend Process (FastAPI Background Task):**
  1. `Unstructured` 解析。
  2. `LangChain` 切片。
  3. Embedding -> `pgvector`.

## 3. 智能问答 (Chat)

### 3.1 发送消息 (SSE Streaming)
- **POST** `/chat/completions`
- **Response:** `EventSourceResponse` (text/event-stream)
- **Stream Events:**
  - `event: thought` -> 检索过程 / 思考链
  - `event: token` -> LLM 生成的字符
  - `event: citation` -> 引用源 metadata
