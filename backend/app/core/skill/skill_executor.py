"""
Skill Executor: variable substitution, RAG integration, and LLM streaming.

This module provides the SkillExecutor class for executing skills with:
- Input validation and variable substitution
- Optional RAG retrieval if knowledge_base is configured
- SSE streaming of thought/token/citation/done events
"""

import json
import logging
import re
from typing import AsyncGenerator, Dict, List, Optional, Any

from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.models.skill import SkillInput
from app.utils.sse import format_sse_event

logger = logging.getLogger(__name__)


class SkillExecutor:
    """Execute skills with variable substitution, RAG, and LLM streaming."""

    def __init__(self):
        self._rag_pipeline = None

    def _get_rag_pipeline(self):
        """Lazy load RAG pipeline."""
        if self._rag_pipeline is None:
            self._rag_pipeline = get_rag_pipeline()
        return self._rag_pipeline

    def validate_inputs(
        self, skill_inputs: List[SkillInput], provided_inputs: Dict[str, str]
    ) -> None:
        """
        Validate that all required inputs are provided.

        Args:
            skill_inputs: List of SkillInput definitions
            provided_inputs: Dictionary of provided input values

        Raises:
            ValueError: If a required input is missing
        """
        for input_def in skill_inputs:
            if input_def.required and (
                input_def.name not in provided_inputs
                or not provided_inputs[input_def.name]
            ):
                raise ValueError(f"Missing required input: '{input_def.name}'")

    def substitute_variables(
        self,
        prompt: str,
        skill_inputs: List[SkillInput],
        provided_inputs: Dict[str, str],
    ) -> str:
        """
        Single-pass variable substitution using {{variable}} syntax.

        Args:
            prompt: The prompt template with {{variable}} placeholders
            skill_inputs: List of SkillInput definitions with defaults
            provided_inputs: Dictionary of provided input values

        Returns:
            Prompt with all variables replaced (single-pass, no recursion)
        """
        # Build a mapping of variable name -> value
        # Priority: provided_inputs > default values > empty string
        variable_values: Dict[str, str] = {}

        for input_def in skill_inputs:
            name = input_def.name
            default = input_def.default

            if not isinstance(name, str) or not name:
                continue

            if name in provided_inputs:
                variable_values[name] = provided_inputs[name]
            else:
                variable_values[name] = default if default else ""

        # Single-pass regex substitution
        # Match {{variable_name}} - variable names are alphanumeric with underscores/hyphens
        def replace_match(match: re.Match[str]) -> str:
            var_name = match.group(1).strip()
            return variable_values.get(var_name, "")

        # Pattern: {{variable_name}} where variable_name can contain letters, numbers, underscores, hyphens
        result = re.sub(r"\{\{([a-zA-Z0-9_-]+)\}\}", replace_match, prompt)

        return result

    async def execute(
        self,
        skill: Any,
        inputs: Dict[str, str],
        user_id: int | str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute a skill with the provided inputs.

        Args:
            skill: SkillDetail object or dict with skill configuration
            inputs: Dictionary of input values

        Yields:
            SSE event strings (thought, token, citation, done)

        Events:
            - thought: RAG retrieval status and results
            - token: LLM generated content chunks
            - citation: Source metadata from retrieved documents
            - done: Completion marker
        """
        try:
            # Extract skill properties
            skill_inputs = getattr(skill, "inputs", []) or []
            if isinstance(skill, dict):
                skill_inputs = skill.get("inputs", [])

            prompt = getattr(skill, "prompt", "") or ""
            if isinstance(skill, dict):
                prompt = skill.get("prompt", "")

            knowledge_base = getattr(skill, "knowledge_base", None)
            if isinstance(skill, dict):
                knowledge_base = skill.get("knowledge_base")

            model_config = getattr(skill, "model", None) or {}
            if isinstance(skill, dict):
                model_config = skill.get("model", {})

            # Step 1: Validate required inputs
            yield format_sse_event("thought", {"type": "validation", "status": "start"})

            try:
                self.validate_inputs(skill_inputs, inputs)
                yield format_sse_event(
                    "thought",
                    {
                        "type": "validation",
                        "status": "complete",
                        "message": "All required inputs provided",
                    },
                )
            except ValueError as e:
                yield format_sse_event(
                    "thought",
                    {"type": "validation", "status": "error", "error": str(e)},
                )
                yield format_sse_event("done", {"status": "error", "message": str(e)})
                return

            # Step 2: Variable substitution
            yield format_sse_event(
                "thought", {"type": "substitution", "status": "start"}
            )

            substituted_prompt = self.substitute_variables(prompt, skill_inputs, inputs)

            yield format_sse_event(
                "thought",
                {
                    "type": "substitution",
                    "status": "complete",
                    "message": "Variables substituted",
                },
            )

            # Step 3: RAG retrieval if knowledge_base is configured
            retrieved_results: List[Dict[str, Any]] = []
            has_error = False
            error_message = ""

            if knowledge_base:
                yield format_sse_event(
                    "thought",
                    {"type": "retrieval", "status": "start", "kb_id": knowledge_base},
                )

                yield format_sse_event(
                    "thought",
                    {
                        "type": "retrieval",
                        "status": "searching",
                        "kb_id": knowledge_base,
                        "query": substituted_prompt[:200],  # First 200 chars as query
                    },
                )

                try:
                    rag_pipeline = self._get_rag_pipeline()
                    # Use the first 500 chars of prompt as query for RAG
                    query = (
                        substituted_prompt[:500]
                        if len(substituted_prompt) > 500
                        else substituted_prompt
                    )
                    retrieved_results = await rag_pipeline.search(
                        knowledge_base, query, top_k=5
                    )

                    # Format top results for thought event
                    top_results = [
                        {
                            "text": r["text"][:200] + "..."
                            if len(r["text"]) > 200
                            else r["text"],
                            "doc_id": r["metadata"].get("doc_id", ""),
                            "score": r["score"],
                        }
                        for r in retrieved_results[:3]
                    ]

                    yield format_sse_event(
                        "thought",
                        {
                            "type": "retrieval",
                            "status": "complete",
                            "kb_id": knowledge_base,
                            "results_count": len(retrieved_results),
                            "top_results": top_results,
                        },
                    )

                    # Emit citation event if results found
                    if retrieved_results:
                        sources = [
                            {
                                "doc_id": r["metadata"].get("doc_id", ""),
                                "chunk_index": r["metadata"].get("chunk_index", 0),
                                "score": r["score"],
                                "text": r["text"][:200] + "..."
                                if len(r["text"]) > 200
                                else r["text"],
                            }
                            for r in retrieved_results
                        ]
                        yield format_sse_event("citation", {"sources": sources})

                except Exception:
                    logger.warning(
                        "Skill retrieval failed for knowledge base '%s'",
                        knowledge_base,
                        exc_info=True,
                    )
                    yield format_sse_event(
                        "thought",
                        {
                            "type": "retrieval",
                            "status": "error",
                            "kb_id": knowledge_base,
                            "error": "Retrieval failed",
                        },
                    )
                    # Continue without RAG context if retrieval fails
                    retrieved_results = []

            # Step 4: Build messages for LLM
            messages: List[Dict[str, str]] = []

            # Build system prompt with RAG context if available
            system_content = "You are a helpful AI assistant."

            if retrieved_results:
                context_parts = []
                for i, r in enumerate(retrieved_results[:3], 1):
                    context_parts.append(f"[{i}] {r['text']}")
                context_str = "\n\n".join(context_parts)

                system_content += (
                    "\n\nAnswer the user's request based on the provided context. "
                    "If the context doesn't contain relevant information, say so clearly.\n\n"
                    f"Context:\n{context_str}"
                )

            messages.append({"role": "system", "content": system_content})
            messages.append({"role": "user", "content": substituted_prompt})

            # Step 5: Stream LLM tokens
            yield format_sse_event("thought", {"type": "generation", "status": "start"})

            temperature = (
                model_config.get("temperature", 0.7)
                if isinstance(model_config, dict)
                else 0.7
            )

            try:
                async for token in chat_completion_stream(
                    messages,
                    temperature=temperature,
                    user_id=user_id,
                ):
                    yield format_sse_event("token", {"content": token})
            except Exception:
                logger.warning(
                    "LLM streaming failed during skill execution", exc_info=True
                )
                has_error = True
                error_message = "Generation failed"
                yield format_sse_event("error", {"message": error_message})

            # Step 6: Done event
            if has_error:
                yield format_sse_event(
                    "done", {"status": "error", "message": error_message}
                )
            else:
                yield format_sse_event(
                    "done",
                    {
                        "status": "success",
                        "message": "Skill execution completed successfully",
                    },
                )

        except Exception:
            # Catch-all for unexpected errors
            logger.warning("Skill execution failed unexpectedly", exc_info=True)
            yield format_sse_event(
                "thought",
                {
                    "type": "error",
                    "status": "error",
                    "error": "Skill execution failed",
                },
            )
            yield format_sse_event(
                "done",
                {"status": "error", "message": "Skill execution failed"},
            )


# Global executor instance
_skill_executor: Optional[SkillExecutor] = None


def get_skill_executor() -> SkillExecutor:
    """Get the global skill executor instance."""
    global _skill_executor
    if _skill_executor is None:
        _skill_executor = SkillExecutor()
    return _skill_executor
