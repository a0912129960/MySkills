# Status Tracking Reference

Use this reference whenever starting, resuming, or updating a feature package.

## Required Status Files

Every feature package must include:

```text
00-spec-workflow-status.md
00-stage-manifest.md
```

`00-spec-workflow-status.md` is the resume point. `00-stage-manifest.md` is the order source of truth.

## When To Read Them

Read the status file before doing anything else when:

- The feature folder already exists.
- The user asks to continue a previous spec.
- The user references an existing Gate 1, Gate 2, or final-package document.
- The user says a gate is confirmed.
- The user provides a previously missing architecture source.
- The user asks what remains to be done.

Read `00-context-inventory.md` together with the status file when resuming.

## When To Update Them

Update the status file whenever:

- The feature folder is created.
- A source requirement is captured.
- The feature name is inferred or confirmed.
- The stage manifest is created or revised.
- The context inventory is created or updated.
- Project mode is detected or changed.
- A context gap is raised.
- The user provides an architecture source.
- Critical questions are asked.
- The user answers questions.
- Assumptions are made or accepted.
- `09-gate1-flow-sketch.md` is created, revised, confirmed, skipped as trivial, or superseded.
- `19-gate2-solution-sketch.md` is created, revised, confirmed, skipped as trivial, or superseded.
- Gate 1 or Gate 2 files are generated or revised.
- Mermaid files are generated.
- SVG rendering succeeds, fails, or is skipped.
- The user requests revisions.
- Gate 1 is confirmed.
- Deep architecture verification completes for existing mode, or greenfield architecture design is confirmed.
- Proposed project-level facts are recorded, and verified project-level facts are written back to `.ai-dev/context/project-context.md` only during optional post-implementation convergence when evidence supports the update.
- A confirmed gate is re-opened because verified facts contradict confirmed content.
- Gate 2 is confirmed.
- Final package files are generated.
- Readiness changes.
- Optional post-implementation convergence completes.
- The workflow is blocked.

## Status Values

Use these stage values:

- `intake`
- `stage-manifest`
- `context-scan`
- `clarification`
- `gate1-flow-sketch`
- `business-draft`
- `business-feedback`
- `architecture-verification`
- `greenfield-design-confirmation`
- `gate2-solution-sketch`
- `solution-draft`
- `solution-feedback`
- `ready-to-finalize`
- `finalizing`
- `readiness-review`
- `convergence`
- `complete`
- `blocked`

Use these status values:

- `not-started`
- `in-progress`
- `waiting-for-user`
- `confirmed`
- `approved`
- `stale`
- `superseded`
- `rejected`
- `complete`
- `blocked`

## Resume Rule

When resuming, continue from `Next AI Action`.

Do not ask the user to repeat:

- Answered questions
- Confirmed decisions
- Accepted assumptions
- Previously confirmed review content
- Previously provided architecture sources
- Previously confirmed greenfield technology and architecture decisions

If the status file and generated files disagree, treat the status file as the navigation aid and the manifest plus generated artifacts as the source artifacts. Reconcile by updating the status file with what is actually present.

## Workflow State

When waiting for the user, the status file must show:

- `Waiting for user: yes`
- Current status: `waiting-for-user`
- The exact pending questions or confirmation request
- Which output is blocked
- What the user can answer next
- Any stale or superseded artifacts that need regeneration

When readiness is in progress, the status file must also show:

- Approved baseline file
- Task index file
- Task prompt files
- Traceability file
- Analysis file
- Readiness result file
- Dashboard file

When waiting on an early flow sketch, the status file must show:

- Current stage: `gate1-flow-sketch`
- Waiting for user: `yes`
- Sketch file path
- Draft user-flow diagram path
- Flow decisions, material assumptions, and blocking questions awaiting confirmation

When waiting on an early Gate 2 solution sketch, the status file must show:

- Current stage: `gate2-solution-sketch`
- Waiting for user: `yes`
- Sketch file path
- Draft API-flow diagram path
- Draft cross-project-flow diagram path, if applicable
- Provider/consumer direction, solution assumptions, Test ID direction, capability-slice boundaries, parallel ownership seams, and blocking questions awaiting confirmation

## Completion

Mark `complete` only when:

- Final package files exist.
- Dashboard exists.
- No pending blocking questions remain.
- No context gap remains unresolved or unaccepted.
- In greenfield mode, no planned component needed by Gate 2 remains unconfirmed.
- Optional post-implementation convergence completed, if implementation evidence was provided.
- The next action is to use the generated prompts for future development work.
