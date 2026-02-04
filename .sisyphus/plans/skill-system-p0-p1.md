# Skill System (P0 + P1)

## TL;DR

> **Quick Summary**: Build a file-backed Skill system compatible with Agent Skills SKILL.md, including CRUD, editor, run, workflow node, Chat @skill, and LLM node loading. Follow existing FileLock + SSE patterns, defer auth/user integration, and keep the editor as a simple textarea MVP.
> 
> **Deliverables**:
> - Backend Skill models + loader + executor + API routes
> - Frontend Skills list/editor/run UI + node UI
> - Workflow Skill node execution + LLM node load-skill option
> - Chat @skill parsing and execution
> - Tests-after coverage for key API + views
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Branch → Backend loader/API/executor → Frontend Skills UI → Workflow/Chat/LLM integrations → Tests

---

## Context

### Original Request
“Read docs/skill-system-design.md and make a development plan.”

### Interview Summary
**Key Discussions**:
- Scope: P0 + P1 (CRUD + list/editor/run + workflow node + Chat @skill + LLM node load)
- Editor: textarea MVP (no heavy editor dependencies)
- Auth: deferred (Phase 1, user_id null, global visibility)
- Size limit: soft limit <50KB with friendly error
- Tests: tests-after (key API + front-end views + core logic)
- Git: create branch `feature/skill-system` before implementation

**Research Findings**:
- File CRUD + FileLock pattern exists in `backend/app/api/workflow.py` and `backend/app/api/knowledge.py`
- SSE streaming pattern exists in `backend/app/api/chat.py`
- Workflow node execution/registration in `backend/app/core/workflow_nodes.py` and `backend/app/core/workflow_engine.py`
- Frontend SSE parsing in `frontend/src/views/ChatTerminal.vue`
- Agent Skills spec at `https://agentskills.io/specification` (name constraints, standard fields)

### Metis Review
**Identified Gaps (addressed)**:
- Name normalization + filesystem mapping defined (lowercase, case-insensitive uniqueness)
- Variable substitution security defined (single-pass, no recursion, validate placeholders)
- Renaming explicitly excluded from MVP
- Path traversal protection required for skill file paths

---

## Work Objectives

### Core Objective
Deliver a P0+P1 Skill system that is file-backed, Agent Skills compatible, and integrated into workflow and chat with SSE streaming, while keeping UX minimal and deferring auth.

### Concrete Deliverables
- `backend/app/models/skill.py` with Pydantic models
- `backend/app/core/skill_loader.py` for SKILL.md parsing + CRUD + validation
- `backend/app/core/skill_executor.py` for variable substitution + RAG + LLM streaming
- `backend/app/api/skill.py` with CRUD + run endpoints
- Skill router registered in `backend/main.py`
- `/skills/` directory with example SKILL.md
- `frontend/src/views/SkillsView.vue` and `frontend/src/views/SkillEditor.vue`
- Workflow Skill node in backend + frontend components
- Chat @skill parsing/execution
- LLM node load-skill support

### Definition of Done
- [x] All API routes respond per spec (list/get/create/update/delete/run)
- [x] Skill run streams SSE events (thought/token/citation/done)
- [x] Skills list/editor/run UI works end-to-end
- [x] Workflow Skill node executes and returns output in context
- [x] Chat @skill triggers skill execution with required input mapping
- [x] LLM node can load skill prompt/model
- [x] Tests-after run successfully for key API + view flows

### Must Have
- Agent Skills compatible frontmatter, strict name validation
- FileLock around file operations
- Path traversal protection
- Soft size limit (<50KB) with friendly error

### Must NOT Have (Guardrails)
- No auth/user isolation in this phase
- No skill renaming via API
- No recursive variable substitution
- No heavy editor dependency (Monaco/CodeMirror)

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks MUST be verifiable WITHOUT any human action. The executing agent will run CLI, API calls, and Playwright/interactive_bash checks directly.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after
- **Frameworks**: Vitest (frontend), pytest (backend)

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)
All tasks include runnable, tool-based scenarios with explicit commands/selectors/data and evidence paths under `.sisyphus/evidence/`.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
- Task 1: Create feature branch
- Task 2: Backend models + loader (validation + file I/O)
- Task 3: Backend executor + run API (SSE)

Wave 2 (After Wave 1):
- Task 4: Backend CRUD API + router registration
- Task 5: Frontend Skills list/editor/run UI
- Task 6: Workflow Skill node (backend + frontend)

Wave 3 (After Wave 2):
- Task 7: Chat @skill integration
- Task 8: LLM node load-skill integration
- Task 9: Tests-after (backend + frontend)

Critical Path: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7/8 → Task 9

