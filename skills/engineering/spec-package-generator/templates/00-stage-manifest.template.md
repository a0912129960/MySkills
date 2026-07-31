---
artifactId: 00-stage-manifest
stage: intake
status: template
version: 2
dependsOn: []
invalidates: []
summary: Stage manifest template that defines optimized artifact order.
keyDecisions: []
openQuestions: []
---

# Stage Manifest

## Feature

- Feature name:
- Generated time:
- Package type: optimized
- Project mode: greenfield / existing / unknown
- Current stage:
- Resume stage:

## Logical Order

| Order | Stage ID | Artifact | Purpose | Status | Depends On |
|---|---|---|---|---|---|

## Durable Decision Clarification Status

- Status: not-started / in-progress / waiting-for-user / complete / superseded
- Decision log: `14-decision-log.md`
- Open-question register: `15-open-questions.md`
- Active Question ID:
- Active-question source: `00-spec-workflow-status.md`

## Gate 1 Flow Sketch Status

- Required: yes/no (required in greenfield mode)
- Status: not-started / drafted / waiting-for-user / confirmed / skipped-trivial / superseded
- Artifact: `09-gate1-flow-sketch.md`
- Draft diagram: `diagrams/user-flow.mmd`

## Gate 2 Solution Sketch Status

- Required: yes/no (required in greenfield mode)
- Status: not-started / drafted / waiting-for-user / confirmed / skipped-trivial / superseded
- Artifact: `19-gate2-solution-sketch.md`
- Draft API diagram: `diagrams/api-flow.mmd`
- Draft cross-project diagram: `diagrams/cross-project-flow.mmd`

## Task Plan Gate Status

- Status: not-started / drafted / waiting-for-user / human-confirmed / revision-requested / superseded
- Artifact: `32-task-plan-review.md`
- Confirmed Task IDs:
- Tasks returned for re-slicing:
- Gate reopened:

## Artifact Ownership

| Concern | Owning Artifact | Conflict Rule |
|---|---|---|

## Artifact Invalidation

| Artifact | Invalidates When Changed |
|---|---|

## Artifact Conflicts

| Conflict | Current Owner | Other Artifact | Resolution | User Confirmation Needed? |
|---|---|---|---|---|

## Resume Instructions

- Read `00-spec-workflow-status.md` first.
- Read this manifest second.
- Continue from:
