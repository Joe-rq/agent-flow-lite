# Agent Flow Lite 优化执行计划

> 本文档为 AI 执行手册，包含可直接执行的具体指令
> 执行顺序：按 Phase 顺序执行，每个 Phase 内的 Task 可并行

---

## 执行概览

```
Phase 1: 紧急修复（数据安全）     ████░░░░░░  4 tasks
Phase 2: 核心功能（工作流引擎）   ██████░░░░  6 tasks
Phase 3: 功能完善               ████░░░░░░  4 tasks
Phase 4: 稳定性优化             ███░░░░░░░  3 tasks
```

---

# Phase 1: 紧急修复

## Task 1.1: 修复保存工作流丢失节点配置数据

### 问题
保存工作流时，节点的 `data` 字段（包含 systemPrompt、temperature 等配置）被丢弃。

### 执行指令

**文件**: `frontend/src/views/WorkflowEditor.vue`

**步骤 1**: 找到 `saveWorkflow` 函数（约第 209 行），修改 nodes 映射逻辑：

```typescript
// 修改前（约第 222-227 行）
nodes: flowData.nodes.map((n: any) => ({
  id: n.id,
  type: n.type,
  position: n.position,
  label: n.label
})),

// 修改后
nodes: flowData.nodes.map((n: any) => ({
  id: n.id,
  type: n.type,
  position: n.position,
  label: n.label,
  data: n.data || {}
})),
```

**步骤 2**: 找到 `loadWorkflow` 函数（约第 258 行），修改加载逻辑：

```typescript
// 修改前（约第 265-271 行）
if (graphData && graphData.nodes) {
  setNodes(graphData.nodes.map((n: any) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    label: n.label || (n.type === 'start' ? '开始' : n.type === 'llm' ? 'LLM' : '知识库'),
    data: n.data || {}
  })))
}

// 修改后（确保 data 字段被正确加载）
if (graphData && graphData.nodes) {
  setNodes(graphData.nodes.map((n: any) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    label: n.label || getDefaultLabel(n.type),
    data: n.data || {}
  })))
}

// 在 script setup 中添加辅助函数
function getDefaultLabel(type: string): string {
  const labelMap: Record<string, string> = {
    start: '开始',
    llm: 'LLM',
    knowledge: '知识库',
    end: '结束',
    condition: '条件'
  }
  return labelMap[type] || type
}
```

### 验收标准
1. 创建工作流，添加 LLM 节点
2. 配置 LLM 节点的 systemPrompt 和 temperature
3. 保存工作流
4. 刷新页面，加载该工作流
5. 点击 LLM 节点，确认配置仍然存在

---

## Task 1.2: 修复删除文档时向量数据残留

### 问题
删除文档时，ChromaDB 中的 chunk 数据没有被删除（ID 格式不匹配）。

### 执行指令

**文件**: `backend/app/core/chroma_client.py`

**修改 `delete_document` 方法（约第 117-133 行）**：

```python
# 修改前
def delete_document(self, kb_id: str, document_id: str) -> bool:
    """
    Delete a document from a knowledge base collection.
    """
    try:
        collection = self._client.get_collection(name=f"kb_{kb_id}")
        collection.delete(ids=[document_id])
        return True
    except ValueError:
        return False

# 修改后
def delete_document(self, kb_id: str, document_id: str) -> bool:
    """
    Delete a document and all its chunks from a knowledge base collection.

    Args:
        kb_id: Knowledge base ID
        document_id: Document ID to delete (will delete all chunks with this doc_id)

    Returns:
        True if chunks were deleted, False if collection doesn't exist
    """
    try:
        collection = self._client.get_collection(name=f"kb_{kb_id}")

        # 使用 metadata 过滤删除所有属于该文档的 chunks
        # chunk IDs 格式为: {doc_id}_chunk_0, {doc_id}_chunk_1, ...
        # 但我们通过 metadata 中的 doc_id 字段来删除更可靠
        collection.delete(where={"doc_id": document_id})

        return True
    except ValueError:
        # Collection doesn't exist
        return False
    except Exception as e:
        print(f"Error deleting document {document_id}: {e}")
        return False
```

### 验收标准
1. 上传一个文档到知识库
2. 等待处理完成
3. 在知识库中搜索，确认能找到内容
4. 删除该文档
5. 再次搜索相同内容，确认搜索结果为空

---

## Task 1.3: 修复路径遍历安全漏洞

### 问题
文件上传使用原始文件名，可能导致路径遍历攻击。

### 执行指令

**文件**: `backend/app/api/knowledge.py`

**步骤 1**: 在文件顶部添加导入和辅助函数（约第 10 行后）：

```python
import re
import uuid
from pathlib import Path

def secure_filename(filename: str) -> str:
    """
    清理文件名，防止路径遍历攻击

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 只保留文件名部分（去除路径）
    filename = Path(filename).name

    # 只保留安全字符：字母、数字、下划线、连字符、点
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # 移除前导点（防止隐藏文件）
    filename = filename.lstrip('.')

    # 移除多余空格
    filename = ' '.join(filename.split())

    # 如果清理后为空，生成默认名
    if not filename or filename == '.':
        filename = "unnamed_file"

    return filename
```

**步骤 2**: 修改 `get_upload_path` 函数（约第 58-63 行）：

```python
# 修改前
def get_upload_path(kb_id: str, filename: str) -> Path:
    """Get the full path for saving an uploaded file."""
    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / filename

# 修改后
def get_upload_path(kb_id: str, filename: str) -> tuple[Path, str]:
    """
    Get a safe path for saving an uploaded file.

    Args:
        kb_id: Knowledge base ID
        filename: Original filename from user

    Returns:
        Tuple of (full_path, stored_filename)
    """
    # 清理 kb_id（也可能被注入）
    safe_kb_id = re.sub(r'[^\w\-]', '', kb_id)
    if not safe_kb_id:
        safe_kb_id = "default"

    project_root = Path(__file__).parent.parent.parent
    upload_dir = project_root / "data" / "uploads" / safe_kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 使用 UUID 前缀确保唯一性，保留原始扩展名
    safe_name = secure_filename(filename)
    suffix = Path(safe_name).suffix.lower()
    unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_name}"

    full_path = upload_dir / unique_filename

    # 最终验证：确保路径在预期目录内
    try:
        full_path.resolve().relative_to(upload_dir.resolve())
    except ValueError:
        raise ValueError("Invalid file path detected")

    return full_path, unique_filename
```

