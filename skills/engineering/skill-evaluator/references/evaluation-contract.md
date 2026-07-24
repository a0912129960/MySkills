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
.scratch/skill-evals/<skill>/<run-id>/
  <case>/
    with_skill/
      outputs/
      grading.json
      timing.json
    baseline/
      outputs/
      grading.json
      timing.json
  benchmark.json
  review.html
```

`grading.json` expectations use exactly `text`, `passed`, and `evidence`.
Timing records use `total_tokens`, `duration_ms`, and
`total_duration_seconds`; use `null` when a runner does not expose a value.

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
