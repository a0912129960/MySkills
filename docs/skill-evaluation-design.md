# Skill Evaluation Design

Status: Draft. Confirmed decisions are normative; unresolved decisions do not define a
release gate.

## Purpose

This document defines how MySkills determines whether a Managed Skill satisfies its intended
behavior. It is the normative source for evaluation scope, cases, scoring, escalation, and
acceptance policy.

MySkills as a whole remains in development acceptance. The evaluation subsystem is undergoing
a requirements revision, so existing evaluation results remain historical evidence but do not
prove conformance with the revised model until that model is implemented and run.

## Document boundaries

- `skill-consolidation-design.md` defines repository architecture and how evaluation integrates
  with creation, installation, and release.
- This document defines what is evaluated and how evaluation outcomes are classified.
- `skill-attestation-workflow.md` is an operator runbook for executing evaluations, producing
  reports, and retaining evidence. It does not define acceptance policy.
- `CONTEXT.md` defines shared domain terminology, not evaluation procedures.

## Confirmed evaluation policy

### Capability-based evaluation

Evaluation is selected by Skill capability rather than applying every test type to every Skill:

- Every Managed Skill is evaluated for structure, description-to-capability consistency,
  explicit invocation, and final task outcome.
- An Implicit-invocation Skill is additionally evaluated with positive, negative, boundary,
  paraphrase, and library-regression cases.
- A Skill that uses tools or can cause side effects is additionally evaluated for required
  trajectory constraints, including parameters, ordering, safety, and unacceptable side
  effects.
- Red-team, shadow-mode, and canary evaluation apply only when the Skill's risk and real
  integration capabilities make those stages relevant.

### Invocation classification

Every new or reevaluated Managed Skill declares whether it is an Explicit-invocation Skill or
an Implicit-invocation Skill before its cases are defined. The classification is canonical:
the same Skill has the same classification on every supported platform.

An Explicit-invocation Skill must succeed when explicitly invoked and must not be selected
implicitly. It is not graded on a positive implicit-trigger rate.

### Platform-specific results

Claude and Codex are evaluated and scored independently. Their results cannot offset each
other.

When exactly one platform reaches its required threshold, the evaluation requires human
review and does not receive an automatic pass. A completed platform suite is not
automatically retried to seek a better score. Any later rerun is a new, explicitly authorized
evaluation.

## Unresolved decisions

The following items remain under discussion and are not yet acceptance rules:

- Whether human review may override a one-platform threshold failure and, if so, what evidence
  and conclusion it must record.
- Case counts, sampling protocol, and platform-specific thresholds.
- The result oracle for objective and subjective outcomes.
- Which trajectory constraints are acceptance-critical.
- Token-budget warning and failure criteria.
- Golden Dataset ownership and approval.
- Regression-suite execution conditions.
- Risk levels that require red-team, shadow-mode, or canary evaluation.