**步骤 3**: 修改 `upload_document` 函数中的调用（约第 124-127 行）：

```python
# 修改前
file_path = get_upload_path(kb_id, file.filename)
with open(file_path, "wb") as f:
    f.write(content)

# 修改后
file_path, stored_filename = get_upload_path(kb_id, file.filename)
with open(file_path, "wb") as f:
    f.write(content)
```

**步骤 4**: 修改 metadata 存储（约第 128-137 行）：

```python
# 修改前
metadata = {
    "id": doc_id,
    "kb_id": kb_id,
    "filename": file.filename,
    "file_path": str(file_path),
    # ...
}

# 修改后
metadata = {
    "id": doc_id,
    "kb_id": kb_id,
    "original_filename": file.filename,  # 原始文件名（用于显示）
    "stored_filename": stored_filename,   # 实际存储的文件名
    "file_path": str(file_path),
    "file_size": file_size,
    "status": DocumentStatus.PENDING.value,
    "created_at": timestamp.isoformat(),
    "updated_at": None
}
```

### 验收标准
1. 尝试上传文件名为 `../../../etc/passwd` 的文件
2. 确认文件被安全重命名并存储在正确目录
3. 确认无法遍历到上级目录

---

## Task 1.4: 修复 RAG 搜索重复执行

### 问题
每次聊天请求中，RAG 搜索被执行了两次（一次在主函数，一次在 generator）。

### 执行指令

**文件**: `backend/app/api/chat.py`

**步骤 1**: 修改 `chat_stream_generator` 函数签名（约第 77 行）：

```python
# 修改前
async def chat_stream_generator(
    request: ChatRequest, messages: List[dict]
) -> AsyncGenerator[str, None]:

# 修改后
async def chat_stream_generator(
    request: ChatRequest,
    messages: List[dict],
    pre_retrieved_results: Optional[List[dict]] = None
) -> AsyncGenerator[str, None]:
```

**步骤 2**: 修改 generator 内的 RAG 逻辑（约第 94-154 行）：

```python
# 修改前（约第 94-114 行）
# Step 1: RAG Retrieval (if kb_id provided)
if request.kb_id:
    yield format_sse_event("thought", {
        "type": "retrieval",
        "status": "start",
        "kb_id": request.kb_id,
        "query": request.message
    })

    try:
        rag_pipeline = get_rag_pipeline()
        yield format_sse_event("thought", {
            "type": "retrieval",
            "status": "searching",
            "kb_id": request.kb_id,
            "query": request.message
        })

        retrieved_results = rag_pipeline.search(
            request.kb_id, request.message, top_k=5
        )
        # ... 后续处理

# 修改后
# Step 1: Use pre-retrieved results or skip RAG
retrieved_results: List[dict] = pre_retrieved_results or []

if request.kb_id and pre_retrieved_results:
    # 已有检索结果，发送状态事件
    yield format_sse_event("thought", {
        "type": "retrieval",
        "status": "complete",
        "kb_id": request.kb_id,
        "query": request.message,
        "results_count": len(retrieved_results),
        "top_results": [
            {
                "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                "doc_id": r["metadata"].get("doc_id", ""),
                "score": r["score"]
            }
            for r in retrieved_results[:3]
        ]
    })

    # Send citations if results found
    if retrieved_results:
        sources = [
            {
                "doc_id": r["metadata"].get("doc_id", ""),
                "chunk_index": r["metadata"].get("chunk_index", 0),
                "score": r["score"]
            }
            for r in retrieved_results
        ]
        yield format_sse_event("citation", {"sources": sources})
```

**步骤 3**: 修改 `chat_completions` 函数，将搜索结果传递给 generator（约第 225-285 行）：

```python
# 找到这段代码（约第 229-240 行）
retrieved_context = None
if request.kb_id:
    try:
        rag_pipeline = get_rag_pipeline()
        results = rag_pipeline.search(request.kb_id, request.message, top_k=5)
        if results:
            context_parts = []
            for i, r in enumerate(results[:3], 1):
                context_parts.append(f"[{i}] {r['text']}")
            retrieved_context = "\n\n".join(context_parts)
    except Exception:
        pass  # Continue without RAG context if retrieval fails

# 修改为（保存 results 变量）
retrieved_results: List[dict] = []
retrieved_context = None
if request.kb_id:
    try:
        rag_pipeline = get_rag_pipeline()
        retrieved_results = rag_pipeline.search(request.kb_id, request.message, top_k=5)
        if retrieved_results:
            context_parts = []
            for i, r in enumerate(retrieved_results[:3], 1):
                context_parts.append(f"[{i}] {r['text']}")
            retrieved_context = "\n\n".join(context_parts)
    except Exception:
        pass

# 修改 stream_with_save 中的调用（约第 254 行）
# 修改前
async for chunk in chat_stream_generator(request, messages_for_llm):

# 修改后
async for chunk in chat_stream_generator(request, messages_for_llm, retrieved_results):
```

**步骤 4**: 在文件顶部添加 Optional 导入（如果还没有）：

```python
from typing import AsyncGenerator, List, Optional
```

### 验收标准
1. 发送一条带 kb_id 的聊天请求
2. 查看服务端日志，确认 RAG 搜索只执行了一次
3. 确认前端仍然收到 retrieval 思维链事件

---

# Phase 2: 核心功能（工作流引擎）

## Task 2.1: 创建工作流执行引擎核心模块

### 目标
实现工作流执行引擎，支持拓扑排序执行、变量传递、各类节点处理。

### 执行指令

**创建新文件**: `backend/app/core/workflow_engine.py`

