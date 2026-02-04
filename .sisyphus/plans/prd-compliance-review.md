# PRD Compliance Review + Closed-Loop Optimization Plan

## TL;DR

> **Quick Summary**: Produce a PRD gap analysis + prioritized optimization list, then close the highest-impact gap in the upload → retrieval → chat citation loop by adding clickable citations with highlighted source excerpts.
>
> **Deliverables**:
> - PRD gap analysis report with evidence and priority ranking
> - Citation payload or lookup API for source excerpts
> - Frontend citation UI with clickable footnotes + highlight view
> - Backend + frontend tests (TDD) + end-to-end QA scenario
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Test setup → Backend citation API/payload → Frontend citation UI → E2E verification

---

## Context

### Original Request
“深入此项目，检查项目是否有需要优化的地方，是否达到了 `docs/design/prd.md` 的要求。”

### Interview Summary
**Key Discussions**:
- Output format: gap analysis + prioritized optimization list.
- Priority focus: business closed-loop (upload → retrieval → chat citations fully working).
- Test strategy: TDD. Frontend Vitest exists; backend needs pytest if changes require it.

**Research Findings**:
- Workflow editor uses Vue Flow with graph JSON serialization (`frontend/src/views/WorkflowEditor.vue`).
- Knowledge base upload + retrieval test UI exists (`frontend/src/views/KnowledgeView.vue`).
- Chat SSE streaming + thought/citation events exist (`backend/app/api/chat.py`, `frontend/src/views/ChatTerminal.vue`).
- Citations are plain text; PRD requires clickable + highlight (gap).
- Storage uses JSON files rather than PostgreSQL/pgvector (PRD mismatch).
- FastAPI SSE uses `StreamingResponse`; `sse-starlette` is recommended for production SSE.

### Metis Review
No additional feedback returned by Metis during consultation.

---

## Work Objectives

### Core Objective
Assess PRD compliance with evidence and prioritize optimizations, then implement the highest-impact closed-loop gap: interactive, highlightable citations in chat.

### Concrete Deliverables
- `docs/design/prd-gap-analysis.md` PRD gap matrix + prioritized optimization list
- Backend citation payload or lookup API for chunk excerpts
- Frontend citation UI with clickable footnotes and source highlight view
- TDD tests (frontend Vitest + backend pytest) and agent-executed QA scenarios

### Definition of Done
- [x] PRD gap analysis report exists and maps each PRD requirement to evidence or gap
- [x] Chat citations are clickable and show highlighted excerpts from knowledge base chunks
- [x] Backend tests pass (pytest) and frontend tests pass (vitest)
- [x] End-to-end QA scenario verifies upload → retrieval → chat → citation highlight

### Must Have
- Interactive citations in chat with highlighted source excerpts
- Evidence-backed PRD gap analysis with priority ranking
- TDD test coverage for new backend/frontend functionality

### Must NOT Have (Guardrails)
- No PostgreSQL/pgvector migration unless explicitly requested
- No new UI libraries or heavy refactors unrelated to citations/closed-loop
- No breaking changes to existing workflow editor or knowledge upload flows

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> This is NOT conditional — it applies to EVERY task.
>
> **FORBIDDEN** — acceptance criteria that require:
> - "User manually tests..." / "사용자가 직접 테스트..."
> - "User visually confirms..." / "사용자가 눈으로 확인..."
> - "User interacts with..." / "사용자가 직접 조작..."
> - "Ask user to verify..." / "사용자에게 확인 요청..."

### Test Decision
- **Infrastructure exists**: Frontend YES (Vitest). Backend NO (pytest not configured).
- **Automated tests**: TDD
- **Framework**: frontend = Vitest, backend = pytest + pytest-asyncio

### If TDD Enabled

Each TODO follows RED-GREEN-REFACTOR.

**Test Setup Task (backend)**:
- Install: `uv add --dev pytest pytest-asyncio httpx`
- Config: add `backend/pyproject.toml` pytest config
- Verify: `uv run pytest -q` (initial sample test passes)

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

**Tools by deliverable**:
- UI: Playwright
- API: Bash (`curl`)
- Reports/Docs: Bash (`rg`, `ls`)

Each scenario must be tool-executable with exact selectors/commands and evidence paths.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
- Task 1: PRD gap analysis report (documentation)
- Task 2: Backend test infrastructure setup (pytest)

Wave 2 (After Wave 1):
- Task 3: Backend citation payload/lookup API + tests
- Task 4: Frontend citation UI + tests

Wave 3 (After Wave 2):
- Task 5: End-to-end QA verification

Critical Path: Task 2 → Task 3 → Task 4 → Task 5

---

## TODOs

