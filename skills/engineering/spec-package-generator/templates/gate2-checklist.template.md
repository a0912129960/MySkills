---
artifactId: gate2-checklist
stage: gate2
status: template
version: 1
dependsOn:
  - 00-context-inventory.template.md
  - 19-gate2-solution-sketch.template.md
  - 20-gate2-project-impact.template.md
  - 21-gate2-technical-design.template.md
  - 22-gate2-constitution-compliance.template.md
  - 24-gate2-test-strategy.template.md
  - 25-gate2-review.template.html
  - proposed-context-update.template.md
invalidates: []
summary: Gate 2 review checklist template.
keyDecisions: []
openQuestions: []
---

# Gate 2 Checklist

## Technical Boundary

- [ ] Gate 2 started only after Gate 1 approval.
- [ ] Existing architecture sources were inspected or explicitly recorded as missing; greenfield planned architecture was confirmed as design.
- [ ] Missing critical existing evidence blocks readiness unless formally accepted as UNVERIFIED risk; greenfield planned components needed by Gate 2 are confirmed-design.
- [ ] Gate 2 produced proposed context updates only.
- [ ] Gate 2 did not write to current project context.

## Required Artifacts

- [ ] `00-context-inventory.md` exists and records Gate 2 evidence status, risk level, and open context gaps.
- [ ] `19-gate2-solution-sketch.md` was confirmed, skipped with a reason, or explicitly pre-approved by one-shot instructions.
- [ ] `20-gate2-project-impact.md` exists and is ready for review.
- [ ] `21-gate2-technical-design.md` exists and is ready for review.
- [ ] `22-gate2-constitution-compliance.md` exists and is ready for review.
- [ ] `24-gate2-test-strategy.md` exists and is ready for review.
- [ ] `25-gate2-review.html` exists as a derived review surface.
- [ ] `proposed-context-update.md` exists when new context facts discovered during Gate 2 should be proposed for future update.
- [ ] Gate 2 diagrams exist when the design includes flows or cross-project interactions.

## Impact Checks

- [ ] Impacted systems are listed with role, evidence, and risk.
- [ ] Cross-project changes are tied to verified sources.
- [ ] External dependencies and compatibility risks are explicit.

## Technical Design Checks

- [ ] Design decisions trace back to Gate 1 requirements.
- [ ] Architecture claims cite inspected files or accepted UNVERIFIED evidence.
- [ ] Data, API, state, security, and error-handling impacts are covered when applicable.
- [ ] No design section overrides PRD/EARS/BDD behavior without change control.

## Constitution Checks

- [ ] Effective constitution rules are identified.
- [ ] Proposed amendments have status, scope, effective timing, approval, and affected artifacts.
- [ ] Implementation rules remain in constitution artifacts, not in `SKILL.md`.

## Test Strategy Checks

- [ ] Critical requirements have Test IDs.
- [ ] Test IDs that require executable validation have Test Contracts or planned contracts.
- [ ] Contract tests include inputs, fixture, execution method, assertions, red-state failure, pass criteria, evidence, automation, owner, and status.
- [ ] Final readiness blockers are visible.

## Review Decision

- [ ] Gate 2 contradictions are resolved or recorded as blockers.
- [ ] Accepted risks and UNVERIFIED evidence are recorded.
- [ ] User approval or requested changes are recorded in workflow status.
