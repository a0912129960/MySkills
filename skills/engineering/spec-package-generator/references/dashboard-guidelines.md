# Dashboard Guidelines

Use this reference before generating `36-final-dashboard.html`.

Start from `templates/36-final-dashboard.template.html`: keep its embedded CSS and JavaScript layout and fill in the placeholders for header metadata, readiness, task order, task scope, task handoff details, traceability, risks, and copyable prompts.

Dashboard validation happens after `35a-final-readiness-result.md` and must not be a prerequisite for readiness itself. The readiness result verifies that dashboard source inputs are ready to render; the rendered dashboard then displays that persisted readiness result.

## Requirements

The dashboard must:

- Be a standalone HTML file.
- Use embedded CSS.
- Use embedded JavaScript.
- Avoid external CDN and network dependencies.
- Open directly in a browser from the filesystem.
- Show all AI development items.
- Include copyable prompts.
- Surface the readiness result from `35a-final-readiness-result.md`.

## Required Sections

- Header with feature name, generated time, spec status, and item count
- Summary table with recommended implementation order
- Item cards or accordion sections
- Required input files for each item
- Allowed-to-modify paths
- Read-only paths
- BDD scenario coverage for each item
- Validation mode and required Test IDs for each item
- Evidence requirements, including red-state and green-state evidence when applicable, and manual inspection evidence for manual Test IDs
- Per-task review status controls: `not-started`, `in-progress`, `ready-for-review`, `accepted`, `blocked`, and `deferred`
- Local persistence for per-task review status using `localStorage`, keyed by feature name and task ID
- A visible task status summary showing accepted, blocked, ready-for-review, in-progress, not-started, deferred, and remaining counts
- An export control that produces Markdown status rows suitable for `31-final-task-index.md` or implementation evidence
- Acceptance criteria
- Suggested test cases
- User-observable result and how to see the task working
- Ready-to-copy prompt in a `textarea`
- Copy Prompt button for each item
- Traceability summary
- Residual risks

## Data Source

Use the Markdown files as the source of truth:

- `30-approved-feature-baseline.md`
- `31-final-task-index.md`
- `34-final-traceability-matrix.md`
- `35-final-analysis-report.md`
- `35a-final-readiness-result.md`
- `tasks/TASK-xxx.md`
- `prompts/TASK-xxx.prompt.md`

Do not make the dashboard the only place where important instructions exist.

Task handoff details such as input files, allowed paths, read-only references, BDD coverage, required Test IDs, validation mode, evidence requirements, acceptance criteria, and suggested test cases are derived from `tasks/TASK-xxx.md` and related final package artifacts. The dashboard displays them for execution convenience; it does not define them.

`31-final-task-index.md` is the Markdown source of truth for planned per-task review status across sessions. Dashboard review status stored in `localStorage` is a human convenience layer only. Export dashboard status and reconcile it back to `31-final-task-index.md` or `implementation-evidence.md` for shared review state.

## Task Execution Loop

The dashboard should make the recommended loop obvious:

1. Copy one prompt.
2. Run implementation for that task only.
3. Review evidence and handoff criteria.
4. Set the task status to `accepted` or `blocked`.
5. Continue to the next task only after the current task is accepted or explicitly deferred.

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
