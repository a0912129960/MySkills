---
artifactId: test-case-contract
stage: gate2
status: template
version: 1
dependsOn:
  - 24-gate2-test-strategy.template.md
invalidates: []
summary: Executable test contract template for future implementation planning.
keyDecisions: []
openQuestions: []
---

# Test Case Contract

### TEST-UNIT-xxx / TEST-CONTRACT-xxx

- Title:
- Purpose:
- BDD Scenario ID:
- EARS ID:
- Requirement references:
- Artifact references:
- Test level:
  - unit
  - integration
  - contract
  - E2E
  - manual
- Automation mode:
  - automated
  - semi-automated
  - manual
- Test entry point:
- Fixture / input:
- Files inspected:
- Execution method:
- Assertions:
- Expected red-state failure:
- Pass criteria:
- Evidence output:
- Manual evidence:
- Owning task:
- Fallback if not automatable:
- Status:

## Notes

- Use this template for any stable Test ID that needs executable validation, including `TEST-UNIT-xxx` and `TEST-CONTRACT-xxx`.
- Use `automated` only for local checks that can decide pass/fail without human judgment.
- Use `semi-automated` when local commands collect evidence and a reviewer confirms semantics.
- Use `manual` when reviewer inspection is required.
- Automated and semi-automated contracts must define the entry point, fixture/input, assertions, expected red-state failure, pass criteria, evidence output, and owning task.
- For bootstrap contracts that create the project skeleton or test runner, expected red-state failure may be the absence of required files, scripts, or configuration. Do not require a test-runner command before the task creates it.
- Manual contracts do not require red-state evidence, but they must define inspection points, pass criteria, evidence output, manual evidence, and owning task.
- Do not require network access.
