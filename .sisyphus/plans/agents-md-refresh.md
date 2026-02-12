# AGENTS.md Refresh Plan

## TL;DR

> **Quick Summary**: Refresh the existing root `AGENTS.md` so it stays accurate, concise, and agent-friendly, with commands and conventions sourced from actual config/CI files rather than stale prose.
>
> **Deliverables**:
> - Updated root `AGENTS.md` (target ~150 lines, accuracy first)
> - Command matrix with single-test examples for frontend/backend
> - Style/quality rules aligned with current configs and CI
>
> **Estimated Effort**: Short
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 4

---

## Context

### Original Request
Analyze this repository and improve existing `AGENTS.md` with:
- build/lint/test commands (especially single-test usage)
- code style guidelines (imports, formatting, typing, naming, error handling)
- inclusion of Cursor/Copilot rules if present
- about 150 lines total

### Interview Summary
**Key Discussions**:
- Existing `AGENTS.md` already exists and should be improved in place.
- Authoritative precedence is config + CI files over README prose.
- Cursor/Copilot rule files must be included only if they actually exist.

**Research Findings**:
- Frontend commands from `frontend/package.json`.
- Backend commands from `backend/pyproject.toml` and `uv` workflow usage in CI.
- CI source-of-truth from `.github/workflows/quality-gate.yml`.
- Style sources from frontend lint/format config files.
- No `.cursorrules`, `.cursor/rules/**`, or `.github/copilot-instructions.md` found.

### Metis Review
**Identified Gaps** (addressed):
- Missing explicit shrink strategy for line-budget target -> add content budget guardrail and trim priority.
- Potential stale mismatch (`vitest isolate`) -> verify against current config and replace stale text.
- Ambiguity around command trustworthiness -> require config/CI-backed references and executable checks.

---

## Work Objectives

### Core Objective
Produce a high-signal `AGENTS.md` that helps execution agents run the project safely and consistently, with minimal ambiguity and no stale guidance.

### Concrete Deliverables
- Root file updated: `AGENTS.md`
- Command coverage:
  - frontend install/dev/build/lint/format/test/single-test
  - backend env/install/dev/test/single-test
- Style coverage:
  - formatting, imports, typing, naming, error handling
  - test resource constraints and CI verification posture

### Definition of Done
- [ ] `AGENTS.md` contains command sections for frontend/backend with single-test examples.
- [ ] `AGENTS.md` includes style + error-handling guidance grounded in config files.
- [ ] `AGENTS.md` explicitly states Cursor/Copilot rule-file status based on repository scan.
- [ ] Stale mismatch fixed (`vitest isolate` value aligns with `frontend/vitest.config.ts`).
- [ ] Document length is close to requested target (~150 lines, practical tolerance 130-180).

### Must Have
- Config-backed commands only (prefer package/pyproject/workflow evidence).
- Clear do/don't constraints for test resource safety.
- `uv`-first backend workflow and `uv run` runtime usage.

### Must NOT Have (Guardrails)
- No invented rules for Cursor/Copilot if files do not exist.
- No README-only claims that contradict config/CI.
- No expansion into unrelated docs or code changes.
- No watch-mode recommendation as default automation command.

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> All verification is agent-executed via shell commands and file checks.
> No manual clicking, visual checks, or human interpretation steps.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: None (documentation-focused task)
- **Framework**: N/A for new test authoring

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Scenario: Command references are source-backed
  Tool: Bash
  Preconditions: Repository files accessible
  Steps:
    1. Check command entries against `frontend/package.json` scripts.
    2. Check backend command entries against `backend/pyproject.toml` and CI workflow.
    3. Assert each documented critical command has at least one source file match.
  Expected Result: 100% documented critical commands map to existing config/CI sources.
  Failure Indicators: Any documented command missing from source files.
  Evidence: `.sisyphus/evidence/task-command-source-map.txt`

