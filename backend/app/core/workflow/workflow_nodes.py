"""
Workflow node execution helpers.
"""

from __future__ import annotations

import json
import logging
import asyncio
from typing import Any, AsyncGenerator, Callable

import httpx

from app.core.config import settings
from app.core.feature_flags import is_feature_enabled
from app.core.llm import chat_completion_stream
from app.core.paths import SKILLS_DIR
from app.core.rag import get_rag_pipeline
from app.core.skill.skill_executor import get_skill_executor
from app.core.skill.skill_loader import SkillLoader
from app.core.workflow.workflow_context import ExecutionContext, safe_eval
from app.utils.code_sandbox import execute_python
from app.utils.ssrf_guard import create_ssrf_safe_client, ensure_url_safe

logger = logging.getLogger(__name__)


GetInput = Callable[[str, ExecutionContext], Any]


def _extract_json_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        part = part.strip()
        if not part:
            continue
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index < 0 or index >= len(current):
                return None
            current = current[index]
        else:
            return None
    return current


async def execute_start_node(
    node: dict[str, Any], ctx: ExecutionContext
) -> AsyncGenerator[dict[str, Any], None]:
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
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "llm"}

    data = node.get("data", {})
    skill_name = data.get("skillName")

    system_prompt = data.get("systemPrompt", "You are a helpful assistant.")
    temperature = data.get("temperature", 0.7)
    target_model = data.get("model") or ctx.model
    inherit_chat_history = bool(data.get("inheritChatHistory", False))

    if skill_name:
        try:
            skill_loader = SkillLoader(SKILLS_DIR)
            skill = skill_loader.get_skill(skill_name)

            if skill.prompt:
                system_prompt = skill.prompt

            if skill.model:
                temperature = (
                    skill.model.temperature
                    if skill.model.temperature is not None
                    else temperature
                )

            yield {
                "type": "thought",
                "type_detail": "skill_loaded",
                "node_id": node_id,
                "skill_name": skill_name,
                "has_prompt": bool(skill.prompt),
                "has_model_config": bool(skill.model),
            }
        except Exception as exc:
            logger.warning(
                "Failed to load skill '%s' for LLM node '%s'",
                skill_name,
                node_id,
                exc_info=True,
            )
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"Failed to load skill '{skill_name}': {exc}",
            }
            ctx.set_output(node_id, "")
            return

    system_prompt = ctx.resolve_template(system_prompt)
    input_text = get_input(node_id, ctx)

    messages = [{"role": "system", "content": system_prompt}]
    if inherit_chat_history and ctx.conversation_history:
        messages.extend(ctx.conversation_history)
    messages.append({"role": "user", "content": str(input_text)})

    output = ""
    try:
        async for token in chat_completion_stream(
            messages,
            model=target_model,
            temperature=temperature,
            user_id=ctx.user_id,
        ):
            output += token
            yield {"type": "token", "node_id": node_id, "content": token}
    except Exception as exc:
        logger.warning("LLM call failed for node '%s'", node_id, exc_info=True)
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": f"LLM call failed: {exc}",
        }
        ctx.set_output(node_id, "")
        return

    ctx.set_output(node_id, output)
    yield {"type": "node_complete", "node_id": node_id, "output": output}


async def execute_knowledge_node(
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "knowledge"}

    data = node.get("data", {})
    kb_id = data.get("knowledgeBaseId")
    if not kb_id:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": "Knowledge base not configured",
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
        "query": query,
    }

    try:
        rag_pipeline = get_rag_pipeline()
        results = await rag_pipeline.search(kb_id, query, top_k=5)

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
            "results_count": len(results),
        }
        yield {"type": "node_complete", "node_id": node_id, "output": output}
    except Exception as exc:
        logger.warning(
            "Knowledge retrieval failed for node '%s'", node_id, exc_info=True
        )
        yield {"type": "node_error", "node_id": node_id, "error": str(exc)}
        ctx.set_output(node_id, "")


