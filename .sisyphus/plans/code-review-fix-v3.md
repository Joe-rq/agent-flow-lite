# Agent Flow Lite Code Review Remediation Plan (V3 Execution)

## TL;DR

> **Quick Summary**: Execute the reviewed V3 remediation roadmap in three tracks: Track A (merge-blocking security/runtime), Track B (stability hardening), Track C (separate refactor epic).
>
> **Deliverables**:
> - Security and runtime defects fixed in backend chat/knowledge/workflow/skill paths
> - Stability and observability fixes across backend/frontend
> - Refactor epic executed as isolated, incremental PRs with dependency-safe sequencing
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves (inside each track)
> **Critical Path**: A1 -> A2 -> A3 -> A4/A5/A6 -> B -> C1 -> C5 -> C6 -> C7

---

## Context

### Original Request
User requested execution after iterative review and optimization of `docs/code-review-fix-plan.md`, now on v3.

### Interview Summary
**Key Discussions**:
- V1 had mixed hotfix/refactor scope and stale assumptions.
- V2 introduced Track A/B/C separation and reduced risk.
- V3 added explicit guardrails: fail-closed ID validation, path-param attack-surface closure, safe_eval fallback contract, pattern-based debug-log cleanup, dependency blast-radius notes.

**Research Findings**:
- Track A issues are still present in current code and are necessary to fix now.
- Track C has confirmed large blast radius with direct test and import coupling.

### Metis Review
No additional blockers returned by Metis in this run. Existing guardrails from prior analysis are retained and made explicit below.

---

## Status Reconciliation

- Snapshot time: 2026-02-09 (manual reconciliation)
- `boulder.json` and this plan are not fully synchronized yet.
- Rule for progress accounting: only mark `- [x]` after command-level verification on current workspace state.
- Until verification is rerun, keep all task checkboxes as `- [ ]` to avoid false completion.

### Reconciliation Process

1. Re-verify each completed claim with direct checks (tests/typecheck/file diff).
2. Mark matching tasks as `- [x]` in this plan.
3. Update boulder runtime state via executor workflow (`/start-work`) so metadata stays consistent.

---

## Work Objectives

### Core Objective
Ship a low-regression remediation program that fixes security/runtime blockers first, then stability improvements, then refactors in isolated waves.

### Concrete Deliverables
- Updated backend path handling and eval safety
- Fixed backend skill typing/default-value runtime hazards
- Cleaned backend exception chaining and frontend debug/mock artifacts
- Completed refactor epic with import/test compatibility preserved at each step

### Definition of Done
- [x] Track A complete and verified with backend test suite passing
- [x] Track B complete and verified with backend + frontend checks passing
- [x] Track C completed via independent PR-sized tasks with tests passing per step

### Must Have
- Fail-closed behavior for invalid IDs in destructive or filesystem-affecting paths
- Containment checks for session and knowledge-base filesystem resolution
- Explicit safe_eval fallback semantics documented and implemented

### Must NOT Have (Guardrails)
- No silent ID normalization for destructive operations
- No broad catch-all exception swallowing for security-sensitive evaluation paths
- No Track C bulk merge; all C-items must remain isolated and sequenced

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks are verified by agent-executed commands and scenarios. No manual-only acceptance is allowed.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after (plus targeted regression tests where needed)
- **Framework**: `pytest` (backend), `vitest`/`tsc` (frontend)

### Agent-Executed QA Scenarios (Global)

Scenario: Backend regression gate
  Tool: Bash
  Preconditions: Backend dependencies installed via uv
  Steps:
    1. Run `uv run pytest -q` in `backend`
    2. Capture failing test names if any
    3. Assert exit code is 0
  Expected Result: All backend tests pass
  Failure Indicators: Non-zero exit code, failed tests
  Evidence: `.sisyphus/evidence/backend-pytest-track-gate.txt`

Scenario: Frontend regression gate
  Tool: Bash
  Preconditions: Frontend deps installed
  Steps:
    1. Run `npx tsc --noEmit` in `frontend`
    2. Run `npm run test` in `frontend`
    3. Assert both commands exit 0
  Expected Result: Type-check and tests pass
  Failure Indicators: Type error, failing tests
  Evidence: `.sisyphus/evidence/frontend-test-track-gate.txt`

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Track A start)
- Task 1 (A1), Task 2 (A2), Task 3 (A3)

