---
artifactId: 24-gate2-test-strategy
stage: gate2
status: template
version: 1
dependsOn:
  - 19-gate2-solution-sketch.template.md
  - 21-gate2-technical-design.template.md
  - 22-gate2-constitution-compliance.template.md
invalidates:
  - 31-final-task-index.template.md
  - 34-final-traceability-matrix.template.md
summary: Gate 2 test strategy template.
keyDecisions: []
openQuestions: []
---

# Test Strategy

## Risk Summary

| Risk | Level | Test Focus |
|---|---|---|

## Critical Behaviors

## Unit Tests

## Integration Tests

## Contract Tests

## End-To-End Tests

## Manual Acceptance

## Test Data

## Environment Requirements

## Failure And Rollback Tests

## Concurrency Tests

## Performance Tests

## Test IDs And Traceability

| Test ID | BDD Scenario ID | EARS ID | Test Level | Automation Mode | Owning Task | Status |
|---|---|---|---|---|---|---|

## Validation Feasibility

| Test ID | Validation Mode | Executable Ready? | Missing Contract Fields | Manual Evidence Required | Fallback | Reason |
|---|---|---|---|---|---|---|

## Test Contract Format

Every Test ID must declare one validation mode: `automated`, `semi-automated`, or `manual`.

Automated and semi-automated Test IDs must have a complete executable contract before final readiness can pass. Manual Test IDs do not require red-state evidence, but they must define concrete human inspection evidence, pass criteria, evidence output, and owning task.

Bootstrap Test IDs may be `manual` or `semi-automated` when the project skeleton, package scripts, or test runner does not exist yet. Use file-existence checks, configuration checks, package script checks, or human inspection evidence. Do not require executable red-state test-runner evidence before the test runner is created.

Required fields:

- Test ID
- BDD Scenario ID
- EARS ID
- Test level: unit, integration, contract, E2E, or manual
- Automation mode: automated, semi-automated, or manual
- Test entry point
- Fixture / input
- Assertions
- Expected red-state failure
- Pass criteria
- Evidence output
- Owning task
- Fallback if not automatable
- Manual evidence when automation mode is `manual`

## Example Test Contracts

| Test ID | BDD Scenario ID | EARS ID | Test Level | Automation Mode | Test Entry Point | Fixture / Input | Assertions / Inspection Points | Expected Red-State Failure | Pass Criteria | Evidence Output | Manual Evidence | Owning Task | Fallback If Not Automatable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