---

## TODOs

- [x] 1. Create feature branch `feature/skill-system`

  **What to do**:
  - Create git branch before any changes

  **Must NOT do**:
  - Do not modify git config
  - Do not switch back to main implicitly

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single git command
  - **Skills**: [`git-master`]
    - `git-master`: Required for git operations
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: Not relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES (no dependency)
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Tasks 2-9 (all work)
  - **Blocked By**: None

  **References**:
  - `AGENTS.md` - repo conventions; ensure branch naming aligns with workflow

  **Acceptance Criteria**:
  - [x] `git status` shows branch `feature/skill-system`

  **Agent-Executed QA Scenarios**:
  Scenario: Branch created
    Tool: Bash
    Preconditions: Repo exists
    Steps:
      1. `git checkout -b feature/skill-system`
      2. `git branch --show-current`
    Expected Result: Output equals `feature/skill-system`
    Evidence: `.sisyphus/evidence/task-1-branch.txt`

- [x] 2. Implement Skill models + loader with validation

  **What to do**:
  - Add `backend/app/models/skill.py` with Pydantic models per spec
  - Implement `backend/app/core/skill_loader.py`:
    - Scan `/skills/` directory
    - Parse YAML frontmatter + Markdown body
    - Validate name constraints and case-insensitive uniqueness
    - Enforce soft size limit <50KB
    - Validate placeholders are declared inputs
    - Protect against path traversal
    - FileLock around reads/writes

  **Must NOT do**:
  - Do not allow rename or folder mismatch
  - Do not add auth/user scoping

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Backend file parsing + validation logic
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Tasks 4-8
  - **Blocked By**: None

  **References**:
  - `docs/skill-system-design.md` - data model and SKILL.md format
  - `backend/app/api/workflow.py` - FileLock CRUD patterns
  - `backend/app/api/knowledge.py` - file-based CRUD patterns
  - `https://agentskills.io/specification` - name constraints and standard fields

  **Acceptance Criteria**:
  - [x] SKILL.md parsing returns frontmatter + body
  - [x] Invalid skill name returns 400 with friendly message
  - [x] Size >50KB returns 400 with friendly message
  - [x] Path traversal attempts are rejected

  **Agent-Executed QA Scenarios**:
  Scenario: Load valid skill
    Tool: Bash
    Preconditions: `/skills/article-summary/SKILL.md` exists
    Steps:
      1. Run python snippet to call SkillLoader.get_skill('article-summary')
      2. Assert returned name is `article-summary`
    Expected Result: Skill detail loads
    Evidence: `.sisyphus/evidence/task-2-load-skill.txt`

  Scenario: Invalid name rejected
    Tool: Bash
    Preconditions: None
    Steps:
      1. Call create/update with name `Bad Name` via loader
      2. Capture error
    Expected Result: 400-style exception or error returned
    Evidence: `.sisyphus/evidence/task-2-invalid-name.txt`

- [x] 3. Implement Skill executor + streaming run

  **What to do**:
  - Implement `backend/app/core/skill_executor.py`:
    - Validate required inputs
    - Single-pass variable replacement (no recursion)
    - Use defaults for optional inputs
    - Integrate RAG if `knowledge_base` set
    - Stream SSE events: thought/token/citation/done
  - Add run method used by API and workflow/chat

  **Must NOT do**:
  - Do not recurse on variable substitution
  - Do not emit non-standard event types

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Async streaming + LLM integration
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Tasks 4, 6, 7, 8
  - **Blocked By**: None

  **References**:
  - `backend/app/api/chat.py` - SSE streaming + event formatting
  - `backend/app/core/rag.py` - RAG pipeline integration
  - `backend/app/core/llm.py` - LLM client

  **Acceptance Criteria**:
  - [x] Missing required input returns 400
  - [x] SSE stream yields thought/token/citation/done

  **Agent-Executed QA Scenarios**:
  Scenario: Run skill streams tokens
    Tool: Bash
    Preconditions: Backend running at localhost:8000
    Steps:
      1. `curl -N -X POST http://localhost:8000/api/v1/skills/article-summary/run -H 'Content-Type: application/json' -d '{"inputs":{"article":"hello"}}'`
      2. Observe SSE events with `event: token`
    Expected Result: Token events received
    Evidence: `.sisyphus/evidence/task-3-run-sse.txt`

  Scenario: Missing required input
    Tool: Bash
    Preconditions: Backend running
    Steps:
      1. POST with empty inputs
      2. Assert status 400 and message indicates missing input
    Expected Result: 400 returned
    Evidence: `.sisyphus/evidence/task-3-missing-input.txt`

