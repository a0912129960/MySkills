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
- Readiness must fail when a feature task lacks a cohesive user- or system-observable outcome, end-to-end validation route, runnable completion state, or independently reviewable evidence.
- Readiness must fail when a horizontal enabler lacks a concrete validated deliverable, exception justification, or named capability slices that it unlocks.
- Readiness must fail when tasks claimed to run in parallel have unresolved dependencies, unsafe path ownership overlap, an unfrozen required shared contract, or no integration owner.
- Readiness must fail when `31-final-task-index.md` lacks a per-task review status table with the allowed status values needed for cross-session task review tracking.

## Implementation Approval

The final dashboard is the handoff point for implementation prompts.

- No extra approval gate is required after the final dashboard.
- If implementation evidence later contradicts the approved package, convergence owns the correction.

## Task Execution Loop

The readiness result and dashboard should support independently reviewed tasks in dependency-aware parallel waves:

1. Select any task whose dependencies are accepted or explicitly deferred with a safe exception.
2. Run eligible non-overlapping tasks in the same wave concurrently when ownership and shared contracts make it safe.
3. Have each worker implement only one selected task and report its own evidence.
4. Review and mark each task accepted, blocked, or deferred in `31-final-task-index.md`.
5. Start a dependent wave only after its prerequisites satisfy the recorded eligibility rule.

Dashboard `localStorage` status is a local convenience only. Shared task status must be reconciled back to `31-final-task-index.md` or implementation evidence.
