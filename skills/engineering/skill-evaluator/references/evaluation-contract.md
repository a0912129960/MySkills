# Evaluation contract

## Required evidence

- canonical Skill path and deterministic directory digest;
- structural validation output;
- Claude and Codex discovery and harmless invocation results;
- cases, baseline identity, assertions, grades, and target-specific outcomes;
- elapsed time and token usage when exposed by the runner;
- path to the offline static review and human review status;
- evaluator version and final pass/fail result.

## Workspace shape

Use one directory per case and configuration:

```text
.scratch/skill-evals/batch-<run-id>/
  <skill>/
    <case>/
      with_skill/
        <target>/
          workspace/
          result.json
          grading.json
      baseline/
        <target>/
          workspace/
          result.json
          grading.json
    benchmark.json
    review.html
    attestation-draft.json
```

`grading.json` expectations use exactly `text`, `passed`, and `evidence`.
Each `result.json` records `duration_ms` and records `total_tokens` as `null`
when the runner does not expose it.

Required and trigger cases may declare deterministic UTF-8 `fixtures`; required
cases may also declare Managed `companion_skills`. The runner writes fixtures
only below the isolated workspace, rejects Agent configuration paths and
traversal, and stages only the declared companions. The no-Skill baseline
receives the same fixtures, runtime capabilities, and companions but not the
Skill under evaluation. Declared QMD access uses the verified host executable
against a workspace-local fixture index through a read-only command wrapper.
Before QMD setup, the runner clears host index/config overrides and pins all
QMD/XDG state below the workspace; the wrapper repeats that isolation and
rejects command-line index overrides. The runner validates the executable
against the centrally declared minimum version and records identity plus setup
results in raw evidence. QMD never reads the user's index.

Every run plan records the current primary `skill_digest` and the deterministic
`companion_skill_digests`. Draft audit rebuilds the current plan and rejects raw
evidence when any staged Skill content has changed.

`prepare-review` creates failing-until-reviewed grading templates and preserves
existing human edits. After every planned run has a passing process, target
identity, and completed human grading, `draft-attestation` aggregates the raw
records, writes the offline report, and creates a pending draft. It fails closed
for a missing run, stale plan, target identity failure, process failure, changed
assertion, failed grade, or placeholder evidence.

## Attestation

A compact source-controlled attestation contains:

- `skill_name`, `skill_digest`, `evaluator_version`, and `evaluated_at`;
- the tested Claude and Codex target identities;
- structural, discovery, behavior, baseline, trigger, efficiency, and review
  results;
- unavailable optional capabilities;
- final `passed` status.

Never infer a pass from missing data. A target that could not run is a failure,
not an unavailable optional capability.

The generated draft is not an attestation: its static review, human review, and
overall status remain pending. A human reviews the offline report, records their
identity and notes, changes only those pending review fields, and then runs
`verify-attestation`. The tool never synthesizes a human approval.
