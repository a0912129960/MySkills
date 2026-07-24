# Traceability And Tasking Reference

Use this reference when creating the final package and implementation items.

## Traceability Chain

Source -> PRD -> EARS -> BDD -> technical design -> test ID -> task -> implementation evidence -> convergence

## Task Rules

- Keep each task human-reviewable.
- Do not mix unrelated frontend, backend, database, and external project work in one task.
- Prefer one screen, one API, one service method, one query, or one contract per task where possible.
- A task should be small enough for one focused human review. If it touches more than one major layer, more than roughly 3-5 likely files, or more than one independently testable behavior, split it unless the coupling is explicitly justified.
- Each task must expose machine-checkable split fields: estimated modified file count, major layers touched, single independently testable behavior, split-rule compliant, and exception justification.
- Each task should list its primary Test IDs, validation mode, BDD scenarios covered, EARS requirements covered, review focus, allowed-to-modify paths, read-only references, validation contract rows, and completion evidence.
- Each task must declare one validation mode: `automated`, `semi-automated`, or `manual`. Automated and semi-automated tasks require red-state and green-state evidence. Manual tasks do not require red-state evidence, but must define concrete before/after inspection evidence and user-visible pass criteria.
- `31-final-task-index.md` must include the cross-session task review status table. Individual task files define scope and handoff; the task index owns shared accepted/blocked/deferred status.
- For greenfield projects, generate bootstrap tasks before feature behavior tasks when foundational files or tooling do not exist yet. Typical bootstrap tasks include project initialization, package/workspace setup, test runner setup, lint/type-check setup, app shell/routing setup, database tooling setup, and environment configuration.
- Bootstrap tasks may use `manual` or `semi-automated` validation based on file existence, package scripts, configuration checks, or human inspection. Do not require executable red-state test evidence before the test runner exists.

## Prompt Rules

- Each prompt must be derived from one task.
- Each prompt must say to implement only that task.
- Each prompt must require the AI to stop after the selected task is implemented and report evidence; it must not continue to the next task.
- Each prompt must say not to modify read-only projects or future items.
- Each prompt must include the human verification handoff: what command or inspection to run, what evidence to report, and what must be true before starting the next task.
- Each prompt must report changed files, validation evidence, and the human review checklist before handoff.
- The next task may start only after the current task is accepted or explicitly deferred in `31-final-task-index.md` or implementation evidence.
- Each prompt must require the AI to identify BDD scenarios, EARS requirements, Test IDs, validation mode, and validation contract rows before coding.
- For automated and semi-automated Test IDs, each prompt must require red-state evidence before production-code changes and green-state evidence after implementation.
- For manual Test IDs, each prompt must require explicit before/after inspection evidence and a user-visible result instead of red-state evidence.
- For bootstrap Test IDs, each prompt must use the bootstrap validation contract and must not invent a test-runner command before that command is created by the task.
