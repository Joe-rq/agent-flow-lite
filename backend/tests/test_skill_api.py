"""
Tests for Skill API endpoints.

Tests all CRUD operations and the run endpoint with SSE streaming.
"""
import json
import shutil
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import create_app


# Test data
SAMPLE_SKILL_CONTENT = '''---
name: test-skill
description: A test skill for unit testing
inputs:
  - name: topic
    label: Topic
    type: text
    required: true
    description: The topic to discuss
model:
  temperature: 0.7
  max_tokens: 500
---

Write a brief summary about {{topic}}.
'''

SAMPLE_SKILL_CONTENT_NO_INPUTS = '''---
name: {name}
description: A simple skill without inputs
---

Hello, this is a simple skill with no inputs.
'''


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """Create a test client with isolated skills directory."""
    # Create isolated skills directory
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir(parents=True)

    # Monkeypatch the skills directory in skill_loader
    from app.api import skill as skill_module
    from app.core import skill_loader as skill_loader_module

    original_loader = skill_module.skill_loader
    test_loader = skill_loader_module.SkillLoader(skills_dir)
    skill_module.skill_loader = test_loader

    # Create app and test client
    app = create_app()
    client = TestClient(app)

    yield client

    # Cleanup
    skill_module.skill_loader = original_loader