```python
"""
Workflow Execution Engine

Supports:
- Topological sort execution
- Variable passing between nodes
- Condition branching
- Async streaming output
"""

from typing import Any, Dict, List, Optional, AsyncGenerator
from collections import deque
import re

from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.models.workflow import Workflow


class ExecutionContext:
    """Execution context for storing variables and intermediate results."""

    def __init__(self, initial_input: str):
        self.variables: Dict[str, Any] = {
            "input": initial_input,
        }
        self.step_outputs: Dict[str, Any] = {}

    def set_output(self, node_id: str, value: Any) -> None:
        """Set output for a node."""
        self.step_outputs[node_id] = value
        self.variables[f"{node_id}.output"] = value

    def get_variable(self, var_path: str) -> Any:
        """
        Resolve variable path like 'step1.output'.

        Args:
            var_path: Variable path (e.g., 'node_1.output')

        Returns:
            Variable value or None if not found
        """
        parts = var_path.split('.')
        current = self.variables
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def resolve_template(self, template: str) -> str:
        """
        Resolve template string with variable references {{var}}.

        Args:
            template: Template string with {{variable}} placeholders

        Returns:
            Resolved string with variables replaced
        """
        def replace_var(match):
            var_path = match.group(1)
            value = self.get_variable(var_path)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{(\w+(?:\.\w+)*)\}\}', replace_var, template)


class WorkflowEngine:
    """Workflow execution engine."""

    def __init__(self, workflow: Workflow):
        """
        Initialize the workflow engine.

        Args:
            workflow: Workflow model with graph_data
        """
        self.workflow = workflow
        self.nodes: Dict[str, dict] = {
            n["id"]: n for n in workflow.graph_data.nodes
        }
        self.edges: List[dict] = workflow.graph_data.edges
        self.adjacency = self._build_adjacency()

    def _build_adjacency(self) -> Dict[str, List[str]]:
        """Build adjacency list from edges."""
        adj: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target and source in adj:
                adj[source].append(target)
        return adj

    def _get_in_edges(self) -> Dict[str, List[str]]:
        """Build reverse adjacency (incoming edges)."""
        in_edges: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target and target in in_edges:
                in_edges[target].append(source)
        return in_edges

    def _topological_sort(self) -> List[str]:
        """
        Topological sort of nodes using Kahn's algorithm.

        Returns:
            List of node IDs in execution order

        Raises:
            ValueError: If workflow contains cycles
        """
        in_degree = {node_id: 0 for node_id in self.nodes}

        for edge in self.edges:
            target = edge.get("target")
            if target and target in in_degree:
                in_degree[target] += 1

        # Start with nodes that have no incoming edges
        queue = deque([
            node_id for node_id, degree in in_degree.items()
            if degree == 0
        ])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for neighbor in self.adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains cycles - cannot execute")

        return result

    def _get_source_nodes(self, node_id: str) -> List[str]:
        """Get all source nodes pointing to this node."""
        sources = []
        for edge in self.edges:
            if edge.get("target") == node_id:
                sources.append(edge.get("source"))
        return [s for s in sources if s]

    def _get_input_for_node(self, node_id: str, ctx: ExecutionContext) -> Any:
        """Get input value for a node from its source nodes."""
        source_nodes = self._get_source_nodes(node_id)

        # If multiple sources, use the first one with output
        for source_id in source_nodes:
            if source_id in ctx.step_outputs:
                return ctx.step_outputs[source_id]

        # Fall back to initial input
        return ctx.variables.get("input", "")

    async def _execute_start_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """Execute start node."""
        node_id = node["id"]

        yield {
            "type": "node_start",
            "node_id": node_id,
            "node_type": "start"
        }

        # Start node passes through the initial input
        data = node.get("data", {})
        input_var = data.get("inputVariable", "input")
        output = ctx.variables.get("input", "")

        ctx.set_output(node_id, output)

        yield {
            "type": "node_complete",
            "node_id": node_id,
            "output": output[:100] + "..." if len(str(output)) > 100 else output
        }

    async def _execute_llm_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """Execute LLM node."""
        node_id = node["id"]

        yield {
            "type": "node_start",
            "node_id": node_id,
            "node_type": "llm"
        }

        data = node.get("data", {})
        system_prompt = data.get("systemPrompt", "You are a helpful assistant.")
        temperature = data.get("temperature", 0.7)

        # Resolve variables in system prompt
        system_prompt = ctx.resolve_template(system_prompt)

        # Get input from source node
        input_text = self._get_input_for_node(node_id, ctx)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(input_text)}
        ]

        yield {
            "type": "thought",
            "node_id": node_id,
            "content": f"Calling LLM with temperature={temperature}"
        }

        output = ""
        try:
            async for token in chat_completion_stream(messages, temperature=temperature):
                output += token
                yield {
                    "type": "token",
                    "node_id": node_id,
                    "content": token
                }
        except Exception as e:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"LLM call failed: {str(e)}"
            }
            return

        ctx.set_output(node_id, output)

        yield {
            "type": "node_complete",
            "node_id": node_id,
            "output": output[:100] + "..." if len(output) > 100 else output
        }

    async def _execute_knowledge_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """Execute knowledge retrieval node."""
        node_id = node["id"]

        yield {
            "type": "node_start",
            "node_id": node_id,
            "node_type": "knowledge"
        }

        data = node.get("data", {})
        kb_id = data.get("knowledgeBaseId")

        if not kb_id:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": "Knowledge base not configured"
            }
            ctx.set_output(node_id, "")
            return

        # Get query from input
        query = str(self._get_input_for_node(node_id, ctx))

        yield {
            "type": "thought",
            "node_id": node_id,
            "content": f"Searching knowledge base: {kb_id}"
        }

        try:
            rag_pipeline = get_rag_pipeline()
            results = rag_pipeline.search(kb_id, query, top_k=5)

            # Format results as context
            context_parts = []
            for i, r in enumerate(results[:3], 1):
                context_parts.append(f"[{i}] {r['text']}")

            output = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
            ctx.set_output(node_id, output)

            yield {
                "type": "retrieval_result",
                "node_id": node_id,
                "results_count": len(results),
                "top_results": [
                    {
                        "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                        "score": r["score"]
                    }
                    for r in results[:3]
                ]
            }

            yield {
                "type": "node_complete",
                "node_id": node_id,
                "output": f"Found {len(results)} relevant chunks"
            }

        except Exception as e:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": str(e)
            }
            ctx.set_output(node_id, "")

    async def _execute_condition_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """Execute condition node."""
        node_id = node["id"]

        yield {
            "type": "node_start",
            "node_id": node_id,
            "node_type": "condition"
        }

        data = node.get("data", {})
        expression = data.get("expression", "true")

        # Resolve variables in expression
        resolved_expr = ctx.resolve_template(expression)

        yield {
            "type": "thought",
            "node_id": node_id,
            "content": f"Evaluating: {resolved_expr}"
        }

        # Simple safe evaluation
        result = self._safe_eval_condition(resolved_expr)

        ctx.set_output(node_id, result)

        yield {
            "type": "condition_result",
            "node_id": node_id,
            "expression": resolved_expr,
            "result": result,
            "branch": "true" if result else "false"
        }

        yield {
            "type": "node_complete",
            "node_id": node_id,
            "output": result
        }

    def _safe_eval_condition(self, expression: str) -> bool:
        """
        Safely evaluate a condition expression.
        Only supports simple comparisons, not arbitrary code.
        """
        expression = expression.strip()

        # Handle simple boolean strings
        if expression.lower() in ("true", "yes", "1"):
            return True
        if expression.lower() in ("false", "no", "0", ""):
            return False

        # Handle simple comparisons
        try:
            # Try equality check
            if "===" in expression or "==" in expression:
                parts = expression.replace("===", "==").split("==")
                if len(parts) == 2:
                    left = parts[0].strip().strip("'\"")
                    right = parts[1].strip().strip("'\"")
                    return left == right

            # Try inequality check
            if "!==" in expression or "!=" in expression:
                parts = expression.replace("!==", "!=").split("!=")
                if len(parts) == 2:
                    left = parts[0].strip().strip("'\"")
                    right = parts[1].strip().strip("'\"")
                    return left != right

            # Try contains check
            if " contains " in expression.lower():
                parts = expression.lower().split(" contains ")
                if len(parts) == 2:
                    left = parts[0].strip().strip("'\"")
                    right = parts[1].strip().strip("'\"")
                    return right in left

            # Default to truthy check
            return bool(expression)

        except Exception:
            return False

    async def _execute_end_node(
        self,
        node: dict,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """Execute end node."""
        node_id = node["id"]

        yield {
            "type": "node_start",
            "node_id": node_id,
            "node_type": "end"
        }

        # Collect output from source nodes
        final_output = self._get_input_for_node(node_id, ctx)

        data = node.get("data", {})
        output_var = data.get("outputVariable", "result")

        ctx.set_output(node_id, final_output)
        ctx.variables[output_var] = final_output

        yield {
            "type": "node_complete",
            "node_id": node_id,
            "output": str(final_output)[:100] + "..." if len(str(final_output)) > 100 else final_output
        }

        yield {
            "type": "workflow_complete",
            "final_output": final_output,
            "output_variable": output_var
        }

    async def _execute_node(
        self,
        node_id: str,
        ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        """Execute a single node based on its type."""
        if node_id not in self.nodes:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"Node not found: {node_id}"
            }
            return

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

    async def execute(self, initial_input: str) -> AsyncGenerator[dict, None]:
        """
        Execute the entire workflow.

        Args:
            initial_input: Initial input string

        Yields:
            Execution events including:
            - workflow_start
            - node_start
            - token (LLM output chunks)
            - thought (processing status)
            - retrieval_result (knowledge search results)
            - condition_result (condition evaluation)
            - node_complete
            - node_error
            - workflow_complete
            - workflow_error
        """
        yield {
            "type": "workflow_start",
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name,
            "node_count": len(self.nodes)
        }

        if not self.nodes:
            yield {
                "type": "workflow_error",
                "error": "Workflow has no nodes"
            }
            return

        try:
            execution_order = self._topological_sort()
            ctx = ExecutionContext(initial_input)

            yield {
                "type": "thought",
                "content": f"Execution order: {' -> '.join(execution_order)}"
            }

            for node_id in execution_order:
                async for event in self._execute_node(node_id, ctx):
                    yield event

                    # Stop on error
                    if event.get("type") == "node_error":
                        yield {
                            "type": "workflow_error",
                            "error": event.get("error"),
                            "failed_node": node_id
                        }
                        return

        except ValueError as e:
            yield {
                "type": "workflow_error",
                "error": str(e)
            }
        except Exception as e:
            yield {
                "type": "workflow_error",
                "error": f"Unexpected error: {str(e)}"
            }
```

