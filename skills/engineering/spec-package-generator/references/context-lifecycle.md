# Context Lifecycle Reference

Use this reference for project context and architecture evidence timing.

## Scope

- `.ai-dev/context/project-context.md` stores reusable verified project facts.
- `00-context-inventory.md` stores feature-specific evidence and verification status.
- `proposed-context-update.md` stores proposed reusable facts before convergence.
- `verified-context-update.md` stores evidence-backed facts after convergence.

## Timing Rules

- Gate 1 may read project context for lightweight context scan only.
- Gate 1 must not perform architecture verification or write back to project context.
- Gate 1 must not load constitution or implementation guidance.
- Gate 2 may read project context and produce `proposed-context-update.md`.
- Gate 2 does not update current project context directly.
- Gate 2 must not create `verified-context-update.md`.
- Convergence may create `verified-context-update.md` only after implementation evidence exists and supports the proposed facts.
- `.ai-dev/context/project-context.md` may be updated only after verified convergence supports the update.

## Project Modes

Use these project modes in `00-spec-workflow-status.md` and `00-context-inventory.md`:

- `existing`: relevant implementation sources already exist and Gate 2 must be grounded by verification.
- `greenfield`: the project or feature has no implementation sources yet; Gate 2 is grounded by user-confirmed planned architecture and schema design.
- `unknown`: use only during intake before the agent can classify the project.

Greenfield mode must not block because code, schemas, entry points, or test runners do not exist yet. Record planned components in `00-context-inventory.md` and move them from `planned` to `confirmed-design` only after user confirmation.

## Proposed Context Updates

`proposed-context-update.md` is a Gate 2 proposal, not a current-fact file.

It must record:

- Proposed reusable facts.
- Source Gate 2 artifact and context inventory evidence.
- Target project-context section.
- Verification required after implementation.
- Status for each fact: `proposed`, `rejected`, or `deferred`.

Do not copy proposed facts into `.ai-dev/context/project-context.md` during Gate 2 or final package generation.

Proposal status values describe the Gate 2 proposal lifecycle:

- `proposed`: candidate reusable fact awaiting convergence evidence.
- `deferred`: candidate fact intentionally postponed before convergence.
- `rejected`: candidate fact rejected before convergence.

## Verified Context Updates

`verified-context-update.md` is created during convergence only.

It must record:

- Every proposed fact evaluated during convergence.
- Implementation evidence that proves or disproves the fact.
- Convergence report reference.
- Final action: `promote`, `defer`, or `reject`.

Only facts with final action `promote` may be applied to `.ai-dev/context/project-context.md`.

Final action values describe the convergence decision:

- `promote`: implementation evidence supports applying the fact to project context.
- `defer`: evidence is incomplete; keep the fact out of project context.
- `reject`: implementation evidence contradicts the proposed fact.

## Sequential Feature Bootstrapping

`proposed-context-update.md` may be used by later feature planning as a read-only hint to reduce rediscovery work.

Rules:

- Proposed updates are advisory only; they are not current project context.
- A later feature may cite a proposed update in its context inventory, but it must still re-check the relevant source before treating the fact as `verified`.
- Only `verified-context-update.md` from convergence may be promoted to `.ai-dev/context/project-context.md`.
- This intentionally trades some repeated verification for avoiding unimplemented or abandoned designs becoming reusable project facts.

## Context Inventory Risk Level

Use these values in `00-context-inventory.md`:

- `low`: single-system or already-known behavior with verified sources and limited downstream impact.
- `medium`: verified behavior with multiple modules, contract handling for verified released contracts or active consumers, or moderate release coordination.
- `high`: cross-system behavior, contract changes, data transition or adoption work, release ordering, or incomplete verification risk.
- `critical`: security, data integrity, compliance, irreversible operations, or user-accepted unverified architecture risk.

Greenfield status values:

- `planned`: proposed architecture, component, schema, or tooling choice awaiting user confirmation.
- `confirmed-design`: user-confirmed planned architecture used as Gate 2 grounding before implementation exists.

Set the initial value during the lightweight scan when obvious from the requirement, then revise it during existing architecture verification or greenfield design confirmation.

## Project Context Content

Project context should contain:

- Systems and repos
- Verified entry points
- Integration mechanisms
- Response formats
- Conventions
- Last verified date

Feature-specific decisions must stay in the feature folder.
