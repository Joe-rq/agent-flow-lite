# Fix Quality Gate Double Failure (Backend CI + Frontend P0)

## TL;DR

> **Quick Summary**: This plan fixes two blocking critical checks in one pass: backend CI dependency command mismatch (`.[dev]` vs dependency-groups) and frontend App P0 test instability.
>
> **Deliverables**:
> - Backend critical test job in `.github/workflows/quality-gate.yml` no longer fails at dependency install.
> - Frontend `src/__tests__/App.spec.ts` no longer fails on authenticated chrome and logout flow in CI.
> - Quality Gate Summary turns green when critical layer passes.
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential (risk-controlled)
> **Critical Path**: Task 0 -> Task 1 -> Task 2 -> Task 3 -> Task 4 -> Task 5

---

## Context

### Original Request
User received GitHub Actions "Quality Gate" failure and asked what to provide, then provided full failing snippets and run link.

### Interview Summary
**Key Discussions**:
- Backend P0 fails at `uv pip install -e ".[dev]"` with "No virtual environment found".
- Frontend P0 fails with 3 test failures in `src/__tests__/App.spec.ts`.
- User selected "one unified fix" and test strategy "tests-after".

**Research Findings**:
- Critical workflow file is `.github/workflows/quality-gate.yml`.
- Frontend failing tests target header/sidebar visibility and logout click behavior.
- `backend/pyproject.toml` uses `[dependency-groups]` (not `[project.optional-dependencies]`), so `uv pip install -e ".[dev]"` is the wrong install strategy.
- `App.spec.ts` has both selector ambiguity (`find('button')`) and authenticated chrome timing/flush risk.

### Metis Review
**Identified Gaps (addressed)**:
- Missing guardrails to avoid scope creep into non-critical jobs -> explicitly restricted to critical lane only.
- Missing explicit selector stability requirement for logout interaction -> added deterministic selector policy.
- Missing acceptance specificity -> added command-level + job-level pass criteria.

---

## Work Objectives

### Core Objective
Restore Quality Gate critical layer by fixing one backend CI bootstrap defect and one frontend P0 test stability defect, without expanding into full test suite cleanup.

### Concrete Deliverables
- Updated `.github/workflows/quality-gate.yml` backend critical install path to work in clean CI runners.
- Updated `frontend/src/__tests__/App.spec.ts` (and minimal supporting UI selector only if needed) for stable authenticated chrome/logout assertions.
- Successful rerun evidence from GitHub Actions run showing critical checks pass.

### Definition of Done
- [ ] `Backend Critical Tests (P0)` job exits success in Actions.
- [ ] `Frontend Critical Tests (P0)` job exits success in Actions.
- [ ] `Quality Gate Summary` reports `PASS - All critical checks passed`.

### Must Have
- Fixes are minimal and directly tied to observed failure logs.
- No unrelated refactor, dependency upgrades, or full-suite debt cleanup.

### Must NOT Have (Guardrails)
- Do not touch non-critical workflow jobs except where dependency wiring requires a mirrored safe fix.
- Do not "fix" unrelated failing tests from full layer/e2e layer.
- Do not rewrite auth logic in app/store; focus on test determinism and CI bootstrap.
- Do not introduce brittle sleeps when deterministic await/assert primitives exist.

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> All verification must be executable by agent tools only.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after
- **Framework**: Vitest (frontend), Pytest (backend)

### Agent-Executed QA Scenarios (MANDATORY)

Scenario: Backend critical dependency install in clean runner
  Tool: Bash
  Preconditions: Fresh CI runner or clean local env without active venv in backend
  Steps:
    1. Execute backend install sequence mirroring workflow with dependency-groups compatible command.
    2. Run `uv sync --group dev` (unblock-first baseline).
    3. Optional hardening pass: run lock consistency check (`uv lock --check`) and then adopt `--locked` once lock discipline is stable.
    4. Assert command exits 0 and dev tooling (`pytest`, `pytest-asyncio`) is available in environment.
  Expected Result: Dependency installation succeeds.
  Failure Indicators: Exit code non-zero; lock mismatch; missing `pytest`; use of `.[dev]` persists.
  Evidence: CI step logs from backend-critical-tests job.