### 验收标准
1. 文件创建成功
2. 无 Python 语法错误
3. 导入测试通过: `python -c "from app.core.workflow_engine import WorkflowEngine"`

---

## Task 2.2: 修改 Chat API 支持工作流执行

### 目标
当请求包含 workflow_id 时，使用工作流引擎执行而非普通对话。

### 执行指令

**文件**: `backend/app/api/chat.py`

**步骤 1**: 添加导入（在文件顶部）：

```python
from app.core.workflow_engine import WorkflowEngine
from app.api.workflow import get_workflow  # 确保这个函数存在
```

**步骤 2**: 添加工作流流式处理函数（在 `chat_stream_generator` 函数后面）：

```python
async def workflow_stream_generator(
    request: ChatRequest,
    session: SessionHistory
) -> AsyncGenerator[str, None]:
    """
    Execute workflow and stream results.

    Args:
        request: Chat request with workflow_id
        session: Session history for saving messages

    Yields:
        SSE formatted events
    """
    # Load workflow
    try:
        from app.api.workflow import load_workflows, workflow_to_model
        data = load_workflows()
        workflows = data.get("workflows", {})

        if request.workflow_id not in workflows:
            yield format_sse_event("error", {
                "message": f"Workflow not found: {request.workflow_id}"
            })
            yield format_sse_event("done", {"status": "error"})
            return

        workflow = workflow_to_model(request.workflow_id, workflows[request.workflow_id])
    except Exception as e:
        yield format_sse_event("error", {
            "message": f"Failed to load workflow: {str(e)}"
        })
        yield format_sse_event("done", {"status": "error"})
        return

    # Create engine and execute
    engine = WorkflowEngine(workflow)
    full_output = ""
    has_error = False

    async for event in engine.execute(request.message):
        event_type = event.get("type", "unknown")

        if event_type == "workflow_start":
            yield format_sse_event("thought", {
                "type": "workflow",
                "status": "start",
                "workflow_name": event.get("workflow_name"),
                "node_count": event.get("node_count")
            })

        elif event_type == "node_start":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "start",
                "node_id": event.get("node_id"),
                "node_type": event.get("node_type")
            })

        elif event_type == "token":
            content = event.get("content", "")
            full_output += content
            yield format_sse_event("token", {"content": content})

        elif event_type == "thought":
            yield format_sse_event("thought", {
                "type": "thinking",
                "node_id": event.get("node_id"),
                "content": event.get("content")
            })

        elif event_type == "retrieval_result":
            yield format_sse_event("thought", {
                "type": "retrieval",
                "status": "complete",
                "results_count": event.get("results_count"),
                "top_results": event.get("top_results")
            })

        elif event_type == "condition_result":
            yield format_sse_event("thought", {
                "type": "condition",
                "expression": event.get("expression"),
                "result": event.get("result"),
                "branch": event.get("branch")
            })

        elif event_type == "node_complete":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "complete",
                "node_id": event.get("node_id")
            })

        elif event_type == "node_error":
            has_error = True
            yield format_sse_event("error", {
                "node_id": event.get("node_id"),
                "message": event.get("error")
            })

        elif event_type == "workflow_complete":
            final_output = event.get("final_output", full_output)

            # Save assistant message
            assistant_message = ChatMessage(
                role="assistant",
                content=str(final_output) if final_output else full_output,
                timestamp=datetime.utcnow()
            )
            session.messages.append(assistant_message)
            save_session(session)

            yield format_sse_event("done", {
                "status": "success",
                "message": "Workflow completed"
            })

        elif event_type == "workflow_error":
            has_error = True
            yield format_sse_event("error", {
                "message": event.get("error"),
                "failed_node": event.get("failed_node")
            })
            yield format_sse_event("done", {
                "status": "error",
                "message": event.get("error")
            })

    # If no explicit done event was sent
    if not has_error and full_output:
        yield format_sse_event("done", {
            "status": "success",
            "message": "Workflow completed"
        })
```

