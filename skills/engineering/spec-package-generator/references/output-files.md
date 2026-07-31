# Output Files Reference

Use this reference to keep generated files consistent.

File numbers follow generation order only as a readability hint. `00-stage-manifest.md` controls the actual order.

## Output Stages

Gate 1 stage:

- `00-source-requirement.md`
- `00-spec-workflow-status.md`
- `00-stage-manifest.md`
- `00-context-inventory.md`
- `14-decision-log.md`; required durable cross-stage decision memory
- `15-open-questions.md`; required durable cross-stage question queue
- `09-gate1-flow-sketch.md` when the flow is not trivial or project mode is greenfield; early micro-gate artifact before full Gate 1 generation
- `10-gate1-prd.md`
- `11-gate1-ears.md`
- `12-gate1-bdd.feature`
- `13-gate1-review.html`
- `gate1-checklist.md` if created; optional derived Gate 1 review checklist
- `diagrams/user-flow.mmd`
- `diagrams/user-flow.svg` when a renderer is available

Gate 2 stage:

- `19-gate2-solution-sketch.md`; early micro-gate artifact before full Gate 2 generation
- `20-gate2-project-impact.md`
- `21-gate2-technical-design.md`
- `22-gate2-constitution-compliance.md`
- `24-gate2-test-strategy.md`
- `proposed-context-update.md`
- `25-gate2-review.html`
- `gate2-checklist.md` if created; optional derived Gate 2 review checklist
- `diagrams/api-flow.mmd`
- `diagrams/api-flow.svg` when a renderer is available
- `diagrams/cross-project-flow.mmd` when applicable
- `diagrams/cross-project-flow.svg` when applicable and a renderer is available

Final package stage:

- `30-approved-feature-baseline.md`
- `31-final-task-index.md`
- `tasks/TASK-xxx.md`
- `32-task-plan-review.md`
- `manifests/TASK-xxx.execution.yaml`
- `prompts/TASK-xxx.prompt.md`
- `34-final-traceability-matrix.md`
- `35-final-analysis-report.md`
- `35a-final-readiness-result.md`
- `36-final-dashboard.html`
- `37-implementation-package-approval.md` if the team explicitly requires a named approval record

Optional post-implementation convergence stage:

- `implementation-evidence.md`
- `40-convergence-report.md`
- `verified-context-update.md`
- `.ai-dev/context/project-context.md` only when verified convergence supports reusable project-context updates

Do not generate full Gate 2 files until Gate 1 is confirmed, all in-scope existing systems are `verified` or explicitly accepted with inventory status `accepted-unverified`, all in-scope greenfield components are `confirmed-design`, and the Gate 2 solution sketch is confirmed or skipped with a reason. Do not generate Task planning files until the Gate 2 review is confirmed or the user explicitly says to proceed with assumptions. Do not generate execution Manifests or prompts until the Task Plan Gate is human-confirmed.

## `00-source-requirement.md`

Store the raw user input or a reference to the local source file.

Include:

- Source path, if any
- Raw pasted content, if any
- Date generated
- Notes about missing source material

## `00-spec-workflow-status.md`

Track the resumable workflow state.

Include:

- Current stage
- Current status
- Waiting-for-user flag
- Next AI Action
- Progress checklist
- Pending user questions
- Answered questions and decisions
- Accepted assumptions
- Context gaps summary
- Generated files
- Files still needed
- Stale or superseded artifacts
- Diagram render status
- Last update summary

Read this file first when resuming an existing feature package.

## `00-stage-manifest.md`

Define the exact artifact order for the current package.

Include:

- Logical stage order
- Artifact ownership
- Artifact invalidation links
- Resume stage

Use the manifest to determine what to read next. Do not sort by file name alone.

## `00-context-inventory.md`

Prevent invented architecture.

Record every existing system or planned greenfield component in the requirement's flows, its architecture source or planned design source, its status (`verified` / `missing` / `user-will-provide` / `accepted-unverified` / `planned` / `confirmed-design`), risk level, and the key facts or planned decisions. Include systems whose behavior is being removed. Record what carried over from `.ai-dev/context/project-context.md` and track proposed or verified context updates without writing directly to project context.

Rules:

