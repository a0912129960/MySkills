---
artifactId: 31-final-task-index
stage: final
status: template
version: 1
dependsOn:
  - 30-approved-feature-baseline.template.md
  - 24-gate2-test-strategy.template.md
invalidates:
  - 34-final-traceability-matrix.template.md
  - 35a-final-readiness-result.template.md
summary: Final task index template.
keyDecisions: []
openQuestions: []
---

# Final Task Index

## Feature

## Breakdown Summary

## Breakdown Strategy

## Recommended Development Order

| Order | Task ID | Title | Project | Goal | Depends On | Risk | Primary Test IDs | BDD Scenarios | Split Compliant? | TDD Ready? | Review Focus |
|---|---|---|---|---|---|---|---|---|---|---|---|

For greenfield projects, list bootstrap tasks before feature behavior tasks when foundational project files or tooling do not exist yet.

## Bootstrap Task Plan

Use this section for greenfield projects.

| Order | Task ID | Bootstrap Area | Creates / Confirms | Validation Mode | Evidence |
|---|---|---|---|---|---|

## Task Review Status

This table is the Markdown source of truth for per-task review status across sessions. Keep `36-final-dashboard.html` local browser status reconciled back here or into `implementation-evidence.md`.

Allowed status values: `not-started`, `in-progress`, `ready-for-review`, `accepted`, `blocked`, `deferred`.

| Task ID | Status | Reviewer | Review Date | Evidence Link | Blocked Reason | Deferred Reason | Next Eligible? |
|---|---|---|---|---|---|---|---|

## Split Decision Notes

For each task, explain why the scope is small enough for one focused human review. Split any task that touches more than one major layer, more than roughly 3-5 likely files, or more than one independently testable behavior unless the coupling is explicitly justified.

| Task ID | Estimated Modified File Count | Major Layers Touched | Single Independently Testable Behavior | Split-Rule Compliant | Exception Justification |
|---|---|---|---|---|---|

## Task Files To Generate

| Task ID | Task File | Prompt File | Status |
|---|---|---|---|
