# Constitution Governance Reference

Use this reference for constitution loading, amendment classification, and scope separation.

## Constitution Scopes

- Skill workflow constitution: rules for how the spec-package-generator workflow behaves.
- Project implementation constitution: rules for how future implementation tasks should code and test.

## Loading Terms

Use these terms:

- load skill baseline constitution
- load project constitution if available
- load feature-scoped approved exceptions if available
- resolve effective constitution set
- classify proposed amendments

Do not use ambiguous phrasing such as "load technical Constitution".

## Amendment Types

- Governance amendment: workflow, quality, safety, AI behavior, evidence, or review rules.
- Architecture-dependent amendment: architecture changes that may not yet exist in the codebase.

## Timing Rules

- Governance amendments may become effective after Gate 2 approval.
- Architecture-dependent amendments stay proposed or approved-pending-implementation until convergence, explicit adoption approval, or explicit new-work-only scope.

## Required Topics

The project implementation constitution should cover:

- SOLID
- KISS
- YAGNI
- Separation of concerns
- Minimal change
- No unrelated refactoring
- TDD
- Contract compatibility when verified released contracts or active consumers exist
- Security
- Completion evidence
