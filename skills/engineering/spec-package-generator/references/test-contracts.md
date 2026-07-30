# Test Contracts

## Purpose

Stable Test IDs are not enough by themselves. Each Test ID must define repeatable inputs, inspected files, assertions, pass criteria, and evidence output before it can be treated as executable validation.

Use this reference for static and template-oriented validation of the skill package. Do not require network access, external services, or downstream application behavior tests.

## Required Test Contract Fields

Canonical full test contract fields are defined here and in `templates/test-case-contract.template.md`.

Each test contract must include:

- Test ID
- Title
- Purpose
- Requirement references
- Artifact references
- Inputs
- Fixture
- Files inspected
- Execution method
- Assertions
- Expected red-state failure for automated or semi-automated validation
- Pass criteria
- Evidence output
- Manual evidence
- Automation
- Owner
- Status

Allowed automation values:

- `automated`
- `semi-automated`
- `manual`

## Validation Methods

Valid validation methods for this skill are:

- Static text assertions.
- YAML/frontmatter validation.
- Required-section validation.
- Cross-reference validation.
- Normative ID validation.
- Golden-file comparison.
- Generated feature-package fixture comparison.
- Optimized package resume simulation.
- Optimized manifest recovery simulation.
- Stale artifact conflict simulation.
- Stage invalidation simulation.
- Prompt scope assertion.
- Dashboard readiness-order assertion.
- Manual reviewer checklist.

## Automation Levels

`automated` means a local script or command can decide pass/fail without human judgment.

`semi-automated` means local commands can collect evidence, but a reviewer must confirm semantic correctness.

`manual` means a reviewer must inspect generated artifacts or rendered HTML directly.

Manual Test IDs do not require red-state evidence, but they must include inspection points, pass criteria, evidence output, manual evidence, and owning task.

Bootstrap Test IDs may use `manual` or `semi-automated` validation when the project skeleton, package scripts, or test runner does not exist yet. They must define concrete file-existence checks, configuration checks, package script checks, or human inspection evidence. Do not require red-state test-runner evidence before the test runner is created.

No validation contract may require network access.

## Contract Field Authority

Use these layers consistently:

- Canonical full contract: `references/test-contracts.md` and `templates/test-case-contract.template.md`. These define the complete field set and automation-level meanings.
- Gate 2 summary: `24-gate2-test-strategy.md`. It may use compact columns for human review, but it must not omit required canonical fields for automated or semi-automated Test IDs when final readiness is evaluated.
- Task-scoped contract: `tasks/TASK-xxx.md`. It includes only Test IDs owned by that task, but it must preserve validation mode, required evidence, and the fields needed to execute or inspect the task.
- Readiness minimum: `35a-final-readiness-result.md`. It checks whether required fields exist and are traceable; it does not redefine the canonical contract.

## Task TDD Pattern

RED:

- Define a failing static, contract, or fixture validation.
- Record the expected red-state failure.
- For greenfield bootstrap tasks that create the test runner or project skeleton, the red state may be "required file/script/configuration is absent" instead of an executable failing test.

GREEN:

- Modify the required template, reference, or instruction.
- Run the focused validation.

REFACTOR:

- Remove duplicated checklist wording.
- Keep detailed policy in references, not `SKILL.md`.
- Keep templates concise and fillable.

REGRESSION:

- Run related workflow, compatibility, and artifact authority checks.

## Contract Index For Optimized Workflow

### TEST-UNIT-007

- Title: Constitution amendment required fields
- Purpose: Verify amendment records can distinguish governance changes from architecture-dependent changes.
- Requirement references: DEC-003
- Artifact references: `templates/constitution-amendment.template.md`
- Inputs: Constitution amendment template.
- Fixture: One governance amendment and one architecture-dependent amendment.
- Files inspected: `templates/constitution-amendment.template.md`
- Execution method: Required-section and field-name review.
- Assertions:
  - Amendment type, status, effective timing, scope, approval, and affected artifacts are represented.
  - Architecture-dependent amendments are not treated as effective current implementation rules without the required lifecycle condition.
- Expected red-state failure: Amendment template has approval text but no effective timing or affected artifact fields.
- Pass criteria: Required lifecycle fields are present and unambiguous.
- Evidence output: Static validation note or checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-UNIT-008

