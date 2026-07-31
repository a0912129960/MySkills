# Stage Manifest Reference

Use this reference when determining artifact order and stage ownership.

## Authority

- `00-stage-manifest.md` is the order source of truth.
- File names alone do not determine execution order.
- This skill uses the optimized artifact model only.

## Logical Stage Order

1. Intake
2. Stage manifest
3. Context scan
4. Gate 1 durable decision clarification and flow-sketch drafting
5. Gate 1 flow-sketch confirmation
6. Gate 1
7. Architecture grounding: existing verification or greenfield design confirmation
8. Gate 2 durable decision clarification and solution-sketch drafting
9. Gate 2 solution-sketch confirmation
10. Gate 2
11. Task planning
12. Task Plan Gate
13. Execution artifacts
14. Readiness review
15. Optional post-implementation convergence

## Manifest Requirements

The stage manifest should record:

- Current stage
- Next stage
- Package type: `optimized`
- Project mode: `greenfield`, `existing`, or `unknown`
- Artifact ownership
- Stage dependencies
- Stale artifact relationships
- Separate Gate 1 and Gate 2 durable clarification stage statuses, plus links
  to `14-decision-log.md`, `15-open-questions.md`, and
  `00-spec-workflow-status.md`
- Whether `09-gate1-flow-sketch.md` is required, skipped as trivial, confirmed, or superseded. It is required in greenfield mode.
- Whether `19-gate2-solution-sketch.md` is required, skipped as trivial, confirmed, or superseded. It is required in greenfield mode.
- Whether `32-task-plan-review.md` is pending, human-confirmed, or returned for
  revision, and which Task IDs are confirmed.
- Resume instructions

The clarification stages own initial creation and decision-driven revision of
their draft sketch artifacts. A draft sketch may therefore exist while its
clarification stage is `waiting-for-user`. The following sketch stage owns only
the final human confirmation or correction request and must not begin until the
applicable clarification stage is `complete`.

## Resume Rule

When resuming a package:

- Read `00-spec-workflow-status.md` first.
- Read `00-stage-manifest.md` second.
- Follow the manifest's next-action entry.
- Treat `00-spec-workflow-status.md` as the sole owner of the active Question
  ID. The manifest records clarification phase order and status only.
- Do not infer order from file numbers alone.

If `00-stage-manifest.md` is missing but generated artifacts exist:

- Create `00-stage-manifest.md` before changing any stage artifact.
- Record existing optimized artifacts.
- Set resume stage from `00-spec-workflow-status.md` when possible; otherwise choose the earliest logical stage that is missing, stale, or needs review.

## Conflict Rules

- Conflicts must be recorded in the manifest with one artifact marked as the current stage owner.
- If the current owner cannot be determined from the manifest or status file, stop and ask the user.
