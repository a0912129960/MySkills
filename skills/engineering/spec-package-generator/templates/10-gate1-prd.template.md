---
artifactId: 10-gate1-prd
stage: gate1
status: template
version: 1
dependsOn:
  - 00-source-requirement.template.md
  - 00-context-inventory.template.md
invalidates:
  - 11-gate1-ears.template.md
  - 12-gate1-bdd.template.feature
summary: Gate 1 PRD template for business direction and scope.
keyDecisions: []
openQuestions: []
---

# PRD

## Intake Context Summary

Use this section only to identify systems, planned greenfield components, source status, and missing architecture sources. Do not include architecture verification, API design, database schema design, or implementation guidance in Gate 1.

| System | Source | Status |
|---|---|---|

## Feature Summary

## User Scenarios

### Scenario Clarification Matrix

Scenario field status values: `extracted`, `assumed`, `asked`, `blocking`, `not-applicable`.

| Scenario ID | Actor / Role | Trigger | Preconditions | Main Flow | Observable Outcome | Exception Flow | State Transition | Permission Rule | Out Of Scope | Acceptance Criteria | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|

## User Stories

## Acceptance Criteria

## Operation Flow

## State Model And Business Rules

## UI Behavior

## Error Scenarios

## Assumptions

## Open Questions

Open question status values are tracked in `15-open-questions.md`: `open`, `answered`, `resolved`, `deferred`, `superseded`.

| Question ID | Layer | Question | Why It Matters | Default Assumption If Unanswered | Affected Artifacts | Blocking? | Decision Link |
|---|---|---|---|---|---|---|---|
