"""
Tests for workflow skill node execution.

Tests cover:
- Skill node execution with input mappings
- Skill loading and validation
- Input mapping from upstream nodes
- SSE event parsing and forwarding
- Error handling for missing skills
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.workflow_nodes import execute_skill_node
from app.core.workflow_context import ExecutionContext


class TestExecuteSkillNode:
    """Tests for execute_skill_node function."""

    def setup_method(self):
        """Set up test context and mock get_input function."""
        self.ctx = ExecutionContext("test input")
        self.ctx.step_outputs = {
            "node-1": "output from node-1",
            "node-2": "output from node-2"
        }
        self.get_input = MagicMock(return_value="default input")

    @pytest.mark.asyncio
    async def test_skill_node_missing_skill_name(self):
        """Test error when skill name is not configured."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {}
        }

        events = []
        async for event in execute_skill_node(node, self.ctx, self.get_input):
            events.append(event)

        # Should have node_start and node_error events
        assert events[0]["type"] == "node_start"
        assert events[0]["node_id"] == "skill-node-1"
        assert events[1]["type"] == "node_error"
        assert "Skill not selected" in events[1]["error"]

    @pytest.mark.asyncio
    async def test_skill_node_skill_not_found(self):
        """Test error when skill cannot be loaded."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {"skillName": "nonexistent-skill"}
        }

        # Mock SkillLoader to raise exception
        mock_loader = MagicMock()
        mock_loader.get_skill.side_effect = Exception("Skill not found")

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            events = []
            async for event in execute_skill_node(node, self.ctx, self.get_input):
                events.append(event)

        assert events[0]["type"] == "node_start"
        assert any(e["type"] == "node_error" for e in events)

    @pytest.mark.asyncio
    async def test_skill_node_successful_execution(self):
        """Test successful skill node execution."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {
                "skillName": "test-skill",
                "inputMappings": {"text": "node-1"}
            }
        }

        # Mock skill
        mock_skill = MagicMock()
        mock_skill.inputs = []
        mock_skill.prompt = "Process: {{text}}"
        mock_skill.knowledge_base = None
        mock_skill.model = {"temperature": 0.7}

        # Mock SkillLoader
        mock_loader = MagicMock()
        mock_loader.get_skill.return_value = mock_skill

        # Mock executor
        async def mock_execute(skill, inputs):
            yield "event: thought\ndata: {\"status\": \"start\"}\n\n"
            yield "event: token\ndata: {\"content\": \"Hello\"}\n\n"
            yield "event: token\ndata: {\"content\": \" World\"}\n\n"
            yield "event: done\ndata: {\"status\": \"success\"}\n\n"

        mock_executor = MagicMock()
        mock_executor.execute = mock_execute

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            with patch('app.core.workflow_nodes.get_skill_executor', return_value=mock_executor):
                events = []
                async for event in execute_skill_node(node, self.ctx, self.get_input):
                    events.append(event)

        # Check events
        assert events[0]["type"] == "node_start"
        assert events[0]["node_type"] == "skill"

        # Should have token events
        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) == 2
        assert token_events[0]["content"] == "Hello"
        assert token_events[1]["content"] == " World"

        # Should have node_complete
        complete_events = [e for e in events if e["type"] == "node_complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["output"] == "Hello World"

        # Should store output in context
        assert self.ctx.step_outputs["skill-node-1"] == "Hello World"

    @pytest.mark.asyncio
    async def test_skill_node_input_mapping(self):
        """Test that input mappings are correctly resolved."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {
                "skillName": "test-skill",
                "inputMappings": {
                    "article": "node-1",
                    "style": "node-2"
                }
            }
        }

        mock_skill = MagicMock()
        mock_skill.inputs = []
        mock_skill.prompt = "Summarize: {{article}} in {{style}} style"
        mock_skill.knowledge_base = None
        mock_skill.model = {}

        mock_loader = MagicMock()
        mock_loader.get_skill.return_value = mock_skill

        captured_inputs = {}

        async def mock_execute(skill, inputs):
            nonlocal captured_inputs
            captured_inputs = inputs
            yield "event: done\ndata: {\"status\": \"success\"}\n\n"

        mock_executor = MagicMock()
        mock_executor.execute = mock_execute

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            with patch('app.core.workflow_nodes.get_skill_executor', return_value=mock_executor):
                async for _ in execute_skill_node(node, self.ctx, self.get_input):
                    pass

        # Verify inputs were mapped correctly
        assert captured_inputs["article"] == "output from node-1"
        assert captured_inputs["style"] == "output from node-2"

    @pytest.mark.asyncio
    async def test_skill_node_auto_mapping(self):
        """Test auto-mapping when no explicit mappings provided."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {
                "skillName": "test-skill"
                # No inputMappings
            }
        }

        # Mock skill with inputs
        mock_skill = MagicMock()
        mock_skill.inputs = [
            MagicMock(name="text", required=True),
            MagicMock(name="style", required=False)
        ]
        mock_skill.inputs[0].name = "text"
        mock_skill.inputs[0].required = True
        mock_skill.inputs[1].name = "style"
        mock_skill.inputs[1].required = False
        mock_skill.prompt = "Process: {{text}}"
        mock_skill.knowledge_base = None
        mock_skill.model = {}

        mock_loader = MagicMock()
        mock_loader.get_skill.return_value = mock_skill

        captured_inputs = {}

        async def mock_execute(skill, inputs):
            nonlocal captured_inputs
            captured_inputs = inputs
            yield "event: done\ndata: {\"status\": \"success\"}\n\n"

        mock_executor = MagicMock()
        mock_executor.execute = mock_execute

        self.get_input.return_value = "upstream output"

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            with patch('app.core.workflow_nodes.get_skill_executor', return_value=mock_executor):
                async for _ in execute_skill_node(node, self.ctx, self.get_input):
                    pass

        # Should map upstream input to first required input
        assert captured_inputs["text"] == "upstream output"

    @pytest.mark.asyncio
    async def test_skill_node_execution_error(self):
        """Test handling of skill execution error."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {"skillName": "test-skill"}
        }

        mock_skill = MagicMock()
        mock_skill.inputs = []
        mock_skill.prompt = "Test"
        mock_skill.knowledge_base = None
        mock_skill.model = {}

        mock_loader = MagicMock()
        mock_loader.get_skill.return_value = mock_skill

        async def mock_execute(skill, inputs):
            yield "event: done\ndata: {\"status\": \"error\", \"message\": \"Execution failed\"}\n\n"

        mock_executor = MagicMock()
        mock_executor.execute = mock_execute

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            with patch('app.core.workflow_nodes.get_skill_executor', return_value=mock_executor):
                events = []
                async for event in execute_skill_node(node, self.ctx, self.get_input):
                    events.append(event)

        # Should have node_error event
        error_events = [e for e in events if e["type"] == "node_error"]
        assert len(error_events) == 1
        assert "Execution failed" in error_events[0]["error"]

    @pytest.mark.asyncio
    async def test_skill_node_thought_events(self):
        """Test that thought events are forwarded correctly."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {"skillName": "test-skill"}
        }

        mock_skill = MagicMock()
        mock_skill.inputs = []
        mock_skill.prompt = "Test"
        mock_skill.knowledge_base = None
        mock_skill.model = {}

        mock_loader = MagicMock()
        mock_loader.get_skill.return_value = mock_skill

        async def mock_execute(skill, inputs):
            yield "event: thought\ndata: {\"type\": \"validation\", \"status\": \"start\"}\n\n"
            yield "event: thought\ndata: {\"type\": \"validation\", \"status\": \"complete\"}\n\n"
            yield "event: done\ndata: {\"status\": \"success\", \"message\": \"OK\"}\n\n"

        mock_executor = MagicMock()
        mock_executor.execute = mock_execute

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            with patch('app.core.workflow_nodes.get_skill_executor', return_value=mock_executor):
                events = []
                async for event in execute_skill_node(node, self.ctx, self.get_input):
                    events.append(event)

        # Should have thought events
        thought_events = [e for e in events if e["type"] == "thought"]
        assert len(thought_events) == 2
        assert thought_events[0]["type_detail"] == "validation"

    @pytest.mark.asyncio
    async def test_skill_node_citation_events(self):
        """Test that citation events are forwarded correctly."""
        node = {
            "id": "skill-node-1",
            "type": "skill",
            "data": {"skillName": "test-skill"}
        }

        mock_skill = MagicMock()
        mock_skill.inputs = []
        mock_skill.prompt = "Test"
        mock_skill.knowledge_base = "test-kb"
        mock_skill.model = {}

        mock_loader = MagicMock()
        mock_loader.get_skill.return_value = mock_skill

        async def mock_execute(skill, inputs):
            yield "event: citation\ndata: {\"sources\": [{\"doc_id\": \"doc1\"}]}\n\n"
            yield "event: done\ndata: {\"status\": \"success\"}\n\n"

        mock_executor = MagicMock()
        mock_executor.execute = mock_execute

        with patch('app.core.workflow_nodes.SkillLoader', return_value=mock_loader):
            with patch('app.core.workflow_nodes.get_skill_executor', return_value=mock_executor):
                events = []
                async for event in execute_skill_node(node, self.ctx, self.get_input):
                    events.append(event)

        # Should have citation event
        citation_events = [e for e in events if e["type"] == "citation"]
        assert len(citation_events) == 1
        assert citation_events[0]["sources"][0]["doc_id"] == "doc1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
