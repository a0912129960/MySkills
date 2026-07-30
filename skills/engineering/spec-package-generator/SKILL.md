---
name: spec-package-generator
description: "Generate an AI-ready specification package from a requirement, discussed spec, or wish list. This specification-only skill uses a manifest-driven two-gate PRD/EARS/BDD workflow, vertically sliced capability tasks, dependency-aware parallel work, readiness-checked prompts, dashboard handoff, and post-implementation convergence."
---

# Spec Package Generator Skill

## Purpose

Convert a requirement source into a reviewable, AI-ready development specification package under `.ai-dev/features/<feature-name>/`.

This skill is specification-only. It may create and update `.ai-dev/**` specification, context, dashboard, and prompt artifacts. It must not edit downstream production application code.

## Operating Model

Use this file as the entry point only. Detailed workflow rules, generated file responsibilities, and template structures live in `references/` and `templates/`.

Primary authorities:

- `references/workflow.md` for sequencing, gates, re-open rules, one-shot mode, and optional post-implementation convergence.
- `references/stage-manifest.md` for manifest-driven artifact order.
- `references/status-tracking.md` for resumable workflow state.
- `references/output-files.md` for file responsibilities.
- `references/context-lifecycle.md` for lightweight context scan, project mode, deep verification, greenfield design confirmation, proposed updates, verified updates, and risk levels.
- `references/artifact-authority-and-invalidation.md` for source-of-truth and stale artifact rules.
- `references/question-and-decision-governance.md` for decisions and open questions.
- `references/ears-bdd-tdd.md` for PRD/EARS/BDD/TDD transformation rules.
- `references/test-contracts.md` for validation mode, test contract fields, automation levels, and readiness-oriented validation contract rules.
- `references/constitution-governance.md` for constitution and amendment handling.
- `references/traceability-and-tasking.md` for final task and prompt rules.
- `references/context-window-management.md` for bounded reads and task-scoped context.
- `references/machine-readiness.md` before declaring final readiness.
- `references/dashboard-guidelines.md` before rendering final dashboards.
- `references/mermaid-rendering.md` before deciding whether to render SVG diagrams.
- `references/cross-project-analysis.md` when multiple systems or projects may be affected.
- `references/markdown-ai-compatibility.md` when another AI will consume the generated package.

Use `templates/` for artifact structure. Do not copy full template bodies into this file.

## Artifact Model

This skill is in clean optimized-only mode.

New and resumed packages must use this artifact family:

- Intake and governance: `00-source-requirement.md`, `00-spec-workflow-status.md`, `00-stage-manifest.md`, `00-context-inventory.md`, `14-decision-log.md`, `15-open-questions.md`
- Gate 1: `09-gate1-flow-sketch.md`, `10-gate1-prd.md`, `11-gate1-ears.md`, `12-gate1-bdd.feature`, `13-gate1-review.html`
- Gate 2: `19-gate2-solution-sketch.md`, `20-gate2-project-impact.md`, `21-gate2-technical-design.md`, `22-gate2-constitution-compliance.md`, `24-gate2-test-strategy.md`, `25-gate2-review.html`, `proposed-context-update.md`
- Final package: `30-approved-feature-baseline.md`, `31-final-task-index.md`, `tasks/TASK-xxx.md`, `prompts/TASK-xxx.prompt.md`, `34-final-traceability-matrix.md`, `35-final-analysis-report.md`, `35a-final-readiness-result.md`, `36-final-dashboard.html`
- Optional convergence: `implementation-evidence.md`, `40-convergence-report.md`, `verified-context-update.md`

Only this optimized artifact family is supported.

## Default Entry

When the user asks to generate a spec from a requirement:

1. Read or preserve the requirement in `00-source-requirement.md`.
2. Infer the feature name, or ask when unclear.
3. Create or update `00-spec-workflow-status.md`.
4. Create or update `00-stage-manifest.md`; it is the artifact order authority.
5. Detect project mode as `greenfield` or `existing`, run the intake lightweight context scan, and create `00-context-inventory.md`.
6. In existing mode, ask for missing architecture sources immediately; these questions do not count against clarification budgets and do not block Gate 1. In greenfield mode, ask for missing technology or planned architecture decisions instead.
7. Ask up to 8 critical business clarification questions per round when needed for a useful Gate 1 draft. Use the Gate 1 clarification matrix and human-facing question format in `references/question-and-decision-governance.md`, and use additional rounds only when the previous answers reveal new blocking ambiguity.
8. Before full Gate 1 generation, create `09-gate1-flow-sketch.md` and draft `diagrams/user-flow.mmd` when the flow is not trivial, and always do this for greenfield projects, so the user can correct the business flow early. Stop for this micro-gate until the user confirms or revises the sketch.
9. Produce Gate 1 artifacts and stop for final Gate 1 confirmation. `13-gate1-review.html` is the only required human review surface for final Gate 1 confirmation; Markdown and feature files remain authoritative details linked from it.