async def execute_condition_node(
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "condition"}

    data = node.get("data", {})
    expression = data.get("expression", "true")
    resolved = ctx.resolve_expression(expression)
    result = safe_eval(resolved)

    # Store boolean for branch routing (used by engine)
    ctx.variables[f"{node_id}.__branch"] = result
    # Pass through predecessor's output so downstream nodes get useful
    # content instead of a bare boolean.
    passthrough = get_input(node_id, ctx)
    ctx.set_output(node_id, passthrough)

    yield {
        "type": "thought",
        "type_detail": "condition",
        "node_id": node_id,
        "expression": resolved,
        "branch": "true" if result else "false",
    }
    yield {"type": "node_complete", "node_id": node_id, "output": passthrough}


async def execute_end_node(
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "end"}

    output = get_input(node_id, ctx)
    ctx.set_output(node_id, output)
    yield {"type": "node_complete", "node_id": node_id, "output": output}
    yield {"type": "workflow_complete", "final_output": output}


async def execute_skill_node(
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    """Execute a skill node with input mapping from upstream nodes."""
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "skill"}

    data = node.get("data", {})
    skill_name = data.get("skillName")
    input_mappings = data.get(
        "inputMappings", {}
    )  # Map skill input name -> upstream node id

    if not skill_name:
        yield {"type": "node_error", "node_id": node_id, "error": "Skill not selected"}
        ctx.set_output(node_id, "")
        return

    # Load the skill
    try:
        skill_loader = SkillLoader(SKILLS_DIR)
        skill = skill_loader.get_skill(skill_name)
    except Exception as exc:
        logger.warning(
            "Failed to load skill '%s' for skill node '%s'",
            skill_name,
            node_id,
            exc_info=True,
        )
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": f"Failed to load skill '{skill_name}': {exc}",
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
                        event_data = json.loads(line[6:])
                    except Exception:
                        event_data = {"content": line[6:]}

            if event_type == "token" and "content" in event_data:
                output_parts.append(event_data["content"])
                yield {
                    "type": "token",
                    "node_id": node_id,
                    "content": event_data["content"],
                }
            elif event_type == "thought":
                yield {
                    "type": "thought",
                    "type_detail": event_data.get("type", "skill_execution"),
                    "node_id": node_id,
                    **{k: v for k, v in event_data.items() if k != "type"},
                }
            elif event_type == "citation":
                yield {"type": "citation", "node_id": node_id, **event_data}
            elif event_type == "done":
                if event_data.get("status") == "error":
                    yield {
                        "type": "node_error",
                        "node_id": node_id,
                        "error": event_data.get("message", "Skill execution failed"),
                    }
                    ctx.set_output(node_id, "")
                    return

    except Exception as exc:
        logger.warning("Skill execution failed for node '%s'", node_id, exc_info=True)
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": f"Skill execution failed: {exc}",
        }
        ctx.set_output(node_id, "")
        return

    final_output = "".join(output_parts)
    ctx.set_output(node_id, final_output)
    yield {"type": "node_complete", "node_id": node_id, "output": final_output}


