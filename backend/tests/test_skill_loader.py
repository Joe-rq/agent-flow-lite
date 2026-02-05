"""
Tests for skill_loader module.

Covers validation logic, CRUD operations, and error handling.
"""
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.core.skill_loader import SkillLoader, SkillValidationError
from app.models.skill import SkillInput, SkillModelConfig


@pytest.fixture
def temp_skills_dir():
    """Create a temporary directory for skills."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def loader(temp_skills_dir):
    """Create a SkillLoader instance with temp directory."""
    return SkillLoader(temp_skills_dir)


class TestNameValidation:
    """Test skill name format validation."""

    def test_valid_names(self, loader):
        """Test that valid names pass validation."""
        valid_names = [
            "article-summary",
            "code-review",
            "test123",
            "a",
            "my-skill-name",
            "skill123-test",
        ]
        for name in valid_names:
            loader._validate_name_format(name)

    def test_empty_name_raises_error(self, loader):
        """Test that empty name raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_name_format("")
        assert "required" in exc_info.value.message.lower()
        assert exc_info.value.field == "name"

    def test_uppercase_raises_error(self, loader):
        """Test that uppercase letters raise error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_name_format("Article-Summary")
        assert "lowercase" in exc_info.value.message.lower()
        assert exc_info.value.field == "name"

    def test_leading_hyphen_raises_error(self, loader):
        """Test that leading hyphen raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_name_format("-article-summary")
        assert "start" in exc_info.value.message.lower()
        assert exc_info.value.field == "name"

    def test_trailing_hyphen_raises_error(self, loader):
        """Test that trailing hyphen raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_name_format("article-summary-")
        assert "end" in exc_info.value.message.lower()
        assert exc_info.value.field == "name"

    def test_consecutive_hyphens_raise_error(self, loader):
        """Test that consecutive hyphens raise error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_name_format("article--summary")
        assert "consecutive" in exc_info.value.message.lower()
        assert exc_info.value.field == "name"

    def test_invalid_characters_raise_error(self, loader):
        """Test that special characters raise error."""
        invalid_names = [
            "article_summary",
            "article.summary",
            "article summary",
            "article@summary",
            "article#summary",
        ]
        for name in invalid_names:
            with pytest.raises(SkillValidationError) as exc_info:
                loader._validate_name_format(name)
            assert exc_info.value.field == "name"

    def test_name_too_long_raises_error(self, loader):
        """Test that names over 64 characters raise error."""
        long_name = "a" * 65
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_name_format(long_name)
        assert "64" in exc_info.value.message
        assert exc_info.value.field == "name"


class TestSizeValidation:
    """Test file size validation."""

    def test_valid_size_passes(self, loader):
        """Test that content under 50KB passes."""
        content = "x" * (50 * 1024 - 1)
        loader._validate_size(content)

    def test_size_at_limit_passes(self, loader):
        """Test that content exactly at 50KB passes."""
        content = "x" * (50 * 1024)
        loader._validate_size(content)

    def test_size_over_limit_raises_error(self, loader):
        """Test that content over 50KB raises error."""
        content = "x" * (50 * 1024 + 1)
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_size(content)
        assert "50KB" in exc_info.value.message
        assert "soft limit" in exc_info.value.message.lower()
        assert exc_info.value.field == "content"


class TestPlaceholderValidation:
    """Test placeholder validation in prompts."""

    def test_valid_placeholders_pass(self, loader):
        """Test that declared placeholders pass validation."""
        prompt = "Hello {{name}}, your age is {{age}}"
        inputs = [
            SkillInput(name="name", label="Name", type="text"),
            SkillInput(name="age", label="Age", type="text"),
        ]
        loader._validate_placeholders(prompt, inputs)

    def test_no_placeholders_pass(self, loader):
        """Test that prompts without placeholders pass."""
        prompt = "Hello world"
        inputs = [SkillInput(name="name", label="Name", type="text")]
        loader._validate_placeholders(prompt, inputs)

    def test_no_inputs_no_placeholders_pass(self, loader):
        """Test that prompts without inputs and placeholders pass."""
        prompt = "Hello world"
        loader._validate_placeholders(prompt, None)

    def test_undeclared_placeholder_raises_error(self, loader):
        """Test that undeclared placeholders raise error."""
        prompt = "Hello {{name}}, your age is {{age}}"
        inputs = [SkillInput(name="name", label="Name", type="text")]
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_placeholders(prompt, inputs)
        assert "age" in exc_info.value.message
        assert "Undeclared" in exc_info.value.message
        assert exc_info.value.field == "prompt"

    def test_multiple_undeclared_placeholders(self, loader):
        """Test that multiple undeclared placeholders are all reported."""
        prompt = "Hello {{a}}, {{b}}, {{c}}"
        inputs = []
        with pytest.raises(SkillValidationError) as exc_info:
            loader._validate_placeholders(prompt, inputs)
        assert "a" in exc_info.value.message
        assert "b" in exc_info.value.message
        assert "c" in exc_info.value.message