**步骤 3**: 修改 `chat_completions` 函数支持工作流分支（约第 177 行）：

```python
@router.post("/completions")
async def chat_completions(request: ChatRequest) -> StreamingResponse:
    """
    SSE streaming chat completion endpoint.

    Supports:
    - Simple chat (no workflow_id, no kb_id)
    - RAG-enhanced chat (with kb_id)
    - Workflow execution (with workflow_id)
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    # Load or create session
    session = load_session(request.session_id)
    if session is None:
        session = SessionHistory(
            session_id=request.session_id,
            kb_id=request.kb_id,
            workflow_id=request.workflow_id
        )

    # Update session metadata
    if request.kb_id:
        session.kb_id = request.kb_id
    if request.workflow_id:
        session.workflow_id = request.workflow_id

    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    session.messages.append(user_message)

    # Choose execution mode
    if request.workflow_id:
        # Workflow execution mode
        return StreamingResponse(
            workflow_stream_generator(request, session),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Standard RAG/chat mode (existing logic)
        # ... 保持现有的 RAG 对话逻辑不变 ...

        # Prepare messages for LLM
        messages_for_llm: List[dict] = []

        # RAG retrieval
        retrieved_results: List[dict] = []
        retrieved_context = None
        if request.kb_id:
            try:
                rag_pipeline = get_rag_pipeline()
                retrieved_results = rag_pipeline.search(request.kb_id, request.message, top_k=5)
                if retrieved_results:
                    context_parts = []
                    for i, r in enumerate(retrieved_results[:3], 1):
                        context_parts.append(f"[{i}] {r['text']}")
                    retrieved_context = "\n\n".join(context_parts)
            except Exception:
                pass

        system_prompt = build_system_prompt(bool(request.kb_id), retrieved_context)
        messages_for_llm.append({"role": "system", "content": system_prompt})

        # Add conversation history (last 10 messages)
        for msg in session.messages[-10:]:
            messages_for_llm.append({"role": msg.role, "content": msg.content})

        async def stream_with_save():
            assistant_content = ""

            async for chunk in chat_stream_generator(request, messages_for_llm, retrieved_results):
                if chunk.startswith("event: token"):
                    try:
                        lines = chunk.strip().split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                data = json.loads(line[6:])
                                assistant_content += data.get("content", "")
                    except (json.JSONDecodeError, IndexError):
                        pass
                yield chunk

            if assistant_content:
                assistant_message = ChatMessage(
                    role="assistant",
                    content=assistant_content,
                    timestamp=datetime.utcnow()
                )
                session.messages.append(assistant_message)
                save_session(session)

        return StreamingResponse(
            stream_with_save(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
```

### 验收标准
1. 发送不带 workflow_id 的请求，正常进行 RAG 对话
2. 发送带 workflow_id 的请求，执行工作流
3. 工作流执行过程中能看到 thought 事件
4. 工作流执行完成后消息被保存到会话

---

## Task 2.3: 前端添加工作流/知识库选择器

### 目标
在 ChatTerminal 中添加工作流和知识库选择功能。

### 执行指令

**文件**: `frontend/src/views/ChatTerminal.vue`

**步骤 1**: 在 template 的 input-area 之前添加选择器（约第 57 行前）：

```vue
<!-- 在 </div> <!-- messages-container --> 之后，<div class="input-area"> 之前添加 -->

<!-- 配置区域 -->
<div class="config-bar">
  <div class="config-item">
    <label>工作流:</label>
    <select v-model="selectedWorkflowId" :disabled="isStreaming">
      <option value="">无（普通对话）</option>
      <option v-for="wf in workflows" :key="wf.id" :value="wf.id">
        {{ wf.name }}
      </option>
    </select>
  </div>
  <div class="config-item">
    <label>知识库:</label>
    <select v-model="selectedKbId" :disabled="isStreaming || !!selectedWorkflowId">
      <option value="">无</option>
      <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
        {{ kb.name }}
      </option>
    </select>
  </div>
</div>
```

**步骤 2**: 在 script setup 中添加状态和加载函数（约第 100 行后）：

