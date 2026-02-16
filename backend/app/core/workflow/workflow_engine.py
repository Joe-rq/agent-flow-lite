"""
Workflow execution engine.
"""

from __future__ import annotations

from collections import deque
from typing import Any, AsyncGenerator, Optional

from app.core.workflow.workflow_context import ExecutionContext
from app.core.workflow.workflow_nodes import (
    execute_code_node,
    execute_condition_node,
    execute_end_node,
    execute_http_node,
    execute_knowledge_node,
    execute_llm_node,
    execute_skill_node,
    execute_start_node,
)
from app.models.workflow import Workflow


class WorkflowEngine:
    """Workflow execution engine."""

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        graph_data = workflow.graph_data
        self.nodes: dict[str, dict[str, Any]] = {n["id"]: n for n in graph_data.nodes}
        self.edges: list[dict[str, Any]] = graph_data.edges
        self.adjacency = self._build_adjacency()
        self.last_executed_id: str | None = None

    def _build_adjacency(self) -> dict[str, list[dict[str, Any]]]:
        adjacency: dict[str, list[dict[str, Any]]] = {
            node_id: [] for node_id in self.nodes
        }
        for edge in self.edges:
            source = edge.get("source")
            if source in adjacency:
                adjacency[source].append(edge)
        return adjacency

    def _has_cycle(self) -> bool:
        """Detect cycles via DFS coloring (0=white, 1=gray, 2=black)."""
        color: dict[str, int] = {nid: 0 for nid in self.nodes}

        def dfs(nid: str) -> bool:
            color[nid] = 1
            for edge in self.adjacency.get(nid, []):
                target = edge.get("target")
                if not target or target not in color:
                    continue
                if color[target] == 1:
                    return True
                if color[target] == 0 and dfs(target):
                    return True
            color[nid] = 2
            return False

        return any(color[nid] == 0 and dfs(nid) for nid in self.nodes)

    def _get_next_nodes(self, node_id: str, branch: Optional[str]) -> list[str]:
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
    ) -> AsyncGenerator[dict[str, Any], None]:
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
            "condition": lambda n: execute_condition_node(
                n, ctx, self._get_input_for_node
            ),
            "end": lambda n: execute_end_node(n, ctx, self._get_input_for_node),
            "skill": lambda n: execute_skill_node(n, ctx, self._get_input_for_node),
            "http": lambda n: execute_http_node(n, ctx, self._get_input_for_node),
            "code": lambda n: execute_code_node(n, ctx, self._get_input_for_node),
        }
        executor = executors.get(node_type)
        if not executor:
            yield {
                "type": "node_error",
                "node_id": node_id,
                "error": f"Unknown node type: {node_type}",
            }
            return

        async for event in executor(node):
            yield event

    async def execute(
        self,
        initial_input: str,
        user_id: int | None = None,
        model: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        yield {
            "type": "workflow_start",
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name,
        }

        start_nodes = [
            node_id
            for node_id, node in self.nodes.items()
            if node.get("type") == "start"
        ]
        if not start_nodes:
            yield {"type": "workflow_error", "error": "Workflow has no start node"}
            return

        if self._has_cycle():
            yield {"type": "workflow_error", "error": "Workflow contains a cycle"}
            return

        ctx = ExecutionContext(
            initial_input,
            user_id=user_id,
            model=model,
            conversation_history=conversation_history,
        )
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
            self.last_executed_id = node_id
            node_type = self.nodes[node_id].get("type")
            branch = None
            if node_type == "condition":
                branch = "true" if ctx.variables.get(f"{node_id}.__branch") else "false"

            for next_id in self._get_next_nodes(node_id, branch):
                if next_id not in executed:
                    queue.append(next_id)

        final_output = None
        if self.last_executed_id:
            final_output = ctx.step_outputs.get(self.last_executed_id)
        yield {"type": "workflow_complete", "final_output": final_output}