- [x] 4. Build Skill CRUD API + router registration

  **What to do**:
  - Create `backend/app/api/skill.py` with CRUD + run endpoints
  - Register router in `backend/main.py`
  - Use SkillLoader/SkillExecutor

  **Must NOT do**:
  - Do not add auth dependencies
  - Do not allow rename (name immutable on update)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Tasks 7, 8, 9
  - **Blocked By**: Tasks 2, 3

  **References**:
  - `backend/app/api/knowledge.py` - CRUD API structure
  - `backend/app/api/workflow.py` - FileLock CRUD pattern
  - `docs/skill-system-design.md` - route spec

  **Acceptance Criteria**:
  - [ ] GET /api/v1/skills returns list
  - [ ] GET /api/v1/skills/{name} returns detail
  - [ ] POST creates skill and folder
  - [ ] PUT updates SKILL.md (name unchanged)
  - [ ] DELETE removes skill folder

  **Agent-Executed QA Scenarios**:
  Scenario: CRUD happy path
    Tool: Bash
    Preconditions: Backend running
    Steps:
      1. POST create `test-skill`
      2. GET list; assert `test-skill` present
      3. GET detail; assert name matches
      4. PUT update content; assert updated_at changes
      5. DELETE; assert removed
    Expected Result: All endpoints return 2xx
    Evidence: `.sisyphus/evidence/task-4-crud.txt`

- [x] 5. Frontend Skills list/editor/run UI (textarea)

  **What to do**:
  - Create `frontend/src/views/SkillsView.vue` (list + run modal)
  - Create `frontend/src/views/SkillEditor.vue` (textarea editor + preview)
  - Add simple run panel to execute skill and stream output
  - Use existing API client patterns

  **Must NOT do**:
  - Do not add Monaco/CodeMirror

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Ensures deliberate UI even with simple editor

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 6)
  - **Blocks**: Task 9
  - **Blocked By**: Task 4

  **References**:
  - `frontend/src/views/KnowledgeView.vue` - list view patterns
  - `frontend/src/views/ChatTerminal.vue` - SSE UI patterns
  - `frontend/src/router/index.ts` - routes pattern

  **Acceptance Criteria**:
  - [ ] Skills list renders name/description/inputs
  - [ ] Editor loads and saves SKILL.md content
  - [ ] Run panel streams output to UI

  **Agent-Executed QA Scenarios**:
  Scenario: Skill list loads
    Tool: Playwright
    Preconditions: Dev server running on localhost:5173
    Steps:
      1. Navigate to `/skills`
      2. Wait for `.skills-list` visible
      3. Assert at least one card contains `article-summary`
      4. Screenshot `.sisyphus/evidence/task-5-list.png`
    Expected Result: Skills list visible
    Evidence: `.sisyphus/evidence/task-5-list.png`

  Scenario: Run skill from editor
    Tool: Playwright
    Preconditions: Skill exists
    Steps:
      1. Navigate to `/skills/article-summary`
      2. Fill textarea input for `article`
      3. Click `Run`
      4. Wait for output panel to contain text
      5. Screenshot `.sisyphus/evidence/task-5-run.png`
    Expected Result: Output streams into panel
    Evidence: `.sisyphus/evidence/task-5-run.png`

- [x] 6. Workflow Skill node (backend + frontend)

  **What to do**:
  - Add `execute_skill_node` in `backend/app/core/workflow_nodes.py`
  - Register node type in `backend/app/core/workflow_engine.py`
  - Add `frontend/src/components/nodes/SkillNode.vue`
  - Wire node config in workflow editor

  **Must NOT do**:
  - Do not change existing node execution semantics

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 2, 3

  **References**:
  - `backend/app/core/workflow_nodes.py` - node execution patterns
  - `backend/app/core/workflow_engine.py` - node registration
  - `frontend/src/components/nodes/LLMNode.vue` - node UI pattern
  - `frontend/src/views/WorkflowEditor.vue` - node palette

  **Acceptance Criteria**:
  - [ ] Workflow node executes skill and stores output in context
  - [ ] Node UI supports selecting skill + mapping inputs

  **Agent-Executed QA Scenarios**:
  Scenario: Skill node executes in workflow
    Tool: Playwright
    Preconditions: Workflow editor available
    Steps:
      1. Open workflow editor
      2. Add Skill node and select `article-summary`
      3. Map input to fixed value
      4. Run workflow
      5. Assert output contains summary text
      6. Screenshot `.sisyphus/evidence/task-6-workflow.png`
    Expected Result: Workflow runs with Skill output
    Evidence: `.sisyphus/evidence/task-6-workflow.png`

