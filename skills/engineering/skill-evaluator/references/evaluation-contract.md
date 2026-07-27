# Evaluation contract

## Required evidence

- canonical Skill path and deterministic directory digest;
- structural validation output;
- Claude and Codex discovery and harmless invocation results;
- cases, assertions, grades, and target-specific outcomes;
- elapsed time and token usage when exposed by the runner;
- path to the offline static review and human review status;
- evaluator version and final pass/fail result.

## Workspace shape

Use one directory per case and target:

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
    attestation-draft.json
```

`grading.json` expectations use exactly `text`, `passed`, and `evidence`.
Each `result.json` records `duration_ms` and records `total_tokens` as `null`
when the runner does not expose it.

Required and trigger cases may declare deterministic UTF-8 `fixtures`; required
cases may also declare Managed `companion_skills`. The runner writes fixtures
only below the isolated workspace, rejects Agent configuration paths and
traversal, and stages only the declared companions. Declared QMD access uses
the verified host executable
against a workspace-local fixture index through a read-only command wrapper.
Before QMD setup, the runner clears host index/config overrides and pins all
QMD/XDG state below the workspace; the wrapper repeats that isolation and
rejects command-line index overrides. The runner validates the executable
against the centrally declared minimum version and records identity plus setup
results in raw evidence. QMD never reads the user's index.

Each Codex run uses an ephemeral, evaluator-owned profile. Its generated
`config.toml` disables every discovered user Skill but not the Skill staged
inside the workspace. Evaluator-owned exec-policy rules allow only case-declared
guarded launcher names, and Codex uses `untrusted` approval. Absolute host
executables and undeclared commands therefore remain unmatched and are rejected
by the non-interactive run instead of bypassing the guarded launcher; user
exec-policy rules are not copied into the ephemeral profile.
Every target runs from a disposable OS temporary workspace outside the source
repository. Claude read-only cases use `dontAsk` with only case-declared tools
pre-approved, scoped to the disposable execution workspace. Its
evaluator-owned settings deny file-tool reads from the source repository and
host Skill/config roots and force implicitly safe shell commands through the
non-interactive permission gate for those cases. Claude emits verbose stream
JSON; aggregation retains assistant text,
tool use, tool results, the final response, metadata, parse warnings, and
machine-detected isolation violations for human review. Draft audit reparses
the raw trace and compares a recomputed result with the stored result. A
missing, malformed, changed, or non-empty isolation audit blocks attestation.
Undeclared Bash commands are isolation violations in read-only cases;
temporary-workspace cases retain their existing command policy.

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
- structural, discovery, behavior, trigger, efficiency, and review
  results;
- unavailable optional capabilities;
- final `passed` status.

Never infer a pass from missing data. A target that could not run is a failure,
not an unavailable optional capability.

The generated draft is not an attestation: its static review, human review, and
overall status remain pending. A human reviews the offline report, records their
identity and notes, changes only those pending review fields, and then runs
`verify-attestation`. The tool never synthesizes a human approval.