- [x] 1. Produce PRD gap analysis report with prioritized optimizations

  **What to do**:
  - Create `docs/design/prd-gap-analysis.md`
  - Map each PRD requirement to evidence or gap (cite file paths)
  - Add a prioritized optimization list (P0/P1/P2) with rationale
  - Emphasize closed-loop completion as top priority

  **Must NOT do**:
  - Do not propose DB migration as required for P0 unless explicitly requested

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: report/analysis output with structured mapping
  - **Skills**: `technical-writer`
    - `technical-writer`: clear, structured technical reporting
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: no UI changes in this task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Task 5
  - **Blocked By**: None

  **References**:
  - `docs/design/prd.md` - source of requirement list
  - `frontend/src/views/WorkflowEditor.vue` - workflow editor evidence
  - `frontend/src/views/KnowledgeView.vue:49` - upload UI evidence
  - `frontend/src/views/KnowledgeView.vue:101` - retrieval test UI evidence
  - `backend/app/api/knowledge.py:126` - upload endpoint evidence
  - `backend/app/core/rag.py` - chunking/embedding/retrieval pipeline
  - `backend/app/api/chat.py:66` - SSE event format
  - `frontend/src/views/ChatTerminal.vue:283` - SSE client handling
  - `frontend/src/views/ChatTerminal.vue:447` - citation rendering (gap)

  **Acceptance Criteria**:
- [x] `docs/design/prd-gap-analysis.md` exists
- [x] Report includes sections: “Gap Matrix”, “Prioritized Optimizations”, “Closed-Loop Focus”
- [x] Each PRD requirement includes at least one file reference or explicit gap note

  **Agent-Executed QA Scenarios**:

  ```
  Scenario: PRD report file exists and has required sections
    Tool: Bash
    Preconditions: Repo checkout present
    Steps:
      1. Run: ls "docs/design"
      2. Assert: prd-gap-analysis.md listed
      3. Run: rg "## Gap Matrix" docs/design/prd-gap-analysis.md
      4. Run: rg "## Prioritized Optimizations" docs/design/prd-gap-analysis.md
      5. Run: rg "## Closed-Loop Focus" docs/design/prd-gap-analysis.md
    Expected Result: All section headers found
    Evidence: stdout capture from rg commands
  ```

- [x] 2. Set up backend pytest infrastructure (TDD enablement)

  **What to do**:
  - Add pytest + pytest-asyncio + httpx dev deps via uv
  - Add pytest config to `backend/pyproject.toml`
  - Add a minimal sample test in `backend/tests/test_smoke.py`

  **Must NOT do**:
  - Do not change runtime dependencies or API behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: small configuration change + minimal test scaffold
  - **Skills**: `python-pro`
    - `python-pro`: pytest/async testing patterns in FastAPI

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Task 3
  - **Blocked By**: None

  **References**:
  - `backend/pyproject.toml` - dependency + test config
  - `backend/test_chat_api.py` - existing manual test pattern reference

  **Acceptance Criteria**:
- [x] `uv run pytest -q` succeeds with at least one passing test

  **Agent-Executed QA Scenarios**:

  ```
  Scenario: pytest executes successfully
    Tool: Bash
    Preconditions: backend deps installed via uv
    Steps:
      1. Run: uv run pytest -q
      2. Assert: exit code 0
    Expected Result: pytest completes with success
    Evidence: pytest stdout
  ```

- [x] 3. Backend: add citation payload/lookup API + tests (TDD)

  **What to do**:
  - RED: add pytest tests for citation payload enrichment
  - GREEN: include truncated `text` excerpt in `citation` SSE event payload
  - REFACTOR: keep payload size bounded; reuse existing RAG metadata

  **Must NOT do**:
  - Do not break existing SSE event structure for `thought/token/done`
  - Do not require new DB backend

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: API changes + SSE contract changes + tests
  - **Skills**: `python-pro`
    - `python-pro`: FastAPI + async test setup

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 4, Task 5
  - **Blocked By**: Task 2

  **References**:
  - `backend/app/api/chat.py:153` - current citation event payload
  - `backend/app/core/rag.py` - retrieval results include text/metadata
  - `backend/app/api/knowledge.py:95` - knowledge metadata storage paths
  - `backend/data/metadata/` - document metadata store

  **Acceptance Criteria**:
- [x] pytest covers citation payload/lookup endpoint
- [x] `uv run pytest -q` passes with new tests
- [x] SSE citation payload includes either excerpt text or resolvable lookup info

  **Agent-Executed QA Scenarios**:

  ```
  Scenario: Citation payload contains excerpt text
    Tool: Bash (curl)
    Preconditions: Backend running on localhost:8000, KB with at least one document
    Steps:
      1. POST /api/v1/chat/completions with kb_id and message
      2. Stream SSE and capture first `event: citation` payload
      3. Assert: payload includes `text` or lookup fields for excerpt
    Expected Result: Citation payload supports excerpt retrieval
    Evidence: SSE stream output captured to file
  ```