Scenario: Frontend App authenticated chrome visibility
  Tool: Bash (Vitest)
  Preconditions: Node dependencies installed in `frontend`
  Steps:
    1. Run `npm run test -- --run src/__tests__/App.spec.ts`.
    2. Ensure test awaits render flush (`nextTick`/equivalent) before assertions.
    3. Assert test `should render header when user is authenticated` passes.
    4. Assert test `should render sidebar when user is authenticated` passes.
  Expected Result: Both authenticated chrome assertions pass reliably.
  Failure Indicators: `.app-header` or `.app-sidebar` not found under authenticated setup.
  Evidence: Vitest stdout in CI log and local run output.

Scenario: Frontend App logout redirect behavior
  Tool: Bash (Vitest)
  Preconditions: Authenticated state prepared inside App.spec
  Steps:
    1. Run targeted logout test in `App.spec.ts`.
    2. Trigger logout through deterministic selector/component target.
    3. Assert route becomes `/login`.
  Expected Result: Redirect test passes without empty DOMWrapper errors.
  Failure Indicators: "Cannot call trigger on an empty DOMWrapper".
  Evidence: Vitest output showing the specific test passed.

Scenario: Quality Gate critical aggregation
  Tool: Bash (GitHub Actions rerun)
  Preconditions: Fix branch pushed with updated workflow/tests
  Steps:
    1. Re-run workflow for same branch/PR.
    2. Inspect critical jobs: frontend-type-check, frontend-build, frontend-critical-tests, backend-critical-tests.
    3. Inspect summary decision output.
  Expected Result: Summary prints `PASS - All critical checks passed`.
  Failure Indicators: Any critical job result != success.
  Evidence: Run URL + summary section logs.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1:
- Task 0: Backend command semantics proof (`dependency-groups` vs `.[dev]`)

Wave 2:
- Task 1: Backend workflow install command correction
- Task 2: Backend critical pytest lane verification

Wave 3:
- Task 3: Frontend App.spec root-cause stabilization (render flush + deterministic selector)
- Task 4: Frontend P0 lane verification

Wave 4:
- Task 5: End-to-end critical lane rerun + summary validation
- Task 6: Optional lock-hardening follow-up (`--locked`) after gate is green

Critical Path: Task 0 -> Task 1 -> Task 2 -> Task 3 -> Task 4 -> Task 5
Parallel Speedup: none (intentional risk reduction)

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 0 | None | 1 | None |
| 1 | 0 | 2 | None |
| 2 | 1 | 5 | None |
| 3 | 2 | 4 | None |
| 4 | 3 | 5 | None |
| 5 | 2, 4 | 6 | None |
| 6 | 5 | None | None |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 0 | `task(category="quick", load_skills=["git-master"])` |
| 2 | 1,2 | sequential CI workflow + backend verification |
| 3 | 3,4 | sequential frontend stabilization + P0 verification |
| 4 | 5,6 | final CI rerun, then optional lock hardening |

---

## TODOs

- [ ] 0. Prove backend install command semantics before editing workflow

  **What to do**:
  - Confirm that `backend/pyproject.toml` uses `[dependency-groups]` and not `optional-dependencies` for `dev`.
  - Confirm CI command must be changed away from `uv pip install -e ".[dev]"`.
  - Select final command policy: `uv sync --group dev --locked` (preferred when lock is authoritative).

  **Must NOT do**:
  - No speculative workflow edits before command semantics are confirmed.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: 1
  - **Blocked By**: None

  **References**:
  - `backend/pyproject.toml:29` - dependency-groups declaration.
  - `.github/workflows/quality-gate.yml:133` - currently incorrect extras-style install command.

  **Acceptance Criteria**:
  - [ ] Command policy explicitly documented as dependency-groups compatible.
  - [ ] No `.[dev]` usage remains in backend workflow path.

  **Commit**: NO

- [ ] 0.1 Verify frontend Vitest resource constraints (OOM guardrail)

  **What to do**:
  - Verify `frontend/vitest.config.ts` still contains required resource constraints before any test-lane changes.

  **Must NOT do**:
  - Do not run parallel memory-heavy jobs if constraints are missing.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: 4
  - **Blocked By**: None

  **References**:
  - `frontend/vitest.config.ts:13` - `pool: 'forks'`
  - `frontend/vitest.config.ts:16` - `maxForks: 2`
  - `frontend/vitest.config.ts:20` - `maxConcurrency: 5`
  - `frontend/vitest.config.ts:21` - `isolate: false`

  **Acceptance Criteria**:
  - [ ] All four constraints exist with explicit numeric values.
  - [ ] If any constraint missing, plan execution pauses and patches config before running test lanes.

  **Commit**: NO