Scenario: Rule-file presence status is accurate (negative case)
  Tool: Bash
  Preconditions: Repository root available
  Steps:
    1. Verify `.cursorrules` absence/presence.
    2. Verify `.cursor/rules/**` absence/presence.
    3. Verify `.github/copilot-instructions.md` absence/presence.
    4. Assert AGENTS wording matches discovered state.
  Expected Result: AGENTS reflects actual file existence without fabricated guidance.
  Failure Indicators: AGENTS claims file exists when it does not (or vice versa).
  Evidence: `.sisyphus/evidence/task-rule-file-scan.txt`

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately):
- Task 1: Build source-of-truth matrix and conflict list
- Task 3: Detect optional rule files and status wording

Wave 2 (After Wave 1):
- Task 2: Rewrite AGENTS content with budget and guardrails
- Task 4: Validation pass + line-budget tuning + final consistency checks

Critical Path: Task 1 -> Task 2 -> Task 4
Parallel Speedup: ~25% vs fully sequential

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|----------------------|
| 1 | None | 2, 4 | 3 |
| 2 | 1, 3 | 4 | None |
| 3 | None | 2 | 1 |
| 4 | 2 | None | None |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|--------------------|
| 1 | 1, 3 | `task(category="quick", load_skills=["writing"-adjacent])` style for documentation discovery |
| 2 | 2, 4 | single focused agent to preserve editorial consistency |

---

## TODOs

- [x] 1. Build authoritative command/style source matrix

  **What to do**:
  - Extract canonical frontend commands from `frontend/package.json`.
  - Extract canonical backend commands from `backend/pyproject.toml` and CI (`uv sync --group dev`, `uv run pytest ...`).
  - Build a mismatch list between existing `AGENTS.md` and current configs (notably Vitest `isolate`).

  **Must NOT do**:
  - Do not copy command examples only from README if config disagrees.
  - Do not normalize commands to personal preference (keep repository truth).

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Deterministic extraction/checking work.
  - **Skills**: `[]`
    - Domain does not require special browser/git skills.
  - **Skills Evaluated but Omitted**:
    - `playwright`: not needed for file-based command extraction.
    - `git-master`: no git history operation required for completion.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 3)
  - **Blocks**: 2, 4
  - **Blocked By**: None

  **References**:
  - `frontend/package.json:6` - authoritative script list for frontend commands.
  - `backend/pyproject.toml:29` - dev dependency group; confirms `uv` workflow basis.
  - `backend/pyproject.toml:36` - pytest options and defaults.
  - `.github/workflows/quality-gate.yml:95` - CI-critical frontend test invocation patterns.
  - `.github/workflows/quality-gate.yml:135` - CI-critical backend test invocation patterns.
  - `AGENTS.md:93` - current test resource section to reconcile with config reality.
  - `frontend/vitest.config.ts:21` - actual `isolate` value to sync in AGENTS.

  **Acceptance Criteria**:
  - [ ] A source matrix exists mapping each AGENTS command block item to config/CI source lines.
  - [ ] Mismatch list includes stale entries and required replacements.

  **Agent-Executed QA Scenarios**:
  ```text
  Scenario: Source matrix completeness
    Tool: Bash
    Preconditions: Files are readable
    Steps:
      1. Parse frontend scripts from frontend/package.json.
      2. Parse backend test/install commands from pyproject + workflow.
      3. Compare with AGENTS command bullets.
      4. Assert no critical command lacks source mapping.
    Expected Result: Complete source mapping for all critical commands.
    Failure Indicators: Unmapped commands or ambiguous source.
    Evidence: .sisyphus/evidence/task-1-source-matrix.txt

  Scenario: Stale-setting detection
    Tool: Bash
    Preconditions: Existing AGENTS and vitest config present
    Steps:
      1. Read AGENTS mention of vitest isolate.
      2. Read frontend/vitest.config.ts isolate value.
      3. Assert mismatch captured in issue list.
    Expected Result: Mismatch explicitly identified for correction.
    Failure Indicators: No mismatch report despite divergent values.
    Evidence: .sisyphus/evidence/task-1-stale-mismatch.txt
  ```

  **Commit**: NO

