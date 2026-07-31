---
artifactId: gate1-checklist
stage: gate1
status: template
version: 2
dependsOn:
  - 00-source-requirement.template.md
  - 00-spec-workflow-status.template.md
  - 00-stage-manifest.template.md
  - 10-gate1-prd.template.md
  - 11-gate1-ears.template.md
  - 12-gate1-bdd.template.feature
  - 13-gate1-review.template.html
  - 14-decision-log.template.md
  - 15-open-questions.template.md
invalidates: []
summary: Gate 1 review checklist template.
keyDecisions: []
openQuestions: []
---

# Gate 1 Checklist

## Product Boundary

- [ ] Gate 1 used only product/business context.
- [ ] Gate 1 did not perform architecture verification.
- [ ] Gate 1 did not load constitution or implementation guidance.
- [ ] Gate 1 did not write back to project context.

## Required Artifacts

- [ ] `00-source-requirement.md` exists and preserves the source requirement.
- [ ] `00-spec-workflow-status.md` exists and records current workflow state.
- [ ] `00-stage-manifest.md` exists and records artifact order and resume behavior.
- [ ] `10-gate1-prd.md` exists and is ready for review.
- [ ] `11-gate1-ears.md` exists and is ready for review.
- [ ] `12-gate1-bdd.feature` exists and is ready for review.
- [ ] `13-gate1-review.html` exists as a derived review surface.
- [ ] `diagrams/user-flow.mmd` exists.
- [ ] `14-decision-log.md` exists as durable decision memory.
- [ ] `15-open-questions.md` exists as the canonical question register.

## PRD Checks

- [ ] Goal, users, scope, and non-scope are explicit.
- [ ] Business workflow and business rules are stated.
- [ ] Assumptions are visible.
- [ ] No critical blocking Question ID remains unresolved.
- [ ] Question and Decision IDs link to the canonical governance artifacts.

## EARS Checks

- [ ] Each EARS requirement has an ID.
- [ ] Each EARS requirement maps to a PRD source.
- [ ] Each EARS requirement has a pattern, priority, and verification note.
- [ ] Requirements are observable and testable.
- [ ] EARS requirements do not redefine PRD scope.

## BDD Checks

- [ ] Each scenario maps to one or more EARS IDs.
- [ ] Scenarios use Given/When/Then acceptance examples.
- [ ] BDD examples do not add behavior outside PRD/EARS.
- [ ] Supporting Gate 1 diagrams stay business-level and do not include API, database, or implementation design.

## Review Decision

- [ ] Gate 1 contradictions and critical blocking questions are resolved.
- [ ] Non-blocking questions are recorded for later stages.
- [ ] User approval or requested changes are recorded in workflow status.