```typescript
// 新增状态
const selectedWorkflowId = ref<string>('')
const selectedKbId = ref<string>('')
const workflows = ref<{id: string, name: string}[]>([])
const knowledgeBases = ref<{id: string, name: string}[]>([])

// 加载工作流列表
async function loadWorkflows() {
  try {
    const response = await axios.get('/api/v1/workflows')
    workflows.value = (response.data.items || []).map((w: any) => ({
      id: w.id,
      name: w.name
    }))
  } catch (error) {
    console.error('加载工作流列表失败:', error)
  }
}

// 加载知识库列表
async function loadKnowledgeBases() {
  try {
    const response = await axios.get('/api/v1/knowledge')
    const items = response.data.items || response.data || []
    knowledgeBases.value = items.map((kb: any) => ({
      id: kb.id,
      name: kb.name
    }))
  } catch (error) {
    console.error('加载知识库列表失败:', error)
  }
}
```

**步骤 3**: 修改 onMounted 加载数据（约第 362 行）：

```typescript
onMounted(() => {
  if (sessions.value.length === 0) {
    createNewSession()
  }
  // 加载工作流和知识库列表
  loadWorkflows()
  loadKnowledgeBases()
})
```

**步骤 4**: 修改 connectSSE 函数传递参数（约第 207-218 行）：

```typescript
async function connectSSE(sessionId: string, message: string) {
  const response = await fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
      workflow_id: selectedWorkflowId.value || undefined,
      kb_id: selectedKbId.value || undefined,
    }),
  })
  // ... 后续代码不变
}
```

**步骤 5**: 在 style scoped 中添加样式（文件末尾）：

```css
/* 配置栏 */
.config-bar {
  display: flex;
  gap: 20px;
  padding: 12px 20px;
  background-color: #f8f9fa;
  border-top: 1px solid #e0e0e0;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-item label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

.config-item select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background-color: white;
  min-width: 150px;
  cursor: pointer;
}

.config-item select:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.config-item select:focus {
  outline: none;
  border-color: #2c3e50;
}
```

### 验收标准
1. 页面加载后能看到工作流和知识库选择器
2. 选择器能正确加载后端数据
3. 选择工作流后发送消息，请求中包含 workflow_id
4. 选择知识库后发送消息，请求中包含 kb_id

---

## Task 2.4: 处理工作流执行的前端事件

### 目标
在 ChatTerminal 中正确处理工作流执行的各种 SSE 事件。

### 执行指令

**文件**: `frontend/src/views/ChatTerminal.vue`

**修改 handleSSEEvent 函数（约第 273-330 行）**：

```typescript
function handleSSEEvent(eventType: string, data: any, lastMessage: Message | undefined) {
  if (!lastMessage || lastMessage.role !== 'assistant') return

  switch (eventType) {
    case 'thought':
      // 处理各类思维链事件
      if (data.type === 'workflow') {
        if (data.status === 'start') {
          currentThought.value = `🚀 开始执行工作流: ${data.workflow_name}`
        }
      } else if (data.type === 'node') {
        if (data.status === 'start') {
          const nodeLabels: Record<string, string> = {
            start: '开始',
            llm: 'LLM',
            knowledge: '知识库',
            condition: '条件',
            end: '结束'
          }
          const label = nodeLabels[data.node_type] || data.node_type
          currentThought.value = `⚙️ 执行节点: ${label}`
        } else if (data.status === 'complete') {
          currentThought.value = `✅ 节点完成: ${data.node_id}`
        }
      } else if (data.type === 'retrieval') {
        if (data.status === 'start') {
          currentThought.value = '🔍 正在检索知识库...'
        } else if (data.status === 'searching') {
          currentThought.value = '🔍 正在搜索相关文档...'
        } else if (data.status === 'complete') {
          const count = data.results_count || 0
          currentThought.value = `📚 检索完成，找到 ${count} 个相关片段`
          setTimeout(() => {
            if (currentThought.value.includes('检索完成')) {
              currentThought.value = ''
            }
          }, 2000)
        } else if (data.status === 'error') {
          currentThought.value = '❌ 检索出错: ' + (data.error || '未知错误')
        }
      } else if (data.type === 'condition') {
        currentThought.value = `🔀 条件判断: ${data.expression} → ${data.branch}`
      } else if (data.type === 'thinking') {
        currentThought.value = `💭 ${data.content}`
      } else if (data.content) {
        currentThought.value = data.content
      }
      break

    case 'token':
      // 打字机效果
      lastMessage.content += data.content
      scrollToBottom()
      break

    case 'citation':
      // 引用来源
      if (data.sources && Array.isArray(data.sources)) {
        const citations = data.sources.map((s: any, i: number) =>
          `[引用${i + 1}] doc:${s.doc_id?.slice(0, 8)}, score:${(s.score || 0).toFixed(2)}`
        ).join('\n')
        // 不直接追加到消息，可以存储起来用于显示
        console.log('Citations:', citations)
      }
      break

    case 'error':
      // 错误处理
      const errorMsg = data.message || data.content || '未知错误'
      lastMessage.content += `\n\n❌ 错误: ${errorMsg}`
      currentThought.value = `❌ ${errorMsg}`
      break

    case 'done':
      // 完成
      isStreaming.value = false
      lastMessage.isStreaming = false
      if (data.status === 'success') {
        currentThought.value = ''
      } else {
        currentThought.value = `⚠️ ${data.message || '执行结束'}`
      }
      break

    default:
      console.log('Unknown SSE event:', eventType, data)
  }
}
```

### 验收标准
1. 执行工作流时能看到节点执行的状态提示
2. LLM 节点的输出能正确显示打字机效果
3. 错误能正确显示
4. 工作流完成后状态正确重置

---

## Task 2.5: 添加工作流执行 API 端点

### 目标
添加一个独立的工作流测试执行端点（非聊天模式）。

### 执行指令

**文件**: `backend/app/api/workflow.py`

**在文件末尾添加**：

