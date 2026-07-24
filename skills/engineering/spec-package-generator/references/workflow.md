# Workflow Reference

Use this reference as the workflow authority. The user should not need to choose a mode or gate.

## Workflow Authority

- `00-stage-manifest.md` is the order source of truth.
- File numbers are readability hints, not the execution order.
- `00-spec-workflow-status.md` is the resume point.
- `00-context-inventory.md` is the architecture evidence ledger.
- `30-approved-feature-baseline.md` is the approved final-package index.
- Derived files such as HTML dashboards and prompts never redefine the normative Markdown artifacts.

## Pipeline Overview

```text
intake
  -> read 00-spec-workflow-status.md
  -> read 00-stage-manifest.md
  -> preserve source requirement
  -> detect project mode: greenfield or existing
  -> lightweight context scan -> 00-context-inventory.md (missing sources -> ask user, does not block Gate 1)
  -> business clarification questions (max 8 per round, business layer only)
  -> 09-gate1-flow-sketch.md + draft user-flow diagram when the flow is not trivial or project mode is greenfield -> user confirms/revises the sketch
  -> Gate 1: 10-gate1-prd.md + 11-gate1-ears.md + 12-gate1-bdd.feature + 13-gate1-review.html + optional gate1-checklist.md + user-flow diagram
  -> Gate 1 confirmation
  -> existing mode: deep architecture verification
  -> greenfield mode: planned architecture and schema design confirmation
  -> solution clarification questions (max 8 per round, solution layer only)
  -> 19-gate2-solution-sketch.md + draft api-flow/cross-project diagrams when applicable or project mode is greenfield -> user confirms/revises the solution sketch
  -> Gate 2: 20-gate2-project-impact.md + 21-gate2-technical-design.md + 22-gate2-constitution-compliance.md + 24-gate2-test-strategy.md + proposed-context-update.md + 25-gate2-review.html + optional gate2-checklist.md + api-flow/cross-project diagrams
  -> Gate 2 confirmation
  -> final package: 30-approved-feature-baseline.md + 31-final-task-index.md + tasks + prompts + 34-final-traceability-matrix.md + 35-final-analysis-report.md + 35a-final-readiness-result.md + 36-final-dashboard.html
  -> optional post-implementation convergence after implementation evidence: implementation-evidence.md + 40-convergence-report.md + verified-context-update.md
```

Gate 1 owns WHAT. Gate 2 owns HOW. Optional post-implementation convergence owns what was actually implemented.

## Default Entry

When the user says something like "read this file and generate the spec", start the default intake-to-Gate-1 flow.

The agent should:

- Read the requirement file or pasted requirement.
- If the source is a wish list, loose idea list, or discussion notes, break it down in `00-source-requirement.md` before drafting Gate 1: map each wish item to an inferred goal, user scenario, ambiguity or gap, suggested assumption, clarification question, and decision status.
- Detect project mode and record it in `00-spec-workflow-status.md` and `00-context-inventory.md`: use `greenfield` when the project or feature has no existing implementation sources to verify; use `existing` when relevant code, contracts, schemas, or docs already exist.
- Infer the feature name, or ask for it if unclear.
- Create or update `00-spec-workflow-status.md`.
- Read `00-stage-manifest.md` if it exists, then follow the manifest order.
- Read `.ai-dev/context/project-context.md` first if it exists for lightweight scan only, then create `00-context-inventory.md`.
- In existing mode, ask for any missing architecture sources immediately; these do not count against the clarification budget and do not block Gate 1. In greenfield mode, ask for missing technology or planned architecture decisions instead.
- Ask only critical business clarification questions that block a useful business draft. Ask at most 8 questions in one round; if the answers reveal new blocking ambiguity, ask a focused follow-up round instead of overloading the user.
- Use the Gate 1 clarification matrix from `references/question-and-decision-governance.md` to classify extracted facts, assumptions, and blocking questions.
- Produce `09-gate1-flow-sketch.md` during clarification when the flow is not trivial, and always produce it for greenfield projects. The sketch micro-gate must include the draft scenario list, operation flow, user-flow diagram, up to 8 critical business questions, and material assumptions to confirm or override. Stop for user confirmation or revision before full Gate 1 review generation.
- When stopping for the sketch micro-gate, include the review artifact path, Mermaid source path, SVG path when available, and a concise diagram preview or summary in the chat response.
- Generate the Gate 1 business artifacts and `diagrams/user-flow.mmd`; render `diagrams/user-flow.svg` when a renderer is available.
- Ask the user to confirm or revise the business draft.
- Include the Gate 1 review artifact path, diagram paths, and exact confirmation points in the chat response.
- Stop before architecture verification output and Gate 2 artifacts.