- [ ] 1. Fix backend critical job install bootstrap

  **What to do**:
  - Replace backend critical install command with dependency-groups compatible command (`uv sync --group dev`) to prioritize unblock.
  - Apply same safe pattern to backend full test/e2e backend install sections only if they share identical failing bootstrap path.

  **Must NOT do**:
  - No dependency version upgrades.
  - No unrelated workflow restructuring.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: single-file CI fix with clear failure signature.
  - **Skills**: [`git-master`]
    - `git-master`: ensures minimal, reviewable workflow diff and safe commit slicing.
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: not relevant to CI YAML fix.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: 2, 5
  - **Blocked By**: 0

  **References**:
  - `.github/workflows/quality-gate.yml:131` - backend dependency install step failing in CI.
  - `.github/workflows/quality-gate.yml:211` - backend full tests install path consistency check.
  - `.github/workflows/quality-gate.yml:259` - e2e backend startup install path consistency check.
  - `backend/pyproject.toml:29` - dev deps defined via dependency groups; avoid mistaken extras assumptions.

  **Acceptance Criteria**:
  - [ ] Backend install step uses dependency-groups compatible syntax.
  - [ ] Backend install step no longer emits "No virtual environment found".
  - [ ] Backend install step does not use `.[dev]` extras syntax.
  - [ ] Backend critical job reaches pytest execution step.
  - [ ] CI backend critical job exit code is 0.

  **Commit**: YES (group with Task 2)

- [ ] 2. Verify backend P0 test lane after bootstrap fix

  **What to do**:
  - Execute backend critical pytest list exactly as workflow defines.
  - Confirm no hidden bootstrap regressions.

  **Must NOT do**:
  - No test list expansion.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: 5
  - **Blocked By**: 1

  **References**:
  - `.github/workflows/quality-gate.yml:135` - exact backend P0 pytest command and file list.
  - `backend/tests/test_auth.py` - auth critical lane.
  - `backend/tests/test_chat_citation.py` - citation critical lane.
  - `backend/tests/test_workflow_api.py` - workflow API critical lane.

  **Acceptance Criteria**:
  - [ ] Command equivalent to workflow backend P0 test step passes.
  - [ ] No bootstrap or import errors in backend lane.

  **Commit**: YES (group with Task 1)

- [ ] 3. Stabilize failing frontend App P0 test design (root-cause constrained)

  **What to do**:
  - Stabilize authenticated chrome rendering assertions (`header`/`sidebar`) with explicit render flush after mount.
  - Replace ambiguous selector strategy (`find('button')`) with deterministic logout target.
  - Remove brittle fixed sleep waits; use deterministic async completion strategy.
  - Keep changes minimal to P0 file(s) only.

  **Concrete Edit Targets**:
  - `frontend/src/__tests__/App.spec.ts:119` - replace `wrapper.find('button')` with deterministic selector.
  - `frontend/src/App.vue:36` - add stable selector attribute on logout button only if existing markup lacks deterministic handle.
  - `frontend/src/__tests__/App.spec.ts:124` - replace fixed `setTimeout` wait with deterministic routing/promise flush.
  - `frontend/src/__tests__/App.spec.ts:75` and `frontend/src/__tests__/App.spec.ts:93` - enforce post-mount flush before asserting header/sidebar existence.

  **Must NOT do**:
  - No broad rewrite of App component business logic.
  - No unrelated updates to full-layer tests.

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: small but subtle test determinism repair.
  - **Skills**: [`frontend-ui-ux`, `git-master`]
    - `frontend-ui-ux`: align with existing component markup semantics/selectors.
    - `git-master`: keep test fix diff minimal and auditable.
  - **Skills Evaluated but Omitted**:
    - `playwright`: this is unit/spec lane, not browser E2E.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: 4, 5
  - **Blocked By**: 2

  **References**:
  - `frontend/src/__tests__/App.spec.ts:82` - header authenticated assertion failure site.
  - `frontend/src/__tests__/App.spec.ts:100` - sidebar authenticated assertion failure site.
  - `frontend/src/__tests__/App.spec.ts:121` - empty DOMWrapper trigger failure site.
  - `frontend/src/App.vue:36` - logout button rendering path.
  - `frontend/src/App.vue:48` - sidebar toggle button that can steal generic selector matches.
  - `frontend/src/stores/auth.ts:18` - authenticated state definition (`token && user`).

  **Acceptance Criteria**:
  - [ ] App.spec no longer uses ambiguous click target for logout test.
  - [ ] App.spec no longer relies on fragile fixed timeout for route assertion.
  - [ ] Authenticated header/sidebar assertions run after explicit render flush.
  - [ ] Authenticated chrome tests pass in targeted run.
  - [ ] No regressions introduced in login/auth related P0 tests.

  **Commit**: YES (group with Task 4)