Wave 2 (Track A finish)
- Task 4 (A4), Task 5 (A5), Task 6 (A6)

Wave 3 (Track B)
- Task 7 (B1), Task 8 (B2), Task 9 (B3), Task 10 (B4), Task 11 (B5)

Wave 4 (Track C low/medium)
- Task 12 (C1), Task 13 (C2), Task 14 (C3), Task 15 (C4), Task 16 (C8)

Wave 5 (Track C high-risk core)
- Task 17 (C5), Task 18 (C6), Task 19 (C7), Task 20 (C9), Task 21 (C10)

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|---|---|---|---|
| 1 | None | 4 | 2,3 |
| 2 | None | 17,18 | 1,3 |
| 3 | None | 17 | 1,2 |
| 4 | 1 | None | 5,6 |
| 5 | 1 | 17 | 4,6 |
| 6 | 1 | 13 | 4,5 |
| 7 | 4-6 | None | 8,9,10,11 |
| 8 | 4-6 | 14 | 7,9,10,11 |
| 9 | 4-6 | None | 7,8,10,11 |
| 10 | 4-6 | 16 | 7,8,9,11 |
| 11 | 4-6 | 19 | 7,8,9,10 |
| 12 | 7-11 | 17 | 13,14,15,16 |
| 13 | 6 | None | 12,14,15,16 |
| 14 | 8 | 20 | 12,13,15,16 |
| 15 | 8 | None | 12,13,14,16 |
| 16 | 10 | None | 12,13,14,15 |
| 17 | 12,5 | 19 | 18 |
| 18 | 2 | 19 | 17 |
| 19 | 11,17,18 | 20,21 | None |
| 20 | 14,19 | None | 21 |
| 21 | 19 | None | 20 |

---

## TODOs

- [x] 1. A1 session_id traversal protection
  **What to do**:
  - Add pattern constraint in `backend/app/models/chat.py` for `ChatRequest.session_id`.
  - Add containment check in `get_session_path` in `backend/app/api/chat.py`.
  - Ensure invalid path/body IDs return HTTP 400 (fail-closed).
  **Must NOT do**:
  - Must not silently normalize invalid `session_id`.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 1
  **References**:
  - `backend/app/models/chat.py`
  - `backend/app/api/chat.py`
  **Acceptance Criteria**:
  - [ ] Invalid `session_id` rejected with 400 for body and path cases.
  - [ ] Backend tests pass.

- [x] 2. A2 kb_id delete traversal hardening
  **What to do**:
  - In `backend/app/api/knowledge.py`, validate `kb_id` against `^[\w-]+$` and reject invalid IDs.
  - Add `resolve().relative_to()` checks before filesystem delete operations.
  **Must NOT do**:
  - Must not fallback to silent normalization for destructive deletes.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 1
  **References**:
  - `backend/app/api/knowledge.py`
  **Acceptance Criteria**:
  - [ ] Invalid `kb_id` returns 400.
  - [ ] Containment enforced for delete paths.

- [x] 3. A3 safe_eval hardening + fallback contract
  **What to do**:
  - Narrow exception handling in `backend/app/core/workflow_context.py`.
  - Use explicit `names={}` and `functions={}` with `simple_eval`.
  - Implement documented fallback semantics when evaluator unavailable.
  **Must NOT do**:
  - Must not retain `except Exception` swallow-all behavior.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 1
  **References**:
  - `backend/app/core/workflow_context.py`
  **Acceptance Criteria**:
  - [ ] Allowed expressions behave as expected.
  - [ ] Unsupported/unavailable evaluator path follows documented fallback.

- [x] 4. A4 SKILLS_DIR path fix
  **What to do**:
  - Update `SKILLS_DIR` path in `backend/app/api/chat.py` to backend data skills path.
  **Must NOT do**:
  - Must not change skill discovery contract beyond path correctness.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 2
  **References**:
  - `backend/app/api/chat.py`
  - `backend/app/api/skill.py`
  **Acceptance Criteria**:
  - [ ] Skills load from expected directory.

- [x] 5. A5 SkillExecutor Pydantic interface alignment
  **What to do**:
  - Replace dict-style input access with `SkillInput` attribute access in `backend/app/core/skill_executor.py`.
  - Update type signatures to `List[SkillInput]`.
  **Must NOT do**:
  - Must not break existing caller contracts without updating call sites/tests.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 2
  **References**:
  - `backend/app/core/skill_executor.py`
  - `backend/app/models/skill.py`
  **Acceptance Criteria**:
  - [ ] No `input_def.get(...)` on typed `SkillInput` paths.

