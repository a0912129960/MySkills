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
- Readiness must fail when BDD scenarios, Test IDs, Tasks, Manifests, and prompts are not traceably connected.
- Readiness must fail when automated or semi-automated Test IDs lack complete Test Contract fields: entry point, fixture/input, assertions, expected red-state failure, pass criteria, evidence output, and owning task.
- For bootstrap Test IDs that create the project skeleton or test runner, expected red-state failure may be the absence of required files, scripts, or configuration instead of an executable failing test command.
- Readiness must fail when manual Test IDs lack explicit human inspection evidence, pass criteria, evidence output, or owning task.
- Readiness must fail when a feature task lacks a cohesive user- or system-observable outcome, end-to-end validation route, runnable completion state, or independently reviewable evidence.
- Readiness must fail when a horizontal enabler lacks a concrete validated deliverable, exception justification, or named capability slices that it unlocks.
- Readiness must fail when tasks claimed to run in parallel have unresolved dependencies, unsafe path ownership overlap, an unfrozen required shared contract, or no integration owner.
- Readiness must fail when `31-final-task-index.md` lacks a per-task review status table with the allowed status values needed for cross-session task review tracking.
- Readiness must fail when `32-task-plan-review.md` is not
  `human-confirmed` for every generated Task Manifest.
- Readiness must fail when a Task Manifest selects anything other than one
  formal Task, lacks a required accepted dependency, omits scope/Skill
  Plan/validation/evidence/freshness data, or has a missing or incorrect
  SHA-256 digest for a pinned normative artifact.
- Readiness must fail when a generated prompt contains execution instructions
  beyond `$implement-spec-task <manifest-path>` and path substitution guidance.

## Implementation Approval

The final dashboard is the handoff point for Manifest-backed executor
invocations.

- No extra approval gate is required after the final dashboard.
- If implementation evidence later contradicts the approved package, convergence owns the correction.

## Task Execution Loop

The readiness result and dashboard should support independently reviewed tasks in dependency-aware parallel waves:

1. Select one Task whose required dependencies are all human-`accepted`.
2. Invoke `implement-spec-task` with that Task's Manifest and approve its
   Execution Preflight.
3. Allow controlled same-Task Work Units only inside the approved ownership
   boundary.
4. Review the integrated evidence after `ready-for-review`; only the human may
   mark `accepted`.
5. Do not start the next Task automatically.

Dashboard `localStorage` status is a local convenience only. Shared task status must be reconciled back to `31-final-task-index.md` or implementation evidence.
