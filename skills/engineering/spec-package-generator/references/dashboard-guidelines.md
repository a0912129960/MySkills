# Dashboard Guidelines

Use this reference before generating `36-final-dashboard.html`.

Start from `templates/36-final-dashboard.template.html`: keep its embedded CSS and JavaScript layout and fill in the placeholders for header metadata, readiness, Task Plan approval, Manifest path, dependency and parallel waves, task scope, capability outcome, ownership, task handoff details, traceability, risks, and copyable executor invocations.

Dashboard validation happens after `35a-final-readiness-result.md` and must not be a prerequisite for readiness itself. The readiness result verifies that dashboard source inputs are ready to render; the rendered dashboard then displays that persisted readiness result.

## Requirements

The dashboard must:

- Be a standalone HTML file.
- Use embedded CSS.
- Use embedded JavaScript.
- Avoid external CDN and network dependencies.
- Open directly in a browser from the filesystem.
- Show all AI development items.
- Include copyable `$implement-spec-task <manifest-path>` invocations.
- Surface the readiness result from `35a-final-readiness-result.md`.

## Required Sections

- Header with feature name, generated time, spec status, and item count
- Dependency-aware parallel-wave summary and task eligibility
- Item cards or accordion sections
- Required input files for each item
- Allowed-to-modify paths
- Read-only paths
- BDD scenario coverage for each item
- Validation mode and required Test IDs for each item
- Evidence requirements, including red-state and green-state evidence when applicable, and manual inspection evidence for manual Test IDs
- Per-task review status controls for `not-started`,
  `awaiting-preflight-approval`, `in-progress`, `ready-for-review`,
  `changes-requested`, `accepted`, `re-slice-required`,
  `spec-revision-required`, `blocked`, and `deferred`
- Local persistence for per-task review status using `localStorage`, keyed by feature name and task ID
- A visible task status summary covering every lifecycle state plus remaining
  count
- An export control that produces Markdown status rows suitable for `31-final-task-index.md` or implementation evidence
- Acceptance criteria
- Suggested test cases
- User-observable result and how to see the task working
- Capability outcome, public validation seam, exclusive ownership paths, shared contracts, and integration handoff
- Ready-to-copy prompt in a `textarea`
- Copy Prompt button for each item
- Traceability summary
- Residual risks

## Data Source

Use the Markdown files as the source of truth:

- `30-approved-feature-baseline.md`
- `31-final-task-index.md`
- `32-task-plan-review.md`
- `34-final-traceability-matrix.md`
- `35-final-analysis-report.md`
- `35a-final-readiness-result.md`
- `tasks/TASK-xxx.md`
- `manifests/TASK-xxx.execution.yaml`
- `prompts/TASK-xxx.prompt.md`

Do not make the dashboard the only place where important instructions exist.

Task handoff details such as input files, allowed paths, read-only references, capability outcome, public validation seam, parallel wave, dependency state, ownership, integration handoff, BDD coverage, required Test IDs, validation mode, evidence requirements, acceptance criteria, and suggested test cases are derived from `tasks/TASK-xxx.md` and related final package artifacts. The dashboard displays them for execution convenience; it does not define them.

`31-final-task-index.md` is the Markdown source of truth for planned per-task review status across sessions. Dashboard review status stored in `localStorage` is a human convenience layer only. Export dashboard status and reconcile it back to `31-final-task-index.md` or `implementation-evidence.md` for shared review state.

## Task Execution Loop

The dashboard should make the dependency-aware loop obvious:

1. Select one Task whose dependencies are human-accepted.
2. Copy its Manifest-backed executor invocation.
3. Approve Execution Preflight before production edits; same-Task Work Units
   may then run within exclusive ownership.
4. Review integrated capability evidence after `ready-for-review`.
5. Only the human sets `accepted`; do not start the next Task automatically.

## HTML Boundaries

- The dashboard is a human review and execution surface only.
- It must not replace the Markdown source files.
- It must not become the source of truth for task scope or validation rules.

## UI Constraints

- Keep the layout readable on desktop and mobile.
- Do not require a build step.
- Do not include external fonts, frameworks, or icons.
- Keep item details scannable.
- Use plain HTML controls for copyable prompts.