- Title: Test contract required fields
- Purpose: Verify Test IDs can be made executable through repeatable contracts.
- Requirement references: `24-gate2-test-strategy.md`
- Artifact references: `templates/test-case-contract.template.md`, `references/test-contracts.md`
- Inputs: Test contract template and reference.
- Fixture: A single Test ID contract.
- Files inspected: `templates/test-case-contract.template.md`, `references/test-contracts.md`
- Execution method: Required-field validation.
- Assertions:
  - Inputs, fixture, execution method, assertions or inspection points, red-state failure for automated/semi-automated checks, pass criteria, evidence output, manual evidence for manual checks, automation, owner, and status are present.
  - Automation values are bounded to `automated`, `semi-automated`, or `manual`.
- Expected red-state failure: Template lists an automated Test ID but omits evidence output or red-state failure, or lists a manual Test ID without manual evidence.
- Pass criteria: All required fields are present in template and reference.
- Evidence output: Static validation note or checklist result.
- Automation: automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-UNIT-011

- Title: PRD required sections
- Purpose: Verify Gate 1 PRD captures product behavior without technical design ownership.
- Requirement references: REQ-003, DEC-007
- Artifact references: `templates/10-gate1-prd.template.md`
- Inputs: PRD template.
- Fixture: Minimal wish-list requirement.
- Files inspected: `templates/10-gate1-prd.template.md`
- Execution method: Required-section validation.
- Assertions:
  - Goal, users, scope, non-scope, business workflow, business rules, assumptions, and Blocking questions are represented.
  - Technical architecture decisions are not required in the PRD.
- Expected red-state failure: PRD template mixes architecture design into Gate 1 product review.
- Pass criteria: Product sections are present and Gate 1 boundaries remain clear.
- Evidence output: Checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-UNIT-012

- Title: EARS traceability fields
- Purpose: Verify each EARS statement is precise, testable, and traceable.
- Requirement references: REQ-003, REQ-007, DEC-007
- Artifact references: `templates/11-gate1-ears.template.md`
- Inputs: EARS template.
- Fixture: PRD requirement with at least two behaviors.
- Files inspected: `templates/11-gate1-ears.template.md`
- Execution method: Required-field validation.
- Assertions:
  - Each EARS row has ID, source PRD reference, pattern, statement, priority, and verification note.
  - Statements are observable and do not redefine PRD scope.
- Expected red-state failure: EARS rows have statements but no source PRD references.
- Pass criteria: EARS rows support PRD-to-EARS traceability.
- Evidence output: Checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-UNIT-013

- Title: BDD acceptance example traceability
- Purpose: Verify BDD scenarios remain acceptance examples mapped to EARS.
- Requirement references: REQ-003, REQ-007, DEC-007
- Artifact references: `templates/12-gate1-bdd.template.feature`
- Inputs: BDD template.
- Fixture: EARS statement with one happy path and one edge case.
- Files inspected: `templates/12-gate1-bdd.template.feature`
- Execution method: Required-pattern validation.
- Assertions:
  - Scenarios reference EARS IDs.
  - Scenarios use Given/When/Then acceptance examples.
  - BDD does not introduce behavior absent from PRD/EARS.
- Expected red-state failure: Scenario has Given/When/Then but no EARS mapping.
- Pass criteria: BDD examples are traceable and bounded.
- Evidence output: Checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-UNIT-014

- Title: Implementation constitution coverage
- Purpose: Verify implementation rules are sourced from the project constitution artifact.
- Requirement references: REQ-005, DEC-006
- Artifact references: `templates/implementation-constitution.template.md`
- Inputs: Implementation constitution template.
- Fixture: Project constitution with core engineering rules.
- Files inspected: `templates/implementation-constitution.template.md`
- Execution method: Required-section validation.
- Assertions:
  - SOLID, KISS, YAGNI, TDD, minimal change, security, data integrity, compatibility, and completion evidence sections exist.
  - The template describes implementation rules, not feature workflow policy.
- Expected red-state failure: Implementation rules appear only in `SKILL.md` and not in the constitution template.
- Pass criteria: Future implementation prompts can load effective constitution rules from context artifacts.
- Evidence output: Checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-UNIT-015

