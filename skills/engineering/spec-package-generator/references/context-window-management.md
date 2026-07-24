# Context Window Management Reference

Use this reference to keep package reads bounded as artifact count grows.

## Core Rule

Read only the artifacts needed for the current stage, unless a stale, missing, contradictory, or user-requested condition requires broader context.

## Resume Reads

When resuming an existing package:

1. Read `00-spec-workflow-status.md` first.
2. Read `00-stage-manifest.md` second.
3. Read `00-context-inventory.md` when the current stage depends on architecture evidence, context gaps, or verification status.
4. Prefer artifact metadata, summaries, and manifest ownership before reading full artifact bodies.

Do not infer execution order from file names alone.

## Gate Reads

Gate 1 reads product/business inputs and the intake context inventory only to identify systems, planned greenfield components, and missing architecture sources. It must not perform architecture verification, load implementation guidance, or write project context.

Gate 2 reads the verified context sources or confirmed greenfield design entries needed to translate approved product behavior into solution design. It must record reusable facts as `proposed-context-update.md`, not as current project context.

## Final Package Reads

For final task and prompt generation, prefer:

- `30-approved-feature-baseline.md`
- `31-final-task-index.md`
- the selected `tasks/TASK-xxx.md`
- effective constitution/context artifacts explicitly referenced by that task
- exact PRD/EARS/BDD/design sections needed for that task

Avoid rereading every generated artifact for every task unless traceability, readiness, stale artifacts, or contradictions require it.

## Prompt Scope

Generated prompts must be task scoped:

- Implement only the selected task.
- Do not implement future tasks.
- Do not modify read-only paths.
- Do not refactor unrelated code.
- Follow the approved baseline, task contract, technical design, and test strategy.

Prompt files are derived execution entries. They must not redefine task scope or source-of-truth behavior.

## Escalation To Broader Reads

Read broader package context only when:

- the status or manifest is missing,
- the manifest marks relevant artifacts stale,
- two artifacts conflict and ownership is unclear,
- readiness or traceability checks fail,
- the user explicitly asks for a full consistency review.
