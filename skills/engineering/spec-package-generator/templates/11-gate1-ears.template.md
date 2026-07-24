---
artifactId: 11-gate1-ears
stage: gate1
status: template
version: 1
dependsOn:
  - 10-gate1-prd.template.md
invalidates:
  - 12-gate1-bdd.template.feature
summary: Gate 1 EARS template for precise and testable requirements.
keyDecisions: []
openQuestions: []
---

# EARS

## Requirement Mapping

| EARS ID | PRD Reference | Source Question / Decision ID | Pattern | Requirement Statement | Priority | Verification Note | BDD Coverage |
|---|---|---|---|---|---|---|---|

## Notes

- Every EARS row must map to a PRD source.
- Every EARS row must cite the question, assumption, or decision that clarified it when the source requirement was incomplete.
- Every EARS statement must be observable and testable.
- EARS must not redefine PRD scope.
- Every critical EARS row must map to at least one BDD scenario unless marked `manual-only` or `not-scenario-suitable` with a reason.