- [x] 7. Chat @skill parsing + execution

  **What to do**:
  - Add `parse_at_skill` logic in chat API
  - When detected, load skill and map remaining text to first required input
  - Stream SSE response
  - Add frontend @skill autocomplete in chat input

  **Must NOT do**:
  - Do not alter default chat flow for non-@skill messages

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 8)
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 3, 4, 5

  **References**:
  - `backend/app/api/chat.py` - current chat handling + SSE
  - `frontend/src/views/ChatTerminal.vue` - input handling
  - `docs/skill-system-design.md` - @skill parsing logic

  **Acceptance Criteria**:
  - [ ] `@skill` triggers skill execution
  - [ ] Non-@skill messages continue normal chat

  **Agent-Executed QA Scenarios**:
  Scenario: @skill invocation
    Tool: Playwright
    Preconditions: Chat UI running
    Steps:
      1. Open chat view
      2. Type `@article-summary this is a test`
      3. Send message
      4. Wait for stream to display output
      5. Screenshot `.sisyphus/evidence/task-7-chat.png`
    Expected Result: Skill output displayed
    Evidence: `.sisyphus/evidence/task-7-chat.png`

- [x] 8. LLM node load-skill support

  **What to do**:
  - Extend LLM node config to allow selecting a skill
  - When selected, load skill prompt + model config into node
  - Ensure backend LLM node execution uses resolved prompt

  **Must NOT do**:
  - Do not break existing LLM node behavior when no skill selected

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 7)
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 2, 3, 6

  **References**:
  - `frontend/src/components/nodes/LLMNode.vue` - node UI
  - `backend/app/core/workflow_nodes.py` - LLM execution
  - `docs/skill-system-design.md` - LLM node loading requirements

  **Acceptance Criteria**:
  - [ ] LLM node can select a skill
  - [ ] LLM node uses skill prompt + model config

  **Agent-Executed QA Scenarios**:
  Scenario: LLM node loads skill
    Tool: Playwright
    Preconditions: Workflow editor running
    Steps:
      1. Add LLM node
      2. Select skill in node config
      3. Save workflow
      4. Run workflow
      5. Assert output matches skill prompt behavior
      6. Screenshot `.sisyphus/evidence/task-8-llm.png`
    Expected Result: LLM node output matches skill
    Evidence: `.sisyphus/evidence/task-8-llm.png`

- [x] 9. Tests-after coverage

  **What to do**:
  - Backend pytest: CRUD + run + missing inputs
  - Frontend vitest: SkillsView + SkillEditor + run panel

  **Must NOT do**:
  - Do not add flaky E2E tests

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 7, 8)
  - **Blocks**: None
  - **Blocked By**: Tasks 4-8

  **References**:
  - `frontend/vitest.config.ts` - test setup
  - `backend/pyproject.toml` - pytest setup
  - `frontend/src/components/__tests__/ChatMessage.spec.ts` - test style
  - `backend/tests/test_chat_api.py` - API test pattern

  **Acceptance Criteria**:
  - [x] `npm run test` passes
  - [x] `uv run pytest -q` passes

  **Agent-Executed QA Scenarios**:
  Scenario: Frontend tests
    Tool: Bash
    Preconditions: Frontend deps installed
    Steps:
      1. `cd frontend && npm run test`
    Expected Result: Exit code 0
    Evidence: `.sisyphus/evidence/task-9-frontend-tests.txt`

  Scenario: Backend tests
    Tool: Bash
    Preconditions: Backend deps installed
    Steps:
      1. `cd backend && uv run pytest -q`
    Expected Result: Exit code 0
    Evidence: `.sisyphus/evidence/task-9-backend-tests.txt`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2-4 | `feat(skill): backend loader api executor` | backend/app/models/skill.py, backend/app/core/skill_*.py, backend/app/api/skill.py, backend/main.py | `uv run pytest -q` |
| 5-6 | `feat(skill): skills ui and workflow node` | frontend/src/views/SkillsView.vue, frontend/src/views/SkillEditor.vue, frontend/src/components/nodes/SkillNode.vue, workflow files | `npm run test` |
| 7-8 | `feat(skill): chat and llm skill integration` | backend/app/api/chat.py, frontend/src/views/ChatTerminal.vue, LLM node files | `npm run test` |
| 9 | `test(skill): add skill tests` | tests files | `npm run test` + `uv run pytest -q` |

---

## Success Criteria

### Verification Commands
```bash
cd backend && uv run pytest -q
cd frontend && npm run test
```

### Final Checklist
- [x] All P0+P1 deliverables implemented
- [x] No auth/user integration added
- [x] SSE streaming works for skill run and chat @skill
- [x] Skill node and LLM node integrations verified
- [x] Tests pass