```python
from fastapi.responses import StreamingResponse
from app.core.workflow_engine import WorkflowEngine
import json


def format_sse(event: str, data: dict) -> str:
    """Format SSE event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    input_data: dict
) -> StreamingResponse:
    """
    Execute a workflow with given input.

    This endpoint is for testing workflows directly without going through chat.

    - **workflow_id**: Workflow ID to execute
    - **input_data**: JSON body with 'input' field containing the initial input

    Returns SSE stream of execution events.
    """
    data = load_workflows()
    workflows = data.get("workflows", {})

    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    workflow = workflow_to_model(workflow_id, workflows[workflow_id])
    initial_input = input_data.get("input", "")

    if not initial_input:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    async def generate():
        engine = WorkflowEngine(workflow)

        async for event in engine.execute(initial_input):
            event_type = event.pop("type", "unknown")
            yield format_sse(event_type, event)

        yield format_sse("done", {"status": "complete"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### 验收标准
1. 可以通过 `POST /api/v1/workflows/{id}/execute` 执行工作流
2. 返回 SSE 格式的执行事件流
3. Swagger 文档中能看到该端点

---

## Task 2.6: 修复工作流 API 导入依赖

### 目标
确保 workflow.py 中可以正确导入 workflow_engine。

### 执行指令

**文件**: `backend/app/api/workflow.py`

**在文件顶部添加条件导入（避免循环依赖）**：

```python
# 在现有导入之后添加
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.workflow_engine import WorkflowEngine
```

**在 execute_workflow 函数内部进行实际导入**：

```python
@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    input_data: dict
) -> StreamingResponse:
    # 在函数内部导入以避免循环依赖
    from app.core.workflow_engine import WorkflowEngine

    # ... 函数其余部分
```

### 验收标准
1. 服务器启动无导入错误
2. 执行工作流端点正常工作

---

# Phase 3: 功能完善

## Task 3.1: 添加知识库删除 API

### 执行指令

**文件**: `backend/app/api/knowledge.py`

**在文件末尾添加**：

```python
import shutil


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: str) -> None:
    """
    Delete a knowledge base and all its documents.

    This will:
    1. Delete the ChromaDB collection
    2. Delete all uploaded files
    3. Delete all metadata
    4. Remove from knowledge base index

    - **kb_id**: Knowledge base ID to delete
    """
    # Check if knowledge base exists
    metadata = load_kb_metadata()
    if kb_id not in metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{kb_id}' not found"
        )

    project_root = Path(__file__).parent.parent.parent

    # 1. Delete ChromaDB collection
    try:
        chroma_client = get_chroma_client()
        chroma_client.delete_collection(kb_id)
    except Exception as e:
        print(f"Warning: Failed to delete ChromaDB collection: {e}")

    # 2. Delete uploaded files
    upload_dir = project_root / "data" / "uploads" / kb_id
    if upload_dir.exists():
        try:
            shutil.rmtree(upload_dir)
        except Exception as e:
            print(f"Warning: Failed to delete upload directory: {e}")

    # 3. Delete metadata directory
    metadata_dir = project_root / "data" / "metadata" / kb_id
    if metadata_dir.exists():
        try:
            shutil.rmtree(metadata_dir)
        except Exception as e:
            print(f"Warning: Failed to delete metadata directory: {e}")

    # 4. Remove from index
    del metadata[kb_id]
    save_kb_metadata(metadata)
```

### 验收标准
1. 可以通过 `DELETE /api/v1/knowledge/{kb_id}` 删除知识库
2. 删除后 ChromaDB collection 不存在
3. 删除后上传文件夹被清理
4. 删除后元数据被清理

---

## Task 3.2: 修复相似度分数计算

### 执行指令

**文件**: `backend/app/core/rag.py`

**修改 search 方法中的相似度计算（约第 180-194 行）**：

```python
# 修改前
distance = results["distances"][0][i] if results["distances"] else 0
similarity = max(0, 1 - distance)

# 修改后
distance = results["distances"][0][i] if results["distances"] else 0
# ChromaDB uses L2 distance by default
# For normalized vectors, L2 distance ranges from 0 to 2
# Convert to similarity score using inverse relationship
# This formula gives: distance=0 -> similarity=1, distance=2 -> similarity=0.33
similarity = 1 / (1 + distance)
```

### 验收标准
1. 相似度分数在 0-1 范围内
2. 距离越近，相似度越高
3. 不会出现负数分数

---

## Task 3.3: 改进会话列表 API

### 目标
添加获取会话列表的 API，以便前端可以恢复会话。

### 执行指令

**文件**: `backend/app/api/chat.py`

**在 router 定义后添加**：

```python
@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    offset: int = 0
) -> dict:
    """
    List all chat sessions.

    - **limit**: Maximum number of sessions to return (default: 20)
    - **offset**: Number of sessions to skip (default: 0)
    """
    sessions_list = []

    if SESSIONS_DIR.exists():
        session_files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for session_file in session_files[offset:offset + limit]:
            try:
                session_id = session_file.stem
                session = load_session(session_id)
                if session:
                    # Get title from first user message or use default
                    title = "新会话"
                    for msg in session.messages:
                        if msg.role == "user":
                            title = msg.content[:30] + ("..." if len(msg.content) > 30 else "")
                            break

                    sessions_list.append({
                        "session_id": session.session_id,
                        "title": title,
                        "message_count": len(session.messages),
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                        "kb_id": session.kb_id,
                        "workflow_id": session.workflow_id
                    })
            except Exception:
                continue

    return {
        "sessions": sessions_list,
        "total": len(list(SESSIONS_DIR.glob("*.json"))) if SESSIONS_DIR.exists() else 0,
        "limit": limit,
        "offset": offset
    }
```

### 验收标准
1. `GET /api/v1/chat/sessions` 返回会话列表
2. 列表按更新时间倒序排列
3. 包含会话标题和消息数量

---

## Task 3.4: 防止文件覆盖

### 执行指令

此任务已在 Task 1.3 中完成（使用 UUID 前缀生成唯一文件名）。

### 验收标准
1. 上传同名文件不会覆盖已有文件
2. 每个文件有唯一的存储名称

---

# Phase 4: 稳定性优化

## Task 4.1: 添加 JSON 文件并发锁

### 执行指令

**步骤 1**: 安装 filelock 依赖

```bash
cd backend
uv add filelock
# 或者
pip install filelock
```

**步骤 2**: 修改 `backend/app/api/workflow.py`

```python
# 在文件顶部添加导入
from filelock import FileLock

