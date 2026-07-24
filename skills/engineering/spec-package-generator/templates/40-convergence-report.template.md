---
artifactId: 40-convergence-report
stage: convergence
status: template
version: 1
dependsOn:
  - 30-approved-feature-baseline.template.md
  - implementation-evidence.template.md
invalidates:
  - verified-context-update.template.md
summary: Convergence report template for implementation evidence reconciliation.
keyDecisions: []
openQuestions: []
---

# Convergence Report

## Implementation Evidence

| Evidence ID | Source | Summary | Result |
|---|---|---|---|

## Comparison With Approved Baseline

| Baseline Item | Evidence ID | Matches? | Notes |
|---|---|---|---|

## Gaps

| Gap | Severity | Required Follow-Up |
|---|---|---|

## Proposed Context Update Verification

| Fact ID | Proposed Fact | Evidence ID | Decision |
|---|---|---|---|

Allowed decisions:

- `promote`: evidence supports writing the fact through `verified-context-update.md`.
- `defer`: evidence is incomplete; do not update project context.
- `reject`: implementation contradicts the proposed fact; do not update project context.

## Verified Context Update

Create or update `verified-context-update.md` for every proposed fact evaluated during convergence. Do not update `.ai-dev/context/project-context.md` unless the verified context update marks the fact `promote` and convergence evidence supports the change.
