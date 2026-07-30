# Execution Contract

Use this contract to qualify, coordinate, record, and stop one formal Task
execution.

## Authority And Boundary

- The Task Markdown is normative for what to build.
- The Task Execution Manifest owns loading, execution routing, artifact
  digests, dependency eligibility, allowed paths, Skill Plan, validation, and
  evidence destinations.
- Current project rules are authoritative and always re-read during Execution
  Preflight.
- Execute one formal Task per session. A Task Work Unit is internal
  coordination only; it is not independently accepted and must not expand the
  Task.
- Do not modify normative specification artifacts. Production changes are
  limited to the Manifest's allowed paths; evidence and status changes are
  limited to their declared destinations.
- In `31-final-task-index.md`, modify only the Manifest-declared lifecycle
  status fields. Treat Task boundaries, dependencies, scope, and acceptance
  content as read-only normative specification.
- Do not create a branch, worktree, commit, stage, push, merge, or release.
  Subagents work in the same workspace in the first version.

## Fail-Closed Qualification

Make no production-code change and use the applicable state when:

- readiness did not pass, Task Plan approval is not human-confirmed, a required
  dependency is not human-`accepted`, or more than one formal Task is selected;
- a pinned normative artifact is missing or its SHA-256 digest differs;
- current project rules conflict with the approved package;
- scope, acceptance criteria, ownership, validation, or evidence paths
  contradict one another;
- the requested change no longer fits one human-reviewable Task;
- the package has only a legacy copied prompt and no valid Manifest.

Use `re-slice-required` when the Task is too large or incoherent,
`spec-revision-required` when normative behavior or solution content must
change, and `blocked` for an external prerequisite that cannot be resolved
inside the Approved Execution Boundary.

## Execution Preflight

Before code changes, the Task Coordinator presents:

1. selected Task, capability outcome, acceptance boundary, and current
   dependency state;
2. proposed Task Work Units and one bounded Work Unit Brief per writer;
3. exclusive write paths, shared read-only inputs, and all shared files owned
   by the Task Coordinator;
4. Task Test Owner, expected Task-level red state, focused checks, and
   Integrated Task Validation;
5. mandatory, conditional, and justified additional Skills;
6. expected changed paths, risk, and review size;
7. freshness results and any compatible current-rule changes.

No production edit is authorized while state is
`awaiting-preflight-approval`. Human approval creates the Approved Execution
Boundary. New shared-file writers, new risk, or material scope/review growth
requires renewed approval.

## Same-Task Subagents

The Task Coordinator retains the full Task context and owns integration.
Subagents receive only their Work Unit Brief and necessary read-only inputs.
Each writing Work Unit must have an exclusive write scope. Shared files are
single-writer and owned by the Task Coordinator. When safe ownership cannot be
established, use one implementation worker; other subagents may perform
read-only analysis, testing, or review.

The Task Test Owner establishes a valid Task-level red state before independent
implementation Work Units begin when TDD applies. Work Unit checks do not
complete the Task. Only the Coordinator's Integrated Task Validation and fixed
change-set `code-review` can move it to `ready-for-review`.

## Lifecycle

Normal path:

`not-started -> awaiting-preflight-approval -> in-progress -> ready-for-review -> accepted`

Human review repair loop:

`ready-for-review -> changes-requested -> in-progress -> ready-for-review`

Fail-closed outcomes:

`re-slice-required`, `spec-revision-required`, or `blocked`

Only the human may set `accepted`, authorize a renewed Preflight, or authorize
specification revision. `accepted` is the only default state that satisfies a
dependent Task. Do not start the next Task.

## Evidence

Create one immutable, append-only Execution Record per execution,
review-repair, or failed qualification session. Never rewrite an older record.
Record:

- manifest and artifact versions/digests;
- current-rule sources and freshness results;
- approved preflight and Work Unit ownership;
- Skills actually used and deviations;
- changed files, red/green evidence, Integrated Task Validation, and AI review;
- risks, unresolved items, lifecycle transition, and human handoff.

Keep `implementation-evidence.md` as an index and convergence summary that links
to the records. It is not the detailed session log.

## Specification Revision

When implementation evidence shows the approved behavior, solution, Task
boundary, or validation contract is wrong, stop production work and write a
Spec Change Request. Include the Task, code evidence, classification, return
level, affected normative artifacts, and partial change state. Return an exact
`$spec-package-generator <feature-package-path> --revise-from <request-path>`
invocation for the human to authorize. Never invoke the generator as automatic
cross-skill mutation.