- [x] 2. Rewrite `AGENTS.md` with constrained, enforceable structure

  **What to do**:
  - Update existing root `AGENTS.md` in place.
  - Keep sections focused on execution-critical information:
    - repo overview
    - environment + dependency manager rules
    - frontend/backend command matrix (single-test emphasized)
    - style conventions
    - error handling + test constraints
    - CI post-push check instruction
  - Apply line-budget strategy to approach ~150 lines while retaining critical constraints.

  **Must NOT do**:
  - Do not add speculative sections for missing Cursor/Copilot files.
  - Do not include long tutorials or architecture deep-dives.
  - Do not leave contradictory guidance.

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: precision documentation rewrite with consistency constraints.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: visual design skill not relevant to markdown ops guide.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Wave 2)
  - **Blocks**: 4
  - **Blocked By**: 1, 3

  **References**:
  - `AGENTS.md:1` - current file to update.
  - `frontend/.editorconfig:1` - formatting defaults (indent, LF, width).
  - `frontend/.prettierrc.json:3` - frontend style knobs (semi/singleQuote/printWidth).
  - `frontend/eslint.config.ts:12` - lint stack composition and scope.
  - `frontend/.oxlintrc.json:7` - correctness severity and plugin baseline.
  - `scripts/check-ci-status.sh:63` - post-push CI check command pattern.
  - `.github/workflows/quality-gate.yml:31` - required quality gate jobs to reference succinctly.

  **Acceptance Criteria**:
  - [ ] Updated `AGENTS.md` includes all required command/style domains.
  - [ ] Single-test commands exist for both frontend and backend.
  - [ ] No stale conflict remains for Vitest `isolate` guidance.
  - [ ] Cursor/Copilot section accurately states not-found status when applicable.

  **Agent-Executed QA Scenarios**:
  ```text
  Scenario: Required section coverage
    Tool: Bash
    Preconditions: Updated AGENTS.md exists
    Steps:
      1. Assert AGENTS includes headings for commands and style guidance.
      2. Assert frontend single-test example contains `vitest run <file>` pattern.
      3. Assert backend single-test example contains `uv run pytest <file> -q` pattern.
    Expected Result: Mandatory coverage present and discoverable by grep.
    Failure Indicators: Missing section or missing single-test commands.
    Evidence: .sisyphus/evidence/task-2-section-coverage.txt

  Scenario: No fabricated optional-rule guidance
    Tool: Bash
    Preconditions: Optional rule files scan result from Task 3
    Steps:
      1. Search AGENTS for Cursor/Copilot rule statements.
      2. Compare statements against actual file existence.
      3. Assert no false-positive claim exists.
    Expected Result: AGENTS wording matches actual repository state.
    Failure Indicators: Mentioned non-existent instruction file as active source.
    Evidence: .sisyphus/evidence/task-2-optional-rules-consistency.txt
  ```

  **Commit**: NO

