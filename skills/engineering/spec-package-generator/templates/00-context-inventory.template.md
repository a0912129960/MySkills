---
artifactId: 00-context-inventory
stage: intake
status: template
version: 1
dependsOn:
  - 00-source-requirement.template.md
  - 00-spec-workflow-status.template.md
invalidates:
  - 10-gate1-prd.template.md
  - 20-gate2-project-impact.template.md
summary: Architecture evidence inventory template.
keyDecisions: []
openQuestions: []
---

# Context Inventory

## Feature

- Feature name:
- Project mode: greenfield / existing / unknown
- Generated time:
- Last updated:

## Project Context Carry-Over

- `project-context.md` found: yes | no
- Systems carried over:

## Repo Context Files Read

| File | Found? | Key Takeaways |
|---|---|---|

## Systems Or Planned Components In Scope

| System / Component | Role In Feature | Architecture Source Or Planned Design Source | Status | Risk Level | Key Facts Or Planned Decisions |
|---|---|---|---|---|---|

Status values: `verified`, `missing`, `user-will-provide`, `accepted-unverified`, `planned`, `confirmed-design`.

Use `planned` and `confirmed-design` only for greenfield project mode. A `confirmed-design` entry is approved planned architecture, not evidence of existing implementation.

## Requirement-Cited References

| Reference | Found At | Read? | Notes |
|---|---|---|---|

## Open Context Gaps

| Gap | Blocks Gate 2? | Asked User? | User Answer |
|---|---|---|---|

## User-Provided Sources Log

| Date | Provided Source | Systems Verified |
|---|---|---|

## Proposed Context Updates

| Date | Proposed Fact | Systems | Target File | Status |
|---|---|---|---|---|

## Verified Context Updates

| Date | Verified Fact | Systems | Evidence | Target File |
|---|---|---|---|---|