Do not require the user to mention any mode name.

## Gate 1 Review Mode

Gate 1 is the default for normal feature specification requests.

Required behavior:

- Save the source requirement.
- For wish lists or loose notes, convert the raw wishes into inferred goals, user scenarios, ambiguities, assumptions, clarification questions, and decision status in `00-source-requirement.md`.
- Detect and record project mode as `greenfield` or `existing`.
- Create or update the workflow status file.
- Create the stage manifest if it does not exist.
- Complete the lightweight context scan before Gate 1 artifacts: read `.ai-dev/context/project-context.md` if it exists, then create `00-context-inventory.md`. In existing mode, ask immediately for any missing architecture sources. In greenfield mode, ask for missing technology or planned architecture decisions.
- Use the Gate 1 clarification matrix to classify extracted facts, assumptions, and blocking questions.
- Before full Gate 1 artifact generation, create `09-gate1-flow-sketch.md` and a draft `diagrams/user-flow.mmd` when the flow is not trivial or project mode is greenfield. Include the sketch, up to 8 critical questions, and material assumptions in the same micro-gate, then wait for user confirmation or correction.
- Present the sketch and diagram paths in chat when waiting for confirmation.
- Create the business review artifacts only.
- Keep Gate 1 product-only: no architecture verification, no project-context write-back, no constitution loading, no implementation guidance.
- Ensure every core scenario is extracted, safely assumed, or covered by a blocking question before Gate 1 approval.
- Ensure every critical EARS requirement has BDD coverage or an explicit exception reason.
- Present material assumptions as explicit confirm/override items in the Gate 1 review. Unconfirmed material assumptions block Gate 1 approval.
- Treat `13-gate1-review.html` as the primary and only required human review surface for final Gate 1 confirmation; Markdown and feature files remain authoritative details linked from it.
- Ask the user to confirm or revise the draft.

Gate 1 artifacts are:

- `09-gate1-flow-sketch.md` when the flow is not trivial or project mode is greenfield
- `10-gate1-prd.md`
- `11-gate1-ears.md`
- `12-gate1-bdd.feature`
- `13-gate1-review.html`
- `gate1-checklist.md` if created
- `diagrams/user-flow.mmd`

## Deep Architecture Verification

Runs only after Gate 1 is confirmed and project mode is `existing`.

Required behavior:

- Re-check carried-over facts from `.ai-dev/context/project-context.md` when present.
- Read the actual code entry points, contracts, or documents for the in-scope systems.
- Directory names alone are not verification.
- If any source is `missing` or `user-will-provide`, set the workflow to `blocked` and `waiting-for-user`, list exactly what is needed, and wait.
- Never invent architecture. If the user explicitly accepts a gap, mark it `accepted-unverified` and tag the related Gate 2 content `UNVERIFIED`.
- Record verified facts, source paths, statuses, and risk levels in `00-context-inventory.md`.
- Gate 2 derives `proposed-context-update.md` from verified inventory facts and the approved solution review; do not create or update it as the primary verification ledger.
- Gate 2 must not update current project context directly.

## Greenfield Architecture Design Confirmation

Runs only after Gate 1 is confirmed and project mode is `greenfield`.

Required behavior:

- Do not block on missing code, schemas, entry points, or test runners that do not exist yet.
- Convert the confirmed Gate 1 behavior into planned architecture facts in `00-context-inventory.md` with status `planned` or `confirmed-design`.
- Draft the intended project structure, package boundaries, API routes or contracts, database or storage model, auth approach, test runner, build tooling, deployment target, and integration boundaries when applicable.
- Ask up to 8 critical technology and architecture questions per round when more than one reasonable greenfield choice exists.
- Treat user-confirmed planned architecture as the Gate 2 grounding source. Label it `confirmed-design`, not `verified`.
- Use `proposed-context-update.md` to record reusable planned architecture facts, but do not write `.ai-dev/context/project-context.md` before convergence.
- If later implementation evidence contradicts the confirmed design, convergence owns the correction.

## Solution Clarification

Ask at most 8 critical solution clarification questions per round using the Gate 2 solution clarification matrix from `references/question-and-decision-governance.md`. Cover API contract shape, DB schema or query approach, integration mechanics, permission/security decisions, error-code and validation design, logging/audit behavior, release constraints, contract compatibility only when verified released contracts or active consumers exist, Test ID coverage, task split boundaries, and greenfield technology choices when project mode is `greenfield`.

