# Remove Skill Model Field Plan

## TL;DR

> **Quick Summary**: Remove the skill model selector entirely so skills always use the backend default model. Update SkillEditor UI, payload, and SKILL.md preview; adjust tests using TDD.
>
> **Deliverables**:
> - Remove model input/state from `frontend/src/views/SkillEditor.vue`
> - Stop emitting `model:` in generated SKILL.md
> - Stop sending `model` in save payload
> - Update/extend `frontend/src/__tests__/views/SkillEditor.spec.ts`
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential
> **Critical Path**: Task 1 → Task 2

---

## Context

### Original Request
“直接调用默认模型，这个功能去掉。”

### Interview Summary
**Key Discussions**:
- Remove model field entirely (UI, payload, and SKILL.md).
- Test strategy: TDD (Vitest).

**Research Findings**:
- `frontend/src/views/SkillEditor.vue` includes model input, state, payload, and `generatedMarkdown` emits `model:`.
- Tests reference “模型” label and mock `model: deepseek-chat` in `frontend/src/__tests__/views/SkillEditor.spec.ts`.

### Metis Review
**Identified Gaps (addressed)**:
- Guardrails: frontend-only, no backend changes, no data cleanup.
- Acceptance criteria: verify model field absence in UI/payload/preview.
- Decision needed for existing skills that already have a model.

---

## Work Objectives

### Core Objective
Skill editor no longer exposes or persists model selection; skills rely on default backend model.

### Concrete Deliverables
- Model input removed from SkillEditor UI.
- `generatedMarkdown` omits `model:` line.
- Save payload omits `model`.
- Tests updated and new assertions for absence.

### Definition of Done
- [ ] UI contains no “模型” label/input in SkillEditor.
- [ ] Generated SKILL.md preview has no `model:` line.
- [ ] POST/PUT payloads contain no `model` field.
- [ ] `npx vitest run src/__tests__/views/SkillEditor.spec.ts` passes.

### Must Have
- No backend changes; default model behavior comes from existing backend config.

### Must NOT Have (Guardrails)
- Do not modify backend APIs or data.
- Do not refactor SkillEditor outside model removal.
- Do not introduce new dependencies.

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: YES (Vitest)
- **Automated tests**: TDD
- **Framework**: Vitest

### If TDD Enabled

1. **RED**: Add tests asserting no model input, no `model:` in preview, no `model` in payload.
2. **GREEN**: Remove model state/field and payload usage; update preview generator.
3. **REFACTOR**: Minor cleanup only if needed.

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Scenario: Skill editor has no model field
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running on http://localhost:5173; user logged in
  Steps:
    1. Navigate to: http://localhost:5173/skills/new
    2. Assert: page text does NOT contain “模型”
    3. Assert: input[placeholder="deepseek-chat"] does NOT exist
    4. Screenshot: .sisyphus/evidence/skill-model-removed-ui.png
  Expected Result: Model field is absent
  Evidence: .sisyphus/evidence/skill-model-removed-ui.png

Scenario: Save payload excludes model
  Tool: Playwright (playwright skill)
  Preconditions: Dev server running; user logged in
  Steps:
    1. Navigate to: http://localhost:5173/skills/new
    2. Fill: input[placeholder="skill-name"] → "model-less-skill"
    3. Fill: textarea.prompt-textarea → "Test prompt"
    4. Click: button.btn-primary (text contains "保存")
    5. Intercept POST /api/v1/skills and assert request body has no `model` key
    6. Screenshot: .sisyphus/evidence/skill-model-removed-payload.png
  Expected Result: Request body has no `model`
  Evidence: .sisyphus/evidence/skill-model-removed-payload.png

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
└── Task 1: Add TDD tests for model removal

Wave 2 (After Wave 1):
└── Task 2: Remove model field and update payload/preview

Critical Path: Task 1 → Task 2

---

## TODOs

- [x]1. Add TDD tests for model removal (RED)

  **What to do**:
  - Update `frontend/src/__tests__/views/SkillEditor.spec.ts`:
    - Remove expectations for “模型” label and model input.
    - Add assertions that preview does NOT include `model:`.
    - Add assertions that save payload does NOT include `model`.

  **Must NOT do**:
  - Do not change production code yet.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **References**:
  - `frontend/src/__tests__/views/SkillEditor.spec.ts` - Existing tests referencing model field.
  - `frontend/src/views/SkillEditor.vue` - Current UI, `generatedMarkdown`, save payload.

  **Acceptance Criteria**:
  - [ ] `npx vitest run src/__tests__/views/SkillEditor.spec.ts` → FAIL (model still present).

- [x] 2. Remove model field and update payload/preview (GREEN)

  **What to do**:
  - Remove model input block from template.
  - Remove `skillModel` state and loadSkill mapping.
  - Remove `model` from save payload.
  - Remove `model:` emission from `generatedMarkdown`.

  **Must NOT do**:
  - Do not change backend models/APIs.
  - Do not alter other fields or behaviors.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **References**:
  - `frontend/src/views/SkillEditor.vue` - Template, state, `generatedMarkdown`, `saveSkill()`.

  **Acceptance Criteria**:
  - [ ] `npx vitest run src/__tests__/views/SkillEditor.spec.ts` → PASS.
  - [ ] Preview omits `model:` line.
  - [ ] Save payload omits `model`.

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2 | `fix(技能): 移除模型字段` | `frontend/src/views/SkillEditor.vue`, `frontend/src/__tests__/views/SkillEditor.spec.ts` | `npx vitest run src/__tests__/views/SkillEditor.spec.ts` |

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npx vitest run src/__tests__/views/SkillEditor.spec.ts
```

### Final Checklist
- [ ] SkillEditor UI has no model field
- [ ] Preview contains no `model:` line
- [ ] Save payload excludes `model`
- [ ] Tests pass

---

## Decisions Needed

- [x] When editing an existing skill that already has `model`, saving should **drop it** (use default model).