- Title: Progressive disclosure read policy
- Purpose: Verify the skill avoids unnecessary full-package reads.
- Requirement references: REQ-012, DEC-008
- Artifact references: `references/context-window-management.md`
- Inputs: Context-window reference.
- Fixture: Resume workflow with status, manifest, baseline, and task prompt available.
- Files inspected: `references/context-window-management.md`
- Execution method: Static policy review.
- Assertions:
  - Status, manifest, summaries, approved baseline, and task-scoped prompts are preferred over full-package reads.
  - Escalation to full context is limited to stale, missing, or conflicting artifacts.
- Expected red-state failure: Reference instructs the AI to read every artifact by default.
- Pass criteria: Read policy is bounded and stage-aware.
- Evidence output: Static validation note.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-006

- Title: Constitution amendment lifecycle
- Purpose: Verify amendment effective timing is explicit.
- Requirement references: DEC-003
- Artifact references: `templates/constitution-amendment.template.md`, `references/constitution-governance.md`
- Inputs: Amendment records.
- Fixture: Governance amendment and architecture-dependent amendment.
- Files inspected: Constitution governance reference and amendment template.
- Execution method: Lifecycle assertion.
- Assertions:
  - Governance amendments may become effective at Gate 2 approval.
  - Architecture-dependent amendments require convergence evidence, explicit adoption approval, or new-work-only scope before becoming effective as current rules.
- Expected red-state failure: Unimplemented architecture-dependent amendment is marked effective immediately.
- Pass criteria: Effective timing and scope are explicit.
- Evidence output: Checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-007

- Title: Traceability control
- Purpose: Verify critical traceability gaps block readiness.
- Requirement references: REQ-007, REQ-008
- Artifact references: `templates/34-final-traceability-matrix.template.md`, `templates/35a-final-readiness-result.template.md`
- Inputs: Traceability matrix and readiness result.
- Fixture: Missing mapping from EARS to Test ID.
- Files inspected: Traceability and readiness templates.
- Execution method: Cross-reference validation.
- Assertions:
  - Source -> PRD -> EARS -> BDD -> Technical Design -> Test ID -> Task -> Evidence -> Convergence path is represented.
  - Missing or conflicting critical mappings fail readiness.
- Expected red-state failure: Readiness passes while a critical mapping is missing.
- Pass criteria: Readiness is blocked or explicitly exceptioned.
- Evidence output: Readiness checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-008

- Title: Final dashboard execution contract
- Purpose: Verify the dashboard is directly usable after readiness passes.
- Requirement references: REQ-009
- Artifact references: `templates/36-final-dashboard.template.html`
- Inputs: Final dashboard template, task files, prompt files, readiness result.
- Fixture: Package with two ordered tasks and two prompts.
- Files inspected: Dashboard template and final task/prompt artifacts.
- Execution method: Static HTML and manual interaction review.
- Assertions:
  - Dashboard shows readiness status.
  - Dashboard lists task order.
  - Each task card has scope, handoff details, prompt textarea, and Copy Prompt button.
  - Dashboard has no mandatory post-dashboard approval gate.
- Expected red-state failure: Dashboard contains summaries but no prompt copy surface.
- Pass criteria: User can start TASK-001 from the dashboard.
- Evidence output: Dashboard validation note or screenshot.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-009

- Title: PRD/EARS/BDD authority split
- Purpose: Verify Gate 1 artifacts have separate authority and do not override each other.
- Requirement references: REQ-003, DEC-007
- Artifact references: `templates/10-gate1-prd.template.md`, `templates/11-gate1-ears.template.md`, `templates/12-gate1-bdd.template.feature`
- Inputs: Gate 1 templates.
- Fixture: Gate 1 package with one requirement and one acceptance scenario.
- Files inspected: Gate 1 templates and generated artifacts.
- Execution method: Authority and traceability review.
- Assertions:
  - PRD owns product direction.
  - EARS owns precise requirements.
  - BDD owns acceptance examples.
  - Downstream artifacts cannot override Gate 1 behavior without change control.
- Expected red-state failure: BDD scenario adds behavior absent from PRD/EARS.
- Pass criteria: Authority split and mapping are explicit.
- Evidence output: Gate 1 checklist result.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-010