Prefer deriving answers from verified architecture before asking. If answers reveal new blocking technical ambiguity, ask a focused follow-up round. If verification reveals a conflict with confirmed business behavior, that is a Gate Re-Open Rule event, not a solution question.

Before Gate 2 confirmation, `24-gate2-test-strategy.md` must map relevant BDD scenarios to Test IDs and define Test Contract data for automated and semi-automated validation.

## Gate 2 Solution Sketch

Runs after deep architecture verification or greenfield architecture design confirmation and solution clarification, before full Gate 2 artifacts.

Required behavior:

- Create `19-gate2-solution-sketch.md`.
- Create draft `diagrams/api-flow.mmd`.
- Create draft `diagrams/cross-project-flow.mmd` when multiple projects or systems are involved.
- For greenfield projects, create the solution sketch even when the solution appears simple, because the sketch confirms the planned technical shape before task generation.
- Derive every participant, responsibility, and call from `00-context-inventory.md` entries with status `verified`, `confirmed-design`, or explicitly accepted `UNVERIFIED`.
- Include project responsibility split, provider/consumer direction, key solution assumptions, blocking solution questions, initial Test ID coverage direction, and task split boundary concerns.
- Stop and wait for user confirmation or correction before full Gate 2 artifact generation.
- Present the solution sketch path, diagram paths, and exact confirmation or correction request in chat when waiting for confirmation.
- Record the sketch state in `00-spec-workflow-status.md` and `00-stage-manifest.md`.

If project mode is `existing` and the solution is trivial with no API, integration, cross-project, persistence, permission, or test-contract decision, record the sketch as skipped with a reason. Do not skip the sketch merely because the diagrams are simple. Do not skip the Gate 2 solution sketch in greenfield mode.

## Gate 2 Review Mode

Starts only after Gate 1 confirmation and completed architecture verification for existing projects, or confirmed architecture design for greenfield projects.

Required behavior:

- Create or confirm `19-gate2-solution-sketch.md` before full Gate 2 generation.
- Create `20-gate2-project-impact.md`, `21-gate2-technical-design.md`, `22-gate2-constitution-compliance.md`, `24-gate2-test-strategy.md`, `proposed-context-update.md`, and `25-gate2-review.html` from verified context or confirmed greenfield design.
- Create `gate2-checklist.md` when a derived solution-review checklist is needed.
- Create `diagrams/api-flow.mmd` and `diagrams/cross-project-flow.mmd` when applicable; render SVG when a renderer is available.
- Every component in Gate 2 artifacts must be traceable to a `verified`, `confirmed-design`, or explicitly accepted `UNVERIFIED` inventory entry.
- Treat `25-gate2-review.html` as the primary and only required human review surface for final Gate 2 confirmation; Markdown files remain authoritative details linked from it.
- Ask the user to confirm or revise the solution review.
- Include the Gate 2 review artifact path, diagram paths, and exact confirmation points in the chat response.
- Stop before final AI development breakdown.

Do not generate implementation prompts until the Gate 2 review is confirmed or the user explicitly says to proceed with assumptions.

## Gate Re-Open Rule

If, after a gate is confirmed, new verified facts contradict confirmed content:

1. Stop producing downstream artifacts that depend on the contradicted content.
2. Raise the conflict to the user immediately as a blocking question.
3. Move the stage back to `business-feedback` or `solution-feedback` and record the re-open event in the status file.
4. Revise only the affected sections, mark them as revised, and ask the user to re-confirm the changed parts only.
5. Update any downstream artifacts already generated from the old content.

## Finalize Mode

Finalize mode starts only after the Gate 2 solution review is confirmed or the user explicitly says to proceed with assumptions.

Required behavior:

