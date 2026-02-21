"""
Workflow node execution helpers.
"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Callable

from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.core.skill_executor import get_skill_executor
from app.core.skill_loader import SkillLoader
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
    skill_name = data.get("skillName")

    system_prompt = data.get("systemPrompt", "You are a helpful assistant.")
    temperature = data.get("temperature", 0.7)

    if skill_name:
        try:
            from pathlib import Path
            from app.core.config import settings

            skills_dir = Path(__file__).parent.parent.parent / "data" / "skills"
            skill_loader = SkillLoader(skills_dir)
            skill = skill_loader.get_skill(skill_name)

            if skill.prompt:
                system_prompt = skill.prompt

            if skill.model:
                temperature = skill.model.temperature if skill.model.temperature is not None else temperature

            yield {
                "type": "thought",
                "type_detail": "skill_loaded",
                "node_id": node_id,
                "skill_name": skill_name,
                "has_prompt": bool(skill.prompt),
                "has_model_config": bool(skill.model)
            }
        except Exception as exc:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"Failed to load skill '{skill_name}': {exc}"
            }
            ctx.set_output(node_id, "")
            return

    system_prompt = ctx.resolve_template(system_prompt)
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


async def execute_skill_node(
    node: dict, ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict, None]:
    """Execute a skill node with input mapping from upstream nodes."""
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "skill"}

    data = node.get("data", {})
    skill_name = data.get("skillName")
    input_mappings = data.get("inputMappings", {})  # Map skill input name -> upstream node id

    if not skill_name:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": "Skill not selected"
        }
        ctx.set_output(node_id, "")
        return

    # Load the skill
    try:
        from pathlib import Path
        from app.core.config import settings

        skills_dir = Path(__file__).parent.parent.parent / "data" / "skills"
        skill_loader = SkillLoader(skills_dir)
        skill = skill_loader.get_skill(skill_name)
    except Exception as exc:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": f"Failed to load skill '{skill_name}': {exc}"
        }
        ctx.set_output(node_id, "")
        return

    # Build inputs from mappings
    # input_mappings: { "skill_input_name": "upstream_node_id" }
    inputs: dict[str, str] = {}
    for skill_input_name, source_ref in input_mappings.items():
        if isinstance(source_ref, str):
            # source_ref can be a node ID - get output from that node
            if source_ref in ctx.step_outputs:
                inputs[skill_input_name] = str(ctx.step_outputs[source_ref])
            else:
                # Try to resolve as template variable
                resolved = ctx.resolve_template(f"{{{{{source_ref}}}}}")
                inputs[skill_input_name] = resolved
        else:
            # Direct value
            inputs[skill_input_name] = str(source_ref)

    # If no mappings but skill has inputs, use the node's direct input
    if not inputs and skill.inputs:
        upstream_input = get_input(node_id, ctx)
        # Map to first required input or first input
        target_input = None
        for inp in skill.inputs:
            if getattr(inp, "required", False):
                target_input = getattr(inp, "name", "")
                break
        if not target_input and skill.inputs:
            target_input = getattr(skill.inputs[0], "name", "")
        if target_input:
            inputs[target_input] = str(upstream_input)

    # Execute the skill
    executor = get_skill_executor()
    output_parts = []

    try:
        async for event_str in executor.execute(skill, inputs):
            # Parse SSE event string
            lines = event_str.strip().split("\n")
            event_type = None
            event_data = {}

            for line in lines:
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                elif line.startswith("data: "):
                    try:
                        event_data = __import__("json").loads(line[6:])
                    except Exception:
                        event_data = {"content": line[6:]}

            if event_type == "token" and "content" in event_data:
                output_parts.append(event_data["content"])
                yield {
                    "type": "token",
                    "node_id": node_id,
                    "content": event_data["content"]
                }
            elif event_type == "thought":
                yield {
                    "type": "thought",
                    "type_detail": event_data.get("type", "skill_execution"),
                    "node_id": node_id,
                    **{k: v for k, v in event_data.items() if k != "type"}
                }
            elif event_type == "citation":
                yield {
                    "type": "citation",
                    "node_id": node_id,
                    **event_data
                }
            elif event_type == "done":
                if event_data.get("status") == "error":
                    yield {
                        "type": "node_error",
                        "node_id": node_id,
                        "error": event_data.get("message", "Skill execution failed")
                    }
                    ctx.set_output(node_id, "")
                    return

    except Exception as exc:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": f"Skill execution failed: {exc}"
        }
        ctx.set_output(node_id, "")
        return

    final_output = "".join(output_parts)
    ctx.set_output(node_id, final_output)
    yield {"type": "node_complete", "node_id": node_id, "output": final_output}