async def execute_http_node(
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "http"}

    if not await is_feature_enabled("ENABLE_HTTP_NODE"):
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": "此功能已被管理员禁用",
        }
        ctx.set_output(node_id, "")
        return

    data = node.get("data", {})
    method = str(data.get("method", "GET")).upper()
    if method not in {"GET", "POST", "PUT", "DELETE"}:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": "HTTP method not supported",
        }
        ctx.set_output(node_id, "")
        return

    raw_url = str(data.get("url", "")).strip()
    resolved_url = ctx.resolve_template(raw_url)
    if not resolved_url:
        yield {"type": "node_error", "node_id": node_id, "error": "URL is required"}
        ctx.set_output(node_id, "")
        return

    allowlist = [
        item.strip()
        for item in settings().http_node_allow_domains.split(",")
        if item.strip()
    ]
    try:
        safe_url = ensure_url_safe(resolved_url, allow_domains=allowlist)
    except ValueError as exc:
        yield {"type": "node_error", "node_id": node_id, "error": str(exc)}
        ctx.set_output(node_id, "")
        return

    headers: dict[str, str] = {}
    raw_headers = data.get("headers", {})
    if isinstance(raw_headers, dict):
        for key, value in raw_headers.items():
            headers[str(key)] = ctx.resolve_template(str(value))

    timeout_seconds = int(data.get("timeoutSeconds", 10) or 10)
    timeout_seconds = max(1, min(timeout_seconds, 30))

    request_body = data.get("body")
    json_payload: Any = None
    text_payload: str | None = None
    if isinstance(request_body, dict):
        json_payload = {
            str(key): ctx.resolve_template(str(value))
            for key, value in request_body.items()
        }
    elif isinstance(request_body, str) and request_body.strip():
        text_payload = ctx.resolve_template(request_body)

    try:
        async with create_ssrf_safe_client(
            follow_redirects=False,
            trust_env=False,
            timeout=timeout_seconds,
        ) as client:
            response = await client.request(
                method,
                safe_url,
                headers=headers,
                json=json_payload,
                content=text_payload,
            )
    except Exception:
        logger.warning("HTTP node request failed for node '%s'", node_id, exc_info=True)
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": "HTTP request failed",
        }
        ctx.set_output(node_id, "")
        return

    body_limit = 1024 * 1024
    response_text = response.text
    if len(response_text.encode("utf-8", errors="ignore")) > body_limit:
        response_text = response_text.encode("utf-8", errors="ignore")[
            :body_limit
        ].decode("utf-8", errors="ignore")

    response_path = str(data.get("responsePath", "")).strip()
    output: Any = response_text
    if response_path:
        try:
            parsed_json = response.json()
            extracted = _extract_json_path(parsed_json, response_path)
            output = "" if extracted is None else extracted
        except Exception:
            output = ""

    output_str = str(output)
    ctx.set_output(node_id, output_str)
    yield {
        "type": "node_complete",
        "node_id": node_id,
        "output": output_str,
        "status_code": response.status_code,
    }


async def execute_code_node(
    node: dict[str, Any], ctx: ExecutionContext, get_input: GetInput
) -> AsyncGenerator[dict[str, Any], None]:
    node_id = node["id"]
    yield {"type": "node_start", "node_id": node_id, "node_type": "code"}

    if not await is_feature_enabled("ENABLE_CODE_NODE"):
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": "此功能已被管理员禁用",
        }
        ctx.set_output(node_id, "")
        return

    data = node.get("data", {})
    code = str(data.get("code", ""))
    if not code.strip():
        yield {"type": "node_error", "node_id": node_id, "error": "Code is required"}
        ctx.set_output(node_id, "")
        return

    timeout_seconds = int(data.get("timeoutSeconds", 30) or 30)
    timeout_seconds = max(1, min(timeout_seconds, 30))
    memory_limit_mb = int(data.get("memoryLimitMb", 256) or 256)
    memory_limit_mb = max(64, min(memory_limit_mb, 512))

    input_value = str(get_input(node_id, ctx))
    env = {
        "WORKFLOW_INPUT": input_value,
        "USER_ID": str(ctx.user_id) if ctx.user_id is not None else "anonymous",
    }

    extra_env = data.get("env", {})
    if isinstance(extra_env, dict):
        for key, value in extra_env.items():
            env[str(key)] = ctx.resolve_template(str(value))

    result = await asyncio.to_thread(
        execute_python,
        code,
        env,
        timeout_seconds,
        memory_limit_mb,
    )

    if not result.ok:
        yield {
            "type": "node_error",
            "node_id": node_id,
            "error": result.error,
        }
        ctx.set_output(node_id, "")
        return

    output = result.stdout.strip()
    ctx.set_output(node_id, output)
    yield {"type": "node_complete", "node_id": node_id, "output": output}