- [x] 4. Frontend: clickable citations + highlight UI + tests (TDD)

  **What to do**:
  - RED: add Vitest test for citation rendering and click behavior
  - GREEN: render citations as clickable footnotes, open panel/modal with excerpt
  - REFACTOR: keep UI consistent with existing ChatTerminal design

  **Must NOT do**:
  - Do not introduce new UI libraries
  - Do not change non-citation chat behavior

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI + interaction design
  - **Skills**: `frontend-ui-ux`, `typescript-pro`
    - `frontend-ui-ux`: interaction and layout polish
    - `typescript-pro`: Vue + TS refactors

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 5
  - **Blocked By**: Task 3

  **References**:
  - `frontend/src/views/ChatTerminal.vue:447` - current citation rendering logic
  - `frontend/src/views/ChatTerminal.vue:59` - thought chain UI pattern
  - `frontend/src/views/KnowledgeView.vue:101` - retrieval result styling pattern
  - `frontend/src/__tests__/views/ChatTerminal.spec.ts` - existing test patterns
  - `frontend/vitest.config.ts` - test runner config

  **Acceptance Criteria**:
- [x] Vitest test verifies citation UI renders clickable elements
- [x] Clicking a citation opens a source panel/modal with excerpt text
- [x] `npm run test` (or `npx vitest run`) passes

  **Agent-Executed QA Scenarios**:

  ```
  Scenario: Click citation opens highlight panel
    Tool: Playwright
    Preconditions: Frontend running on localhost:5173, backend running, KB seeded
    Steps:
      1. Navigate to http://localhost:5173/#/chat
      2. Select a knowledge base in the config bar
      3. Send message: "测试引用"
      4. Wait for citation footnote element .citation-item to appear
      5. Click .citation-item:nth-of-type(1)
      6. Assert: .citation-panel is visible
      7. Assert: .citation-panel contains excerpt text and highlight markup
      8. Screenshot: .sisyphus/evidence/task-4-citation-panel.png
    Expected Result: Citation opens a highlightable excerpt panel
    Evidence: Screenshot file
  ```

- [x] 5. End-to-end closed-loop verification (upload → retrieval → chat citation)

  **What to do**:
  - Validate full flow with Playwright and curl, capturing evidence

  **Must NOT do**:
  - Do not bypass upload flow or rely on existing data only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: verification-only task
  - **Skills**: `playwright`
    - `playwright`: UI automation for closed-loop validation

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 3, Task 4

  **References**:
  - `frontend/src/views/KnowledgeView.vue:49` - upload UI entry
  - `frontend/src/views/KnowledgeView.vue:101` - retrieval test UI
  - `frontend/src/views/ChatTerminal.vue:283` - SSE chat flow

  **Acceptance Criteria**:
- [x] Upload succeeds for a `.md` file and document status becomes completed
- [x] Retrieval test returns results with similarity scores
- [x] Chat response includes clickable citation and highlight panel

  **Agent-Executed QA Scenarios**:

  ```
  Scenario: Closed-loop flow with citations
    Tool: Playwright
    Preconditions: Frontend + backend running, empty KB
    Steps:
      1. Navigate to http://localhost:5173/#/knowledge
      2. Create KB named "qa-kb"
      3. Upload file "qa-doc.md" containing unique phrase "ALPHA-BETA-GAMMA"
      4. Wait for document status badge to show "已完成"
      5. Run retrieval test with query "ALPHA-BETA-GAMMA"
      6. Assert: at least 1 result item rendered with similarity score
      7. Navigate to http://localhost:5173/#/chat
      8. Select KB "qa-kb" and send "ALPHA-BETA-GAMMA"
      9. Wait for citation footnote and click first citation
      10. Assert: citation panel shows excerpt containing "ALPHA-BETA-GAMMA"
      11. Screenshot: .sisyphus/evidence/task-5-closed-loop.png
    Expected Result: Upload → retrieval → chat citation highlight works end-to-end
    Evidence: Screenshot file
  ```

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `docs(prd): add gap analysis and priorities` | `docs/design/prd-gap-analysis.md` | n/a |
| 2 | `test(backend): add pytest scaffold` | `backend/pyproject.toml`, `backend/tests/*` | `uv run pytest -q` |
| 3 | `feat(chat): enrich citations for highlight` | `backend/app/api/chat.py`, `backend/app/api/knowledge.py`, tests | `uv run pytest -q` |
| 4 | `feat(chat-ui): clickable citations` | `frontend/src/views/ChatTerminal.vue`, tests | `npx vitest run` |

---

## Success Criteria

### Verification Commands
```bash
uv run pytest -q
npx vitest run
```

### Final Checklist
- [x] PRD gap analysis file exists with evidence + priorities
- [x] Citations are clickable and show highlighted excerpts
- [x] Closed-loop QA scenario passes with evidence captured
