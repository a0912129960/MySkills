---
artifactId: 31-final-task-index
stage: final
status: template
version: 2
dependsOn:
  - 30-approved-feature-baseline.template.md
  - 24-gate2-test-strategy.template.md
invalidates:
  - 34-final-traceability-matrix.template.md
  - 35a-final-readiness-result.template.md
summary: Final vertical capability-slice and parallel-wave task index template.
keyDecisions: []
openQuestions: []
---

# Final Task Index

## Feature

## Breakdown Summary

## Breakdown Strategy

Describe how the feature is divided by cohesive user- or system-observable outcomes. Explain any unavoidable enabler tasks and name the capability slices they unlock.

## Dependency And Parallel Plan

| Wave | Task ID | Title | Project | Capability Outcome | Depends On | Can Run With | Exclusive Paths / Shared Contract | Integration Owner | Risk | Primary Test IDs | BDD Scenarios | Slice Compliant? | TDD Ready? | Review Focus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

For greenfield projects, list bootstrap tasks before feature behavior tasks when foundational project files or tooling do not exist yet. Tasks in the same wave may run concurrently only when dependency and ownership fields show that doing so is safe.

## Bootstrap Task Plan

Use this section for greenfield projects.

| Order | Task ID | Bootstrap Area | Creates / Confirms | Validation Mode | Evidence |
|---|---|---|---|---|---|

## Task Review Status

This table is the Markdown source of truth for per-task review status across sessions. Keep `36-final-dashboard.html` local browser status reconciled back here or into `implementation-evidence.md`.

Allowed status values: `not-started`, `in-progress`, `ready-for-review`, `accepted`, `blocked`, `deferred`.

| Task ID | Status | Reviewer | Review Date | Evidence Link | Blocked Reason | Deferred Reason | Dependencies Satisfied? | Eligible Wave? |
|---|---|---|---|---|---|---|---|---|

## Capability Slice Decisions

For each feature task, confirm that it delivers one cohesive observable outcome through an end-to-end validation route. Layer and file counts are planning signals only. For each enabler, justify why it cannot safely live in a capability slice and name the slices it unlocks.

| Task ID | Type | Observable Outcome / Validated Enabler | Demo Or Validation Route | Estimated Files | Layers | Vertical-Slice Compliant | Exception And Unlocked Tasks |
|---|---|---|---|---|---|---|---|

## Parallel Ownership And Integration

| Task ID | Wave | Exclusive Ownership Paths | Shared Read-Only Contract | Integration Seam | Integration Owner | Merge / Release Order | Conflict Risk |
|---|---|---|---|---|---|---|---|

## Task Files To Generate

| Task ID | Task File | Prompt File | Status |
|---|---|---|---|