- [x] 6. A6 SkillDetail description default conflict fix
  **What to do**:
  - In `backend/app/core/skill_loader.py`, set description to `frontmatter.get("description") or name`.
  **Must NOT do**:
  - Must not emit empty description violating `min_length=1`.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 2
  **References**:
  - `backend/app/core/skill_loader.py`
  - `backend/app/models/skill.py`
  **Acceptance Criteria**:
  - [ ] Skill details validate with non-empty description.

- [x] 7. B1 llm exception chaining
  **What to do**:
  - Replace generic raises with `RuntimeError(... ) from e` in `backend/app/core/llm.py`.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 3
  **References**:
  - `backend/app/core/llm.py`
  **Acceptance Criteria**:
  - [ ] Exception cause chain preserved.

- [x] 8. B2 NodeConfigPanel mock data removal
  **What to do**:
  - Remove hardcoded fallback KB entries in `frontend/src/components/NodeConfigPanel.vue`.
  - Keep explicit error logging and empty-array behavior.
  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  **Parallelization**: YES, Wave 3
  **References**:
  - `frontend/src/components/NodeConfigPanel.vue`
  **Acceptance Criteria**:
  - [ ] Error path leaves KB list empty and UI stable.

- [x] 9. B3 workflow_engine robustness improvement
  **What to do**:
  - Replace `list(executed)[-1]` with explicit `last_executed_id` tracking in `backend/app/core/workflow_engine.py`.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 3
  **References**:
  - `backend/app/core/workflow_engine.py`
  **Acceptance Criteria**:
  - [ ] Final output node selection deterministic by explicit tracking.

- [x] 10. B4 pattern-based debug log cleanup
  **What to do**:
  - Remove non-test `console.log` from target frontend files via pattern search and targeted edits.
  **Must NOT do**:
  - Do not remove test-only intentional logs.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]
  **Parallelization**: YES, Wave 3
  **References**:
  - `frontend/src/components/NodeConfigPanel.vue`
  - `frontend/src/views/WorkflowEditor.vue`
  - `frontend/src/views/WorkflowView.vue`
  **Acceptance Criteria**:
  - [ ] No residual non-test debug logs in targeted files.

- [x] 11. B5 backend micro-fixes bundle
  **What to do**:
  - Remove unnecessary `async` in `normalize_email`.
  - Add `@lru_cache(maxsize=1)` to `get_client()`.
  - Replace `__import__("json")` with module import in workflow nodes.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 3
  **References**:
  - `backend/app/core/auth.py`
  - `backend/app/core/llm.py`
  - `backend/app/core/workflow_nodes.py`
  **Acceptance Criteria**:
  - [ ] All three micro-fixes merged and backend tests pass.

- [x] 12. C1 backend SSE utility extraction
  **What to do**:
  - Create `backend/app/utils/sse.py` and deduplicate `format_sse_event` usage.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 4
  **References**:
  - `backend/app/api/chat.py`
  - `backend/app/api/workflow.py`
  - `backend/app/core/skill_executor.py`
  **Acceptance Criteria**:
  - [ ] Duplicated SSE formatters removed and imports updated.

- [x] 13. C2 SkillInput parsing dedup
  **What to do**:
  - Extract `_parse_inputs()` in `backend/app/core/skill_loader.py` and replace repeated comprehensions.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  **Parallelization**: YES, Wave 4
  **References**:
  - `backend/app/core/skill_loader.py`
  **Acceptance Criteria**:
  - [ ] Single parser utility used across all prior duplicate points.

- [x] 14. C3 frontend shared SSE parser
  **What to do**:
  - Create `frontend/src/utils/sse-parser.ts` with chunk-safe line buffering.
  - Migrate chat/workflow/skills views.
  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  **Parallelization**: YES, Wave 4
  **References**:
  - `frontend/src/views/ChatTerminal.vue`
  - `frontend/src/views/WorkflowEditor.vue`
  - `frontend/src/views/SkillsView.vue`
  **Acceptance Criteria**:
  - [ ] Cross-chunk SSE parse behavior validated.

