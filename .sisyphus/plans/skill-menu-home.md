# HomeView Skill Management Menu Plan

## TL;DR

> **Quick Summary**: Add a new Skill Management feature card to the HomeView grid by extending the feature model, adding a new SVG icon variant, and updating HomeView tests using TDD.
>
> **Deliverables**:
> - Updated `frontend/src/views/HomeView.vue` with new `skill` feature and icon styling
> - Updated `frontend/src/__tests__/views/HomeView.spec.ts` to expect 4 cards including Skill Management
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential
> **Critical Path**: Task 1

---

## Context

### Original Request
"Add a Skill Management menu entry in HomeView, alongside Knowledge Base and Workflow, with a new icon and style. Ensure /skills route and SkillsView exist."

### Interview Summary
**Key Discussions**:
- Extend `Feature.icon` union to include `skill`.
- Add new feature entry for Skill Management with route `/skills`.
- Add SVG icon and `.feature-card__icon--skill` style.
- Test strategy: TDD using existing Vitest setup.

**Research Findings**:
- `frontend/src/views/HomeView.vue` defines `Feature` interface, `features` array, SVG icon switch, and icon styles.
- Existing icon classes: `feature-card__icon--workflow`, `--knowledge`, `--chat`.
- Frontend test infrastructure uses Vitest with `frontend/src/__tests__/views/HomeView.spec.ts` in place.

### Metis Review
**Identified Gaps (addressed)**:
- No additional gaps returned by Metis (empty response).

---

## Work Objectives

### Core Objective
Expose Skill Management on the HomeView by adding a new card that matches existing card style, routes to `/skills`, and includes a distinct icon.

### Concrete Deliverables
- `frontend/src/views/HomeView.vue` updated with `skill` card and icon styling.
- `frontend/src/__tests__/views/HomeView.spec.ts` updated/extended to cover 4 cards including Skill Management.

### Definition of Done
- [ ] HomeView shows 4 cards including "技能管理".
- [ ] Clicking the Skill Management card routes to `/skills`.
- [ ] HomeView tests updated and passing.

### Must Have
- New card labeled "技能管理" with description "管理 Agent Skills" (or equivalent per existing copy style).
- Route for the new card is `/skills`.
- SVG icon for `skill` uses the same stroke style as other icons.

### Must NOT Have (Guardrails)
- No routing changes unless `/skills` or `SkillsView.vue` is missing.
- No new UI libraries or global style refactors.
- Do not alter existing card copy or routes other than adding the new card.

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> This applies to EVERY task regardless of test strategy.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: TDD
- **Framework**: Vitest

### If TDD Enabled

Each TODO follows RED-GREEN-REFACTOR:

**Task Structure**:
1. **RED**: Update HomeView test to expect 4 cards and new Skill entry
2. **GREEN**: Implement HomeView changes until tests pass
3. **REFACTOR**: Cleanup to match existing conventions

### Agent-Executed QA Scenarios (MANDATORY - ALL tasks)

**Scenario: HomeView shows Skill Management card**
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running on http://localhost:5173
  Steps:
    1. Navigate to: http://localhost:5173/
    2. Wait for: `.feature-card` visible (timeout: 5s)
    3. Assert: count of `.feature-card` equals 4
    4. Assert: heading text "技能管理" is visible
    5. Screenshot: .sisyphus/evidence/task-1-home-skill-card.png
  Expected Result: Skill Management card is present among 4 cards
  Failure Indicators: Fewer/more than 4 cards, missing "技能管理"
  Evidence: .sisyphus/evidence/task-1-home-skill-card.png

**Scenario: Clicking Skill card navigates to /skills**
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running, `/skills` route exists
  Steps:
    1. Navigate to: http://localhost:5173/
    2. Click: heading "技能管理"
    3. Wait for: URL to match `/skills` (timeout: 5s)
    4. Screenshot: .sisyphus/evidence/task-1-home-skill-nav.png
  Expected Result: URL is `/skills`
  Failure Indicators: URL remains `/` or navigates elsewhere
  Evidence: .sisyphus/evidence/task-1-home-skill-nav.png

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
├── Task 1: Add Skill Management card + tests (TDD)

Critical Path: Task 1
Parallel Speedup: N/A

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|----------------------|
| 1 | None | None | None |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1 | delegate_task(category="quick", load_skills=["frontend-ui-ux"], run_in_background=false) |

---

## TODOs

- [x] 1. Add Skill Management card to HomeView (TDD)

  **What to do**:
  - RED: Update `frontend/src/__tests__/views/HomeView.spec.ts` to expect 4 cards and include "技能管理" card metadata.
    - If adding a click/navigation assertion, ensure the test router includes `/skills`.
  - GREEN: Update `frontend/src/views/HomeView.vue`:
    - Extend `Feature.icon` union with `skill`.
    - Add a `features` entry for Skill Management with route `/skills` and description.
    - Add SVG icon variant for `skill` in the icon switch.
    - Add `.feature-card__icon--skill` style using a distinct color (default: orange accent).
  - REFACTOR: Ensure formatting matches existing conventions (no semicolons, single quotes, 100 width).

  **Must NOT do**:
  - Do not change existing routes or card copy beyond adding the new entry.
  - Do not add new global CSS variables unless already present.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single-file UI update with a small test change.
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Ensures icon style/color remains cohesive with existing UI.
  - **Skills Evaluated but Omitted**:
    - `playwright`: Only needed for QA execution, not for implementation.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References** (existing code to follow):
  - `frontend/src/views/HomeView.vue` - Existing Feature interface, features array, icon switch, and style class pattern.

  **API/Type References** (contracts to implement against):
  - `frontend/src/views/HomeView.vue` - `Feature` interface and `features` array structure.

  **Test References** (testing patterns to follow):
  - `frontend/src/__tests__/views/HomeView.spec.ts` - Existing HomeView test structure to extend.

  **Documentation References** (specs and requirements):
  - `frontend/src/router/index.ts` - Verify `/skills` route presence and naming pattern.
  - `frontend/src/views/SkillsView.vue` - Confirm Skills page exists and component name usage.

  **WHY Each Reference Matters**:
  - `frontend/src/views/HomeView.vue`: Ensures the new card matches existing layout, icon rendering, and styling conventions.
  - `frontend/src/__tests__/views/HomeView.spec.ts`: Keeps test style consistent and reduces brittle assertions.
  - `frontend/src/router/index.ts`: Confirms `/skills` route exists to avoid dead navigation.
  - `frontend/src/views/SkillsView.vue`: Confirms target view is present for navigation.

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test updated: `frontend/src/__tests__/views/HomeView.spec.ts` includes Skill card expectations.
  - [ ] `npx vitest run src/__tests__/views/HomeView.spec.ts` → PASS
  - [ ] HomeView renders 4 cards including "技能管理" with route `/skills`.
  - [ ] If click/navigation assertion added, test router defines `/skills` route.

  **Agent-Executed QA Scenarios (MANDATORY)**:
  - Scenario: HomeView shows Skill Management card (Playwright) with evidence
  - Scenario: Clicking Skill card navigates to /skills (Playwright) with evidence

  **Commit**: NO (not requested)

---

## Commit Strategy

No commits requested. If a commit is needed later, group all HomeView + test changes into a single commit.

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npx vitest run src/__tests__/views/HomeView.spec.ts
```

### Final Checklist
- [ ] Skill Management card visible on HomeView
- [ ] `/skills` navigation works from the card
- [ ] HomeView tests pass