The lightweight context scan may read `.ai-dev/context/project-context.md` if it exists, but only to identify known systems and missing sources. It must not perform architecture verification, load constitution or implementation guidance, or update project context.

## Workflow Stages

### Intake

Create or update:

- `00-source-requirement.md`
- `00-spec-workflow-status.md`
- `00-stage-manifest.md`
- `00-context-inventory.md`
- `09-gate1-flow-sketch.md` when the flow is not trivial or project mode is greenfield

Track every relevant existing system or planned greenfield component in `00-context-inventory.md`. In existing mode, missing sources may proceed through Gate 1 but block Gate 2 unless the user explicitly accepts an `UNVERIFIED` risk. In greenfield mode, missing implementation files do not block Gate 2; planned architecture must be confirmed by the user and recorded as `confirmed-design`.

### Gate 1: Business Confirmation

Gate 1 owns WHAT.

Create:

- `10-gate1-prd.md`
- `11-gate1-ears.md`
- `12-gate1-bdd.feature`
- `13-gate1-review.html`
- `gate1-checklist.md` when useful
- `diagrams/user-flow.mmd`
- `diagrams/user-flow.svg` when a renderer is available

Gate 1 must stay product-only. It must not perform architecture verification, produce API flows, generate technical design, load constitution, provide implementation guidance, or update project context.

Gate 1 must be EARS/BDD-ready:

- Every core user scenario must be extracted, safely assumed, or represented by a blocking question.
- Every critical EARS requirement must map to at least one BDD scenario unless marked `manual-only` or `not-scenario-suitable` with a reason.
- Gate 1 review must include the user-flow diagram and the human confirmation points that affect PRD, EARS, BDD, test strategy, or task scope.
- Gate 1 review must list material assumptions as explicit confirm/override items. Unconfirmed material assumptions block Gate 1 approval and readiness; low-risk non-material assumptions may remain recorded without blocking.

Ask the user to confirm or revise Gate 1 before proceeding.

### Architecture Grounding

Run only after Gate 1 confirmation.

