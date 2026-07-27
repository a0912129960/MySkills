# Evaluation contract

## Required evidence

- canonical Skill path and deterministic directory digest;
- evaluation case-manifest digest and evaluator version;
- target-specific Claude and Codex runner identities;
- case prompts, predeclared outcomes, assertions, grades, and final results;
- observable Skill invocation and relevant Tool calls, parameters, order, and
  returned status;
- elapsed time and token usage, or `null` with a reason when unavailable;
- human review required by subjective rubrics or a one-platform failure;
- sanitization status, warnings, and final pass/fail/invalid classification.

Do not record or infer hidden model reasoning.

## Raw workspace

Use one ignored directory per case and target:

```text
.scratch/skill-evals/batch-<run-id>/
  <skill>/
    <case>/
      <target>/
        workspace/
        result.json
        grading.json
    benchmark.json
    review.html
    record-draft.json
```

`grading.json` expectations use exactly `text`, `passed`, and `evidence`.
Each `result.json` records `duration_ms` and records `total_tokens` as `null`
when the runner does not expose it.

Cases may declare deterministic UTF-8 fixtures, Managed companion Skills,
repository-owned runtimes, and allowlisted external tools. The runner stages
only declared content inside a disposable OS temporary workspace outside the
repository. It rejects Agent configuration paths, traversal, undeclared
commands, and out-of-workspace access.

Declared QMD access uses the verified host executable against a workspace-local
fixture index through a read-only wrapper. The runner clears host index/config
overrides, pins QMD/XDG state below the workspace, validates the centrally
declared minimum version, and records identity plus setup evidence. QMD never
reads the user's index.

Each Codex run uses an evaluator-owned ephemeral profile and `untrusted`
approval. Each Claude read-only run uses evaluator-owned permissions scoped to
declared tools and the disposable workspace. User settings, user exec-policy
rules, and undeclared Skills are not copied.

Every run plan records the current primary Skill digest plus every staged
companion and runtime digest. Review audit rebuilds the plan, reparses raw Tool
traces, recomputes isolation results, and rejects missing, stale, changed, or
non-empty violation evidence.

## Source-controlled evaluation records

After grading, publish every evaluation run at:

```text
evaluations/records/<skill>/<run-id>/
  summary.md
  record.json
```

`record.json` is the machine-readable authority and must satisfy
`evaluations/record.schema.json`. `summary.md` is deterministic, concise, and
states what was tested, platform results, expected and actual outcomes,
observable failure location, reason, and corrective action.

Use `null` plus `unavailable_reason` when a required platform value is not
exposed. Never infer a pass from unavailable evidence. Source-controlled
records are append-only and sanitized; unsanitized output remains ignored in
the raw workspace.

## Release pointer

`attestations/skills/<skill>.json` is a v3 release pointer, not evaluation
history. It contains the current Skill digest, canonical record path, exact
record file digest, selection time, and pass status.

Only a record whose overall status and both target statuses are `pass` may be
selected. `verify-attestation` and the repository release gate reject stale
Skill content, changed records, invalid paths, non-passing targets, or malformed
evidence.