@pytest.fixture
def created_skill(test_client):
    """Create a skill and return its name."""
    response = test_client.post(
        "/api/v1/skills",
        json={
            "name": "test-skill",
            "content": SAMPLE_SKILL_CONTENT
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return "test-skill"


class TestListSkills:
    """Tests for GET /api/v1/skills"""

    def test_list_empty_skills(self, test_client):
        """Test listing skills when none exist."""
        response = test_client.get("/api/v1/skills")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skills"] == []
        assert data["total"] == 0

    def test_list_skills_with_data(self, test_client, created_skill):
        """Test listing skills with existing skills."""
        response = test_client.get("/api/v1/skills")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["skills"]) == 1
        assert data["total"] == 1
        skill = data["skills"][0]
        assert skill["name"] == "test-skill"
        assert skill["description"] == "A test skill for unit testing"
        assert skill["has_inputs"] is True
        assert skill["has_knowledge_base"] is False


class TestGetSkill:
    """Tests for GET /api/v1/skills/{name}"""

    def test_get_existing_skill(self, test_client, created_skill):
        """Test getting an existing skill."""
        response = test_client.get(f"/api/v1/skills/{created_skill}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "test-skill"
        assert data["description"] == "A test skill for unit testing"
        assert data["prompt"] == "Write a brief summary about {{topic}}."
        assert len(data["inputs"]) == 1
        assert data["inputs"][0]["name"] == "topic"

    def test_get_nonexistent_skill(self, test_client):
        """Test getting a skill that doesn't exist."""
        response = test_client.get("/api/v1/skills/nonexistent-skill")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data


class TestCreateSkill:
    """Tests for POST /api/v1/skills"""

    def test_create_skill_success(self, test_client):
        """Test creating a new skill successfully."""
        content = SAMPLE_SKILL_CONTENT_NO_INPUTS.format(name="new-skill")
        response = test_client.post(
            "/api/v1/skills",
            json={
                "name": "new-skill",
                "content": content
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "new-skill"
        assert data["description"] == "A simple skill without inputs"

    def test_create_skill_invalid_name(self, test_client):
        """Test creating a skill with invalid name format."""
        content = SAMPLE_SKILL_CONTENT_NO_INPUTS.format(name="Invalid_Name")
        response = test_client.post(
            "/api/v1/skills",
            json={
                "name": "Invalid_Name",
                "content": content
            }
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_create_skill_duplicate(self, test_client, created_skill):
        """Test creating a skill with duplicate name."""
        content = SAMPLE_SKILL_CONTENT_NO_INPUTS.format(name="test-skill")
        response = test_client.post(
            "/api/v1/skills",
            json={
                "name": "test-skill",
                "content": content
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_skill_empty_content(self, test_client):
        """Test creating a skill with empty content."""
        response = test_client.post(
            "/api/v1/skills",
            json={
                "name": "empty-skill",
                "content": ""
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateSkill:
    """Tests for PUT /api/v1/skills/{name}"""

    def test_update_skill_success(self, test_client, created_skill):
        """Test updating an existing skill."""
        updated_content = '''---
name: test-skill
description: Updated description
inputs:
  - name: topic
    label: Topic
    type: text
    required: true
---

Updated prompt about {{topic}}.
'''
        response = test_client.put(
            f"/api/v1/skills/{created_skill}",
            json={"content": updated_content}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["prompt"] == "Updated prompt about {{topic}}."

    def test_update_skill_name_unchanged(self, test_client, created_skill):
        """Test that skill name cannot be changed via update."""
        # Try to update with different name in frontmatter
        updated_content = '''---
name: different-name
description: Trying to change name
---

Some prompt.
'''
        response = test_client.put(
            f"/api/v1/skills/{created_skill}",
            json={"content": updated_content}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "name" in str(data["detail"]).lower() or "cannot change" in str(data["detail"]).lower()

    def test_update_nonexistent_skill(self, test_client):
        """Test updating a skill that doesn't exist."""
        content = SAMPLE_SKILL_CONTENT_NO_INPUTS.format(name="nonexistent-skill")
        response = test_client.put(
            "/api/v1/skills/nonexistent-skill",
            json={"content": content}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteSkill:
    """Tests for DELETE /api/v1/skills/{name}"""

    def test_delete_skill_success(self, test_client, created_skill):
        """Test deleting an existing skill."""
        response = test_client.delete(f"/api/v1/skills/{created_skill}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        get_response = test_client.get(f"/api/v1/skills/{created_skill}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_skill(self, test_client):
        """Test deleting a skill that doesn't exist."""
        response = test_client.delete("/api/v1/skills/nonexistent-skill")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunSkill:
    """Tests for POST /api/v1/skills/{name}/run"""

    def test_run_skill_streaming(self, test_client, created_skill, monkeypatch):
        """Test running a skill returns SSE stream."""
        # Mock the skill executor to avoid actual LLM calls
        from app.core import skill_executor as executor_module

        async def mock_execute(self, skill, inputs):
            yield "event: thought\ndata: {\"type\": \"validation\", \"status\": \"complete\"}\n\n"
            yield "event: token\ndata: {\"content\": \"Hello\"}\n\n"
            yield "event: done\ndata: {\"status\": \"success\"}\n\n"

        monkeypatch.setattr(
            executor_module.SkillExecutor,
            "execute",
            mock_execute
        )

        response = test_client.post(
            f"/api/v1/skills/{created_skill}/run",
            json={"inputs": {"topic": "AI"}}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        content = response.content.decode("utf-8")
        assert "event: thought" in content
        assert "event: token" in content
        assert "event: done" in content

    def test_run_nonexistent_skill(self, test_client):
        """Test running a skill that doesn't exist."""
        response = test_client.post(
            "/api/v1/skills/nonexistent-skill/run",
            json={"inputs": {}}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_run_skill_missing_required_input(self, test_client, created_skill):
        """Test running a skill without required inputs."""
        response = test_client.post(
            f"/api/v1/skills/{created_skill}/run",
            json={"inputs": {}}  # Missing required "topic" input
        )
        # Should still return 200 with SSE stream that contains error
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


class TestSkillValidation:
    """Tests for skill name validation."""

    @pytest.mark.parametrize("name,should_succeed", [
        ("valid-skill", True),
        ("skill123", True),
        ("a", True),
        ("a" * 64, True),
        ("Invalid_Name", False),
        ("-invalid-start", False),
        ("invalid-end-", False),
        ("invalid--double", False),
        ("invalid space", False),
        ("invalid_underscore", False),
        ("", False),
    ])
    def test_name_validation(self, test_client, name, should_succeed):
        """Test various name formats."""
        content = f'''---\nname: {name}\ndescription: Test\n---\n\nPrompt.\n'''
        response = test_client.post(
            "/api/v1/skills",
            json={"name": name, "content": content}
        )
        if should_succeed:
            if response.status_code == status.HTTP_201_CREATED:
                test_client.delete(f"/api/v1/skills/{name}")
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT]
        else:
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