- Title: Implementation constitution scope
- Purpose: Verify implementation rules come from effective project constitution artifacts.
- Requirement references: REQ-005, DEC-006
- Artifact references: `templates/implementation-constitution.template.md`, `templates/tdd-prompt.template.md`
- Inputs: Effective constitution and task prompt.
- Fixture: Task prompt generated after constitution approval.
- Files inspected: Constitution template and prompt template.
- Execution method: Prompt scope assertion.
- Assertions:
  - Prompts reference effective implementation constitution when implementation rules are needed.
  - `SKILL.md` remains workflow-level and does not become the implementation-rule SSOT.
- Expected red-state failure: Prompt includes SOLID/TDD rules without referencing project constitution.
- Pass criteria: Implementation rules are sourced from the effective constitution artifact.
- Evidence output: Prompt validation note.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-011

- Title: Progressive disclosure contract
- Purpose: Verify resume and implementation flows use bounded context.
- Requirement references: REQ-012, DEC-008
- Artifact references: `references/context-window-management.md`, `templates/tdd-prompt.template.md`
- Inputs: Status file, manifest, approved baseline, task contract, prompt template.
- Fixture: Final package with multiple tasks.
- Files inspected: Context-window reference and prompt template.
- Execution method: Read-scope assertion.
- Assertions:
  - Resume reads status and manifest before broad artifact inspection.
  - Implementation prompts read task-scoped inputs instead of full packages by default.
  - Full-context reads are reserved for conflicts, stale artifacts, or explicit request.
- Expected red-state failure: Prompt instructs AI to read all generated artifacts for every task.
- Pass criteria: Read scope is bounded and justified.
- Evidence output: Static validation note.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

### TEST-CONTRACT-012

- Title: Vertical capability slices and safe parallel waves
- Purpose: Verify final tasks deliver independently demonstrable outcomes and claimed parallel work has safe dependency and ownership contracts.
- Requirement references: `references/traceability-and-tasking.md`
- Artifact references: `templates/task.template.md`, `templates/31-final-task-index.template.md`, `templates/tdd-prompt.template.md`, `templates/35a-final-readiness-result.template.md`
- Inputs: Final task index, two capability tasks, one optional enabler, and derived prompts.
- Fixture: A feature that crosses UI, API, and persistence layers and has two non-overlapping acceptance scenarios.
- Files inspected: Tasking reference and final task, prompt, index, and readiness templates.
- Execution method: Required-field and task-boundary review.
- Assertions:
  - Each feature task names one cohesive user- or system-observable outcome, a public validation seam, a demo route, and a runnable completion state.
  - Required layers stay in the same capability slice unless a validated enabler or frozen dependency justifies separation.
  - Enablers name the capability tasks they unlock.
  - Parallel tasks record satisfied dependencies, exclusive ownership paths or a frozen shared contract, an integration seam, and an integration owner.
  - Prompts require completion evidence for the whole slice and allow other workers to run independent eligible tasks.
- Expected red-state failure: Tasks are split into database, API, and UI layers that cannot be demonstrated independently, or two tasks claim the same parallel wave with unresolved path ownership.
- Pass criteria: Every task is an independently reviewable capability slice or justified enabler, and every claimed parallel wave has a safe coordination contract.
- Evidence output: Static contract checklist and generated-package review note.
- Automation: semi-automated
- Owner: spec-package-generator maintainer
- Status: planned

## Final Readiness Validation Guidance

Final readiness validation is recorded in `35a-final-readiness-result.md`, not in the dashboard.

Before rendering `36-final-dashboard.html`, confirm:

- Approved baseline is current.
- Gate 1 and Gate 2 artifacts are approved or explicitly exceptioned.
- Traceability has no unresolved critical gaps.
- Test contracts exist for critical Test IDs, with validation mode recorded.
- Task files include allowed scope, forbidden scope, read-only references, TDD or validation, and completion evidence.
- Feature task files include a cohesive user- or system-observable outcome, public validation seam, demo route, runnable completion state, and independently reviewable evidence.
- Enabler task files include a validated deliverable, exception justification, and named capability tasks unlocked.
- Parallel waves include satisfied dependencies, safe path ownership or frozen shared contracts, integration seams, and integration owners.
- Prompt files are derived from task files and do not redefine behavior.
- Critical UNVERIFIED evidence is either resolved or formally accepted as risk.
- `proposed-context-update.md` has not been applied to current project context before convergence.

If any critical item fails, readiness must fail and dashboard rendering must not claim ready-to-implement status.