class TestNameUniqueness:
    """Test case-insensitive name uniqueness."""

    def test_duplicate_name_raises_error(self, loader, temp_skills_dir):
        """Test that duplicate names raise error."""
        skill_dir = temp_skills_dir / "article-summary"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: article-summary\n---\n")

        with pytest.raises(SkillValidationError) as exc_info:
            loader._check_name_uniqueness("article-summary")
        assert "conflicts" in exc_info.value.message.lower()

    def test_case_insensitive_duplicate_raises_error(self, loader, temp_skills_dir):
        """Test that case-insensitive duplicates raise error."""
        skill_dir = temp_skills_dir / "Article-Summary"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: Article-Summary\n---\n")

        with pytest.raises(SkillValidationError) as exc_info:
            loader._check_name_uniqueness("article-summary")
        assert "case-insensitive" in exc_info.value.message.lower()

    def test_exclude_path_allows_same_skill(self, loader, temp_skills_dir):
        """Test that excluding path allows same skill for updates."""
        skill_dir = temp_skills_dir / "article-summary"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: article-summary\n---\n")

        # Should not raise when excluding the same file
        loader._check_name_uniqueness(
            "article-summary", exclude_path=skill_file
        )


class TestParseSkillMd:
    """Test SKILL.md parsing."""

    def test_parse_with_frontmatter(self, loader):
        """Test parsing content with YAML frontmatter."""
        content = """---
name: article-summary
description: Summarize articles
inputs:
  - name: article
    label: Article
    type: textarea
---

Please summarize: {{article}}"""

        frontmatter, body = loader.parse_skill_md(content)

        assert frontmatter["name"] == "article-summary"
        assert frontmatter["description"] == "Summarize articles"
        assert len(frontmatter["inputs"]) == 1
        assert frontmatter["inputs"][0]["name"] == "article"
        assert body == "Please summarize: {{article}}"

    def test_parse_without_frontmatter(self, loader):
        """Test parsing content without frontmatter."""
        content = "Just a plain prompt without frontmatter"

        frontmatter, body = loader.parse_skill_md(content)

        assert frontmatter == {}
        assert body == "Just a plain prompt without frontmatter"

    def test_parse_empty_content_raises_error(self, loader):
        """Test that empty content raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader.parse_skill_md("")
        assert "empty" in exc_info.value.message.lower()

    def test_parse_whitespace_only_raises_error(self, loader):
        """Test that whitespace-only content raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader.parse_skill_md("   \n\t  ")
        assert "empty" in exc_info.value.message.lower()

    def test_parse_invalid_yaml_raises_error(self, loader):
        """Test that invalid YAML raises error."""
        content = """---
name: article-summary
description: [invalid yaml: broken
---

Body"""

        with pytest.raises(SkillValidationError) as exc_info:
            loader.parse_skill_md(content)
        assert "YAML" in exc_info.value.message


class TestPathTraversalProtection:
    def test_path_traversal_blocked_by_name_validation(self, loader):
        with pytest.raises(SkillValidationError) as exc_info:
            loader._get_skill_path("../../../etc/passwd")
        assert "lowercase letters, numbers, and hyphens" in exc_info.value.message

    def test_path_traversal_with_valid_name_blocked_by_validation(self, loader):
        with pytest.raises(SkillValidationError) as exc_info:
            loader._get_skill_path("skill-name/../../../etc")
        assert "lowercase letters, numbers, and hyphens" in exc_info.value.message


class TestNormalizeName:
    """Test name normalization."""

    def test_lowercase_conversion(self, loader):
        """Test that uppercase letters are converted to lowercase."""
        assert loader.normalize_name("ArticleSummary") == "articlesummary"

    def test_space_to_hyphen(self, loader):
        """Test that spaces are converted to hyphens."""
        assert loader.normalize_name("article summary") == "article-summary"

    def test_multiple_spaces_collapsed(self, loader):
        """Test that multiple spaces are collapsed."""
        assert loader.normalize_name("article   summary") == "article-summary"

    def test_invalid_chars_removed(self, loader):
        """Test that invalid characters are removed."""
        assert loader.normalize_name("article@summary#test") == "articlesummarytest"

    def test_multiple_hyphens_collapsed(self, loader):
        """Test that multiple hyphens are collapsed."""
        assert loader.normalize_name("article---summary") == "article-summary"

    def test_leading_trailing_hyphens_trimmed(self, loader):
        """Test that leading/trailing hyphens are trimmed."""
        assert loader.normalize_name("-article-summary-") == "article-summary"

    def test_empty_result_defaults_to_skill(self, loader):
        """Test that empty result defaults to 'skill'."""
        assert loader.normalize_name("@#$%") == "skill"

    def test_complex_normalization(self, loader):
        """Test complex name normalization."""
        assert (
            loader.normalize_name("My Article Summary!!!")
            == "my-article-summary"
        )