- No flow, diagram, or analysis may name a component absent from this inventory.
- Existing-source gaps do not block Gate 1; they block Gate 2 until resolved or explicitly accepted by the user with status `accepted-unverified`. Greenfield planned components block Gate 2 until confirmed with status `confirmed-design`.
- Gate 2 content for accepted gaps must still be tagged `UNVERIFIED`.
- Update it whenever a source is verified or provided by the user.

## `09-gate1-flow-sketch.md`

Use as the early human confirmation micro-gate when the business flow is not trivial. Always use it in greenfield mode.

Include:

- Draft scenario list
- Draft operation flow
- Draft state model when relevant
- Draft `diagrams/user-flow.mmd` status
- Critical questions and material assumptions
- Human correction notes

Stop after creating it and wait for user confirmation or revision before producing full Gate 1 PRD/EARS/BDD/review artifacts.

## `.ai-dev/context/project-context.md`

Accumulate reusable project-level architecture facts across features: systems and repos, entry points, integration mechanisms, conventions, response formats, and last-verified date.

Rules:

- Created or updated after convergence when `verified-context-update.md` is supported by implementation evidence.
- Later features read it during the lightweight context scan and only re-check recorded entry points instead of re-discovering.
- Project-level facts only. Feature-specific decisions stay in the feature folder.

## `10-gate1-prd.md`

Use for product direction, scope, user scenarios, and business rules at Gate 1.

Do not include API call flows, cross-project diagrams, or technical analysis.

## `11-gate1-ears.md`

Use for precise, testable requirement statements derived from the PRD.

EARS statements must be traceable to PRD decisions and suitable for BDD derivation.

## `12-gate1-bdd.feature`

Use for Given/When/Then acceptance scenarios derived from EARS.

Each scenario should be independently testable.

## `13-gate1-review.html`

Use as the primary and only required human review surface for final Gate 1 confirmation.

This file must not redefine behavior.

It must link to the authoritative Markdown and feature files and include the exact human confirmation points, open questions, material assumptions, and diagram links needed for approval.

## `14-decision-log.md`

Required cross-stage governance log for material decisions, answers, and
affected artifacts. Append a resolved ruling before asking the next decision
question.

## `15-open-questions.md`

Required cross-stage governance register and interview queue for unresolved
questions, dependencies, status, recommendations, answers, and decision links.
Only one row may be the active user-facing question at a time; the status file
names that Question ID.

## `gate1-checklist.md`

Optional derived Gate 1 review checklist for PRD, EARS, BDD, and review-surface completeness.

This file must not redefine behavior.

## `19-gate2-solution-sketch.md`

Use as the early human confirmation micro-gate after existing architecture verification or greenfield architecture design confirmation and before full Gate 2 generation.

Include:

- Verified context summary used for the sketch
- Draft API flow
- Draft cross-project flow when applicable
- Project responsibility split
- Provider / consumer direction
- Key solution assumptions
- Blocking solution questions
- Initial Test ID coverage direction
- Initial vertical capability-slice boundaries
- Initial dependency waves, parallel ownership, and integration seams
- Human correction notes

Stop after creating it and wait for user confirmation or revision before producing full Gate 2 artifacts. If project mode is `existing` and the solution is trivial, record the skip reason in the status file and manifest. Do not skip this sketch in greenfield mode.

## `20-gate2-project-impact.md`

Gate 2 review document. Requires existing architecture verification or greenfield architecture design confirmation first and user confirmation before finalize.

The projects-involved list must be derived from the context inventory, never from the requirement text alone.

Use even for single-project features.

For single-project features, state:

```text
Single-project feature. No cross-project implementation required.
```

## `21-gate2-technical-design.md`

Gate 2 review document. Requires existing architecture verification or greenfield architecture design confirmation first and user confirmation before finalize.

Translate the confirmed business spec into implementation guidance without coding.

Prefer verified project patterns found during verification, or approved greenfield architecture decisions when no existing pattern applies. List likely files to inspect and modify, but do not edit them. Every named component must trace to a `verified` or `confirmed-design` inventory entry.

## `22-gate2-constitution-compliance.md`

Gate 2 review document for constitution loading, governance, effective timing, and amendment status.

## `24-gate2-test-strategy.md`

Gate 2 test planning document.

Map approved behavior to stable test IDs and executable test contracts.

## `25-gate2-review.html`

Use as the primary and only required human review surface for final Gate 2 confirmation.

