"""
Tests for SkillExecutor.

Tests cover:
- Input validation (required inputs)
- Variable substitution (single-pass, no recursion)
- Default values for optional inputs
- SSE event formatting
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.skill.skill_executor import SkillExecutor, format_sse_event


class TestFormatSSEEvent:
    """Tests for SSE event formatting."""

    def test_format_sse_event_basic(self):
        """Test basic SSE event formatting."""
        event = format_sse_event("token", {"content": "hello"})
        assert event == "event: token\ndata: {\"content\": \"hello\"}\n\n"

    def test_format_sse_event_with_unicode(self):
        """Test SSE event with unicode characters."""
        event = format_sse_event("token", {"content": "你好"})
        assert "你好" in event
        assert event.startswith("event: token\ndata: ")

    def test_format_sse_event_thought(self):
        """Test thought event formatting."""
        data = {"type": "validation", "status": "complete"}
        event = format_sse_event("thought", data)
        assert "event: thought" in event
        assert '"status": "complete"' in event


class TestValidateInputs:
    """Tests for input validation."""

    def setup_method(self):
        """Set up test executor."""
        self.executor = SkillExecutor()

    def test_validate_all_required_present(self):
        """Test validation passes when all required inputs are provided."""
        skill_inputs = [
            {"name": "article", "required": True},
            {"name": "style", "required": False}
        ]
        provided = {"article": "some content"}

        # Should not raise
        self.executor.validate_inputs(skill_inputs, provided)

    def test_validate_missing_required(self):
        """Test validation fails when required input is missing."""
        skill_inputs = [
            {"name": "article", "required": True},
            {"name": "style", "required": False}
        ]
        provided = {}

        with pytest.raises(ValueError, match="Missing required input: 'article'"):
            self.executor.validate_inputs(skill_inputs, provided)

    def test_validate_empty_required(self):
        """Test validation fails when required input is empty string."""
        skill_inputs = [
            {"name": "article", "required": True}
        ]
        provided = {"article": ""}

        with pytest.raises(ValueError, match="Missing required input: 'article'"):
            self.executor.validate_inputs(skill_inputs, provided)

    def test_validate_no_required_fields(self):
        """Test validation passes when no required fields defined."""
        skill_inputs = [
            {"name": "style", "required": False}
        ]
        provided = {}

        # Should not raise
        self.executor.validate_inputs(skill_inputs, provided)

    def test_validate_empty_skill_inputs(self):
        """Test validation passes with empty skill inputs."""
        skill_inputs = []
        provided = {}

        # Should not raise
        self.executor.validate_inputs(skill_inputs, provided)


class TestSubstituteVariables:
    """Tests for variable substitution."""

    def setup_method(self):
        """Set up test executor."""
        self.executor = SkillExecutor()

    def test_substitute_single_variable(self):
        """Test substituting a single variable."""
        prompt = "Hello {{name}}!"
        skill_inputs = [{"name": "name", "default": ""}]
        provided = {"name": "World"}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "Hello World!"

    def test_substitute_multiple_variables(self):
        """Test substituting multiple variables."""
        prompt = "{{greeting}} {{name}}, how is {{thing}}?"
        skill_inputs = [
            {"name": "greeting", "default": ""},
            {"name": "name", "default": ""},
            {"name": "thing", "default": "everything"}
        ]
        provided = {"greeting": "Hi", "name": "Alice"}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "Hi Alice, how is everything?"

    def test_substitute_uses_default(self):
        """Test that default values are used when input not provided."""
        prompt = "Style: {{style}}"
        skill_inputs = [{"name": "style", "default": "formal"}]
        provided = {}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "Style: formal"

    def test_substitute_empty_string_for_missing(self):
        """Test that empty string is used when no default and not provided."""
        prompt = "Content: {{missing}}"
        skill_inputs = [{"name": "missing", "default": ""}]
        provided = {}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "Content: "

    def test_substitute_single_pass_no_recursion(self):
        """Test that substitution is single-pass (no recursion)."""
        # This is a critical requirement - if we had {{a}} -> {{b}} -> value,
        # it should NOT recursively substitute
        prompt = "Value: {{var}}"
        skill_inputs = [{"name": "var", "default": ""}]
        provided = {"var": "{{other}}"}  # The value looks like a variable

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        # Should NOT recursively substitute {{other}}
        assert result == "Value: {{other}}"

    def test_substitute_with_hyphens_and_underscores(self):
        """Test variable names with hyphens and underscores."""
        prompt = "{{my-var}} and {{my_var}}"
        skill_inputs = [
            {"name": "my-var", "default": ""},
            {"name": "my_var", "default": ""}
        ]
        provided = {"my-var": "hyphen", "my_var": "underscore"}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "hyphen and underscore"

    def test_substitute_no_variables(self):
        """Test prompt with no variables."""
        prompt = "Hello World!"
        skill_inputs = []
        provided = {}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "Hello World!"

    def test_substitute_unknown_variable(self):
        """Test that unknown variables are replaced with empty string."""
        prompt = "Known: {{known}}, Unknown: {{unknown}}"
        skill_inputs = [{"name": "known", "default": ""}]
        provided = {"known": "value"}

        result = self.executor.substitute_variables(prompt, skill_inputs, provided)
        assert result == "Known: value, Unknown: "


class TestSkillExecutorIntegration:
    """Integration tests for SkillExecutor.execute."""

    def setup_method(self):
        """Set up test executor."""
        self.executor = SkillExecutor()

    @pytest.mark.asyncio
    async def test_execute_missing_required_input(self):
        """Test that missing required input yields error events."""
        skill = {
            "inputs": [{"name": "article", "required": True}],
            "prompt": "Summarize: {{article}}",
            "knowledge_base": None,
            "model": {}
        }
        inputs = {}  # Missing required 'article'

        events = []
        async for event in self.executor.execute(skill, inputs):
            events.append(event)

        # Should have validation error and done events
        assert any("validation" in e and "error" in e for e in events)
        assert any('"status": "error"' in e for e in events)

    @pytest.mark.asyncio
    async def test_execute_success_flow(self):
        """Test successful execution flow with mocked LLM."""
        skill = {
            "inputs": [{"name": "article", "required": True}],
            "prompt": "Summarize: {{article}}",
            "knowledge_base": None,
            "model": {"temperature": 0.5}
        }
        inputs = {"article": "Test content"}

        # Mock the LLM stream
        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " World"

        with patch('app.core.skill.skill_executor.chat_completion_stream', mock_stream):
            events = []
            async for event in self.executor.execute(skill, inputs):
                events.append(event)

        # Check event types
        event_types = []
        for event in events:
            if event.startswith("event: "):
                event_type = event.split("\n")[0].replace("event: ", "")
                event_types.append(event_type)

        # Should have thought events, token events, and done event
        assert "thought" in event_types
        assert "token" in event_types
        assert "done" in event_types

    @pytest.mark.asyncio
    async def test_execute_with_rag(self):
        """Test execution with knowledge_base triggers RAG retrieval."""
        skill = {
            "inputs": [{"name": "question", "required": True}],
            "prompt": "Answer: {{question}}",
            "knowledge_base": "test-kb",
            "model": {}
        }
        inputs = {"question": "What is AI?"}

        # Mock RAG pipeline
        mock_rag = MagicMock()
        mock_rag.search = AsyncMock(return_value=[
            {
                "text": "AI is artificial intelligence",
                "metadata": {"doc_id": "doc1", "chunk_index": 0},
                "score": 0.95
            }
        ])

        # Mock the LLM stream
        async def mock_stream(*args, **kwargs):
            yield "AI"

        with patch.object(self.executor, '_get_rag_pipeline', return_value=mock_rag):
            with patch('app.core.skill.skill_executor.chat_completion_stream', mock_stream):
                events = []
                async for event in self.executor.execute(skill, inputs):
                    events.append(event)

        # Should have retrieval thought events
        assert any("retrieval" in e for e in events)
        # Should have citation event
        assert any("citation" in e for e in events)

    @pytest.mark.asyncio
    async def test_execute_rag_error_continues(self):
        """Test that RAG error doesn't stop execution."""
        skill = {
            "inputs": [{"name": "question", "required": True}],
            "prompt": "Answer: {{question}}",
            "knowledge_base": "test-kb",
            "model": {}
        }
        inputs = {"question": "What is AI?"}

        # Mock RAG pipeline that raises error
        mock_rag = MagicMock()
        mock_rag.search.side_effect = Exception("RAG failed")

        # Mock the LLM stream
        async def mock_stream(*args, **kwargs):
            yield "Answer"

        with patch.object(self.executor, '_get_rag_pipeline', return_value=mock_rag):
            with patch('app.core.skill.skill_executor.chat_completion_stream', mock_stream):
                events = []
                async for event in self.executor.execute(skill, inputs):
                    events.append(event)

        # Should have retrieval error event
        assert any("retrieval" in e and "error" in e for e in events)
        # Should still complete successfully
        assert any('"status": "success"' in e for e in events)

    @pytest.mark.asyncio
    async def test_execute_llm_error(self):
        """Test handling of LLM streaming error."""
        skill = {
            "inputs": [],
            "prompt": "Hello",
            "knowledge_base": None,
            "model": {}
        }
        inputs = {}

        # Mock the LLM stream to raise error
        async def mock_stream(*args, **kwargs):
            yield "Start"
            raise Exception("LLM failed")

        with patch('app.core.skill.skill_executor.chat_completion_stream', mock_stream):
            events = []
            async for event in self.executor.execute(skill, inputs):
                events.append(event)

        # Should have error in done event
        assert any('"status": "error"' in e for e in events)


class TestSkillExecutorWithSkillDetail:
    """Tests using SkillDetail-like objects."""

    def setup_method(self):
        """Set up test executor."""
        self.executor = SkillExecutor()

    @pytest.mark.asyncio
    async def test_execute_with_object_skill(self):
        """Test execution with object-style skill (not dict)."""
        # Create a mock skill object
        skill = MagicMock()
        skill.inputs = [{"name": "text", "required": True}]
        skill.prompt = "Process: {{text}}"
        skill.knowledge_base = None
        skill.model = {"temperature": 0.7}

        inputs = {"text": "test"}

        # Mock the LLM stream
        async def mock_stream(*args, **kwargs):
            yield "Done"

        with patch('app.core.skill.skill_executor.chat_completion_stream', mock_stream):
            events = []
            async for event in self.executor.execute(skill, inputs):
                events.append(event)

        # Should complete successfully
        assert any('"status": "success"' in e for e in events)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
