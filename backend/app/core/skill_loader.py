"""
Skill Loader - SKILL.md parsing, validation, and file operations.

Provides CRUD operations for skills with FileLock protection,
path traversal protection, and comprehensive validation.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from filelock import FileLock

from app.models.skill import (
    SkillDetail,
    SkillInput,
    SkillModelConfig,
    SkillSummary,
)


class SkillValidationError(Exception):
    """Raised when skill validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class SkillLoader:
    """Load, parse, and manage skills from the filesystem."""

    MAX_FILE_SIZE = 50 * 1024  # 50KB soft limit
    SKILL_FILENAME = "SKILL.md"

    def __init__(self, skills_dir: Path):
        """
        Initialize the skill loader.

        Args:
            skills_dir: Root directory containing skill folders
        """
        self.skills_dir = Path(skills_dir)
        self._ensure_skills_dir()

    def _ensure_skills_dir(self) -> None:
        """Ensure the skills directory exists."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def _get_skill_path(self, name: str) -> Path:
        """
        Get the path to a skill's SKILL.md file.

        Args:
            name: Skill name

        Returns:
            Path to SKILL.md file

        Raises:
            SkillValidationError: If name is invalid or path traversal detected
        """
        self._validate_name_format(name)

        skill_dir = self.skills_dir / name
        skill_file = skill_dir / self.SKILL_FILENAME

        # Path traversal protection: ensure resolved path is within skills_dir
        try:
            resolved = skill_file.resolve()
            resolved.relative_to(self.skills_dir.resolve())
        except (ValueError, RuntimeError) as exc:
            raise SkillValidationError(
                "Invalid skill path: potential path traversal detected",
                field="name",
            ) from exc

        return skill_file

    def _validate_name_format(self, name: str) -> None:
        """
        Validate skill name format according to Agent Skills spec.

        Rules:
        - Lowercase letters, numbers, and hyphens only
        - Cannot start or end with hyphen
        - No consecutive hyphens
        - 1-64 characters

        Args:
            name: Skill name to validate

        Raises:
            SkillValidationError: If name is invalid
        """
        if not name:
            raise SkillValidationError("Skill name is required", field="name")

        if len(name) > 64:
            raise SkillValidationError(
                "Skill name must be 64 characters or less",
                field="name",
            )

        if name != name.lower():
            raise SkillValidationError(
                "Skill name must be lowercase",
                field="name",
            )

        if not re.match(r"^[a-z0-9-]+$", name):
            raise SkillValidationError(
                "Skill name can only contain lowercase letters, numbers, and hyphens",
                field="name",
            )

        if name.startswith("-") or name.endswith("-"):
            raise SkillValidationError(
                "Skill name cannot start or end with a hyphen",
                field="name",
            )

        if "--" in name:
            raise SkillValidationError(
                "Skill name cannot contain consecutive hyphens",
                field="name",
            )

    def _validate_size(self, content: str) -> None:
        """
        Validate file size is under the soft limit.

        Args:
            content: File content to check

        Raises:
            SkillValidationError: If content exceeds size limit
        """
        size_bytes = len(content.encode("utf-8"))
        if size_bytes > self.MAX_FILE_SIZE:
            raise SkillValidationError(
                f"Skill file size ({size_bytes} bytes) exceeds "
                f"the soft limit of {self.MAX_FILE_SIZE} bytes (50KB). "
                "Consider splitting into smaller skills or reducing content.",
                field="content",
            )

    def _validate_placeholders(self, prompt: str, inputs: Optional[List[SkillInput]]) -> None:
        """
        Validate that all {{placeholders}} in prompt are declared inputs.

        Args:
            prompt: The prompt template
            inputs: List of declared input definitions

        Raises:
            SkillValidationError: If undeclared placeholders found
        """
        if not inputs:
            input_names = set()
        else:
            input_names = {inp.name for inp in inputs}

        # Find all {{placeholder}} patterns
        placeholders = set(re.findall(r"\{\{(\w+)\}\}", prompt))

        undeclared = placeholders - input_names
        if undeclared:
            raise SkillValidationError(
                f"Undeclared placeholders in prompt: {', '.join(sorted(undeclared))}. "
                f"Add them to inputs or remove from prompt.",
                field="prompt",
            )

    def _check_name_uniqueness(self, name: str, exclude_path: Optional[Path] = None) -> None:
        """
        Check that skill name is unique (case-insensitive).

        Args:
            name: Skill name to check
            exclude_path: Optional path to exclude from check (for updates)

        Raises:
            SkillValidationError: If name already exists
        """
        name_lower = name.lower()

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / self.SKILL_FILENAME
            if not skill_file.exists():
                continue

            if exclude_path and skill_file.resolve() == exclude_path.resolve():
                continue

            if skill_dir.name.lower() == name_lower:
                raise SkillValidationError(
                    f"Skill name '{name}' conflicts with existing skill "
                    f"'{skill_dir.name}' (names are case-insensitive)",
                    field="name",
                )

    def parse_skill_md(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse SKILL.md content into frontmatter and body.

        Args:
            content: Raw SKILL.md content

        Returns:
            Tuple of (frontmatter dict, markdown body)

        Raises:
            SkillValidationError: If parsing fails
        """
        if not content.strip():
            raise SkillValidationError("Skill content is empty", field="content")

        # Check for YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                body = parts[2].strip()

                try:
                    frontmatter = yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError as exc:
                    raise SkillValidationError(
                        f"Invalid YAML frontmatter: {exc}",
                        field="frontmatter",
                    ) from exc

                return frontmatter, body

        # No frontmatter, entire content is body
        return {}, content.strip()

    def _rebuild_skill_md(self, frontmatter: Dict[str, Any], body: str) -> str:
        """
        Rebuild SKILL.md content from frontmatter and body.

        Args:
            frontmatter: Parsed YAML frontmatter
            body: Markdown body (prompt)

        Returns:
            Reconstructed SKILL.md content
        """
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_content}---\n\n{body}"

    def _build_skill_detail(
        self,
        name: str,
        frontmatter: Dict[str, Any],
        body: str,
        raw_content: str,
        skill_file: Path,
    ) -> SkillDetail:
        """
        Build SkillDetail from parsed content.

        Args:
            name: Skill name
            frontmatter: Parsed YAML frontmatter
            body: Markdown body (prompt)
            raw_content: Original file content
            skill_file: Path to SKILL.md file

        Returns:
            SkillDetail model
        """
        # Parse inputs
        inputs = None
        if frontmatter.get("inputs"):
            inputs = [
                SkillInput(
                    name=inp.get("name", ""),
                    label=inp.get("label", ""),
                    type=inp.get("type", "text"),
                    required=inp.get("required", False),
                    default=inp.get("default"),
                    description=inp.get("description"),
                )
                for inp in frontmatter["inputs"]
                if isinstance(inp, dict) and inp.get("name")
            ]

        # Parse model config (must be a dict, ignore string values)
        model = None
        if frontmatter.get("model") and isinstance(frontmatter["model"], dict):
            model_data = frontmatter["model"]
            model = SkillModelConfig(
                temperature=model_data.get("temperature", 0.7),
                max_tokens=model_data.get("max_tokens", 2000),
            )

        # Get file timestamps
        stat = skill_file.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        updated_at = datetime.fromtimestamp(stat.st_mtime)

        return SkillDetail(
            name=name,
            description=frontmatter.get("description", ""),
            license=frontmatter.get("license"),
            metadata=frontmatter.get("metadata"),
            inputs=inputs if inputs else None,
            knowledge_base=frontmatter.get("knowledge_base"),
            model=model,
            user_id=frontmatter.get("user_id"),
            prompt=body,
            raw_content=raw_content,
            created_at=created_at,
            updated_at=updated_at,
        )

    def list_skills(self, user_id: Optional[str] = None) -> List[SkillSummary]:
        """
        Scan skills directory and return list of all skills.

        Args:
            user_id: Optional user ID to filter by owner (admin sees all)

        Returns:
            List of SkillSummary objects
        """
        skills = []

        if not self.skills_dir.exists():
            return skills

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / self.SKILL_FILENAME
            if not skill_file.exists():
                continue

            try:
                skill = self.get_skill(skill_dir.name)
                # Filter by user_id if provided (non-admin users only see their own skills)
                if user_id is not None:
                    # If skill has a user_id, must match
                    if skill.user_id and skill.user_id != str(user_id):
                        continue
                    # If skill has no user_id, it's orphaned - skip for user-scoped access
                    if not skill.user_id:
                        continue
                skills.append(
                    SkillSummary(
                        name=skill.name,
                        description=skill.description,
                        has_inputs=bool(skill.inputs),
                        has_knowledge_base=bool(skill.knowledge_base),
                        updated_at=skill.updated_at,
                    )
                )
            except (SkillValidationError, Exception):
                from pydantic import ValidationError
                continue

        # Sort by updated_at descending
        skills.sort(key=lambda s: s.updated_at, reverse=True)
        return skills

    def get_skill(self, name: str) -> SkillDetail:
        """
        Load and parse a single skill.

        Args:
            name: Skill name

        Returns:
            SkillDetail model

        Raises:
            SkillValidationError: If skill not found or invalid
        """
        skill_file = self._get_skill_path(name)

        if not skill_file.exists():
            raise SkillValidationError(
                f"Skill '{name}' not found",
                field="name",
            )

        lock = FileLock(str(skill_file) + ".lock")
        with lock:
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except IOError as exc:
                raise SkillValidationError(
                    f"Failed to read skill file: {exc}",
                    field="content",
                ) from exc

        frontmatter, body = self.parse_skill_md(content)

        # Validate that frontmatter name matches folder name
        fm_name = frontmatter.get("name")
        if fm_name and fm_name != name:
            raise SkillValidationError(
                f"Skill name mismatch: folder name '{name}' "
                f"does not match frontmatter name '{fm_name}'",
                field="name",
            )

        return self._build_skill_detail(name, frontmatter, body, content, skill_file)

    def create_skill(self, name: str, content: str, user_id: Optional[str] = None) -> SkillDetail:
        """
        Create a new skill folder and SKILL.md file.

        Args:
            name: Skill name (used as folder name)
            content: Complete SKILL.md content
            user_id: Owner user ID (optional)

        Returns:
            SkillDetail of created skill

        Raises:
            SkillValidationError: If validation fails or skill exists
        """
        self._validate_name_format(name)
        self._validate_size(content)
        self._check_name_uniqueness(name)

        # Parse and validate content
        frontmatter, body = self.parse_skill_md(content)

        # Validate frontmatter name matches if provided
        fm_name = frontmatter.get("name")
        if fm_name and fm_name != name:
            raise SkillValidationError(
                f"Frontmatter name '{fm_name}' does not match "
                f"requested name '{name}'",
                field="name",
            )

        # Validate placeholders
        inputs = None
        if frontmatter.get("inputs"):
            inputs = [
                SkillInput(
                    name=inp.get("name", ""),
                    label=inp.get("label", ""),
                    type=inp.get("type", "text"),
                    required=inp.get("required", False),
                    default=inp.get("default"),
                    description=inp.get("description"),
                )
                for inp in frontmatter["inputs"]
                if isinstance(inp, dict) and inp.get("name")
            ]
        self._validate_placeholders(body, inputs)

        # Inject user_id if provided
        if user_id and "user_id" not in frontmatter:
            frontmatter["user_id"] = user_id

        # Rebuild content with injected user_id
        content = self._rebuild_skill_md(frontmatter, body)

        # Create skill directory and file
        skill_file = self._get_skill_path(name)
        skill_dir = skill_file.parent

        if skill_dir.exists():
            raise SkillValidationError(
                f"Skill '{name}' already exists",
                field="name",
            )

        skill_dir.mkdir(parents=True, exist_ok=True)

        lock = FileLock(str(skill_file) + ".lock")
        with lock:
            try:
                with open(skill_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except IOError as exc:
                # Clean up on failure
                if skill_dir.exists():
                    skill_dir.rmdir()
                raise SkillValidationError(
                    f"Failed to write skill file: {exc}",
                    field="content",
                ) from exc

        return self.get_skill(name)

    def update_skill(self, name: str, content: str) -> SkillDetail:
        """
        Update an existing skill's SKILL.md content.

        Args:
            name: Skill name
            content: New SKILL.md content

        Returns:
            SkillDetail of updated skill

        Raises:
            SkillValidationError: If validation fails or skill not found
        """
        self._validate_size(content)

        skill_file = self._get_skill_path(name)

        if not skill_file.exists():
            raise SkillValidationError(
                f"Skill '{name}' not found",
                field="name",
            )

        # Parse and validate content
        frontmatter, body = self.parse_skill_md(content)

        # Validate frontmatter name matches folder name
        fm_name = frontmatter.get("name")
        if fm_name and fm_name != name:
            raise SkillValidationError(
                f"Cannot change skill name via update. "
                f"Frontmatter name '{fm_name}' does not match '{name}'",
                field="name",
            )

        # Validate placeholders
        inputs = None
        if frontmatter.get("inputs"):
            inputs = [
                SkillInput(
                    name=inp.get("name", ""),
                    label=inp.get("label", ""),
                    type=inp.get("type", "text"),
                    required=inp.get("required", False),
                    default=inp.get("default"),
                    description=inp.get("description"),
                )
                for inp in frontmatter["inputs"]
                if isinstance(inp, dict) and inp.get("name")
            ]
        self._validate_placeholders(body, inputs)

        lock = FileLock(str(skill_file) + ".lock")
        with lock:
            try:
                with open(skill_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except IOError as exc:
                raise SkillValidationError(
                    f"Failed to write skill file: {exc}",
                    field="content",
                ) from exc

        return self.get_skill(name)

    def delete_skill(self, name: str) -> None:
        """
        Delete a skill folder and all its contents.

        Args:
            name: Skill name to delete

        Raises:
            SkillValidationError: If skill not found or cannot be deleted
        """
        skill_file = self._get_skill_path(name)
        skill_dir = skill_file.parent

        if not skill_file.exists():
            raise SkillValidationError(
                f"Skill '{name}' not found",
                field="name",
            )

        lock = FileLock(str(skill_file) + ".lock")
        with lock:
            try:
                import shutil

                shutil.rmtree(skill_dir)
            except OSError as exc:
                raise SkillValidationError(
                    f"Failed to delete skill directory: {exc}",
                    field="name",
                ) from exc

    def normalize_name(self, name: str) -> str:
        """
        Normalize a name to valid skill name format.

        Rules:
        - Convert to lowercase
        - Replace spaces with hyphens
        - Remove invalid characters
        - Collapse multiple hyphens
        - Trim leading/trailing hyphens

        Args:
            name: Raw name to normalize

        Returns:
            Normalized skill name
        """
        # Convert to lowercase
        normalized = name.lower()

        # Replace spaces with hyphens
        normalized = normalized.replace(" ", "-")

        # Remove invalid characters (keep only lowercase letters, numbers, hyphens)
        normalized = re.sub(r"[^a-z0-9-]", "", normalized)

        # Collapse multiple hyphens
        normalized = re.sub(r"-+", "-", normalized)

        # Trim leading/trailing hyphens
        normalized = normalized.strip("-")

        return normalized or "skill"
