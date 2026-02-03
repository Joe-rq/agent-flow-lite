"""
Workflow node execution helpers.
"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Callable

from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.core.workflow_context import ExecutionContext, safe_eval


GetInput = Callable[[str, ExecutionContext], Any]


async def execute_start_node(
    node: dict, ctx: ExecutionContext
) -> AsyncGenerator[dict, None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "start"}

    data = node.get("data", {})
    input_var = data.get("inputVariable")
    value = ctx.variables.get("input", "")
    if input_var:
        ctx.variables[input_var] = value

    ctx.set_output(node_id, value)
    yield {"type": "node_complete", "node_id": node_id, "output": value}


async def execute_llm_node(
    node: dict, ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict, None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "llm"}

    data = node.get("data", {})
    system_prompt = ctx.resolve_template(
        data.get("systemPrompt", "You are a helpful assistant.")
    )
    temperature = data.get("temperature", 0.7)
    input_text = get_input(node_id, ctx)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": str(input_text)}
    ]

    output = ""
    try:
        async for token in chat_completion_stream(messages, temperature=temperature):
            output += token
            yield {"type": "token", "node_id": node_id, "content": token}
    except Exception as exc:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": f"LLM call failed: {exc}"
        }
        return

    ctx.set_output(node_id, output)
    yield {"type": "node_complete", "node_id": node_id, "output": output}


async def execute_knowledge_node(
    node: dict, ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict, None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "knowledge"}

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

    query = str(get_input(node_id, ctx))
    yield {
        "type": "thought",
        "type_detail": "retrieval",
        "status": "start",
        "node_id": node_id,
        "kb_id": kb_id,
        "query": query
    }

    try:
        rag_pipeline = get_rag_pipeline()
        results = rag_pipeline.search(kb_id, query, top_k=5)

        context_parts = []
        for i, result in enumerate(results[:3], 1):
            context_parts.append(f"[{i}] {result['text']}")
        output = "\n\n".join(context_parts) if context_parts else ""

        ctx.set_output(node_id, output)
        yield {
            "type": "thought",
            "type_detail": "retrieval",
            "status": "complete",
            "node_id": node_id,
            "results_count": len(results)
        }
        yield {"type": "node_complete", "node_id": node_id, "output": output}
    except Exception as exc:
        yield {"type": "node_error", "node_id": node_id, "error": str(exc)}
        ctx.set_output(node_id, "")


async def execute_condition_node(
    node: dict, ctx: ExecutionContext
) -> AsyncGenerator[dict, None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "condition"}

    data = node.get("data", {})
    expression = data.get("expression", "true")
    resolved = ctx.resolve_expression(expression)
    result = safe_eval(resolved)

    ctx.set_output(node_id, result)
    yield {
        "type": "thought",
        "type_detail": "condition",
        "node_id": node_id,
        "expression": resolved,
        "branch": "true" if result else "false"
    }
    yield {"type": "node_complete", "node_id": node_id, "output": result}


async def execute_end_node(
    node: dict, ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict, None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "end"}

    output = get_input(node_id, ctx)
    ctx.set_output(node_id, output)
    yield {"type": "node_complete", "node_id": node_id, "output": output}
    yield {"type": "workflow_complete", "final_output": output}
