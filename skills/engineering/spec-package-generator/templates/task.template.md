---
artifactId: task
stage: final
status: template
version: 2
dependsOn:
  - 31-final-task-index.template.md
  - 30-approved-feature-baseline.template.md
invalidates:
  - tdd-prompt.template.md
summary: Human-reviewable vertical capability-slice task contract template.
keyDecisions: []
openQuestions: []
---

# Task

## Item

- Task ID:
- Title:
- Project:
- Task type: capability-slice / enabler / bootstrap / integration / documentation

## Goal

## Capability Outcome

- User- or system-observable outcome:
- Who or what can observe it:
- How to demonstrate it:
- Public validation seam:
- Runnable state after completion:

## Vertical Slice Contract

- Cohesive acceptance bundle:
- Independently demonstrable: yes/no
- End-to-end validation route:
- Vertical-slice compliant: yes/no
- If no, enabler type: bootstrap / shared-contract / migration / platform / other
- Enabler exception justification:
- Capability task IDs unlocked:
- Estimated modified file count:
- Major layers touched:
- Review-size note:

File and layer estimates are planning signals, not automatic split gates. Keep tightly coupled layers together when they are required for the capability outcome.

## Dependencies And Parallelism

- Depends on:
- Dependency acceptance required:
- Parallel wave:
- Can run in parallel with:
- Exclusive ownership paths:
- Shared read-only contracts:
- Shared contract status: draft / frozen / not-applicable
- Integration seam:
- Integration owner:
- Merge or release order:
- Conflict-avoidance notes:

## In Scope

## Out Of Scope

## Required Input Files

## Allowed To Modify

## Read-Only References

## Files Likely To Modify

## Related Contracts And Test IDs

| BDD Scenario ID | EARS ID | Test ID | Required For This Task? | Notes |
|---|---|---|---|---|

## BDD Scenarios Covered

## EARS Requirements Covered

## BDD Scenarios Explicitly Not Covered

## AI Must Know

- Greenfield first bootstrap task: invoke `project-rules-init` with the user-confirmed Gate 2 architecture before feature implementation.

## AI Must Not Do

## Acceptance Criteria

Acceptance criteria must prove the complete scoped capability outcome, not only the presence of one technical layer.

## Suggested Test Cases

## Risk Level

## TDD / Validation

### Validation Mode

- Validation mode: automated / semi-automated / manual
- Bootstrap validation: yes/no
- Why this mode is appropriate:
- Human evidence required:

### TDD Contract

| Test ID | Automation Mode | Test Entry Point | Fixture / Input | Assertions Or Inspection Points | Expected Red-State Failure | Pass Criteria | Evidence Output | Manual Evidence | Fallback If Not Automatable |
|---|---|---|---|---|---|---|---|---|---|

### Validation Rules

- Create or update the failing test first when the Test ID is automated or semi-automated.
- Run and report red-state evidence before production-code changes for automated or semi-automated Test IDs.
- For bootstrap tasks that create the project skeleton or test runner, red-state evidence may be the absence of the required file, script, or configuration. Do not require executing a test command before the command exists.
- Manual Test IDs do not require red-state evidence, but they must define concrete before/after inspection evidence.
- Implement the smallest change needed to pass this task.
- Keep the complete capability slice working through its public validation seam; do not stop after only one required technical layer is implemented.
- Run and report green-state evidence for automated or semi-automated Test IDs.
- For manual Test IDs, report the exact inspection result and the user-visible evidence.
- If automation is not practical, use an approved semi-automated or manual validation mode with explicit human review evidence.

## Completion Evidence

## Human Review Handoff

- Commands or checks to run:
- Evidence to inspect:
- User-observable result:
- How to see it working:
- What visible behavior proves this task is complete:
- Integration handoff:
- What must be true before starting dependent tasks:
- Review status: not-started / in-progress / ready-for-review / accepted / blocked / deferred
