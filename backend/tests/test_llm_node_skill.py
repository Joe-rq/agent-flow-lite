import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.workflow.workflow_nodes import execute_llm_node
from app.core.workflow.workflow_context import ExecutionContext
from app.models.skill import SkillDetail, SkillInput, SkillModelConfig


@pytest.fixture
def temp_skills_dir():
    temp_dir = tempfile.mkdtemp()
    skills_dir = Path(temp_dir) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    test_skill_dir = skills_dir / "test-skill"
    test_skill_dir.mkdir(parents=True, exist_ok=True)

    skill_content = """---
name: test-skill
description: A test skill for LLM node
inputs:
  - name: input_text
    label: Input Text
    type: textarea
    required: true
model:
  temperature: 0.3
  max_tokens: 1000
---

You are a helpful assistant specialized in testing. Process this input: {{input_text}}
"""

    skill_file = test_skill_dir / "SKILL.md"
    skill_file.write_text(skill_content, encoding="utf-8")

    yield skills_dir

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def execution_context():
    return ExecutionContext(initial_input="test input")


class TestLLMNodeSkillLoading:
    @pytest.mark.asyncio
    async def test_llm_node_without_skill(self, execution_context):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "systemPrompt": "You are a helpful assistant.",
                "temperature": 0.7,
            },
        }

        def get_input(node_id, ctx):
            return "Hello, world!"

        events = []
        with patch(
            "app.core.workflow.workflow_nodes.chat_completion_stream"
        ) as mock_stream:
            mock_stream.return_value = AsyncMock()
            mock_stream.return_value.__aiter__.return_value = iter(["Hello", "!"])

            async for event in execute_llm_node(node, execution_context, get_input):
                events.append(event)

        assert events[0]["type"] == "node_start"
        assert events[0]["node_type"] == "llm"

        thought_events = [e for e in events if e["type"] == "thought"]
        assert len(thought_events) == 0

        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) == 2

        complete_events = [e for e in events if e["type"] == "node_complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["output"] == "Hello!"

    @pytest.mark.asyncio
    async def test_llm_node_with_skill_loading(
        self, temp_skills_dir, execution_context
    ):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "test-skill",
                "systemPrompt": "This should be overridden",
                "temperature": 0.9,
            },
        }

        def get_input(node_id, ctx):
            return "Test input"

        events = []

        with patch("app.core.workflow.workflow_nodes.SkillLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            mock_skill = MagicMock()
            mock_skill.prompt = "You are a helpful assistant specialized in testing. Process this input: {{input_text}}"
            mock_skill.model = SkillModelConfig(temperature=0.3, max_tokens=1000)
            mock_loader.get_skill.return_value = mock_skill

            with patch(
                "app.core.workflow.workflow_nodes.chat_completion_stream"
            ) as mock_stream:
                mock_stream.return_value = AsyncMock()
                mock_stream.return_value.__aiter__.return_value = iter(["Result"])

                async for event in execute_llm_node(node, execution_context, get_input):
                    events.append(event)

        assert events[0]["type"] == "node_start"

        skill_loaded_events = [
            e for e in events if e.get("type_detail") == "skill_loaded"
        ]
        assert len(skill_loaded_events) == 1
        assert skill_loaded_events[0]["skill_name"] == "test-skill"
        assert skill_loaded_events[0]["has_prompt"] is True
        assert skill_loaded_events[0]["has_model_config"] is True

        complete_events = [e for e in events if e["type"] == "node_complete"]
        assert len(complete_events) == 1

    @pytest.mark.asyncio
    async def test_llm_node_skill_not_found(self, execution_context):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "non-existent-skill",
                "systemPrompt": "Fallback prompt",
            },
        }

        def get_input(node_id, ctx):
            return "Test input"

        events = []

        with patch("app.core.workflow.workflow_nodes.SkillLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader
            mock_loader.get_skill.side_effect = Exception("Skill not found")

            async for event in execute_llm_node(node, execution_context, get_input):
                events.append(event)

        assert events[0]["type"] == "node_start"

        error_events = [e for e in events if e["type"] == "node_error"]
        assert len(error_events) == 1
        assert "non-existent-skill" in error_events[0]["error"]

    @pytest.mark.asyncio
    async def test_llm_node_skill_prompt_override(self, execution_context):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "test-skill",
                "systemPrompt": "Original prompt that should be overridden",
                "temperature": 0.5,
            },
        }

        def get_input(node_id, ctx):
            return "Test input"

        captured_messages = None

        with patch("app.core.workflow.workflow_nodes.SkillLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            mock_skill = MagicMock()
            mock_skill.prompt = "Skill-specific prompt"
            mock_skill.model = None
            mock_loader.get_skill.return_value = mock_skill

            async def capture_messages(messages, **kwargs):
                nonlocal captured_messages
                captured_messages = messages
                yield "Result"

            with patch(
                "app.core.workflow.workflow_nodes.chat_completion_stream",
                side_effect=capture_messages,
            ):
                events = []
                async for event in execute_llm_node(node, execution_context, get_input):
                    events.append(event)

        assert captured_messages is not None
        assert captured_messages[0]["content"] == "Skill-specific prompt"

    @pytest.mark.asyncio
    async def test_llm_node_skill_temperature_override(self, execution_context):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "test-skill",
                "systemPrompt": "Test prompt",
                "temperature": 0.9,
            },
        }

        def get_input(node_id, ctx):
            return "Test input"

        captured_temperature = None

        with patch("app.core.workflow.workflow_nodes.SkillLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            mock_skill = MagicMock()
            mock_skill.prompt = "Test prompt"
            mock_skill.model = SkillModelConfig(temperature=0.2, max_tokens=1000)
            mock_loader.get_skill.return_value = mock_skill

            async def capture_temperature(messages, **kwargs):
                nonlocal captured_temperature
                captured_temperature = kwargs.get("temperature")
                yield "Result"

            with patch(
                "app.core.workflow.workflow_nodes.chat_completion_stream",
                side_effect=capture_temperature,
            ):
                events = []
                async for event in execute_llm_node(node, execution_context, get_input):
                    events.append(event)

        assert captured_temperature == 0.2

    @pytest.mark.asyncio
    async def test_llm_node_skill_no_model_config(self, execution_context):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "test-skill",
                "systemPrompt": "Test prompt",
                "temperature": 0.8,
            },
        }

        def get_input(node_id, ctx):
            return "Test input"

        captured_temperature = None

        with patch("app.core.workflow.workflow_nodes.SkillLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            mock_skill = MagicMock()
            mock_skill.prompt = "Skill prompt"
            mock_skill.model = None
            mock_loader.get_skill.return_value = mock_skill

            async def capture_temperature(messages, **kwargs):
                nonlocal captured_temperature
                captured_temperature = kwargs.get("temperature")
                yield "Result"

            with patch(
                "app.core.workflow.workflow_nodes.chat_completion_stream",
                side_effect=capture_temperature,
            ):
                events = []
                async for event in execute_llm_node(node, execution_context, get_input):
                    events.append(event)

        assert captured_temperature == 0.8

    @pytest.mark.asyncio
    async def test_llm_node_skill_prompt_with_template_variables(
        self, execution_context
    ):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "test-skill",
                "systemPrompt": "Prompt with {{variable}}",
            },
        }

        execution_context.variables["variable"] = "resolved_value"

        def get_input(node_id, ctx):
            return "Test input"

        captured_messages = None

        with patch("app.core.workflow.workflow_nodes.SkillLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            mock_skill = MagicMock()
            mock_skill.prompt = "Skill with {{variable}}"
            mock_skill.model = None
            mock_loader.get_skill.return_value = mock_skill

            async def capture_messages(messages, **kwargs):
                nonlocal captured_messages
                captured_messages = messages
                yield "Result"

            with patch(
                "app.core.workflow.workflow_nodes.chat_completion_stream",
                side_effect=capture_messages,
            ):
                events = []
                async for event in execute_llm_node(node, execution_context, get_input):
                    events.append(event)

        assert captured_messages is not None
        assert "resolved_value" in captured_messages[0]["content"]

    @pytest.mark.asyncio
    async def test_llm_node_empty_skill_name(self, execution_context):
        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "skillName": "",
                "systemPrompt": "You are a helpful assistant.",
                "temperature": 0.7,
            },
        }

        def get_input(node_id, ctx):
            return "Hello, world!"

        events = []
        with patch(
            "app.core.workflow.workflow_nodes.chat_completion_stream"
        ) as mock_stream:
            mock_stream.return_value = AsyncMock()
            mock_stream.return_value.__aiter__.return_value = iter(["Hello"])

            async for event in execute_llm_node(node, execution_context, get_input):
                events.append(event)

        skill_loaded_events = [
            e for e in events if e.get("type_detail") == "skill_loaded"
        ]
        assert len(skill_loaded_events) == 0

        complete_events = [e for e in events if e["type"] == "node_complete"]
        assert len(complete_events) == 1

    @pytest.mark.asyncio
    async def test_llm_node_supports_model_and_chat_history(self):
        execution_context = ExecutionContext(
            initial_input="test",
            user_id=42,
            model="openai:gpt-4o-mini",
            conversation_history=[
                {"role": "user", "content": "历史问题"},
                {"role": "assistant", "content": "历史回答"},
            ],
        )

        node = {
            "id": "llm-1",
            "type": "llm",
            "data": {
                "model": "qwen:qwen-plus",
                "inheritChatHistory": True,
                "systemPrompt": "You are a helper",
                "temperature": 0.6,
            },
        }

        def get_input(node_id, ctx):
            return "当前问题"

        captured_messages = None
        captured_model = None
        captured_user_id = None

        async def capture_stream(messages, **kwargs):
            nonlocal captured_messages, captured_model, captured_user_id
            captured_messages = messages
            captured_model = kwargs.get("model")
            captured_user_id = kwargs.get("user_id")
            yield "ok"

        with patch(
            "app.core.workflow.workflow_nodes.chat_completion_stream",
            side_effect=capture_stream,
        ):
            events = []
            async for event in execute_llm_node(node, execution_context, get_input):
                events.append(event)

        assert captured_messages is not None
        assert captured_messages[1]["content"] == "历史问题"
        assert captured_messages[2]["content"] == "历史回答"
        assert captured_messages[-1]["content"] == "当前问题"
        assert captured_model == "qwen:qwen-plus"
        assert captured_user_id == 42
        complete_events = [e for e in events if e["type"] == "node_complete"]
        assert len(complete_events) == 1