- [ ] 4. Run frontend P0 lane exactly as workflow and verify stable pass

  **What to do**:
  - Execute exact workflow P0 command list:
    - `src/__tests__/App.spec.ts`
    - `src/__tests__/views/ChatTerminal.spec.ts`
    - `src/__tests__/auth/login.spec.ts`
  - Confirm all pass under CI-like mode.

  **Must NOT do**:
  - No expansion to full test suite.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: 5
  - **Blocked By**: 3

  **References**:
  - `.github/workflows/quality-gate.yml:95` - exact frontend P0 command.
  - `frontend/vitest.config.ts:13` - constrained forks and concurrency config for CI safety.
  - `frontend/package.json:16` - `test` script uses one-shot run mode.

  **Acceptance Criteria**:
  - [ ] Frontend P0 command exits 0.
  - [ ] No App.spec failures remain.
  - [ ] No watch-mode/process-hang behavior in automation.

  **Commit**: YES (group with Task 3)

- [ ] 5. Re-run Quality Gate and validate critical summary pass

  **What to do**:
  - Trigger workflow rerun for target branch/PR.
  - Capture results for the four critical checks and summary decision text.
  - Archive evidence links in `.sisyphus/evidence` markdown note.

  **Must NOT do**:
  - No merge before critical summary is green.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential final gate
  - **Blocks**: None
  - **Blocked By**: 2, 4

  **References**:
  - `.github/workflows/quality-gate.yml:303` - summary output contract.
  - Run URL pattern: `https://github.com/Joe-rq/agent-flow-lite/actions/runs/<run_id>`.

  **Acceptance Criteria**:
  - [ ] `frontend-type-check`, `frontend-build`, `frontend-critical-tests`, `backend-critical-tests` all `success`.
  - [ ] `Quality Gate Summary` outputs `PASS - All critical checks passed`.
  - [ ] Evidence note includes run URL and job result snapshot.

  **Commit**: NO (verification/evidence only)

- [ ] 6. Optional hardening: enforce locked CI after gate is green

  **What to do**:
  - Add lock freshness check (`uv lock --check`) in backend lane.
  - Upgrade install command to `uv sync --group dev --locked` only after lock consistency is confirmed stable in mainline.

  **Must NOT do**:
  - Do not block current unblock-fix release on lock-hardening.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: 5

  **References**:
  - `backend/uv.lock` - lockfile authority source.
  - `.github/workflows/quality-gate.yml:133` - baseline install command location.

  **Acceptance Criteria**:
  - [ ] `uv lock --check` passes in CI.
  - [ ] `uv sync --group dev --locked` succeeds in at least one validation run before becoming default.

  **Commit**: YES (separate hardening commit)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1-2 | `fix(ci): bootstrap backend uv install in quality gate` | `.github/workflows/quality-gate.yml` | backend P0 command + CI job pass |
| 3-4 | `test(frontend): stabilize App P0 chrome/logout assertions` | `frontend/src/__tests__/App.spec.ts` (+ minimal selector support if needed) | frontend P0 command pass |

---

## Success Criteria

### Verification Commands
```bash
# Frontend P0 lane
cd frontend && npm run test -- --run src/__tests__/App.spec.ts src/__tests__/views/ChatTerminal.spec.ts src/__tests__/auth/login.spec.ts

# Backend P0 lane
cd backend && uv run pytest -q tests/test_auth.py tests/test_chat_citation.py tests/test_chat_scoped.py tests/test_workflow_api.py tests/test_knowledge_dimension_mismatch.py
```

### Final Checklist
- [ ] All Must Have items satisfied
- [ ] All Must NOT Have items respected
- [ ] Critical quality gate passes in Actions summary
- [ ] Changes remain scoped to the two identified root causes