# 修改 load_workflows 函数
def load_workflows() -> dict:
    """Load workflows from JSON file with file locking."""
    ensure_data_dir()
    lock = FileLock(str(WORKFLOW_FILE) + ".lock", timeout=10)

    with lock:
        if not WORKFLOW_FILE.exists():
            return {"workflows": {}}
        try:
            with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"workflows": {}}


# 修改 save_workflows 函数
def save_workflows(data: dict) -> None:
    """Save workflows to JSON file with file locking."""
    ensure_data_dir()
    lock = FileLock(str(WORKFLOW_FILE) + ".lock", timeout=10)

    with lock:
        with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

**步骤 3**: 对 `backend/app/api/knowledge.py` 进行类似修改

```python
from filelock import FileLock

def load_kb_metadata() -> dict:
    lock = FileLock(str(KB_METADATA_FILE) + ".lock", timeout=10)
    with lock:
        if not KB_METADATA_FILE.exists():
            return {}
        try:
            with open(KB_METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_kb_metadata(metadata: dict) -> None:
    KB_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(KB_METADATA_FILE) + ".lock", timeout=10)
    with lock:
        with open(KB_METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_documents_metadata(kb_id: str) -> dict:
    metadata_path = get_metadata_path(kb_id)
    lock = FileLock(str(metadata_path) + ".lock", timeout=10)
    with lock:
        if not metadata_path.exists():
            return {}
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_documents_metadata(kb_id: str, metadata: dict) -> None:
    metadata_path = get_metadata_path(kb_id)
    lock = FileLock(str(metadata_path) + ".lock", timeout=10)
    with lock:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
```

### 验收标准
1. 并发请求不会导致数据丢失
2. 锁文件超时后能正确释放

---

## Task 4.2: 修复全局单例线程安全

### 执行指令

**文件**: `backend/app/core/rag.py`

```python
# 修改文件末尾的单例实现
import threading

_rag_pipeline: Optional[RAGPipeline] = None
_rag_pipeline_lock = threading.Lock()


def get_rag_pipeline() -> RAGPipeline:
    """Get the global RAG pipeline instance (thread-safe)."""
    global _rag_pipeline

    if _rag_pipeline is None:
        with _rag_pipeline_lock:
            # Double-checked locking
            if _rag_pipeline is None:
                _rag_pipeline = RAGPipeline()

    return _rag_pipeline
```

**文件**: `backend/app/core/chroma_client.py`

```python
# 修改文件末尾的单例实现
import threading

_chroma_client: Optional[ChromaClient] = None
_chroma_client_lock = threading.Lock()


def get_chroma_client() -> ChromaClient:
    """Get the global ChromaDB client instance (thread-safe)."""
    global _chroma_client

    if _chroma_client is None:
        with _chroma_client_lock:
            if _chroma_client is None:
                _chroma_client = ChromaClient()

    return _chroma_client
```

### 验收标准
1. 高并发下不会创建多个实例
2. 无 race condition 错误

---

## Task 4.3: 改进 Session ID 生成

### 执行指令

**文件**: `frontend/src/views/ChatTerminal.vue`

```typescript
// 修改 generateId 函数
function generateId(): string {
  // 使用 crypto API 生成安全的随机 ID
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}
```

### 验收标准
1. 生成的 ID 长度为 32 个十六进制字符
2. ID 不可预测

---

# 执行检查清单

## Phase 1 完成检查
- [ ] Task 1.1: 保存工作流时 data 字段被正确保存
- [ ] Task 1.2: 删除文档后向量数据被清理
- [ ] Task 1.3: 无法上传带路径遍历的文件名
- [ ] Task 1.4: RAG 搜索只执行一次

## Phase 2 完成检查
- [ ] Task 2.1: workflow_engine.py 创建成功
- [ ] Task 2.2: Chat API 支持 workflow_id 参数
- [ ] Task 2.3: 前端有工作流/知识库选择器
- [ ] Task 2.4: 工作流执行事件正确显示
- [ ] Task 2.5: /execute 端点可用
- [ ] Task 2.6: 无循环导入错误

## Phase 3 完成检查
- [ ] Task 3.1: 知识库删除 API 可用
- [ ] Task 3.2: 相似度分数合理
- [ ] Task 3.3: 会话列表 API 可用
- [ ] Task 3.4: 文件不会被覆盖

## Phase 4 完成检查
- [ ] Task 4.1: JSON 文件操作有锁保护
- [ ] Task 4.2: 单例模式线程安全
- [ ] Task 4.3: Session ID 使用 crypto API

---

# 测试脚本

## 测试工作流执行

```bash
# 1. 创建测试工作流
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "A simple test workflow",
    "graph_data": {
      "nodes": [
        {"id": "1", "type": "start", "position": {"x": 100, "y": 100}, "data": {}},
        {"id": "2", "type": "llm", "position": {"x": 300, "y": 100}, "data": {"systemPrompt": "You are a helpful assistant. Be concise.", "temperature": 0.7}},
        {"id": "3", "type": "end", "position": {"x": 500, "y": 100}, "data": {}}
      ],
      "edges": [
        {"id": "e1-2", "source": "1", "target": "2"},
        {"id": "e2-3", "source": "2", "target": "3"}
      ]
    }
  }'

# 记录返回的 workflow_id

# 2. 执行工作流
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"input": "What is 2+2?"}' \
  --no-buffer

# 3. 通过 Chat API 执行工作流
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-1",
    "message": "Hello, how are you?",
    "workflow_id": "{workflow_id}"
  }' \
  --no-buffer
```

## 测试知识库删除

```bash
# 1. 创建知识库
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -d '{"name": "Test KB"}'

# 记录返回的 kb_id

# 2. 上传文档
curl -X POST http://localhost:8000/api/v1/knowledge/{kb_id}/upload \
  -F "file=@test.txt"

# 3. 等待处理完成，搜索测试
curl "http://localhost:8000/api/v1/knowledge/{kb_id}/search?query=test"

# 4. 删除知识库
curl -X DELETE http://localhost:8000/api/v1/knowledge/{kb_id}

# 5. 确认删除成功
curl http://localhost:8000/api/v1/knowledge
```