This file must not redefine behavior.

It must link to the authoritative Gate 2 Markdown files and include the exact solution confirmation points, open questions, accepted `UNVERIFIED` items, test strategy status, and diagram links needed for approval.

## `gate2-checklist.md`

Optional derived Gate 2 review checklist for project impact, technical design, constitution compliance, test strategy, and review-surface completeness.

This file must not redefine behavior.

## `30-approved-feature-baseline.md`

Use as the final approved summary of the confirmed Gate 1 and Gate 2 content.

This file is the final-package index and approval anchor.

## `31-final-task-index.md`

Split feature work into cohesive, human-reviewable vertical capability slices. A feature task should leave one user- or system-observable outcome working through a defined validation route, even when it must cross frontend, backend, domain, persistence, or integration layers.

Do not mix unrelated outcomes in one item. Do not split tightly coupled work by technical layer merely to reduce the estimated file or layer count. Record unavoidable horizontal prerequisites as validated enablers that name the capability slices they unlock.

Define the dependency DAG, parallel waves, exclusive ownership paths, shared contracts, integration seams, and integration owner. Only claim tasks can run in parallel when dependencies and ownership make concurrent work safe.

This file is the Markdown source of truth for per-task review status across sessions. Include the complete executor lifecycle from `not-started` through preflight, implementation, review, acceptance, revision, and blocked states. Only a human may set `accepted`.

## `tasks/TASK-xxx.md`

Define the scope, observable outcome or validated enabler, dependencies, parallel ownership, acceptance criteria, public validation seam, and completion evidence for one capability slice or justified enabler.

## `32-task-plan-review.md`

Record the Task Plan Gate. The human confirms each Task boundary, Shared
Enabler, dependency, public test boundary, and expected review scope before
execution-routing artifacts exist. Task-only corrections remain here; behavior
gaps reopen Gate 1 and solution gaps reopen Gate 2.

## `manifests/TASK-xxx.execution.yaml`

Provide the only supported input to `implement-spec-task`. Bind exactly one
formal Task to its human Task Plan approval, readiness result, SHA-256-pinned
normative artifacts, accepted dependencies, allowed paths, Skill Plan,
validation contract, evidence destinations, and freshness policy. Current
project rules are re-read at Execution Preflight rather than digest-frozen.

## `prompts/TASK-xxx.prompt.md`

Create a ready-to-copy `$implement-spec-task <manifest-path>` invocation. Do
not restate Task behavior or execution rules in this derived prompt.

## `34-final-traceability-matrix.md`

Use as the mandatory derived control artifact for traceability.

It maps source -> PRD -> EARS -> BDD -> technical design -> test ID -> task -> implementation evidence -> convergence.

## `35-final-analysis-report.md`

Use as a read-only consistency report before readiness is declared.

## `35a-final-readiness-result.md`

Persist the machine-readiness decision before the dashboard is rendered.

## `36-final-dashboard.html`

Create a standalone human-readable dashboard with embedded CSS and JavaScript only.

The dashboard must not replace the Markdown source files.

## `37-implementation-package-approval.md`

Optional approval record for teams that require a named implementation package approval artifact.

This file must not create a mandatory post-dashboard approval gate.

## `implementation-evidence.md`

Index append-only Task Execution Records and summarize current Task status for
optional post-implementation convergence. Do not use it as the detailed mutable
session log.

## `40-convergence-report.md`

Use after implementation evidence exists to compare the package with reality.

## Diagram Files

Mermaid source files by stage:

- Gate 1: `diagrams/user-flow.mmd`
- Gate 2 sketch and review: `diagrams/api-flow.mmd`
- Gate 2 when multi-project: `diagrams/cross-project-flow.mmd`

Every participant and node in Gate 2 diagrams must be traceable to a `verified` or `confirmed-design` context inventory entry, using real component names or approved planned component names; user-accepted exceptions are labeled `UNVERIFIED`.

SVG review files are required whenever Mermaid rendering is available:

- `diagrams/user-flow.svg`
- `diagrams/api-flow.svg`
- `diagrams/cross-project-flow.svg` when applicable

If the centrally managed renderer is unavailable or rendering fails, keep the
authoritative `.mmd` files and document the status in the corresponding review
document. Dependency installation remains a MySkills installer responsibility.
