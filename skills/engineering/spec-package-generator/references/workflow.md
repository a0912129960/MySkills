# Workflow Reference

Use this reference as the workflow authority. The user should not need to choose a mode or gate.

## Workflow Authority

- `00-stage-manifest.md` is the order source of truth.
- File numbers are readability hints, not the execution order.
- `00-spec-workflow-status.md` is the resume point.
- `00-context-inventory.md` is the architecture evidence ledger.
- `30-approved-feature-baseline.md` is the approved final-package index.
- Task Execution Manifests own execution routing but never redefine normative
  Task behavior. Derived files such as HTML dashboards and prompts never
  redefine normative Markdown artifacts.

## Pipeline Overview

```text
intake
  -> read 00-spec-workflow-status.md
  -> read 00-stage-manifest.md
  -> preserve source requirement
  -> detect project mode: greenfield or existing
  -> lightweight context scan -> 00-context-inventory.md (missing sources -> durable one-question queue, does not block Gate 1)
  -> durable grilling + flow-sketch drafting -> persist and resolve one business decision at a time while updating the draft
  -> after critical business decisions are resolved -> user confirms/revises 09-gate1-flow-sketch.md and the draft user-flow diagram
  -> Gate 1: 10-gate1-prd.md + 11-gate1-ears.md + 12-gate1-bdd.feature + 13-gate1-review.html + optional gate1-checklist.md + user-flow diagram
  -> Gate 1 confirmation
  -> existing mode: deep architecture verification
  -> greenfield mode: planned architecture and schema design confirmation
  -> durable grilling + solution-sketch drafting -> persist and resolve one solution decision at a time while updating the draft
  -> after critical solution decisions are resolved -> user confirms/revises 19-gate2-solution-sketch.md and draft api-flow/cross-project diagrams
  -> Gate 2: 20-gate2-project-impact.md + 21-gate2-technical-design.md + 22-gate2-constitution-compliance.md + 24-gate2-test-strategy.md + proposed-context-update.md + 25-gate2-review.html + optional gate2-checklist.md + api-flow/cross-project diagrams
  -> Gate 2 confirmation
  -> task planning: 30-approved-feature-baseline.md + 31-final-task-index.md + tasks
  -> Task Plan Gate: 32-task-plan-review.md -> user confirms/revises Task boundaries
  -> execution package: one YAML Manifest + minimal implement-spec-task prompt per Task + traceability + analysis + readiness + dashboard
  -> optional post-implementation convergence after implementation evidence: implementation-evidence.md + 40-convergence-report.md + verified-context-update.md
```

Gate 1 owns WHAT. Gate 2 owns HOW. Optional post-implementation convergence owns what was actually implemented.

## Default Entry

When the user says something like "read this file and generate the spec", start the default intake-to-Gate-1 flow.

The agent should:

- Read the requirement file or pasted requirement.
- If the source is a wish list, loose idea list, or discussion notes, break it
  down in `00-source-requirement.md` before drafting Gate 1: map each wish item
  to an inferred goal, user scenario, ambiguity or gap, suggested assumption,
  and canonical Question/Decision ID references.
- Detect project mode and record it in `00-spec-workflow-status.md` and `00-context-inventory.md`: use `greenfield` when the project or feature has no existing implementation sources to verify; use `existing` when relevant code, contracts, schemas, or docs already exist.
- Infer the feature name, or ask for it if unclear.
- Create or update `00-spec-workflow-status.md`.
- Read `00-stage-manifest.md` if it exists, then follow the manifest order.
- Read `.ai-dev/context/project-context.md` first if it exists for lightweight scan only, then create `00-context-inventory.md`.
- In existing mode, queue any missing architecture-source questions immediately;
  they do not block Gate 1 and must not become active until post-Gate-1
  architecture grounding. In greenfield mode, queue missing technology or
  planned architecture decisions for post-Gate-1 design confirmation unless a
  choice changes user-visible Gate 1 behavior.
- Create or update `14-decision-log.md` and `15-open-questions.md`, then ask only
  critical business decisions that block a useful business draft. Use the
  durable grilling protocol as the durable one-question loop: persist and ask
  exactly one question, wait, and record and apply its answer before selecting
  another.