class TestCRUDOperations:
    """Test CRUD operations."""

    def test_create_skill(self, loader):
        """Test creating a new skill."""
        content = """---
name: test-skill
description: A test skill
inputs:
  - name: input1
    label: Input 1
    type: text
---

Process this: {{input1}}"""

        skill = loader.create_skill("test-skill", content)

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert len(skill.inputs) == 1
        assert skill.inputs[0].name == "input1"
        assert skill.prompt == "Process this: {{input1}}"
        assert skill.raw_content == content

    def test_create_skill_already_exists_raises_error(self, loader):
        """Test that creating duplicate skill raises error."""
        content = "---\nname: test-skill\ndescription: Test\n---\n\nBody"
        loader.create_skill("test-skill", content)

        with pytest.raises(SkillValidationError) as exc_info:
            loader.create_skill("test-skill", content)
        assert "conflicts" in exc_info.value.message.lower()

    def test_create_skill_name_mismatch_raises_error(self, loader):
        """Test that name mismatch between folder and frontmatter raises error."""
        content = "---\nname: different-name\n---\n\nBody"

        with pytest.raises(SkillValidationError) as exc_info:
            loader.create_skill("test-skill", content)
        assert "does not match" in exc_info.value.message.lower()

    def test_create_skill_undeclared_placeholder_raises_error(self, loader):
        """Test that undeclared placeholders raise error on create."""
        content = "---\nname: test-skill\n---\n\nProcess: {{undeclared}}"

        with pytest.raises(SkillValidationError) as exc_info:
            loader.create_skill("test-skill", content)
        assert "Undeclared" in exc_info.value.message

    def test_get_skill(self, loader):
        """Test retrieving a skill."""
        content = "---\nname: test-skill\ndescription: Test\n---\n\nBody"
        loader.create_skill("test-skill", content)

        skill = loader.get_skill("test-skill")

        assert skill.name == "test-skill"
        assert skill.description == "Test"

    def test_get_skill_not_found_raises_error(self, loader):
        """Test that getting non-existent skill raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader.get_skill("nonexistent")
        assert "not found" in exc_info.value.message.lower()

    def test_get_skill_name_mismatch_raises_error(self, loader, temp_skills_dir):
        """Test that name mismatch raises error on get."""
        skill_dir = temp_skills_dir / "folder-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: different-name\n---\n\nBody"
        )

        with pytest.raises(SkillValidationError) as exc_info:
            loader.get_skill("folder-name")
        assert "mismatch" in exc_info.value.message.lower()

    def test_update_skill(self, loader):
        """Test updating a skill."""
        original = "---\nname: test-skill\ndescription: Original\n---\n\nOriginal"
        loader.create_skill("test-skill", original)

        updated = "---\nname: test-skill\ndescription: Updated\n---\n\nUpdated"
        skill = loader.update_skill("test-skill", updated)

        assert skill.description == "Updated"
        assert skill.prompt == "Updated"

    def test_update_skill_name_change_blocked(self, loader):
        """Test that changing name via update is blocked."""
        original = "---\nname: test-skill\ndescription: Test\n---\n\nBody"
        loader.create_skill("test-skill", original)

        updated = "---\nname: new-name\ndescription: Test\n---\n\nBody"
        with pytest.raises(SkillValidationError) as exc_info:
            loader.update_skill("test-skill", updated)
        assert "cannot change" in exc_info.value.message.lower()

    def test_delete_skill(self, loader, temp_skills_dir):
        """Test deleting a skill."""
        content = "---\nname: test-skill\ndescription: Test\n---\n\nBody"
        loader.create_skill("test-skill", content)

        loader.delete_skill("test-skill")

        assert not (temp_skills_dir / "test-skill").exists()

    def test_delete_skill_not_found_raises_error(self, loader):
        """Test that deleting non-existent skill raises error."""
        with pytest.raises(SkillValidationError) as exc_info:
            loader.delete_skill("nonexistent")
        assert "not found" in exc_info.value.message.lower()

    def test_list_skills(self, loader):
        """Test listing all skills."""
        content1 = "---\nname: skill-one\ndescription: First\n---\n\nBody"
        content2 = "---\nname: skill-two\ndescription: Second\ninputs:\n  - name: x\n    label: X\n---\n\n{{x}}"

        loader.create_skill("skill-one", content1)
        loader.create_skill("skill-two", content2)

        skills = loader.list_skills()

        assert len(skills) == 2
        names = {s.name for s in skills}
        assert names == {"skill-one", "skill-two"}

        # Check summary fields
        skill_two = next(s for s in skills if s.name == "skill-two")
        assert skill_two.has_inputs is True
        assert skill_two.has_knowledge_base is False

    def test_list_skills_empty(self, loader):
        """Test listing skills when none exist."""
        skills = loader.list_skills()
        assert skills == []

    def test_list_skills_sorted_by_updated(self, loader):
        """Test that skills are sorted by updated_at descending."""
        import time

        content1 = "---\nname: skill-first\ndescription: First\n---\n\nBody"
        content2 = "---\nname: skill-second\ndescription: Second\n---\n\nBody"

        loader.create_skill("skill-first", content1)
        time.sleep(0.01)
        loader.create_skill("skill-second", content2)

        skills = loader.list_skills()

        assert skills[0].name == "skill-second"
        assert skills[1].name == "skill-first"

    def test_list_skips_invalid_skills(self, loader, temp_skills_dir):
        """Test that invalid skills are skipped in list."""
        valid_content = "---\nname: valid-skill\ndescription: Valid\n---\n\nBody"
        loader.create_skill("valid-skill", valid_content)

        (temp_skills_dir / "invalid-dir").mkdir()

        bad_dir = temp_skills_dir / "bad-skill"
        bad_dir.mkdir()
        (bad_dir / "SKILL.md").write_text("not valid yaml: [")

        skills = loader.list_skills()

        assert len(skills) == 1
        assert skills[0].name == "valid-skill"


class TestComplexSkillParsing:
    """Test parsing of complex skill definitions."""

    def test_full_skill_with_all_fields(self, loader):
        """Test parsing skill with all possible fields."""
        content = """---
