---
artifactId: tdd-prompt
stage: final
status: template
version: 2
dependsOn:
  - task.template.md
invalidates: []
summary: Derived TDD prompt template that mirrors the task contract without redefining behavior.
keyDecisions: []
openQuestions: []
---

# Prompt

## Selected Item

## Files To Read

## Allowed To Modify

## Read-Only References

## Task Goal

## Capability Outcome And Validation Route

## Dependency And Parallel Context

## Implementation Rules

- Implement only the selected task.
- Do not implement future tasks.
- Stop after this task is implemented and evidence is reported; do not start another task.
- Do not modify read-only paths.
- Do not refactor unrelated code.
- Keep changes minimal and reviewable while completing the entire scoped capability outcome across every required layer.
- Do not stop at a database-only, API-only, or UI-only intermediate state when the task contract requires an end-to-end result.
- Follow the approved baseline, task contract, technical design, and test strategy.
- Stop and ask if task scope, allowed paths, contracts, or acceptance criteria are unclear.

## Before Coding

- Read the selected task file first.
- Re-read current applicable `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, architecture guidance, and ADRs rather than relying on rules copied into this prompt.
- Confirm allowed-to-modify paths and read-only references.
- Confirm the capability outcome, public validation seam, demo route, and runnable state required at completion.
- Confirm dependencies are eligible, the parallel wave is current, exclusive ownership paths do not conflict, and any shared contract is frozen as required.
- Identify the task's BDD scenarios, EARS requirements, required Test IDs, and validation contract rows.
- Identify each Test ID's validation mode: automated, semi-automated, or manual.
- Identify whether this is a bootstrap task and whether the test runner or package script exists yet.
- Load `codebase-design` when the task creates or changes a module interface, seam, adapter, dependency direction, or architectural responsibility; ordinary local edits do not need it.
- Identify the smallest complete vertical implementation path before editing.
- For automated or semi-automated Test IDs, create or update the failing test first.
- Run and report red-state evidence before production-code changes only for automated or semi-automated Test IDs.
- For bootstrap tasks that create the project skeleton or test runner, use the task's bootstrap validation contract. Do not run or invent test commands before the task creates them.
- For manual Test IDs, identify the required before/after human inspection evidence before editing.
- If automation is not practical, use the approved semi-automated or manual validation mode from the task contract. Stop and ask only when no fallback is approved.

## Review And Test Expectations

- Run the task's required validation.
- Run and report green-state evidence after the implementation passes for automated or semi-automated Test IDs.
- For manual Test IDs, report the exact inspection evidence and user-visible result.
- Report commands/checks run and results.
- Report changed files.
- Report any deviations from the task contract.
- Demonstrate the complete capability outcome through the task's public validation seam.
- Report integration-seam and shared-contract evidence when other tasks may be running concurrently.

## After Coding

- Provide completion evidence from the task.
- Provide the human review handoff: commands or inspection steps, expected evidence, and what must pass before the next task starts.
- Report changed files, validation evidence, and the human review checklist.
- Do not mark future tasks complete.
- Do not begin a dependent task until its prerequisites are accepted or explicitly deferred with a safe exception in `31-final-task-index.md` or implementation evidence. Other workers may continue independent eligible tasks in the same wave.
