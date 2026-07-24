---
name: implement
description: Implement a small task stated directly by the human or captured in a to-spec artifact, with project-grounded validation and final code review. Use only when explicitly invoked.
disable-model-invocation: true
---

# Implement

Use this lightweight workflow for a small direct task or a `to-spec` artifact.
Do not use it to execute or wrap a formal `spec-package-generator` package.

## Ground the change

Read applicable `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, architecture and
ADR guidance, the supplied requirement, and nearby representative
implementations. State the observable behavior being changed.

Load `codebase-design` when the task creates or changes a module interface,
seam, adapter, dependency direction, or architectural responsibility.

## Build and verify

Use `tdd` for every behavior change testable through a public seam. When TDD
does not apply, state why in one sentence and name the alternative verification.
Work in small complete slices and run the narrowest useful checks as you go.

Run all required project validation at the end, then invoke `code-review` over
the actual change set. Fix required findings and rerun affected checks. A failed
required check prevents a successful completion report.

Report changed paths, red/green or alternative evidence, final validation, and
remaining risks. Do not create a branch, commit, stage, push, or mutate an issue
tracker unless the human explicitly requested that Git or tracker action.
