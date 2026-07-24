---
artifactId: 35a-final-readiness-result
stage: final
status: template
version: 1
dependsOn:
  - 34-final-traceability-matrix.template.md
  - 35-final-analysis-report.template.md
invalidates:
  - 36-final-dashboard.template.html
summary: Persisted machine-readiness result template.
keyDecisions: []
openQuestions: []
---

# Readiness Result

## Result

Pass / Fail:

## Blocking Issues

| Check | Blocking Issue | Affected Artifact | Required Fix |
|---|---|---|---|

## Non-Blocking Notes

## Approval

## Required Readiness Checks

| Check | Result | Evidence Artifact | Notes |
|---|---|---|---|
| Stage manifest current |  | `00-stage-manifest.md` |  |
| Gate confirmations or approved assumptions recorded |  | `00-spec-workflow-status.md` |  |
| Clarification matrix has no blocking open questions |  | `15-open-questions.md` |  |
| Critical EARS rows map to BDD scenarios or explicit exceptions |  | `11-gate1-ears.md`, `12-gate1-bdd.feature` |  |
| BDD scenarios map to Test IDs |  | `24-gate2-test-strategy.md` |  |
| Test IDs map to tasks |  | `31-final-task-index.md`, `34-final-traceability-matrix.md` |  |
| Automated and semi-automated Test IDs have complete Test Contracts |  | `24-gate2-test-strategy.md`, `tasks/TASK-xxx.md` |  |
| Task split fields are compliant or justified |  | `31-final-task-index.md`, `tasks/TASK-xxx.md` |  |
| Task prompts are derived from task contracts and include BDD/Test ID/validation instructions |  | `prompts/TASK-xxx.prompt.md` |  |
| Dashboard source inputs are ready for rendering |  | `30-approved-feature-baseline.md`, `31-final-task-index.md`, `34-final-traceability-matrix.md`, `35-final-analysis-report.md`, `35a-final-readiness-result.md`, `tasks/TASK-xxx.md`, `prompts/TASK-xxx.prompt.md` | Dashboard validation happens after this readiness result and must not be a prerequisite for readiness itself. |

## Hard Fail Rules

- Fail when any blocking question remains unresolved.
- Fail when a critical EARS requirement lacks BDD coverage and lacks an explicit exception reason.
- Fail when a relevant BDD scenario does not map to a Test ID.
- Fail when an automated or semi-automated Test ID lacks entry point, fixture/input, assertions, expected red-state failure, pass criteria, evidence output, or owning task.
- For bootstrap Test IDs that create the project skeleton or test runner, expected red-state failure may be the absence of required files, scripts, or configuration instead of an executable failing test command.
- Fail when a manual Test ID lacks explicit human inspection evidence, pass criteria, evidence output, or owning task.
- Fail when a task violates the split rule without an exception justification.
- Fail when a task prompt omits required BDD scenarios, Test IDs, validation mode, or validation evidence instructions.
