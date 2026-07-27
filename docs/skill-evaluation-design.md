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

Red-team evaluation is deferred. It is not designed, executed, or used as a release gate in
the current phase. MySkills may introduce it later through a separately reviewed change.

Shadow-mode and canary evaluation are also deferred. They are not current release gates and
will be reconsidered only when MySkills manages a Skill that can affect real external systems
or users.

### Invocation classification

Every new or reevaluated Managed Skill declares whether it is an Explicit-invocation Skill or
an Implicit-invocation Skill before its cases are defined. The classification is canonical:
the same Skill has the same classification on every supported platform.

An Explicit-invocation Skill must succeed when explicitly invoked and must not be selected
implicitly. It is not graded on a positive implicit-trigger rate.

Each Explicit-invocation Skill has three negative implicit-selection cases for each platform.
The prompts are close to the Skill's scope but do not explicitly name or invoke it. Each case
is executed once per platform, and all three must remain untriggered; any implicit selection is
a platform policy failure.

### Implicit trigger evaluation

Each Implicit-invocation Skill has a fixed three-case trigger suite for each platform in an
evaluation run:

- one direct case that should invoke the Skill;
- one paraphrased case that should still invoke the Skill; and
- one nearest-Skill boundary case that should not invoke the Skill.

Each case is executed once per platform. All three classifications must be correct for the
platform to pass trigger evaluation. Results are not retried after they are known.

### Platform-specific results

Claude and Codex are evaluated and scored independently. Their results cannot offset each
other.

When exactly one platform reaches its required threshold, the evaluation requires human
review and does not receive an automatic pass. A completed platform suite is not
automatically retried to seek a better score. Any later rerun is a new, explicitly authorized
evaluation.

### Outcome oracle

Every case defines its expected observable outcome and classification rules before execution.
Objective requirements are graded with deterministic assertions whenever possible. Subjective
quality is graded by a human against a written rubric whose criteria and pass conditions were
fixed before the output was seen.

An expected outcome or rubric is not edited after a run merely to change its result. If review
shows that a case or its oracle was invalid, that run is classified as invalid; the corrected
case receives a new version and is executed only as a new, explicitly authorized evaluation.

### Core outcome evaluation

Every Managed Skill has at least three core outcome cases for each platform:

- a normal-use case;
- a boundary or invalid-input case; and
- a safety or authorization constraint case, or another core capability when no such
  constraint applies.

Each case is executed once per platform in an evaluation run. Every acceptance-critical
assertion must pass; outcome failures are not hidden by averaging scores across cases.
Applicable tool and side-effect cases include their predeclared trajectory assertions in the
same evaluation.

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

Failure localization is based only on observable evidence; the evaluator does not infer hidden
model reasoning. For a black-box Skill without tools or side effects, the concise record needs
only the input, expected result, actual result, and classification. When invocation, tool use,
or external state is observable, the record also identifies the directly observed point of
divergence, such as invocation, tool selection, parameters or ordering, tool-result handling,
or final outcome. If the available evidence cannot support a classification, the evaluation is
invalid rather than a Skill failure.

Observable tool trajectories are evaluation evidence, not hidden model reasoning. A case may
check the selected tool or command, its syntax or parameters, call order, returned status, and
resulting external state. It grades only requirements declared before execution that are
necessary for task correctness or safety. A semantically equivalent command or safe
alternative tool is not a failure unless the Skill contract requires the specific choice. If
a required trajectory cannot be observed, the case cannot receive a trajectory pass.

A trajectory observation causes an acceptance failure only when it:

- changes or jeopardizes the required final outcome;
- violates safety, authorization, or unacceptable-side-effect constraints; or
- violates a mandatory process explicitly defined by the Skill contract.

Using a less efficient but valid approach, a different safe tool, or semantically equivalent
syntax is recorded as a warning rather than a failure. Trajectory requirements are declared
before execution and cannot be added after observing a run.

### Token-budget evaluation

Evaluation records the initial Skill size, reference material actually loaded, and token usage
when the platform exposes it. A `SKILL.md` longer than 5,000 words produces a review warning
but does not fail solely because of its length.

A token-budget observation causes an acceptance failure only when:

- execution exceeds a platform limit or a Skill-specific resource limit declared before the
  run;
- a simple case loads substantial content that is observably unrelated to the task; or
- excessive loaded content causes the required outcome to fail.

Reference loading is evaluated against the needs of the case. A large task may legitimately
load more material than a small task, so absolute content size is not used as a universal
correctness proxy.

### Golden Dataset

A new Skill is not required to begin with a large synthetic Golden Dataset. Its initial
acceptance uses the required core cases, and a Golden Dataset is accumulated as reviewed,
real-use cases become available.

Every Golden case is de-identified, records its provenance, and has a human-approved expected
outcome. AI may propose candidate cases or variants, but a candidate does not become Golden
evidence until a human reviews and approves both the input and expected outcome. Later changes
to an approved case or oracle create a new version rather than rewriting its evaluation
history.

### Regression scope

Regression evaluation follows the behavior that a change can affect:

- Adding or removing a Skill, or changing a Skill name, description, or invocation
  classification, runs the complete Skill Library trigger suite on both Claude and Codex.
  The suite includes every applicable trigger, non-trigger, paraphrase, and boundary case.
- A change limited to a Skill's internal execution content runs that Skill's core cases,
  approved Golden Dataset, and the cases of any explicitly affected dependent Skill.

Each regression case is executed once per platform. A failed result is not automatically
retried.

### Source-controlled record layout

Each Skill evaluation run is stored at:

```text
evaluations/records/<skill>/<run-id>/
|-- summary.md
`-- record.json
```

`summary.md` is the concise human review surface. It states what was tested, platform results,
the directly observed failure point and reason, and the corrective action or later
improvement. `record.json` is the schema-validated machine-readable record containing the
required inputs, observations, assertions, and results.

A required value that the platform does not expose is represented as `null` together with a
reason; it is not silently omitted. The record schema determines whether that unavailable
value permits a valid result for the case.

`attestations/skills/<skill>.json` identifies the currently selected passing record for the
Skill and its digest. It is a release pointer, not the evaluation history. The existing
attestation schema implements the earlier compact-attestation model and must be migrated when
the revised evaluation model is implemented.

Every record must be sanitized before it is staged: credentials, personal data,
machine-specific private paths, and other secrets are never committed. Unsanitized runner
output may exist only as ignored, temporary execution data and is not the repository's
acceptance evidence.

If accumulated evaluation records later become too large or difficult to operate, MySkills
will add an archive mechanism without discarding their history. Archive design is deferred
until an actual size or operability problem is observed.