name: complex-skill
description: A complex skill with all features
license: MIT
metadata:
  author: test-author
  version: "1.0"
  tags:
    - test
    - complex
inputs:
  - name: article
    label: Article Content
    type: textarea
    required: true
    description: The article to process
  - name: style
    label: Output Style
    type: text
    required: false
    default: concise
knowledge_base: my-kb
model:
  temperature: 0.3
  max_tokens: 1000
user_id: user-123
---

Process {{article}} in {{style}} style."""

        skill = loader.create_skill("complex-skill", content)

        assert skill.name == "complex-skill"
        assert skill.description == "A complex skill with all features"
        assert skill.license == "MIT"
        assert skill.metadata == {
            "author": "test-author",
            "version": "1.0",
            "tags": ["test", "complex"],
        }
        assert len(skill.inputs) == 2
        assert skill.inputs[0].name == "article"
        assert skill.inputs[0].required is True
        assert skill.inputs[1].name == "style"
        assert skill.inputs[1].default == "concise"
        assert skill.knowledge_base == "my-kb"
        assert skill.model.temperature == 0.3
        assert skill.model.max_tokens == 1000
        assert skill.user_id == "user-123"

    def test_skill_with_knowledge_base(self, loader):
        """Test skill with knowledge base reference."""
        content = """---
name: kb-skill
description: Uses KB
knowledge_base: product-docs
inputs:
  - name: question
    label: Question
    type: text
---

Answer: {{question}}"""

        skill = loader.create_skill("kb-skill", content)

        assert skill.knowledge_base == "product-docs"
        assert skill.has_knowledge_base is True

    def test_skill_without_inputs(self, loader):
        """Test skill without any inputs."""
        content = """---
name: no-inputs
description: No inputs needed
---

Just a fixed prompt."""

        skill = loader.create_skill("no-inputs", content)

        assert skill.inputs is None
        assert skill.has_inputs is False

    def test_skill_with_model_as_string_does_not_crash(self, loader):
        """Test that model field as string is safely ignored (regression: AttributeError on .get())."""
        content = """---
name: string-model
description: Skill with model as string instead of dict
model: deepseek-chat
---

Just a prompt."""

        skill = loader.create_skill("string-model", content)

        assert skill.name == "string-model"
        assert skill.model is None  # String model should be ignored

    def test_skill_with_model_as_dict(self, loader):
        """Test that model field as dict is parsed correctly."""
        content = """---
name: dict-model
description: Skill with proper model config
model:
  temperature: 0.3
  max_tokens: 1000
---

Just a prompt."""

        skill = loader.create_skill("dict-model", content)

        assert skill.model is not None
        assert skill.model.temperature == 0.3
        assert skill.model.max_tokens == 1000

    def test_skill_without_model_field(self, loader):
        """Test that missing model field results in None."""
        content = """---
name: no-model
description: No model field
---

Just a prompt."""

        skill = loader.create_skill("no-model", content)

        assert skill.model is None
