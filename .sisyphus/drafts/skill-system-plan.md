# Draft: Skill System Plan

## Requirements (confirmed)
- User requested: read docs/skill-system-design.md and produce a development plan.
- Scope decision: P0 + P1 (include Chat @skill + LLM node loading).
- Test strategy: tests-after (关键 API/前端视图测试 + 核心逻辑单测).
- Editor choice: textarea (MVP, no new heavy deps).
- Auth/user integration: defer (Phase 1 only, user_id null, global visibility).
- SKILL.md size limit: soft limit <50KB with friendly error.
- Git workflow: create branch `feature/skill-system` before implementation.

## Technical Decisions
- Skill names: normalize to lowercase for folder name; enforce name constraints and case-insensitive uniqueness.
- Disallow renaming via API in MVP (name immutable on update).
- Variable substitution: single-pass (non-recursive), required inputs validated; optional use defaults; undefined placeholders rejected on create/update.
- Path traversal protection for skill file paths.
- No visibility field in MVP (explicitly defer auth/visibility).

## Research Findings
- Source: docs/skill-system-design.md
  - Skill CRUD API, list page, editor, run, workflow node are P0.
  - Chat @skill and LLM node loading are P1; AI-assisted creation is P2.
  - Skills stored under /skills/{name}/SKILL.md with YAML frontmatter + Markdown body.
  - API base: /api/v1/skills with list/get/create/update/delete/run.
  - Backend modules: backend/app/models/skill.py, core/skill_loader.py, core/skill_executor.py, api/skill.py, register in main.py.
  - Frontend views: SkillsView.vue, SkillEditor.vue; node component SkillNode.vue; routes /skills and /skills/:name.
  - Run API returns SSE events: thought/token/citation/done.
  - Workflow node executes skill with input mapping and context resolution.
  - Chat @skill parsing regex and execution flow defined.
  - Notes: name validation, FileLock for concurrent edits, size limit (<50KB), friendly errors, backward compatible fields.
  - User management integration deferred; user_id string, permissions matrix when integrated.
- Source: repo test infra scan
  - Frontend: Vitest configured in frontend/vitest.config.ts; tests under frontend/src/components/__tests__/ and frontend/src/__tests__/views/; scripts in frontend/package.json.
  - Backend: pytest in backend/pyproject.toml; tests under backend/tests/ (e.g., test_chat_api.py, test_zep_client.py).
  - Commands: npm run test / test:ui, npx vitest run <file>; uv run pytest -q / -k pattern / <file>.
- Source: codebase patterns (explore)
  - Workflow node executors live in backend/app/core/workflow_nodes.py; executor registration in backend/app/core/workflow_engine.py.
  - SSE streaming pattern in backend/app/api/chat.py (StreamingResponse + format_sse_event).
  - FileLock-based CRUD pattern in backend/app/api/workflow.py and backend/app/api/knowledge.py.
  - Frontend SSE handling in frontend/src/views/ChatTerminal.vue.
- Source: Agent Skills spec (agentskills.io)
  - SKILL.md uses YAML frontmatter + Markdown body; name constraints: lowercase letters/digits/hyphen, no leading/trailing hyphen, no consecutive hyphens, must match folder name.
  - Standard fields: name, description, license, metadata, compatibility, allowed-tools.
  - Examples in https://agentskills.io/specification and https://github.com/anthropics/skills.

## Open Questions
No open questions.

## Scope Boundaries
- INCLUDE: Skill system features as defined by scope decision.
- EXCLUDE: Not decided yet.
