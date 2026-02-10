# Code Review Remaining Completion Plan

## TL;DR

> **Quick Summary**: Finish the two partially completed backend items from `docs/code-review-fix-plan.md` (`C6`, `C10`) and explicitly defer optional `C9`.
>
> **Deliverables**:
> - `cleanup_expired_tokens` integrated into a real scheduler path
> - `knowledge.py` further slimmed by moving route-internal logic to `knowledge_store.py`
> - Optional frontend decomposition (`C9`) documented as deferred
>
> **Estimated Effort**: Medium
> **Parallel Execution**: NO (2 sequential tasks)
> **Critical Path**: Task 1 -> Task 2

---

## Context

### Original Request
User requested a new plan to complete remaining unfinished work only.

### Interview Summary
**Confirmed scope**:
- Include: `C10` remaining scheduler integration, `C6` remaining module slimming.
- Exclude: `C9` optional decomposition (deferred unless explicitly requested).

### Metis Review
No blocking gaps returned. Added explicit anti-scope-creep guardrails and concrete acceptance checks.

---

## Work Objectives

### Core Objective
Close the remaining partial items without reopening finished tracks or introducing broad refactor churn.

### Definition of Done
- [x] `C10` complete: expired-token cleanup is scheduled and verifiably executed.
- [x] `C6` complete: `knowledge.py` reduced by moving non-route logic to `knowledge_store.py` while preserving API behavior.
- [x] No regression in backend tests for auth/knowledge flows.

### Must NOT Have (Guardrails)
- No new frontend refactor scope (do not execute `C9`).
- No API contract changes (paths, status codes, payload keys) for knowledge endpoints.
- No silent behavior drift in security checks already completed.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after
- **Framework**: `pytest`

### Agent-Executed QA Scenarios

Scenario: Token cleanup scheduling path works
  Tool: Bash
  Preconditions: Backend env available
  Steps:
    1. Start app lifecycle (test mode)
    2. Seed one expired token and one valid token in DB
    3. Trigger scheduled cleanup path
    4. Assert expired token removed, valid token remains
  Expected Result: Cleanup job runs and only expired records are deleted
  Evidence: `.sisyphus/evidence/c10-token-cleanup.txt`

Scenario: Knowledge routes remain contract-stable after slimming
  Tool: Bash
  Preconditions: Backend tests available
  Steps:
    1. Run `uv run pytest tests/test_knowledge_dimension_mismatch.py -q`
    2. Run knowledge-related API tests
    3. Assert no endpoint schema/status regressions
  Expected Result: Tests pass with unchanged contracts
  Evidence: `.sisyphus/evidence/c6-knowledge-tests.txt`

---

## TODOs

- [x] 1. Complete C10 scheduler integration for expired token cleanup

  **What to do**:
  - Wire `cleanup_expired_tokens` into a real periodic execution path (lifespan scheduler or equivalent backend-safe mechanism).
  - Ensure startup/shutdown behavior is deterministic and non-blocking.
  - Add focused tests proving periodic cleanup behavior.

  **References**:
  - `backend/app/core/auth.py` - `cleanup_expired_tokens` implementation to schedule
  - `backend/main.py` - lifecycle integration point

  **Acceptance Criteria**:
  - [x] Scheduler path is active in app runtime.
  - [x] Expired tokens are removed in scheduled runs.
  - [x] Auth-related tests pass.

- [x] 2. Complete C6 by further slimming `knowledge.py`

  **What to do**:
  - Move remaining route-internal helper logic from `backend/app/api/knowledge.py` into `backend/app/core/knowledge_store.py`.
  - Keep `knowledge.py` focused on routing/HTTP orchestration.
  - Preserve route signatures, response fields, and error semantics.

  **References**:
  - `backend/app/api/knowledge.py` - source of remaining inline logic
  - `backend/app/core/knowledge_store.py` - target for helper extraction
  - `backend/tests/test_knowledge_dimension_mismatch.py` - contract safety net

  **Acceptance Criteria**:
  - [x] `knowledge.py` reduced further and contains route-focused logic.
  - [x] Extracted helpers are covered by existing tests.
  - [x] Knowledge tests pass with no contract regression.

- [x] 3. Record explicit defer of C9 (optional)

  **What to do**:
  - Document in notepad/release notes that C9 remains intentionally deferred.
  - Ensure no accidental C9 refactor is mixed into C6/C10 changes.

  **Acceptance Criteria**:
  - [x] Defer decision documented.
  - [x] No frontend decomposition changes included.

---

## Success Criteria

### Verification Commands
```bash
cd backend
uv run pytest tests/test_knowledge_dimension_mismatch.py -q
uv run pytest -q
```

### Final Checklist
- [x] C10 scheduler path is operational and tested
- [x] C6 slimming completed without API behavior change
- [x] C9 explicitly deferred and isolated from this execution