- Use the Gate 1 clarification matrix from `references/question-and-decision-governance.md` to classify extracted facts, assumptions, and blocking questions.
- Produce and revise `09-gate1-flow-sketch.md` during clarification when the
  flow is not trivial, and always produce it for greenfield projects. The draft
  must include the scenario list, operation flow, user-flow diagram, canonical
  unresolved-question references, and material-assumption decision audit.
  Resolve all critical business decisions first, mark Gate 1 clarification
  complete, then stop for exactly one sketch confirmation or revision request
  before full Gate 1 review generation.
- When stopping for the sketch micro-gate, include the review artifact path, Mermaid source path, SVG path when available, and a concise diagram preview or summary in the chat response.
- Generate the Gate 1 business artifacts and `diagrams/user-flow.mmd`; render `diagrams/user-flow.svg` when a renderer is available.
- Ask the user to confirm or revise the business draft.
- Include the Gate 1 review artifact path, diagram paths, and exact confirmation points in the chat response.
- Stop before architecture verification output and Gate 2 artifacts.

Do not require the user to mention any mode name.

## Gate 1 Review Mode

Gate 1 is the default for normal feature specification requests.

Required behavior:

- Save the source requirement.
- For wish lists or loose notes, convert the raw wishes into inferred goals,
  user scenarios, ambiguities, assumptions, and canonical Question/Decision ID
  references in `00-source-requirement.md`.
- Detect and record project mode as `greenfield` or `existing`.
- Create or update the workflow status file.
- Create the stage manifest if it does not exist.
- Complete the lightweight context scan before Gate 1 artifacts: read
  `.ai-dev/context/project-context.md` if it exists, then create
  `00-context-inventory.md`. In existing mode, queue missing architecture
  sources for post-Gate-1 architecture grounding. In greenfield mode, queue
  technology or planned architecture decisions for post-Gate-1 design
  confirmation unless they change user-visible Gate 1 behavior.
- Use the Gate 1 clarification matrix to classify extracted facts, assumptions, and blocking questions.
- During Gate 1 clarification, create and revise
  `09-gate1-flow-sketch.md` and draft `diagrams/user-flow.mmd` when the flow is
  not trivial or project mode is greenfield. Reference unresolved questions
  from `15-open-questions.md` without copying their mutable fields. After all
  critical business decisions are resolved, move to `gate1-flow-sketch` and
  wait for one user confirmation or correction.
- Present the sketch and diagram paths in chat when waiting for confirmation.
- Create the business review artifacts only.
- Keep Gate 1 product-only: no architecture verification, no project-context write-back, no constitution loading, no implementation guidance.
- Ensure every core scenario is extracted, safely assumed, or covered by a blocking question before Gate 1 approval.
- Ensure every critical EARS requirement has BDD coverage or an explicit exception reason.
- Resolve material assumptions individually through the durable one-question
  loop. Present them with their Decision IDs as audit items in the Gate 1
  review; unconfirmed material assumptions block Gate 1 approval.
- Treat `13-gate1-review.html` as the primary and only required human review surface for final Gate 1 confirmation; Markdown and feature files remain authoritative details linked from it.
- Ask the user to confirm or revise the draft.

Gate 1 artifacts are:

- `09-gate1-flow-sketch.md` when the flow is not trivial or project mode is greenfield
- `10-gate1-prd.md`
- `11-gate1-ears.md`
- `12-gate1-bdd.feature`
- `13-gate1-review.html`
- `gate1-checklist.md` if created
- `diagrams/user-flow.mmd`

## Deep Architecture Verification

Runs only after Gate 1 is confirmed and project mode is `existing`.

Required behavior:

- Re-check carried-over facts from `.ai-dev/context/project-context.md` when present.
- Read the actual code entry points, contracts, or documents for the in-scope systems.
- Directory names alone are not verification.
- If any source is `missing` or `user-will-provide`, persist every source gap
  in the inventory and question register, set the workflow to `blocked` and
  `waiting-for-user`, activate only the highest-impact resolvable Architecture
  Source question, and wait. Keep remaining source gaps as Question ID
  references; do not present a batch request.
- Never invent architecture. If the user explicitly accepts a gap, mark it `accepted-unverified` and tag the related Gate 2 content `UNVERIFIED`.
- Record verified facts, source paths, statuses, and risk levels in `00-context-inventory.md`.
- Gate 2 derives `proposed-context-update.md` from verified inventory facts and the approved solution review; do not create or update it as the primary verification ledger.
- Gate 2 must not update current project context directly.

## Greenfield Architecture Design Confirmation

Runs only after Gate 1 is confirmed and project mode is `greenfield`.

Required behavior:

- Do not block on missing code, schemas, entry points, or test runners that do not exist yet.
- Convert the confirmed Gate 1 behavior into planned architecture facts in `00-context-inventory.md` with status `planned` or `confirmed-design`.
- Draft the intended project structure, package boundaries, API routes or contracts, database or storage model, auth approach, test runner, build tooling, deployment target, and integration boundaries when applicable.
- Resolve critical technology and architecture choices through the durable
  one-question loop when more than one reasonable greenfield choice exists.
- Treat user-confirmed planned architecture as the Gate 2 grounding source. Label it `confirmed-design`, not `verified`.
- Use `proposed-context-update.md` to record reusable planned architecture facts, but do not write `.ai-dev/context/project-context.md` before convergence.
- If later implementation evidence contradicts the confirmed design, convergence owns the correction.

## Solution Clarification

Resolve critical solution decisions one at a time using the Gate 2 solution
clarification matrix and durable grilling protocol from
`references/question-and-decision-governance.md`. Cover API contract shape, DB
schema or query approach, integration mechanics, permission/security decisions,
error-code and validation design, logging/audit behavior, release constraints,
contract compatibility only when verified released contracts or active
consumers exist, Test ID coverage, capability-slice boundaries, parallel
ownership seams, and greenfield technology choices when project mode is
`greenfield`.

Prefer deriving answers from verified architecture before asking. If an answer
reveals new blocking technical ambiguity, persist the dependent question and
ask it only after the current answer is recorded and applied. If verification
reveals a conflict with confirmed business behavior, that is a Gate Re-Open
Rule event, not a solution question.

Use the same durable loop automatically for every critical decision. Keep
clarification inside this workflow so its governance artifacts remain the
single resumable decision record.

Before Gate 2 confirmation, `24-gate2-test-strategy.md` must map relevant BDD scenarios to Test IDs and define Test Contract data for automated and semi-automated validation.

## Gate 2 Solution Sketch

Drafting starts during solution clarification after deep architecture
verification or greenfield architecture design confirmation. Final sketch
confirmation runs only after critical solution clarification is complete and
before full Gate 2 artifacts.

Required behavior:

- Create and revise `19-gate2-solution-sketch.md` during solution clarification.
- Create and revise draft `diagrams/api-flow.mmd` during clarification.
- Create and revise draft `diagrams/cross-project-flow.mmd` during
  clarification when multiple projects or systems are involved.
- For greenfield projects, create the solution sketch even when the solution appears simple, because the sketch confirms the planned technical shape before task generation.
- Derive every participant, responsibility, and call from `00-context-inventory.md` entries with status `verified`, `confirmed-design`, or explicitly accepted `UNVERIFIED`.
- Include project responsibility split, provider/consumer direction, key
  solution assumptions, canonical blocking-question references, initial Test ID
  coverage direction, capability-slice boundaries, and parallel ownership
  seams.
- Resolve all critical solution decisions, mark Gate 2 clarification complete,
  then stop and wait for one user confirmation or correction before full Gate 2
  artifact generation.
- Present the solution sketch path, diagram paths, and exact confirmation or correction request in chat when waiting for confirmation.
- Record the sketch state in `00-spec-workflow-status.md` and `00-stage-manifest.md`.

If project mode is `existing` and the solution is trivial with no API, integration, cross-project, persistence, permission, or test-contract decision, record the sketch as skipped with a reason. Do not skip the sketch merely because the diagrams are simple. Do not skip the Gate 2 solution sketch in greenfield mode.

## Gate 2 Review Mode

Starts only after Gate 1 confirmation and completed architecture verification for existing projects, or confirmed architecture design for greenfield projects.

Required behavior:

- Create or confirm `19-gate2-solution-sketch.md` before full Gate 2 generation.
- Create `20-gate2-project-impact.md`, `21-gate2-technical-design.md`, `22-gate2-constitution-compliance.md`, `24-gate2-test-strategy.md`, `proposed-context-update.md`, and `25-gate2-review.html` from verified context or confirmed greenfield design.
- Create `gate2-checklist.md` when a derived solution-review checklist is needed.
- Create `diagrams/api-flow.mmd` and `diagrams/cross-project-flow.mmd` when applicable; render SVG when a renderer is available.
- Every component in Gate 2 artifacts must be traceable to a `verified`, `confirmed-design`, or explicitly accepted `UNVERIFIED` inventory entry.
- Treat `25-gate2-review.html` as the primary and only required human review surface for final Gate 2 confirmation; Markdown files remain authoritative details linked from it.
- Ask the user to confirm or revise the solution review.
- Include the Gate 2 review artifact path, diagram paths, and exact confirmation points in the chat response.
- Stop before final AI development breakdown.

