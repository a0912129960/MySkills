# EARS BDD TDD Reference

Use this reference when converting product behavior into precise requirements and testable implementation items.

## Layer Ownership

- PRD: direction, scope, user scenarios, business rules
- EARS: precise observable requirements
- BDD: acceptance examples
- TDD: implementation discipline for future tasks

## Rules

- Gate 1 must stay at PRD, EARS, and BDD level.
- Gate 1 must not include architecture verification.
- BDD scenarios should be independently testable.
- Every critical EARS requirement must map to at least one BDD scenario unless explicitly marked `manual-only` or `not-scenario-suitable` with a reason.
- Gate 2 must map relevant BDD scenarios to Test IDs.
- Task Manifests must mark when TDD applies; `implement-spec-task` establishes
  red-state evidence before implementation whenever behavior is testable
  through a public seam.
- Automated and semi-automated Test IDs require a Test Contract before a task can be marked TDD-ready.
- TDD-ready automated or semi-automated tasks must define red-state evidence, pass criteria, green-state evidence, and fallback behavior when automation is not possible.
- Manual validation tasks do not require red-state evidence, but they must define inspection points, pass criteria, evidence output, and user-visible completion evidence.

## Clarify / Checklist / Analyze / Converge

- Clarify: ask only the critical unanswered questions that block an accurate spec.
- Checklist: validate requirement quality and coverage.
- Analyze: compare normative artifacts for consistency.
- Converge: compare implementation evidence with the approved baseline.
