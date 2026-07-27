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

### Human review

Human review cannot override a platform threshold failure by changing it directly to a pass.
The reviewer determines why the evaluation did not prove conformance and records the required
corrective action. If the evaluation itself is invalid, its result is invalidated rather than
passed; evaluation after a correction is a new, explicitly authorized run.

### Evaluation evidence

Every evaluation records both the test process and its result. The retained evidence must let
a reviewer determine what was tested, what happened during the run, what result was produced,
and why the evaluator classified it as a pass, failure, or invalid result. A bare result value
or a `PENDING HUMAN REVIEW` marker without reviewable process evidence is insufficient.

Each evaluation record contains at least:

- the Skill identity and evaluated digest;
- the evaluation specification or case version;
- the target platform and available runner or model version;
- the test input and relevant fixture or context;
- whether and how the Skill was invoked;
- relevant tool calls, parameters, ordering, and returned status;
- the final output or externally observable final state;
- the assertions, scores, and reasons for the classification; and
- elapsed time and token usage when the runner exposes them.

Every evaluation run, including development runs and runs classified as failed or invalid,
has a reviewable record retained in the MySkills Git repository. Records are append-only:
correcting a Skill, case, or evaluator produces a new record rather than deleting or replacing
the earlier result.

The record is concise and human-readable. It identifies the stage at which a failure occurred,
the observed problem, and the corrective action or improvement carried into a later iteration.
Together, the records show how a Skill changed, which problems it previously exhibited, and
whether later evaluations resolved them. Machine-readable evidence supports the human-readable
record but does not replace it.

Every record must be sanitized before it is staged: credentials, personal data,
machine-specific private paths, and other secrets are never committed. Unsanitized runner
output may exist only as ignored, temporary execution data and is not the repository's
acceptance evidence.

If accumulated evaluation records later become too large or difficult to operate, MySkills
will add an archive mechanism without discarding their history. Archive design is deferred
until an actual size or operability problem is observed.

## Unresolved decisions

The following items remain under discussion and are not yet acceptance rules:

- The source-controlled evidence path, schema, representation of unavailable fields, and
  concise human-readable format.
- Case counts, sampling protocol, and platform-specific thresholds.
- The result oracle for objective and subjective outcomes.
- Which trajectory constraints are acceptance-critical.
- Token-budget warning and failure criteria.
- Golden Dataset ownership and approval.
- Regression-suite execution conditions.
- Risk levels that require red-team, shadow-mode, or canary evaluation.