Do not generate Task files until the Gate 2 review is confirmed or the user
explicitly says to proceed with assumptions. Do not generate execution
Manifests or implementation prompts until the Task Plan Gate is
human-confirmed.

## Gate Re-Open Rule

If, after a gate is confirmed, new verified facts contradict confirmed content:

1. Stop producing downstream artifacts that depend on the contradicted content.
2. Raise the conflict to the user immediately as a blocking question.
3. Move the stage back to `business-feedback` or `solution-feedback` and record the re-open event in the status file.
4. Revise only the affected sections, mark them as revised, and ask the user to re-confirm the changed parts only.
5. Update any downstream artifacts already generated from the old content.

## Finalize Mode

Finalize mode starts only after the Gate 2 solution review is confirmed or the user explicitly says to proceed with assumptions.

Required behavior:

- Read `00-spec-workflow-status.md`, `00-stage-manifest.md`, and `00-context-inventory.md` before generating final package files.
- Use `30-approved-feature-baseline.md` as the approved summary of the confirmed gates.
- Break the feature into human-reviewable vertical capability slices. Each feature task must produce one cohesive user- or system-observable outcome with an end-to-end validation route and leave the scoped system in a runnable state.
- Keep the layers needed for that outcome in the same task unless a contract-frozen dependency or unavoidable enabler provides a safer boundary. Do not create separate database, backend, and frontend tasks solely because they touch different layers.
- Use horizontal enabler tasks only for unavoidable bootstrap, contract, migration, or platform prerequisites. Name the capability slices they unlock and give the enabler its own concrete validation evidence.
- Arrange tasks into dependency-aware parallel waves as planning metadata.
  Record exclusive modify paths, shared contracts, integration seams, and an
  integration owner without executing multiple formal Tasks in one
  first-version invocation.
- For greenfield projects, make the first bootstrap task invoke `project-rules-init` with the user-confirmed Gate 2 architecture. Create any remaining project skeleton, package manager, test runner, linting, routing, database tooling, or app-shell bootstrap tasks before feature behavior tasks.
- Create `30-approved-feature-baseline.md`, `31-final-task-index.md`, and the
  Task files first.
- Add machine-checkable vertical-slice fields, dependency and parallel-wave fields, BDD coverage, EARS coverage, required Test IDs, validation mode, and validation contract rows to each task.
- Create `32-task-plan-review.md`, present the Task Plan Gate, and stop. Require
  the human to confirm each Reviewable Capability or Shared Enabler,
  dependencies, public test boundary, and review scope.
- Keep Task-only corrections in the Task Plan. Reopen Gate 1 for behavior gaps
  and Gate 2 for solution gaps.
- After confirmation, generate one YAML
  `manifests/TASK-xxx.execution.yaml` per Task. Make the Manifest own loading,
  dependency eligibility, allowed paths, Skill Plan, validation, evidence
  destinations, and freshness. Digest-pin approved normative artifacts and
  require current project rules to be re-read during Execution Preflight.
- Implementation review and test handoff is distributed across `24-gate2-test-strategy.md`, `34-final-traceability-matrix.md`, `35-final-analysis-report.md`, `35a-final-readiness-result.md`, and `tasks/TASK-xxx.md`.
- Prompts are per-task files generated from the Task Manifest using
  `templates/tdd-prompt.template.md`. Each prompt contains only the
  `$implement-spec-task <manifest-path>` invocation and must not duplicate the
  execution contract.
- Create `37-implementation-package-approval.md` only when the team explicitly requires a named approval record.
- Create the standalone HTML dashboard with readiness result.
- Treat `31-final-task-index.md` as the Markdown source of truth for per-task review status. The dashboard may store local status and export updates, but shared status must be reconciled back to Markdown.
- The dashboard must show dependency eligibility and parallel waves. In the
  first version, one invocation implements one formal Task, may coordinate
  approved same-Task Work Units, and stops at human review without starting the
  next Task.

## Optional Post-Implementation Convergence

Optional post-implementation convergence runs after implementation evidence is available. It is not required for the final specification package to be ready for implementation.

Required behavior:

- Collect or update `implementation-evidence.md`.
- Compare implementation evidence against the approved baseline.
- Create `40-convergence-report.md`.
- Write `verified-context-update.md` only when evidence supports the update.
- Update `.ai-dev/context/project-context.md` only after verified convergence.
- Do not promote any `proposed-context-update.md` fact unless the convergence report links it to implementation evidence.

## Spec Change Request Revision

Run only after a human invokes
`$spec-package-generator <feature-package-path> --revise-from <request-path>`.

1. Read the Spec Change Request, linked code evidence, Partial Change State,
   workflow status, stage manifest, and affected normative artifacts.
2. Reopen the declared Return Level: Gate 1 for behavior, Gate 2 for solution
   or validation design, or Task Plan Gate for Task boundary/task-only
   validation.
3. Never modify, revert, stage, or commit production code. The request may
   reference either committed evidence or uncommitted review changes.
4. Revise only affected specification content and mark every dependent
   artifact stale according to invalidation rules.
5. Ask the human to re-confirm the changed gate content.
6. After confirmation, generate a new Task Execution Manifest version and
   digests. Preserve old append-only Execution Records and do not resume
   implementation automatically.

## One-Shot Mode

One-shot mode is not the default. Use it only when the user explicitly
pre-approves proceeding through Gate 1 and Gate 2 with documented assumptions.

Rules:

- The context scan and existing architecture verification or greenfield design confirmation still run internally; project-context write-back happens only through optional post-implementation convergence when evidence supports it.
- One-shot mode does not stop at Gate 1 or Gate 2 confirmation points. It is allowed only after the user explicitly requests one-pass generation or explicitly approves documented assumptions.
- One-shot mode still creates `09-gate1-flow-sketch.md` and `19-gate2-solution-sketch.md` when applicable, but marks their human confirmation as pre-approved by the user's one-shot instruction and documented assumptions.
- One-shot mode does not pre-approve or skip the Task Plan Gate. Stop after
  generating the Task Plan and wait for human confirmation before Manifests,
  prompts, readiness, or dashboard generation.
- Resolve any critical business or solution decisions through the durable
  one-question loop. One-shot pre-approval permits documented assumptions, but
  it does not permit batching unresolved human decisions.
- Generate through the Task Plan only after resolving high-impact ambiguity or
  documenting assumptions, with `UNVERIFIED` tags where the user accepted
  gaps.
- Keep generated development items cohesive and reviewable as vertical capability slices; preserve dependency-aware parallel waves.

## Stop Conditions

Stop and ask the user when:

- No clear feature name can be inferred.
- The requirement conflicts with itself.
- A high-impact business rule is missing.
- In existing mode, an architecture source for an in-scope system is unknown or unread and a Gate 2 artifact would need it.
- In greenfield mode, a blocking technology or architecture choice is unresolved and Gate 2 would need it.
- A flow or diagram would need a component that is not in the context inventory.
- A non-trivial Gate 1 flow sketch or Gate 2 solution sketch has not been confirmed, skipped with a reason, or explicitly pre-approved by one-shot instructions.
- Verified facts contradict confirmed gate content.
- The Gate 1 draft or Gate 2 review has not been confirmed.
- The requested output would require modifying source code.

Do not stop only because SVG rendering is unavailable. Keep the authoritative `.mmd` files and add the standard rendering-skipped note from `references/mermaid-rendering.md`.

## Resume Behavior

When a feature folder already exists, read `00-spec-workflow-status.md` first, then `00-stage-manifest.md`, then `00-context-inventory.md`, and continue from `Next AI Action`.

If `00-stage-manifest.md` is missing but generated artifacts exist, recreate it from the optimized artifacts that are present before changing any stage artifact.

If the user asks to continue but does not identify the feature name:

- Resume automatically only when `.ai-dev/features/` contains exactly one feature folder.
- If multiple feature folders exist, list them and ask the user which one to continue.
- If no feature folder exists, ask for the requirement source or feature name.

When the user provides a previously missing architecture source:

- Read and verify it.
- Update the context inventory and the status file.
- Record verified facts in `00-context-inventory.md`; derive proposed context updates during Gate 2 and promote them to `.ai-dev/context/project-context.md` only after verified convergence.
- Revise any Gate 2 artifacts affected by the new facts and ask the user to re-confirm the changed parts.

Do not restart from the source requirement unless:

- The status file is missing.
- The user asks to restart.
- The existing files are inconsistent and cannot be reconciled.

When the status file is missing but other generated files exist, recreate it from the optimized files that are present and ask only for missing high-impact information.