- Read `00-spec-workflow-status.md`, `00-stage-manifest.md`, and `00-context-inventory.md` before generating final package files.
- Use `30-approved-feature-baseline.md` as the approved summary of the confirmed gates.
- Break the feature into human-reviewable AI development items.
- For greenfield projects, make the first bootstrap task invoke `project-rules-init` with the user-confirmed Gate 2 architecture. Create any remaining project skeleton, package manager, test runner, linting, routing, database tooling, or app-shell bootstrap tasks before feature behavior tasks.
- Create task input packages and ready-to-copy prompts.
- Add machine-checkable split fields, BDD coverage, EARS coverage, required Test IDs, validation mode, and validation contract rows to each task.
- Implementation review and test handoff is distributed across `24-gate2-test-strategy.md`, `34-final-traceability-matrix.md`, `35-final-analysis-report.md`, `35a-final-readiness-result.md`, and `tasks/TASK-xxx.md`.
- Prompts are per-task files generated from `tasks/TASK-xxx.md` using `templates/tdd-prompt.template.md`.
- Create `37-implementation-package-approval.md` only when the team explicitly requires a named approval record.
- Create the standalone HTML dashboard with readiness result.
- Treat `31-final-task-index.md` as the Markdown source of truth for per-task review status. The dashboard may store local status and export updates, but shared status must be reconciled back to Markdown.
- The dashboard must support the intended one-task-at-a-time loop: copy one prompt, implement one task, review evidence, mark the task accepted or blocked, then proceed.

## Optional Post-Implementation Convergence

Optional post-implementation convergence runs after implementation evidence is available. It is not required for the final specification package to be ready for implementation.

Required behavior:

- Collect or update `implementation-evidence.md`.
- Compare implementation evidence against the approved baseline.
- Create `40-convergence-report.md`.
- Write `verified-context-update.md` only when evidence supports the update.
- Update `.ai-dev/context/project-context.md` only after verified convergence.
- Do not promote any `proposed-context-update.md` fact unless the convergence report links it to implementation evidence.

## One-Shot Mode

One-shot mode is not the default. Use it only when the user explicitly requests a one-pass complete package or explicitly approves proceeding with assumptions.

Rules:

- The context scan and existing architecture verification or greenfield design confirmation still run internally; project-context write-back happens only through optional post-implementation convergence when evidence supports it.
- One-shot mode does not stop at Gate 1 or Gate 2 confirmation points. It is allowed only after the user explicitly requests one-pass generation or explicitly approves documented assumptions.
- One-shot mode still creates `09-gate1-flow-sketch.md` and `19-gate2-solution-sketch.md` when applicable, but marks their human confirmation as pre-approved by the user's one-shot instruction and documented assumptions.
- Ask at most 8 critical business clarification questions per round and at most 8 critical solution clarification questions per round if needed.
- Generate the full package only after resolving high-impact ambiguity or documenting assumptions, with `UNVERIFIED` tags where the user accepted gaps.
- Keep generated development items small and reviewable.

## Stop Conditions

Stop and ask the user when:

- No clear feature name can be inferred.
- The requirement conflicts with itself.
- A high-impact business rule is missing.
- In existing mode, an architecture source for an in-scope system is unknown or unread and a Gate 2 artifact would need it.
- In greenfield mode, a blocking technology or architecture choice is unresolved and Gate 2 would need it.
- A flow or diagram would need a component that is not in the context inventory.
- A non-trivial Gate 1 flow sketch or Gate 2 solution sketch has not been confirmed, skipped with a reason, or explicitly pre-approved by one-shot instructions.
- Verified facts contradict confirmed gate content.
- The Gate 1 draft or Gate 2 review has not been confirmed.
- The requested output would require modifying source code.

Do not stop only because SVG rendering is unavailable. Keep the authoritative `.mmd` files and add the standard rendering-skipped note from `references/mermaid-rendering.md`.

## Resume Behavior

When a feature folder already exists, read `00-spec-workflow-status.md` first, then `00-stage-manifest.md`, then `00-context-inventory.md`, and continue from `Next AI Action`.

If `00-stage-manifest.md` is missing but generated artifacts exist, recreate it from the optimized artifacts that are present before changing any stage artifact.

If the user asks to continue but does not identify the feature name:

- Resume automatically only when `.ai-dev/features/` contains exactly one feature folder.
- If multiple feature folders exist, list them and ask the user which one to continue.
- If no feature folder exists, ask for the requirement source or feature name.

When the user provides a previously missing architecture source:

- Read and verify it.
- Update the context inventory and the status file.
- Record verified facts in `00-context-inventory.md`; derive proposed context updates during Gate 2 and promote them to `.ai-dev/context/project-context.md` only after verified convergence.
- Revise any Gate 2 artifacts affected by the new facts and ask the user to re-confirm the changed parts.

Do not restart from the source requirement unless:

- The status file is missing.
- The user asks to restart.
- The existing files are inconsistent and cannot be reconciled.

When the status file is missing but other generated files exist, recreate it from the optimized files that are present and ask only for missing high-impact information.