In existing mode, verify actual architecture sources for every in-scope system needed by the solution: applicable `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, architecture and ADR sources, representative code entry points, contracts, schemas, integration mechanisms, validation commands, or user-provided sources. Update `00-context-inventory.md` with verified facts, status, and risk level.

In greenfield mode, do not block on code, schemas, entry points, or test runners that do not exist yet. Convert the confirmed Gate 1 behavior into planned architecture, schema, tooling, and test strategy decisions. Ask for blocking technology choices, then record user-confirmed planned architecture as `confirmed-design` in `00-context-inventory.md`.

If verified facts contradict confirmed Gate 1 behavior, apply the Gate Re-Open Rule in `references/workflow.md`.

Do not update `.ai-dev/context/project-context.md` here. Record verified facts, sources, statuses, and risk levels in `00-context-inventory.md`; Gate 2 derives `proposed-context-update.md` from that inventory and the approved solution review.

### Solution Clarification

Run after deep architecture verification for existing projects, or after greenfield architecture design confirmation for greenfield projects, and before Gate 2 artifacts.

Ask up to 8 critical solution clarification questions per round when verified architecture or greenfield planned architecture leaves more than one reasonable design choice. Use the Gate 2 solution clarification matrix and focused grilling protocol in `references/question-and-decision-governance.md`. Focus on API contracts, data/query approach, integration mechanics, permissions/security, error handling, validation, logging/audit, release order, compatibility when verified released contracts or active consumers exist, greenfield technology choices, Test ID coverage, capability-slice boundaries, and parallel ownership seams. Use additional rounds only when the user's answers reveal new blocking technical ambiguity.

Before Gate 2 can be confirmed, the test strategy must define Test IDs for relevant BDD scenarios and enough Test Contract data to support TDD when automation or semi-automation is expected.

### Gate 2 Solution Sketch

Before full Gate 2 generation, create `19-gate2-solution-sketch.md` and draft `diagrams/api-flow.mmd` plus `diagrams/cross-project-flow.mmd` when applicable, so the user can correct the technical flow early. In greenfield mode, always create this sketch. Stop for this micro-gate until the user confirms or revises the sketch.

The sketch must be derived from verified inventory entries, `confirmed-design` greenfield entries, or explicitly accepted `UNVERIFIED` risks. It should cover draft API flow, cross-project responsibility direction, provider/consumer boundaries, material solution assumptions, blocking solution questions, initial Test ID direction, capability-slice boundaries, and parallel ownership seams.

### Gate 2: Solution Review

Gate 2 owns HOW.

Create:

- `19-gate2-solution-sketch.md`
- `20-gate2-project-impact.md`
- `21-gate2-technical-design.md`
- `22-gate2-constitution-compliance.md`
- `24-gate2-test-strategy.md`
- `proposed-context-update.md`
- `25-gate2-review.html`
- `gate2-checklist.md` when useful
- `diagrams/api-flow.mmd`
- `diagrams/api-flow.svg` when a renderer is available
- `diagrams/cross-project-flow.mmd` and `.svg` when applicable

Gate 2 must derive solution content from verified inventory entries, `confirmed-design` greenfield entries, or explicitly accepted `UNVERIFIED` risks. Gate 2 may propose project-context updates but must not write current project context directly.

Ask the user to confirm or revise Gate 2 before finalization. `25-gate2-review.html` is the only required human review surface for final Gate 2 confirmation; Markdown files remain authoritative details linked from it.

### Final Package

Finalize only after Gate 2 confirmation or explicit user approval to proceed with documented assumptions.

Create:

- `30-approved-feature-baseline.md`
- `31-final-task-index.md`
- `tasks/TASK-xxx.md`
- `prompts/TASK-xxx.prompt.md`
- `34-final-traceability-matrix.md`
- `35-final-analysis-report.md`
- `35a-final-readiness-result.md`
- `36-final-dashboard.html`
- `37-implementation-package-approval.md` only when the team explicitly requires a named approval record

Readiness must be calculated and persisted in `35a-final-readiness-result.md` before rendering `36-final-dashboard.html`. The final dashboard is the direct implementation entry point after readiness passes and must not redefine the Markdown artifacts.

Prompt files are derived from task files. They must not redefine behavior, widen scope, or override task constraints.

`31-final-task-index.md` is the Markdown source of truth for per-task review status across sessions. The dashboard may persist local browser state and export status updates, but shared task status must be reconciled back to the task index or implementation evidence.

Final task contracts must expose machine-checkable vertical-slice fields, dependency and parallel-wave fields, BDD coverage, EARS coverage, required Test IDs, validation mode, and validation contract rows. Every feature task must leave a user- or system-observable capability working through a defined validation route. Readiness fails when critical behavior is not traceably connected from EARS to BDD to Test ID to task and prompt.

For greenfield packages, final tasks must begin with a bootstrap task that explicitly invokes `project-rules-init` using the user-confirmed Gate 2 architecture. Follow it with any project skeleton, package manager, test runner, linting, routing, database tooling, or app-shell bootstrap tasks needed before feature behavior. Bootstrap tasks may use manual or semi-automated validation based on file existence, configuration checks, package script checks, and human inspection; do not require executable red-state test evidence before the test runner exists.

After the dashboard is generated, the recommended implementation loop is dependency-aware:

1. Select any task whose dependencies are accepted or explicitly deferred with a safe exception.
2. Run non-overlapping tasks in the same parallel wave concurrently when their contracts and allowed paths do not conflict.
3. Let each AI implement only its selected capability slice.
4. Review each task's executable evidence, user- or system-observable result, and human handoff checklist independently.
5. Mark each task accepted, blocked, or deferred before starting a dependent wave.

### Optional Post-Implementation Convergence

Run optional post-implementation convergence only after implementation evidence exists. Convergence is not required for the specification package to be ready for implementation.

Create or update:

- `implementation-evidence.md`
- `40-convergence-report.md`
- `verified-context-update.md`
- `.ai-dev/context/project-context.md` only after verified convergence supports the update

Convergence compares actual implementation evidence against the approved baseline, tasks, tests, and proposed context updates.

Gate 2 produces only `proposed-context-update.md`. `verified-context-update.md` and `.ai-dev/context/project-context.md` updates are convergence-only outputs after implementation evidence supports them.

## Modes

- Default mode: intake -> project mode detection -> Gate 1 -> confirmation -> existing verification or greenfield design confirmation -> Gate 2 -> confirmation -> final package.
- Gate 1 review mode: produce or revise business artifacts only, using up to 8 critical business questions per round.
- Gate 2 review mode: verify existing architecture or confirm greenfield planned architecture, ask solution clarification questions when needed, produce or revise the solution sketch and solution artifacts, and stop before final package.
- Finalize mode: produce final task, prompt, traceability, readiness, and dashboard artifacts.
- One-shot mode: allowed only when the user explicitly asks for a one-pass package or explicitly approves assumptions. It still runs context scan, architecture verification, gate logic, readiness, and post-implementation convergence timing rules, but it does not stop at Gate 1 or Gate 2 confirmation points. Missing architecture sources still require either a source or explicit `UNVERIFIED` acceptance.
- Convergence mode: reconcile implementation evidence and update verified project context only when evidence supports it.

## Artifact Authority

Resolve conflicts by ownership, not file order:

- Source requirement: original user request.
- Product behavior: PRD, EARS, and BDD.
- Architecture and implementation approach: Gate 2 project impact and technical design.
- Constitution compliance: Gate 2 constitution compliance and project constitution sources.
- Test planning: Gate 2 test strategy and test contracts.
- Implementation scope: individual `tasks/TASK-xxx.md`.
- Execution prompts: derived `prompts/TASK-xxx.prompt.md`.
- Readiness: `35a-final-readiness-result.md`.
- Project context: `.ai-dev/context/project-context.md` after verified convergence only.

Derived HTML dashboards, review HTML, prompts, checklists, summaries, and traceability views must not redefine normative Markdown artifacts.

## Strict Rules

- Keep this skill specification-only.
- Never edit production source code.
- Never invent architecture. In greenfield mode, propose architecture as planned design and require user confirmation before treating it as Gate 2 grounding.
- Never skip `00-spec-workflow-status.md`, `00-stage-manifest.md`, or `00-context-inventory.md`.
- Never generate Gate 2 artifacts from missing existing architecture sources unless the user explicitly accepts `UNVERIFIED` risk. For greenfield projects, use user-confirmed `confirmed-design` entries instead of missing source verification.
- Never write `.ai-dev/context/project-context.md` before verified convergence.
- Never let stale critical artifacts pass readiness.
- Never let prompts or HTML override PRD, EARS, BDD, technical design, test strategy, or task contracts.
- Never continue downstream work when verified facts contradict confirmed gate content; reopen the affected gate.
- Render SVG diagrams whenever the centrally managed Mermaid CLI is available; otherwise retain the complete authoritative `.mmd` output and record that optional SVG rendering was skipped.
- Prefer vertically sliced feature tasks that deliver one cohesive, independently demonstrable capability, even when the slice crosses UI, API, domain, or persistence layers.
- Do not split feature work by technical layer merely to reduce file count. Treat file count and layer count as planning signals, not automatic split rules.
- Allow horizontal enabler tasks only when a runnable capability slice cannot own the prerequisite safely; require a named unlocked capability, concrete validation, and explicit justification.
- Define dependency waves, allowed paths, shared contracts, and integration ownership so non-overlapping ready tasks can be developed in parallel.

## Bundled Resources

Use templates by artifact name instead of embedding formats here:

- Intake and governance templates: `00-source-requirement`, `00-spec-workflow-status`, `00-stage-manifest`, `00-context-inventory`, `14-decision-log`, `15-open-questions`.
- Gate 1 templates: `09-gate1-flow-sketch`, `10-gate1-prd`, `11-gate1-ears`, `12-gate1-bdd`, `13-gate1-review`, `gate1-checklist`.
- Gate 2 templates: `19-gate2-solution-sketch`, `20-gate2-project-impact`, `21-gate2-technical-design`, `22-gate2-constitution-compliance`, `24-gate2-test-strategy`, `25-gate2-review`, `gate2-checklist`, `proposed-context-update`, `test-case-contract`.
- Final templates: `30-approved-feature-baseline`, `31-final-task-index`, `task`, `tdd-prompt`, `34-final-traceability-matrix`, `35-final-analysis-report`, `35a-final-readiness-result`, `36-final-dashboard`, `37-implementation-package-approval`.
- Convergence templates: `implementation-evidence`, `40-convergence-report`, `verified-context-update`, `project-context`.
- Constitution templates: `constitution`, `implementation-constitution`, `constitution-amendment`.

## Completion Criteria

The package is ready for implementation when:

- Gate 1 and Gate 2 are confirmed or explicitly documented assumptions are accepted.
- Required artifacts are current according to `00-stage-manifest.md` and invalidation rules.
- Traceability maps source -> PRD -> EARS -> BDD -> technical design -> test ID -> task.
- `35a-final-readiness-result.md` passes.
- `36-final-dashboard.html` presents the ready-to-implement task order and per-task copyable prompts.

Convergence is not required for the specification package to be ready for implementation. It is a post-implementation maintenance flow for reconciling actual implementation evidence and promoting verified reusable context.