- [x] 3. Resolve optional rule-file status (Cursor/Copilot)

  **What to do**:
  - Re-scan for `.cursorrules`, `.cursor/rules/**`, `.github/copilot-instructions.md`.
  - Produce one definitive status line for AGENTS.

  **Must NOT do**:
  - Do not infer rules from unrelated files.
  - Do not duplicate stale assumptions from templates.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: small deterministic discovery task.
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: 2
  - **Blocked By**: None

  **References**:
  - `.cursorrules` - optional rule file path to verify.
  - `.cursor/rules/` - optional Cursor rules directory to verify.
  - `.github/copilot-instructions.md` - optional Copilot instruction file to verify.

  **Acceptance Criteria**:
  - [ ] Optional rule-file existence table produced (present/absent).
  - [ ] AGENTS wording mirrors this table exactly.

  **Agent-Executed QA Scenarios**:
  ```text
  Scenario: Optional rule-file negative verification
    Tool: Bash
    Preconditions: Repository root available
    Steps:
      1. Run file existence checks for all 3 optional locations.
      2. Persist result table.
      3. Assert AGENTS contains matching status statement.
    Expected Result: Exact match between filesystem reality and AGENTS statement.
    Failure Indicators: Any mismatch or omitted location.
    Evidence: .sisyphus/evidence/task-3-rule-file-status.txt

  Scenario: Future-proof wording check
    Tool: Bash
    Preconditions: AGENTS updated
    Steps:
      1. Ensure wording is conditional ("if present") where needed.
      2. Ensure no hardcoded assumption of future files.
    Expected Result: Wording remains correct if files are later added.
    Failure Indicators: Absolutist phrasing that will become stale immediately.
    Evidence: .sisyphus/evidence/task-3-wording-check.txt
  ```

  **Commit**: NO

- [x] 4. Final verification and line-budget tuning

  **What to do**:
  - Validate consistency between AGENTS and source configs.
  - Run line-count check and trim low-value text to stay near target.
  - Confirm CI post-push check commands are documented (`gh run list`, `gh run view`).

  **Must NOT do**:
  - Do not sacrifice critical safety constraints to hit an arbitrary line count.
  - Do not leave unresolved placeholder text.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: deterministic validation and concise edits.
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (final)
  - **Blocks**: None
  - **Blocked By**: 2

  **References**:
  - `AGENTS.md` - final target file under validation.
  - `scripts/check-ci-status.sh:63` - canonical post-push CI check commands.
  - `.github/workflows/quality-gate.yml:31` - critical job names to keep aligned.

  **Acceptance Criteria**:
  - [ ] `AGENTS.md` line count in practical target band (130-180; preferred ~150).
  - [ ] No contradiction remains against package/pyproject/vitest/workflow configs.
  - [ ] CI follow-up guidance appears and is executable.

  **Agent-Executed QA Scenarios**:
  ```text
  Scenario: Line-budget and contradiction check
    Tool: Bash
    Preconditions: AGENTS final draft complete
    Steps:
      1. Count AGENTS lines.
      2. Verify critical keywords exist: uv run, vitest run, maxForks, gh run list.
      3. Verify stale keyword/value combos are absent.
    Expected Result: Near-target length with no known contradiction markers.
    Failure Indicators: Missing critical keyword or known stale value persists.
    Evidence: .sisyphus/evidence/task-4-budget-consistency.txt

  Scenario: CI instruction operability
    Tool: Bash
    Preconditions: gh CLI available in environment (or documented as prerequisite)
    Steps:
      1. Validate documented CI commands syntax matches script usage.
      2. Confirm references include workflow name and run inspection command.
    Expected Result: Documented commands are syntactically valid and aligned with scripts.
    Failure Indicators: Broken command syntax or mismatched workflow naming.
    Evidence: .sisyphus/evidence/task-4-ci-command-validity.txt
  ```

  **Commit**: NO

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| N/A | N/A | N/A | N/A |

---

## Success Criteria

### Verification Commands
```bash
# line count target check
wc -l AGENTS.md

# command coverage checks
grep -n "vitest run" AGENTS.md
grep -n "uv run pytest" AGENTS.md

# safety constraints checks
grep -n "maxForks" AGENTS.md
grep -n "gh run list" AGENTS.md

# optional rule-file status checks
test -f .cursorrules; echo $?
test -f .github/copilot-instructions.md; echo $?
```

### Final Checklist
- [ ] All required command domains documented (with single-test emphasis).
- [ ] Style/type/naming/error guidance aligned with current configs.
- [ ] Optional Cursor/Copilot rule-file status accurately reflected.
- [ ] Test-resource and CI-post-push guidance present and correct.
- [ ] AGENTS document concise and near requested line budget.
