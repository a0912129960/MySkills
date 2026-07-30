# Traceability And Tasking Reference

Use this reference when creating the final package and implementation items.

## Traceability Chain

Source -> PRD -> EARS -> BDD -> technical design -> test ID -> task -> implementation evidence -> convergence

## Task Rules

- Make a feature task one vertical capability slice: a cohesive user- or system-observable outcome that can be implemented, demonstrated, validated, reviewed, and accepted independently.
- Keep all layers required to make that outcome real in the same task when the changes are tightly coupled. Crossing UI, API, domain, persistence, or integration layers is expected and is not by itself a reason to split.
- Do not create horizontal tasks such as "add database fields", "build API", and "wire UI" when none produces a usable or observable capability alone.
- Split when a task contains multiple independently valuable outcomes, unrelated acceptance bundles, conflicting ownership, or a dependency that can be frozen and validated independently. Do not split solely because of an estimated file count or number of layers.
- Treat estimated file count, major layers, and review effort as planning signals. When a slice is too large for one focused implementation and review cycle, narrow the scenario, actor, operation, happy path, or supported variation while preserving an end-to-end outcome.
- Allow a horizontal enabler only when bootstrap, a shared contract, a migration, or platform work cannot safely belong to the first capability slice. Require a concrete validated deliverable, an exception reason, and the IDs of the capability slices it unlocks.
- Require every feature task to name its observable outcome, public validation seam, demo or inspection route, cohesive acceptance bundle, and vertical-slice compliance.
- Require every task to list primary Test IDs, validation mode, BDD scenarios covered, EARS requirements covered, review focus, allowed-to-modify paths, read-only references, validation contract rows, and completion evidence.
- Each task must declare one validation mode: `automated`, `semi-automated`, or `manual`. Automated and semi-automated tasks require red-state and green-state evidence. Manual tasks do not require red-state evidence, but must define concrete before/after inspection evidence and user-visible pass criteria.
- `31-final-task-index.md` must include the cross-session task review status table. Individual task files define scope and handoff; the task index owns shared accepted/blocked/deferred status.
- For greenfield projects, generate bootstrap tasks before feature behavior tasks when foundational files or tooling do not exist yet. Typical bootstrap tasks include project initialization, package/workspace setup, test runner setup, lint/type-check setup, app shell/routing setup, database tooling setup, and environment configuration.
- Bootstrap tasks may use `manual` or `semi-automated` validation based on file existence, package scripts, configuration checks, or human inspection. Do not require executable red-state test evidence before the test runner exists.

## Parallel Development Rules

- Build a dependency DAG and assign each task to a parallel wave. A task is eligible when its required dependencies are accepted or explicitly deferred with a safe exception.
- Permit tasks in the same wave to run concurrently only when their allowed-to-modify paths do not overlap, or when a frozen shared contract and integration owner make the overlap safe.
- Record exclusive ownership paths, shared read-only contracts, expected integration seam, merge or release order, and integration owner for each concurrent task.
- Prefer contract-first coordination over layer-first task splitting. A shared contract may be an enabler task when it is independently validated and unlocks named consumer/provider capability slices.
- Each worker implements only one selected task. This does not prevent other workers from implementing other eligible, non-overlapping tasks at the same time.
- Do not start a dependent wave until prerequisite tasks are accepted or the task index records an explicit safe deferral.

## Boundary Examples

Avoid this horizontal breakdown:

- TASK-001: add database fields
- TASK-002: add backend endpoint
- TASK-003: add frontend form

None is a complete capability by itself, so review and testing are deferred until all three merge.

Prefer this vertical breakdown:

- TASK-001: a requester submits the minimal happy-path form and can observe the created request; include the required schema, API, UI, and end-to-end validation for that path.
- TASK-002: a requester receives and can correct validation errors; include only the cross-layer changes and tests required for that observable behavior.
- TASK-003: an approver views and approves a submitted request; include its own observable outcome and validation route.

If all slices require a new project skeleton or a frozen shared contract, create one validated enabler in an earlier wave, name the slices it unlocks, and keep later capability tasks independently demonstrable.

## Prompt Rules

- Each prompt must be derived from one task.
- Each prompt must say to implement only that task.
- Each prompt must require the AI to stop after the selected task is implemented and report evidence; it must not continue to another task.
- Each prompt must say not to modify read-only projects or future items.
- Each prompt must include the human verification handoff: what command or inspection to run, what evidence to report, and what must be true before starting the next task.
- Each prompt must report changed files, validation evidence, and the human review checklist before handoff.
- A dependent task may start only after its prerequisites are accepted or explicitly deferred with a safe exception in `31-final-task-index.md` or implementation evidence. Independent eligible tasks may run concurrently.
- Each prompt must identify the capability outcome, public validation seam, parallel wave, dependency state, exclusive modify paths, shared contracts, and integration handoff before coding.
- Each prompt must require the AI to identify BDD scenarios, EARS requirements, Test IDs, validation mode, and validation contract rows before coding.
- For automated and semi-automated Test IDs, each prompt must require red-state evidence before production-code changes and green-state evidence after implementation.
- For manual Test IDs, each prompt must require explicit before/after inspection evidence and a user-visible result instead of red-state evidence.
- For bootstrap Test IDs, each prompt must use the bootstrap validation contract and must not invent a test-runner command before that command is created by the task.