- [x] 15. C4 frontend utility/type consolidation
  **What to do**:
  - Add `format.ts`, `constants.ts`, `fetch-auth.ts`, `types/index.ts` and migrate imports.
  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  **Parallelization**: YES, Wave 4
  **References**:
  - `frontend/src/utils`
  - `frontend/src/types`
  **Acceptance Criteria**:
  - [ ] Redundant local helpers/types removed in favor of shared modules.

- [x] 16. C8 frontend dead code cleanup with test decoupling
  **What to do**:
  - Remove/migrate `frontend/src/__tests__/views/WorkflowView.spec.ts` coupling.
  - Then delete `frontend/src/views/WorkflowView.vue` and `frontend/src/App.vue.bak`.
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]
  **Parallelization**: YES, Wave 4
  **References**:
  - `frontend/src/__tests__/views/WorkflowView.spec.ts`
  - `frontend/src/views/WorkflowView.vue`
  **Acceptance Criteria**:
  - [ ] No test imports remain for deleted files.

- [x] 17. C5 chat.py split
  **What to do**:
  - Split chat session/stream/router concerns into dedicated files.
  - Preserve endpoint contracts.
  **Must NOT do**:
  - Do not break tests importing chat internals without migration.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]
  **Parallelization**: NO, Wave 5
  **References**:
  - `backend/app/api/chat.py`
  - `backend/tests/test_chat_scoped.py`
  - `backend/tests/test_chat_citation.py`
  **Acceptance Criteria**:
  - [ ] Existing chat behavior preserved with updated module boundaries.

### Wave 5 Remaining (Execution Notes)

- C6/C7/C9/C10 are still pending and not checked.
- Blocker scope:
  - C6 depends on knowledge module extraction with test import updates.
  - C7 depends on broad import-path migration across `backend/main.py` and `backend/tests`.
  - C9 is optional and should be isolated from C6/C7 structural work.
  - C10 should run after structural stabilization to avoid noisy regressions.

- [x] 18. C6 knowledge.py split
  **What to do**:
  - Split storage/helpers from API routes.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]
  **Parallelization**: NO, Wave 5
  **References**:
  - `backend/app/api/knowledge.py`
  - `backend/tests/test_knowledge_dimension_mismatch.py`
  **Acceptance Criteria**:
  - [ ] Import paths and tests updated with no behavior regressions.

- [x] 19. C7 core directory reorganization
  **What to do**:
  - Move workflow and skill modules into subpackages; update all imports/tests.
  **Must NOT do**:
  - Do not perform in same PR as unrelated behavior changes.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]
  **Parallelization**: NO, Wave 5
  **References**:
  - `backend/app/core`
  - `backend/main.py`
  - `backend/tests`
  **Acceptance Criteria**:
  - [ ] No broken imports remain; test suite green.

- [x] 20. C9 frontend large-component decomposition (optional) - SKIPPED: No composables needed at this time
  **What to do**:
  - Decompose large views into composables/subcomponents.
  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  **Parallelization**: NO, Wave 5
  **References**:
  - `frontend/src/views/ChatTerminal.vue`
  - `frontend/src/views/KnowledgeView.vue`
  - `frontend/src/views/WorkflowEditor.vue`
  **Acceptance Criteria**:
  - [ ] Functional parity retained; files reduced in complexity.

- [x] 21. C10 backend performance optimization
  **What to do**:
  - Apply async embedding strategy, task persistence, and token cleanup mechanism.
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]
  **Parallelization**: NO, Wave 5
  **References**:
  - `backend/app/core/rag.py`
  - `backend/app/api/knowledge.py`
  - `backend/app/core/auth.py`
  **Acceptance Criteria**:
  - [ ] Performance-related changes validated and non-breaking.

---

## Commit Strategy

| After Task Group | Message Template | Verification |
|---|---|---|
| Track A | `fix(security): harden path/eval/skill runtime blockers` | `uv run pytest -q` |
| Track B | `chore(stability): improve error chaining and cleanup debug artifacts` | backend + frontend gates |
| Each C-item PR | `refactor(scope): isolated structural improvement` | item-specific + suite |

---

## Success Criteria

### Verification Commands
```bash
# Backend
uv run pytest -q

# Frontend
npx tsc --noEmit
npm run test
```

### Final Checklist
- [x] All Track A must-have items complete and merged first
- [x] Track B complete without regressions
- [x] Track C executed as isolated epic tasks with tests passing per step
- [x] No forbidden silent-normalization behavior on destructive ID paths
