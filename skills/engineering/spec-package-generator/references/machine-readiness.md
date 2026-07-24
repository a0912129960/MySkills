# Machine Readiness Reference

Use this reference when calculating whether the final package is ready for implementation.

## Readiness Order

1. `34-final-traceability-matrix.md`
2. `35-final-analysis-report.md`
3. `35a-final-readiness-result.md`
4. `36-final-dashboard.html`

## Readiness Rules

- Readiness is a persisted result, not an informal note.
- `35a-final-readiness-result.md` must exist before the dashboard is rendered.
- Dashboard validation happens after readiness and must not be a prerequisite for readiness itself.
- The dashboard is the final implementation working surface, not a source of truth.
- Readiness must fail when critical artifacts are stale, contradictory, unresolved, or missing.
- Readiness must fail when blocking clarification questions remain unresolved.
- Readiness must fail when critical EARS requirements are not covered by BDD scenarios or explicit exception reasons.
- Readiness must fail when BDD scenarios, Test IDs, tasks, and prompts are not traceably connected.
- Readiness must fail when automated or semi-automated Test IDs lack complete Test Contract fields: entry point, fixture/input, assertions, expected red-state failure, pass criteria, evidence output, and owning task.
- For bootstrap Test IDs that create the project skeleton or test runner, expected red-state failure may be the absence of required files, scripts, or configuration instead of an executable failing test command.
- Readiness must fail when manual Test IDs lack explicit human inspection evidence, pass criteria, evidence output, or owning task.
- Readiness must fail when a task violates the split rule without an explicit exception justification.
- Readiness must fail when `31-final-task-index.md` lacks a per-task review status table with the allowed status values needed for cross-session task review tracking.

## Implementation Approval

The final dashboard is the handoff point for implementation prompts.

- No extra approval gate is required after the final dashboard.
- If implementation evidence later contradicts the approved package, convergence owns the correction.

## Task Execution Loop

The readiness result and dashboard should support one reviewed task at a time:

1. Copy one task prompt.
2. Implement only that task.
3. Review the reported evidence and task handoff checklist.
4. Mark the task accepted, blocked, or deferred in `31-final-task-index.md`.
5. Start the next task only after the current task is accepted or explicitly deferred.

Dashboard `localStorage` status is a local convenience only. Shared task status must be reconciled back to `31-final-task-index.md` or implementation evidence.
