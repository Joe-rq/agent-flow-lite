"""
Workflow execution engine.
"""
from __future__ import annotations

from collections import deque
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.workflow_context import ExecutionContext
from app.core.workflow_nodes import (
    execute_condition_node,
    execute_end_node,
    execute_knowledge_node,
    execute_llm_node,
    execute_skill_node,
    execute_start_node
)
from app.models.workflow import Workflow


class WorkflowEngine:
    """Workflow execution engine."""

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.nodes: Dict[str, dict] = {n["id"]: n for n in workflow.graph_data.nodes}
        self.edges: List[dict] = workflow.graph_data.edges
        self.adjacency = self._build_adjacency()

    def _build_adjacency(self) -> Dict[str, List[dict]]:
        adjacency: Dict[str, List[dict]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            source = edge.get("source")
            if source in adjacency:
                adjacency[source].append(edge)
        return adjacency

    def _get_next_nodes(self, node_id: str, branch: Optional[str]) -> List[str]:
        outgoing = self.adjacency.get(node_id, [])
        next_nodes = []
        for edge in outgoing:
            if branch and edge.get("sourceHandle") not in (None, branch):
                continue
            target = edge.get("target")
            if target:
                next_nodes.append(target)
        return next_nodes

    def _get_input_for_node(self, node_id: str, ctx: ExecutionContext) -> Any:
        for edge in self.edges:
            if edge.get("target") == node_id:
                source_id = edge.get("source")
                if source_id and source_id in ctx.step_outputs:
                    return ctx.step_outputs[source_id]
        return ctx.variables.get("input", "")

    async def _execute_node(
        self, node_id: str, ctx: ExecutionContext
    ) -> AsyncGenerator[dict, None]:
        node = self.nodes.get(node_id)
        if not node:
            yield {"type": "node_error", "node_id": node_id, "error": "Node not found"}
            return

        node_type = node.get("type", "")
        executors = {
            "start": lambda n: execute_start_node(n, ctx),
            "llm": lambda n: execute_llm_node(n, ctx, self._get_input_for_node),
            "knowledge": lambda n: execute_knowledge_node(
                n, ctx, self._get_input_for_node
            ),
            "condition": lambda n: execute_condition_node(n, ctx),
            "end": lambda n: execute_end_node(n, ctx, self._get_input_for_node),
            "skill": lambda n: execute_skill_node(n, ctx, self._get_input_for_node)
        }
        executor = executors.get(node_type)
        if not executor:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"Unknown node type: {node_type}"
            }
            return

        async for event in executor(node):
            yield event

    async def execute(self, initial_input: str) -> AsyncGenerator[dict, None]:
        yield {
            "type": "workflow_start",
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name
        }

        start_nodes = [
            node_id for node_id, node in self.nodes.items() if node.get("type") == "start"
        ]
        if not start_nodes:
            yield {"type": "workflow_error", "error": "Workflow has no start node"}
            return

        ctx = ExecutionContext(initial_input)
        queue = deque(start_nodes)
        executed: set[str] = set()

        while queue:
            node_id = queue.popleft()
            if node_id in executed:
                continue

            async for event in self._execute_node(node_id, ctx):
                yield event
                if event.get("type") == "node_error":
                    yield {"type": "workflow_error", "error": event.get("error")}
                    return
                if event.get("type") == "workflow_complete":
                    return

            executed.add(node_id)
            node_type = self.nodes[node_id].get("type")
            branch = None
            if node_type == "condition":
                branch = "true" if ctx.step_outputs.get(node_id) else "false"

            for next_id in self._get_next_nodes(node_id, branch):
                if next_id not in executed:
                    queue.append(next_id)

        final_output = None
        if executed:
            last_id = list(executed)[-1]
            final_output = ctx.step_outputs.get(last_id)
        yield {"type": "workflow_complete", "final_output": final_output}
