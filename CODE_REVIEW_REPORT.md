# Agent Flow Lite 代码审查报告

> 审查日期: 2026-02-03
> 审查范围: 全部核心代码（前端 + 后端）
> 审查目标: 识别逻辑漏洞、功能缺陷、安全问题、优化空间

---

## 目录

1. [项目设计目标回顾](#项目设计目标回顾)
2. [严重逻辑漏洞（P0）](#一严重逻辑漏洞p0)
3. [中等问题（P1）](#二中等问题p1)
4. [并发与性能问题（P2）](#三并发与性能问题p2)
5. [安全问题](#四安全问题)
6. [架构设计问题](#五架构设计问题)
7. [详细优化方案](#六详细优化方案)
8. [优先级排序与实施路线图](#七优先级排序与实施路线图)

---

## 项目设计目标回顾

Agent Flow Lite 的核心愿景是：

- **可视化工作流编排** - 用户通过拖拽节点、连线的方式设计 AI 处理流程
- **智能 RAG 对话** - 基于知识库的增强检索问答
- **工作流驱动的对话** - Chat 按照工作流定义的逻辑执行

**核心发现**: 当前实现与设计目标存在严重偏离，工作流编辑器是"画图工具"，Chat 是"独立的 RAG 对话"，两者**完全没有打通**。

---

## 一、严重逻辑漏洞（P0）

### 1.1 工作流执行引擎完全缺失

**问题描述**

设计了完整的工作流编辑器（支持 5 种节点类型、连线、配置面板），但后端**没有任何代码执行工作流**。用户画好的工作流只能保存为 JSON 数据，永远不会被执行。

**影响范围**

- `backend/app/api/workflow.py` - 只有 CRUD，没有执行
- `frontend/src/views/WorkflowEditor.vue` - 只能编辑，不能运行

**当前行为 vs 期望行为**

```
当前行为:
用户画工作流 → 保存到 workflows.json → 结束（死数据）

期望行为:
用户画工作流 → 保存 → 在 Chat 中选择工作流 → 按拓扑顺序执行各节点 → 返回结果
```

**缺失的核心组件**

```python
# 需要实现: backend/app/core/workflow_engine.py

class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.graph = self._build_graph()
        self.step_outputs = {}  # 存储各节点的输出

    def _build_graph(self) -> dict:
        """从 nodes/edges 构建邻接表"""
        pass

    def _topological_sort(self) -> List[str]:
        """拓扑排序确定执行顺序"""
        pass

    def _execute_node(self, node_id: str, input_data: Any) -> Any:
        """执行单个节点"""
        node = self._get_node(node_id)
        node_type = node["type"]

        if node_type == "start":
            return self._execute_start_node(node, input_data)
        elif node_type == "llm":
            return self._execute_llm_node(node, input_data)
        elif node_type == "knowledge":
            return self._execute_knowledge_node(node, input_data)
        elif node_type == "condition":
            return self._execute_condition_node(node, input_data)
        elif node_type == "end":
            return self._execute_end_node(node, input_data)

    async def execute(self, initial_input: str) -> dict:
        """执行整个工作流"""
        execution_order = self._topological_sort()
        current_data = initial_input

        for node_id in execution_order:
            current_data = await self._execute_node(node_id, current_data)
            self.step_outputs[node_id] = current_data

        return self.step_outputs
```

---

### 1.2 Chat 与 Workflow 完全割裂

**问题描述**

`ChatTerminal.vue` 发送消息时**从不传递 workflow_id**，即使后端 API 支持该参数，也从未被使用。

**问题代码位置**

```typescript
// frontend/src/views/ChatTerminal.vue:207-218
async function connectSSE(sessionId: string, message: string) {
  const response = await fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
      // 缺失: workflow_id
      // 缺失: kb_id
    }),
  })
  // ...
}
```

```python
# backend/app/api/chat.py:177-195
@router.post("/completions")
async def chat_completions(request: ChatRequest) -> StreamingResponse:
    # request.workflow_id 被接收但从未使用
    # 没有任何代码调用工作流执行引擎
```

**优化方案**

```typescript
// 前端 - 添加工作流和知识库选择
const selectedWorkflowId = ref<string>('')
const selectedKbId = ref<string>('')

async function connectSSE(sessionId: string, message: string) {
  const response = await fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
      workflow_id: selectedWorkflowId.value || undefined,
      kb_id: selectedKbId.value || undefined,
    }),
  })
}
```

```python
# 后端 - 根据 workflow_id 决定执行逻辑
@router.post("/completions")
async def chat_completions(request: ChatRequest) -> StreamingResponse:
    if request.workflow_id:
        # 使用工作流引擎执行
        workflow = await get_workflow(request.workflow_id)
        engine = WorkflowEngine(workflow)
        result = await engine.execute(request.message)
        # 流式返回执行过程和结果
    else:
        # 普通 RAG 对话（当前实现）
        pass
```

---

### 1.3 条件节点表达式无法执行

**问题描述**

条件节点让用户填写 JavaScript 表达式（如 `{{step1.output}} === 'yes'`），但：

1. 后端是 Python，无法直接执行 JavaScript
2. 没有实现变量引用解析（`{{step1.output}}` 替换逻辑）
3. 即使实现了，用 `eval()` 会有严重安全问题

**问题代码位置**

```vue
<!-- frontend/src/components/NodeConfigPanel.vue:81-93 -->
<div v-if="nodeType === 'condition'" class="config-section">
  <textarea
    v-model="config.expression"
    placeholder="例如: {{step1.output}} === 'yes'"
  ></textarea>
  <small>使用 {{stepId.output}} 引用其他节点的输出</small>
</div>
```

**优化方案**

方案 A: 使用结构化条件（推荐）

```python
# 定义结构化条件模型
class ConditionRule(BaseModel):
    left_operand: str      # 变量引用，如 "step1.output"
    operator: str          # "equals", "contains", "greater_than" 等
    right_operand: str     # 比较值

class ConditionConfig(BaseModel):
    rules: List[ConditionRule]
    logic: str = "and"     # "and" 或 "or"

# 执行条件判断
def evaluate_condition(config: ConditionConfig, step_outputs: dict) -> bool:
    results = []
    for rule in config.rules:
        left_value = resolve_variable(rule.left_operand, step_outputs)
        right_value = rule.right_operand
        result = compare(left_value, rule.operator, right_value)
        results.append(result)

    if config.logic == "and":
        return all(results)
    return any(results)
```

方案 B: 使用安全表达式引擎

```python
# 使用 simpleeval 库（需要安装）
from simpleeval import simple_eval

def evaluate_expression(expression: str, step_outputs: dict) -> bool:
    # 替换变量引用
    for step_id, output in step_outputs.items():
        expression = expression.replace(
            f"{{{{{step_id}.output}}}}",
            repr(output)
        )

    # 安全执行（simpleeval 只允许基础操作）
    return simple_eval(expression)
```

---

### 1.4 删除文档时向量数据残留

**问题描述**

删除文档时，ChromaDB 中的向量数据没有被正确删除。

**问题代码位置**

```python
# backend/app/core/chroma_client.py:117-133
def delete_document(self, kb_id: str, document_id: str) -> bool:
    try:
        collection = self._client.get_collection(name=f"kb_{kb_id}")
        collection.delete(ids=[document_id])  # 错误！
        return True
    except ValueError:
        return False
```

**问题分析**

文档存储时使用的 ID 格式是 `{doc_id}_chunk_0`, `{doc_id}_chunk_1` 等：

```python
# backend/app/core/rag.py:131
ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
```

但删除时只传了 `doc_id`，无法匹配任何记录。

**优化方案**

```python
# 方案 1: 使用 metadata 过滤删除
def delete_document(self, kb_id: str, document_id: str) -> bool:
    try:
        collection = self._client.get_collection(name=f"kb_{kb_id}")
        # 使用 where 条件按 doc_id 元数据删除所有 chunks
        collection.delete(where={"doc_id": document_id})
        return True
    except Exception as e:
        print(f"Delete failed: {e}")
        return False

# 方案 2: 先查询再删除
def delete_document(self, kb_id: str, document_id: str) -> bool:
    try:
        collection = self._client.get_collection(name=f"kb_{kb_id}")
        # 查询所有属于该文档的 chunk IDs
        results = collection.get(
            where={"doc_id": document_id},
            include=[]
        )
        if results["ids"]:
            collection.delete(ids=results["ids"])
        return True
    except Exception as e:
        return False
```

---

### 1.5 RAG 搜索执行了两次

**问题描述**

每次聊天请求中，RAG 搜索被调用了两次：
1. 在 `chat_completions` 中构建 system prompt 时
2. 在 `chat_stream_generator` 中发送思维链事件时

**问题代码位置**

```python
# backend/app/api/chat.py:229-240 - 第一次搜索
if request.kb_id:
    try:
        rag_pipeline = get_rag_pipeline()
        results = rag_pipeline.search(request.kb_id, request.message, top_k=5)
        # ...用于构建 system prompt

# backend/app/api/chat.py:103-114 (chat_stream_generator) - 第二次搜索
if request.kb_id:
    rag_pipeline = get_rag_pipeline()
    retrieved_results = rag_pipeline.search(
        request.kb_id, request.message, top_k=5
    )
    # ...用于发送思维链事件
```

**影响**

- Embedding API 调用次数翻倍
- 响应延迟增加
- 成本增加

**优化方案**

```python
@router.post("/completions")
async def chat_completions(request: ChatRequest) -> StreamingResponse:
    # 只搜索一次，结果传递给 generator
    retrieved_results = []
    retrieved_context = None

    if request.kb_id:
        try:
            rag_pipeline = get_rag_pipeline()
            retrieved_results = rag_pipeline.search(
                request.kb_id, request.message, top_k=5
            )
            if retrieved_results:
                context_parts = [f"[{i}] {r['text']}" for i, r in enumerate(retrieved_results[:3], 1)]
                retrieved_context = "\n\n".join(context_parts)
        except Exception:
            pass

    system_prompt = build_system_prompt(bool(request.kb_id), retrieved_context)
    # ...

    # 将搜索结果传递给 generator，不再重复搜索
    async def stream_with_save():
        async for chunk in chat_stream_generator(
            request,
            messages_for_llm,
            pre_retrieved_results=retrieved_results  # 传递已有结果
        ):
            yield chunk
```

---

## 二、中等问题（P1）

### 2.1 保存工作流丢失节点配置数据

**问题描述**

用户在节点配置面板中设置的参数（systemPrompt, temperature, knowledgeBaseId 等）在保存工作流时被丢弃。

**问题代码位置**

```typescript
// frontend/src/views/WorkflowEditor.vue:217-233
async function saveWorkflow() {
  const flowData = toObject()
  const response = await axios.post(`${API_BASE}/workflows`, {
    name: workflowName,
    graph_data: {
      nodes: flowData.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        label: n.label
        // 缺失: data: n.data  <-- 节点配置数据在这里！
      })),
      edges: flowData.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target
      }))
    }
  })
}
```

**优化方案**

```typescript
async function saveWorkflow() {
  const flowData = toObject()
  const response = await axios.post(`${API_BASE}/workflows`, {
    name: workflowName,
    description: '',
    graph_data: {
      nodes: flowData.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        label: n.label,
        data: n.data || {}  // 添加这一行！
      })),
      edges: flowData.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,  // 可选：保存连接点信息
        targetHandle: e.targetHandle
      }))
    }
  })
}
```

同时修改加载逻辑：

```typescript
// frontend/src/views/WorkflowEditor.vue:265-271
if (graphData && graphData.nodes) {
  setNodes(graphData.nodes.map((n: any) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    label: n.label || getDefaultLabel(n.type),
    data: n.data || {}  // 确保加载时也包含 data
  })))
}
```

---

### 2.2 会话历史前后端不同步

**问题描述**

- 前端 `sessions` 数组存储在组件内存中
- 后端会话存储在 `data/sessions/{session_id}.json`
- 两者独立，没有同步机制

**问题表现**

1. 刷新页面后，前端会话列表清空
2. 后端数据仍然存在，但前端看不到
3. 新建会话 ID 可能与已有后端数据冲突

**优化方案**

方案 A: 启动时从后端加载会话列表

```typescript
// 添加获取会话列表的 API
// 后端: GET /api/v1/chat/sessions

// 前端启动时加载
onMounted(async () => {
  try {
    const response = await axios.get('/api/v1/chat/sessions')
    sessions.value = response.data.sessions.map((s: any) => ({
      id: s.session_id,
      title: s.title || '会话 ' + s.session_id.slice(0, 8),
      createdAt: new Date(s.created_at).getTime(),
      updatedAt: new Date(s.updated_at).getTime(),
      messages: s.messages || []
    }))

    if (sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].id
    } else {
      createNewSession()
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
    createNewSession()
  }
})
```

方案 B: 使用 LocalStorage 持久化前端状态

```typescript
// 保存会话到 LocalStorage
watch(sessions, (newSessions) => {
  localStorage.setItem('chat_sessions', JSON.stringify(newSessions))
}, { deep: true })

// 启动时恢复
onMounted(() => {
  const saved = localStorage.getItem('chat_sessions')
  if (saved) {
    sessions.value = JSON.parse(saved)
    if (sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].id
    }
  }
  if (sessions.value.length === 0) {
    createNewSession()
  }
})
```

---

### 2.3 知识库删除 API 不存在

**问题描述**

有创建知识库的 API，但没有删除知识库的 API。用户创建错误的知识库后无法通过界面删除。

**优化方案**

```python
# backend/app/api/knowledge.py - 添加删除接口

@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: str) -> None:
    """
    删除知识库及其所有文档和向量数据

    - **kb_id**: 知识库 ID
    """
    # 1. 检查知识库是否存在
    metadata = load_kb_metadata()
    if kb_id not in metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{kb_id}' not found"
        )

    # 2. 删除 ChromaDB collection
    chroma_client = get_chroma_client()
    chroma_client.delete_collection(kb_id)

    # 3. 删除上传的文件
    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / kb_id
    if upload_dir.exists():
        import shutil
        shutil.rmtree(upload_dir)

    # 4. 删除元数据文件
    metadata_dir = project_root / "data" / "metadata" / kb_id
    if metadata_dir.exists():
        import shutil
        shutil.rmtree(metadata_dir)

    # 5. 从知识库索引中删除
    del metadata[kb_id]
    save_kb_metadata(metadata)
```

---

### 2.4 相似度分数计算不准确

**问题描述**

当前的相似度计算公式在某些情况下会产生负数或不准确的结果。

**问题代码位置**

```python
# backend/app/core/rag.py:184-188
distance = results["distances"][0][i] if results["distances"] else 0
similarity = max(0, 1 - distance)  # L2 距离范围可能超过 1
```

**问题分析**

- ChromaDB 默认使用 L2（欧几里得）距离
- 对于归一化向量，L2 距离范围是 [0, 2]
- BGE-M3 输出的向量通常已归一化
- 当距离 > 1 时，`1 - distance` 为负数，被截断为 0

**优化方案**

```python
# 方案 1: 使用更合理的转换公式
def distance_to_similarity(distance: float) -> float:
    """将 L2 距离转换为 0-1 相似度分数"""
    # 使用指数衰减：距离越大，相似度衰减越快
    return 1 / (1 + distance)

# 方案 2: 改用余弦相似度
# 在创建 collection 时指定距离函数
collection = self._client.get_or_create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"}  # 使用余弦距离
)

# 余弦距离范围 [0, 2]，转换为相似度 [0, 1]
def cosine_distance_to_similarity(distance: float) -> float:
    return 1 - distance / 2

# 方案 3: 直接使用 ChromaDB 的内积（需要归一化向量）
collection = self._client.get_or_create_collection(
    name=collection_name,
    metadata={"hnsw:space": "ip"}  # 内积（对归一化向量等于余弦相似度）
)
# 内积结果直接就是相似度
```

---

### 2.5 文件覆盖风险

**问题描述**

使用原始文件名存储上传文件，同名文件会相互覆盖。

**问题代码位置**

```python
# backend/app/api/knowledge.py:124
file_path = get_upload_path(kb_id, file.filename)
with open(file_path, "wb") as f:
    f.write(content)
```

**优化方案**

```python
import uuid
from pathlib import Path

def get_safe_upload_path(kb_id: str, original_filename: str) -> tuple[Path, str]:
    """
    生成安全的文件存储路径

    Returns:
        (file_path, stored_filename)
    """
    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 提取扩展名
    suffix = Path(original_filename).suffix.lower()

    # 使用 UUID 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}{suffix}"

    return upload_dir / unique_filename, unique_filename


# 修改上传逻辑
@router.post("/{kb_id}/upload")
async def upload_document(...):
    # ...
    file_path, stored_filename = get_safe_upload_path(kb_id, file.filename)

    with open(file_path, "wb") as f:
        f.write(content)

    metadata = {
        "id": doc_id,
        "kb_id": kb_id,
        "original_filename": file.filename,  # 保留原始文件名用于显示
        "stored_filename": stored_filename,   # 实际存储的文件名
        "file_path": str(file_path),
        # ...
    }
```

---

## 三、并发与性能问题（P2）

### 3.1 JSON 文件无并发保护

**问题描述**

所有 JSON 文件操作都是 load → 修改 → save 模式，没有任何锁机制。

**受影响的文件**

- `data/workflows.json`
- `data/kb_metadata.json`
- `data/metadata/{kb_id}/documents.json`
- `data/sessions/{session_id}.json`

**并发场景示例**

```
时间线:
T1: 用户A load() -> {"w1": {...}}
T2: 用户B load() -> {"w1": {...}}
T3: 用户A 添加 w2, save() -> {"w1": {...}, "w2": {...}}
T4: 用户B 添加 w3, save() -> {"w1": {...}, "w3": {...}}

结果: w2 被覆盖丢失
```

**优化方案**

方案 A: 使用文件锁

```python
# 安装: pip install filelock
from filelock import FileLock

def load_workflows() -> dict:
    ensure_data_dir()
    lock = FileLock(str(WORKFLOW_FILE) + ".lock")

    with lock:
        if not WORKFLOW_FILE.exists():
            return {"workflows": {}}
        try:
            with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"workflows": {}}


def save_workflows(data: dict) -> None:
    ensure_data_dir()
    lock = FileLock(str(WORKFLOW_FILE) + ".lock")

    with lock:
        with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

方案 B: 改用 SQLite（推荐长期方案）

```python
# 使用 SQLite 替代 JSON 文件
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = DATA_DIR / "agent_flow.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                graph_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
```

---

### 3.2 全局单例在多线程下不安全

**问题描述**

全局单例的创建没有线程锁保护，在并发场景下可能创建多个实例。

**问题代码位置**

```python
# backend/app/core/rag.py:200-208
_rag_pipeline: Optional[RAGPipeline] = None

def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:  # 检查和赋值之间存在竞态条件
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
```

**同样问题存在于**

- `backend/app/core/chroma_client.py:164-174`
- `backend/app/core/config.py`（如果有类似实现）

**优化方案**

```python
import threading

_rag_pipeline: Optional[RAGPipeline] = None
_rag_pipeline_lock = threading.Lock()

def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline

    if _rag_pipeline is None:
        with _rag_pipeline_lock:
            # Double-checked locking
            if _rag_pipeline is None:
                _rag_pipeline = RAGPipeline()

    return _rag_pipeline
```

或者使用 FastAPI 的依赖注入：

```python
from functools import lru_cache

@lru_cache()
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline()
```

---

### 3.3 后台任务无状态追踪

**问题描述**

文档处理使用 `BackgroundTasks`，但：
- 没有返回任务 ID 给前端
- 没有进度查询接口
- 处理失败后用户只能刷新列表查看状态

**优化方案**

方案 A: 添加任务状态查询接口

```python
# 使用全局字典追踪任务状态（生产环境应使用 Redis）
processing_tasks: Dict[str, dict] = {}

@router.post("/{kb_id}/upload")
async def upload_document(...):
    # ...
    task_id = str(uuid.uuid4())

    processing_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "doc_id": doc_id,
        "kb_id": kb_id,
        "started_at": datetime.utcnow().isoformat()
    }

    background_tasks.add_task(
        process_document_task,
        kb_id,
        doc_id,
        task_id  # 传递任务 ID
    )

    return DocumentResponse(
        id=doc_id,
        task_id=task_id,  # 返回任务 ID
        # ...
    )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """查询任务处理状态"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return processing_tasks[task_id]


def process_document_task(kb_id: str, doc_id: str, task_id: str):
    """带状态更新的后台任务"""
    try:
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["progress"] = 10

        # ... 处理步骤，每步更新进度 ...

        processing_tasks[task_id]["status"] = "completed"
        processing_tasks[task_id]["progress"] = 100
    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)
```

方案 B: 使用 WebSocket 推送进度

```python
# 使用 FastAPI WebSocket
from fastapi import WebSocket

@router.websocket("/ws/tasks/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    await websocket.accept()

    while True:
        if task_id in processing_tasks:
            status = processing_tasks[task_id]
            await websocket.send_json(status)

            if status["status"] in ("completed", "failed"):
                break

        await asyncio.sleep(0.5)

    await websocket.close()
```

---

## 四、安全问题

### 4.1 路径遍历漏洞

**问题描述**

文件上传使用用户提供的文件名，可能导致路径遍历攻击。

**问题代码位置**

```python
# backend/app/api/knowledge.py:58-63
def get_upload_path(kb_id: str, filename: str) -> Path:
    upload_dir = project_root / "data" / "uploads" / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / filename  # filename 可能是 "../../../etc/passwd"
```

**攻击示例**

```
POST /api/v1/knowledge/kb1/upload
Content-Disposition: form-data; name="file"; filename="../../../app/main.py"

# 恶意内容会覆盖 main.py
```

**优化方案**

```python
from pathlib import Path
import re

def secure_filename(filename: str) -> str:
    """
    清理文件名，移除路径遍历字符
    """
    # 只保留文件名部分
    filename = Path(filename).name

    # 移除危险字符
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # 移除前导点（隐藏文件）
    filename = filename.lstrip('.')

    # 如果清理后为空，使用默认名
    if not filename:
        filename = "unnamed_file"

    return filename


def get_upload_path(kb_id: str, filename: str) -> Path:
    # 清理 kb_id（也可能被注入）
    safe_kb_id = re.sub(r'[^\w\-]', '', kb_id)

    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / safe_kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = secure_filename(filename)
    full_path = upload_dir / safe_filename

    # 最后验证：确保路径在预期目录内
    try:
        full_path.resolve().relative_to(upload_dir.resolve())
    except ValueError:
        raise ValueError("Invalid file path")

    return full_path
```

---

### 4.2 Session ID 可预测

**问题描述**

前端使用 `Math.random()` 生成 Session ID，不够安全。

**问题代码位置**

```typescript
// frontend/src/views/ChatTerminal.vue:117-119
function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}
```

**优化方案**

```typescript
function generateSecureId(): string {
  // 使用 Web Crypto API（浏览器原生支持）
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}
```

或者让后端生成 Session ID：

```python
# 后端生成安全的 Session ID
import secrets

@router.post("/sessions")
async def create_session() -> dict:
    session_id = secrets.token_urlsafe(32)
    # ... 创建会话
    return {"session_id": session_id}
```

---

### 4.3 条件节点 eval 风险预警

**问题描述**

如果将来实现条件表达式执行，使用 `eval()` 或 `exec()` 会导致远程代码执行（RCE）漏洞。

**危险示例**

```python
# 千万不要这样做！
def evaluate_condition(expression: str, context: dict) -> bool:
    return eval(expression, {"__builtins__": {}}, context)  # 仍然不安全！

# 攻击者输入: ().__class__.__bases__[0].__subclasses__()[104]().load_module('os').system('rm -rf /')
```

**安全方案**

参考 1.3 节的结构化条件方案或使用 `simpleeval` 库。

---

## 五、架构设计问题

### 5.1 前端状态分散

**问题描述**

每个 View 组件自己管理状态，没有使用 Pinia 做全局状态管理。

**当前状态分布**

| 组件 | 状态 | 问题 |
|------|------|------|
| `WorkflowEditor.vue` | workflows 列表 | 切换页面后丢失 |
| `KnowledgeView.vue` | 知识库列表 | 切换页面后丢失 |
| `ChatTerminal.vue` | sessions 列表 | 刷新后丢失 |

**优化方案**

```typescript
// stores/workflow.ts
import { defineStore } from 'pinia'

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    workflows: [] as Workflow[],
    currentWorkflowId: null as string | null,
    isLoading: false,
  }),

  getters: {
    currentWorkflow: (state) =>
      state.workflows.find(w => w.id === state.currentWorkflowId),
  },

  actions: {
    async fetchWorkflows() {
      this.isLoading = true
      try {
        const response = await axios.get('/api/v1/workflows')
        this.workflows = response.data.items
      } finally {
        this.isLoading = false
      }
    },

    async saveWorkflow(workflow: WorkflowCreate) {
      const response = await axios.post('/api/v1/workflows', workflow)
      this.workflows.unshift(response.data)
      return response.data
    },
  },
})
```

```typescript
// stores/knowledge.ts
export const useKnowledgeStore = defineStore('knowledge', {
  state: () => ({
    knowledgeBases: [] as KnowledgeBase[],
    documents: {} as Record<string, Document[]>,  // kb_id -> documents
  }),
  // ...
})
```

```typescript
// stores/chat.ts
export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [] as Session[],
    currentSessionId: null as string | null,
  }),

  persist: true,  // 使用 pinia-plugin-persistedstate 持久化
  // ...
})
```

---

### 5.2 API 返回格式不统一

**问题描述**

不同接口返回格式不一致，前端处理时需要适配多种情况。

**当前情况**

```python
# 返回 Pydantic 模型
async def create_workflow(...) -> Workflow:

# 返回裸 dict
async def get_knowledge_base_info(...) -> dict:

# 返回 JSONResponse
async def delete_document(...) -> JSONResponse:
```

**优化方案**

定义统一的响应格式：

```python
# backend/app/models/response.py
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20


# 使用示例
@router.get("/{kb_id}/info", response_model=APIResponse[KnowledgeBaseInfo])
async def get_knowledge_base_info(kb_id: str) -> APIResponse[KnowledgeBaseInfo]:
    info = ...
    return APIResponse(data=info)


@router.delete("/{kb_id}/documents/{doc_id}", response_model=APIResponse[None])
async def delete_document(kb_id: str, doc_id: str) -> APIResponse[None]:
    # ... 删除逻辑
    return APIResponse(message="Document deleted successfully")
```

---

## 六、详细优化方案

### 6.1 工作流执行引擎完整实现

```python
# backend/app/core/workflow_engine.py
"""
工作流执行引擎

支持:
- 拓扑排序执行
- 变量传递
- 条件分支
- 异步流式输出
"""

from typing import Any, Dict, List, Optional, AsyncGenerator
from collections import deque
import asyncio

from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.models.workflow import Workflow


class ExecutionContext:
    """执行上下文，存储变量和中间结果"""

    def __init__(self, initial_input: str):
        self.variables: Dict[str, Any] = {
            "input": initial_input,
        }
        self.step_outputs: Dict[str, Any] = {}

    def set_output(self, node_id: str, value: Any):
        self.step_outputs[node_id] = value
        self.variables[f"{node_id}.output"] = value

    def get_variable(self, var_path: str) -> Any:
        """解析变量路径，如 'step1.output'"""
        parts = var_path.split('.')
        current = self.variables
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def resolve_template(self, template: str) -> str:
        """解析模板字符串中的变量引用 {{var}}"""
        import re

        def replace_var(match):
            var_path = match.group(1)
            value = self.get_variable(var_path)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{(\w+(?:\.\w+)*)\}\}', replace_var, template)


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.nodes = {n["id"]: n for n in workflow.graph_data.nodes}
        self.edges = workflow.graph_data.edges
        self.adjacency = self._build_adjacency()

    def _build_adjacency(self) -> Dict[str, List[str]]:
        """构建邻接表"""
        adj: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            source = edge["source"]
            target = edge["target"]
            if source in adj:
                adj[source].append(target)
        return adj

    def _topological_sort(self) -> List[str]:
        """拓扑排序"""
        in_degree = {node_id: 0 for node_id in self.nodes}

        for edge in self.edges:
            target = edge["target"]
            if target in in_degree:
                in_degree[target] += 1

        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for neighbor in self.adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains cycles")

        return result

    def _find_start_node(self) -> Optional[str]:
        """找到开始节点"""
        for node_id, node in self.nodes.items():
            if node.get("type") == "start":
                return node_id
        return None

    async def _execute_start_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """执行开始节点"""
        yield {
            "type": "node_start",
            "node_id": node["id"],
            "node_type": "start"
        }

        # 开始节点直接传递输入
        output = ctx.variables["input"]
        ctx.set_output(node["id"], output)

        yield {
            "type": "node_complete",
            "node_id": node["id"],
            "output": output
        }

    async def _execute_llm_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """执行 LLM 节点"""
        yield {
            "type": "node_start",
            "node_id": node["id"],
            "node_type": "llm"
        }

        data = node.get("data", {})
        system_prompt = data.get("systemPrompt", "You are a helpful assistant.")
        temperature = data.get("temperature", 0.7)

        # 解析系统提示词中的变量
        system_prompt = ctx.resolve_template(system_prompt)

        # 获取输入（来自上一个节点）
        input_text = ctx.variables.get("input", "")
        for source_id in self._get_source_nodes(node["id"]):
            if source_id in ctx.step_outputs:
                input_text = ctx.step_outputs[source_id]
                break

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(input_text)}
        ]

        output = ""
        async for token in chat_completion_stream(messages, temperature=temperature):
            output += token
            yield {
                "type": "token",
                "node_id": node["id"],
                "content": token
            }

        ctx.set_output(node["id"], output)

        yield {
            "type": "node_complete",
            "node_id": node["id"],
            "output": output[:100] + "..." if len(output) > 100 else output
        }

    async def _execute_knowledge_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """执行知识库检索节点"""
        yield {
            "type": "node_start",
            "node_id": node["id"],
            "node_type": "knowledge"
        }

        data = node.get("data", {})
        kb_id = data.get("knowledgeBaseId")

        if not kb_id:
            yield {
                "type": "node_error",
                "node_id": node["id"],
                "error": "Knowledge base not configured"
            }
            return

        # 获取查询文本
        query = ctx.variables.get("input", "")
        for source_id in self._get_source_nodes(node["id"]):
            if source_id in ctx.step_outputs:
                query = str(ctx.step_outputs[source_id])
                break

        yield {
            "type": "thought",
            "node_id": node["id"],
            "content": f"Searching knowledge base: {kb_id}"
        }

        try:
            rag_pipeline = get_rag_pipeline()
            results = rag_pipeline.search(kb_id, query, top_k=5)

            # 格式化检索结果
            context_parts = []
            for i, r in enumerate(results[:3], 1):
                context_parts.append(f"[{i}] {r['text']}")

            output = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
            ctx.set_output(node["id"], output)

            yield {
                "type": "node_complete",
                "node_id": node["id"],
                "output": f"Found {len(results)} relevant chunks",
                "results": results[:3]
            }

        except Exception as e:
            yield {
                "type": "node_error",
                "node_id": node["id"],
                "error": str(e)
            }

    async def _execute_condition_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """执行条件节点"""
        yield {
            "type": "node_start",
            "node_id": node["id"],
            "node_type": "condition"
        }

        data = node.get("data", {})
        expression = data.get("expression", "true")

        # 解析表达式中的变量
        resolved_expr = ctx.resolve_template(expression)

        # 使用安全的表达式求值
        try:
            from simpleeval import simple_eval
            result = simple_eval(resolved_expr)
        except Exception as e:
            # 如果 simpleeval 未安装，使用简单的比较
            result = resolved_expr.lower() in ("true", "yes", "1")

        ctx.set_output(node["id"], result)

        yield {
            "type": "node_complete",
            "node_id": node["id"],
            "output": result,
            "branch": "true" if result else "false"
        }

    async def _execute_end_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """执行结束节点"""
        yield {
            "type": "node_start",
            "node_id": node["id"],
            "node_type": "end"
        }

        # 收集所有上游节点的输出
        final_output = None
        for source_id in self._get_source_nodes(node["id"]):
            if source_id in ctx.step_outputs:
                final_output = ctx.step_outputs[source_id]
                break

        ctx.set_output(node["id"], final_output)

        yield {
            "type": "node_complete",
            "node_id": node["id"],
            "output": final_output
        }

        yield {
            "type": "workflow_complete",
            "final_output": final_output
        }

    def _get_source_nodes(self, node_id: str) -> List[str]:
        """获取指向该节点的所有源节点"""
        sources = []
        for edge in self.edges:
            if edge["target"] == node_id:
                sources.append(edge["source"])
        return sources

    async def _execute_node(
        self,
        node_id: str,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """执行单个节点"""
        node = self.nodes[node_id]
        node_type = node.get("type", "unknown")

        executors = {
            "start": self._execute_start_node,
            "llm": self._execute_llm_node,
            "knowledge": self._execute_knowledge_node,
            "condition": self._execute_condition_node,
            "end": self._execute_end_node,
        }

        executor = executors.get(node_type)
        if executor:
            async for event in executor(node, ctx):
                yield event
        else:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"Unknown node type: {node_type}"
            }

    async def execute(
        self,
        initial_input: str
    ) -> AsyncGenerator[dict, None]:
        """
        执行整个工作流

        Yields:
            执行事件流，包括:
            - workflow_start
            - node_start
            - token (LLM 输出)
            - thought (思考过程)
            - node_complete
            - node_error
            - workflow_complete
        """
        yield {
            "type": "workflow_start",
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name
        }

        try:
            execution_order = self._topological_sort()
            ctx = ExecutionContext(initial_input)

            for node_id in execution_order:
                async for event in self._execute_node(node_id, ctx):
                    yield event

                    # 如果遇到错误，停止执行
                    if event.get("type") == "node_error":
                        yield {
                            "type": "workflow_error",
                            "error": event.get("error")
                        }
                        return

        except Exception as e:
            yield {
                "type": "workflow_error",
                "error": str(e)
            }
```

---

### 6.2 修改 Chat API 支持工作流执行

```python
# backend/app/api/chat.py - 修改版

from app.core.workflow_engine import WorkflowEngine
from app.api.workflow import get_workflow

@router.post("/completions")
async def chat_completions(request: ChatRequest) -> StreamingResponse:
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    # 加载或创建会话
    session = load_session(request.session_id)
    if session is None:
        session = SessionHistory(
            session_id=request.session_id,
            kb_id=request.kb_id,
            workflow_id=request.workflow_id
        )

    # 添加用户消息
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    session.messages.append(user_message)

    # 判断执行模式
    if request.workflow_id:
        # 工作流模式
        return StreamingResponse(
            workflow_stream(request, session),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    else:
        # 普通 RAG 对话模式（现有逻辑）
        return StreamingResponse(
            rag_stream(request, session),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )


async def workflow_stream(
    request: ChatRequest,
    session: SessionHistory
) -> AsyncGenerator[str, None]:
    """工作流执行流"""

    # 加载工作流
    try:
        workflow = await get_workflow(request.workflow_id)
    except HTTPException:
        yield format_sse_event("error", {
            "message": f"Workflow not found: {request.workflow_id}"
        })
        return

    # 创建执行引擎
    engine = WorkflowEngine(workflow)

    # 收集完整输出
    full_output = ""

    # 执行工作流并流式输出
    async for event in engine.execute(request.message):
        event_type = event.get("type", "unknown")

        if event_type == "workflow_start":
            yield format_sse_event("thought", {
                "type": "workflow",
                "status": "start",
                "workflow_name": event.get("workflow_name")
            })

        elif event_type == "node_start":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "start",
                "node_id": event.get("node_id"),
                "node_type": event.get("node_type")
            })

        elif event_type == "token":
            full_output += event.get("content", "")
            yield format_sse_event("token", {
                "content": event.get("content")
            })

        elif event_type == "thought":
            yield format_sse_event("thought", {
                "type": "thinking",
                "content": event.get("content")
            })

        elif event_type == "node_complete":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "complete",
                "node_id": event.get("node_id")
            })

        elif event_type == "workflow_complete":
            final_output = event.get("final_output", full_output)

            # 保存助手回复
            assistant_message = ChatMessage(
                role="assistant",
                content=str(final_output),
                timestamp=datetime.utcnow()
            )
            session.messages.append(assistant_message)
            save_session(session)

            yield format_sse_event("done", {
                "status": "success",
                "message": "Workflow completed"
            })

        elif event_type in ("node_error", "workflow_error"):
            yield format_sse_event("error", {
                "message": event.get("error")
            })
            yield format_sse_event("done", {
                "status": "error",
                "message": event.get("error")
            })
```

---

## 七、优先级排序与实施路线图

### 优先级定义

| 级别 | 含义 | 标准 |
|------|------|------|
| **P0** | 阻断性 | 核心功能无法工作 |
| **P1** | 严重 | 功能缺陷或数据丢失 |
| **P2** | 中等 | 性能问题或用户体验差 |
| **P3** | 轻微 | 代码质量或架构优化 |

### 问题优先级总览

| # | 问题 | 优先级 | 工作量 | 影响 |
|---|------|--------|--------|------|
| 1.1 | 工作流执行引擎缺失 | P0 | 大 | 核心功能 |
| 1.2 | Chat 与 Workflow 割裂 | P0 | 中 | 核心功能 |
| 1.3 | 条件表达式无法执行 | P0 | 中 | 核心功能 |
| 1.4 | 删除文档向量残留 | P0 | 小 | 数据一致性 |
| 1.5 | RAG 搜索重复执行 | P1 | 小 | 性能 |
| 2.1 | 保存工作流丢失数据 | P0 | 小 | 数据丢失 |
| 2.2 | 会话历史不同步 | P1 | 中 | 用户体验 |
| 2.3 | 知识库删除 API | P1 | 小 | 功能完整性 |
| 2.4 | 相似度计算不准 | P2 | 小 | 准确性 |
| 2.5 | 文件覆盖风险 | P1 | 小 | 数据安全 |
| 3.1 | JSON 无并发保护 | P2 | 中 | 数据一致性 |
| 3.2 | 单例线程不安全 | P2 | 小 | 稳定性 |
| 3.3 | 后台任务无追踪 | P2 | 中 | 用户体验 |
| 4.1 | 路径遍历漏洞 | P0 | 小 | 安全 |
| 4.2 | Session ID 可预测 | P2 | 小 | 安全 |
| 5.1 | 前端状态分散 | P3 | 大 | 代码质量 |
| 5.2 | API 格式不统一 | P3 | 中 | 代码质量 |

### 实施路线图

#### 阶段 1: 紧急修复（1-2 天）

1. ✅ 修复保存工作流丢失 data 字段
2. ✅ 修复删除文档向量残留
3. ✅ 修复路径遍历漏洞
4. ✅ 修复 RAG 搜索重复执行

#### 阶段 2: 核心功能补全（3-5 天）

1. 🔨 实现工作流执行引擎
2. 🔨 修改 Chat API 支持工作流
3. 🔨 实现条件表达式安全求值
4. 🔨 前端 Chat 添加工作流/知识库选择

#### 阶段 3: 功能完善（2-3 天）

1. 📝 添加知识库删除 API
2. 📝 实现会话历史同步
3. 📝 修复相似度计算
4. 📝 修复文件覆盖风险

#### 阶段 4: 稳定性优化（2-3 天）

1. 🔧 添加 JSON 文件并发锁
2. 🔧 修复全局单例线程安全
3. 🔧 添加后台任务状态追踪
4. 🔧 改进 Session ID 生成

#### 阶段 5: 架构优化（可选，3-5 天）

1. 🏗 前端状态管理重构（Pinia）
2. 🏗 API 响应格式统一
3. 🏗 考虑使用 SQLite 替代 JSON

---

## 总结

这份审查报告识别了 **17 个问题**，其中：

- **P0 级别**: 6 个（核心功能阻断）
- **P1 级别**: 4 个（严重缺陷）
- **P2 级别**: 5 个（中等问题）
- **P3 级别**: 2 个（代码质量）

**最核心的问题是**：工作流编辑器和 Chat 对话完全割裂。你画了一个漂亮的图，但它永远不会被执行。要让这个项目达到设计目标，必须先实现工作流执行引擎，并将其与 Chat 系统打通。

建议按照路线图分阶段实施，先修复紧急问题，再补全核心功能，最后优化架构。
