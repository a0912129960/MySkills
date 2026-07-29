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

## Source-controlled cases

`evaluations/cases.json` is the v4 catalog. It lists one sorted
`evaluations/cases/<skill>.json` source per Managed Skill, so case ownership
does not overlap. The loader merges those sources only after checking filenames,
inventory membership, invocation classification, duplicate identifiers,
fixtures, tools, and complete coverage.

Every Skill source declares exactly three core cases and three invocation
cases. Every case has a positive integer version that binds its prompt and
oracle. Each plan item has `max_attempts: 1` and is run once on Claude and once
on Codex. Core cases contain a predeclared expected outcome and typed
assertions. Explicit Skills expect `not-invoked` in all three invocation cases;
Implicit Skills require direct and paraphrase invocation plus a non-invoking
boundary case. Baseline comparisons and automatic retries are not part of the
contract.

Golden cases are optional. A Golden case must be de-identified and record its
provenance, version, human approver, timezone-qualified approval time, expected
outcome, and assertions before it enters a plan. Changing its prompt or oracle
increments the case version rather than rewriting earlier evidence.

## Raw workspace

Use one ignored directory per case and target:

```text
.scratch/skill-evals/batch-<run-id>/
  plan.json
  <skill>/
    <case>/
      <target>/
        workspace/
        result.json
        grading.json
    benchmark.json
    review.html
    review.json
    record-draft.json
```

`grading.json` schema v3 expectations preserve `assertion_id`, `kind`,
`description`, and `required` from the plan, plus the reviewer-controlled
`status` and `evidence`. Status is `pending`, `pass`, `fail`, or `invalid`.
Every assertion must be reviewed. A non-passing required assertion blocks the
case; a non-passing optional assertion is retained as a warning. The grading
also records observable invocation as `explicit`, `implicit`, `not-invoked`,
or `unknown`, together with the trace evidence for that classification;
templates always start at `unknown`. `unknown` cannot pass final audit. Each
trajectory assertion predeclares exactly one acceptable observation in the
source case: Tool trace, external state, or verified absence. Its grade must
match that declaration and the observable evidence. A positive Tool-call
requirement cannot pass through verified absence. Non-trajectory grades use
final output, invocation trace, or not applicable as appropriate.

`review.json` records the batch reviewer, timezone-qualified review time,
reason, and optional corrective action. Its `pass` status means review was
completed, not that a failed target is accepted. It separately requires human
confirmation that the retained record is sanitized.
Each `result.json` records `duration_ms` and records `total_tokens` as `null`
when the runner does not expose it.

Cases may declare deterministic UTF-8 fixtures, Managed companion Skills,
repository-owned runtimes, and allowlisted external tools. The runner stages
only declared content inside a disposable filesystem workspace outside the
repository. Before staging, no external parent of that workspace may contain a
Claude Skill-discovery root. It rejects Agent configuration paths, traversal,
undeclared commands, and out-of-workspace access.

Declared QMD access uses the verified host executable against a workspace-local
fixture index through a read-only wrapper. The runner clears host index/config
overrides, pins QMD/XDG state below the workspace, validates the centrally
declared minimum version, and records identity plus setup evidence. QMD never
reads the user's index.

Each Codex run uses an evaluator-owned ephemeral profile and `untrusted`
approval. Each Claude read-only run uses evaluator-owned permissions scoped to
declared tools and the disposable workspace. User settings, user exec-policy
rules, and undeclared Skills are not copied.
Claude launch evidence must show project/local-only settings, a strict
evaluator-owned MCP configuration file inside the disposable workspace,
disabled Chrome integration, and a sanitized child environment manifest whose
home, AppData, and XDG paths remain inside the ephemeral profile or execution
workspace. The MCP file must contain only an empty `mcpServers` object, and the
manifest records its fixed workspace-relative path and post-execution content
digest. New runs emit environment evidence version 2; the record validator
continues to read version 1 evidence in append-only historical records, while
record publication rejects version 1 as new evidence. Every new non-invalid
Claude case requires version 2 evidence; `null` is valid only for an invalid
measurement.
Evaluator-owned deny and ask rules are written to the disposable workspace's
project settings so the declared setting sources load them; QMD may relocate
XDG state only to its declared workspace-local runtime directories. Missing,
malformed, or changed launch or environment evidence is an invalid
measurement, not a Skill failure.

Before staging, every parent outside the Claude execution workspace must be
free of a `.claude/skills` directory. The evaluator then populates the
workspace-local `.claude/skills` root with only the declared primary and
companion Skills. Before isolation, it captures a name-only inventory of
installed host Skills. The raw Claude stream must contain exactly one
`system/init` event whose `skills` list includes every staged Skill. Any
non-staged visible Skill that also occurs in the captured host inventory
invalidates the measurement. Raw results retain the host inventory so review
and aggregation recompute this check; missing, malformed, or contradictory
Skill-discovery evidence fails closed.

`commands` previews logical commands without staging their referenced
workspace. Only an executing `run` or `run-batch --execute` invocation creates
the evaluator-owned MCP file at the launch boundary.

Every run plan records the current primary Skill digest plus every staged
companion and runtime digest. Review audit rebuilds the plan, reparses raw Tool
traces, recomputes isolation results, and rejects missing, stale, changed, or
non-empty violation evidence.

`run-batch` writes the complete fixed `plan.json` before its first target call
and refuses to reuse an existing plan. An interrupted batch therefore retains
the full intended call set; missing or malformed results become `invalid`
records instead of being omitted. `prepare-review` scaffolds every planned run,
and aggregation labels missing or malformed raw evidence instead of aborting
the review.

Immediately before and after each target call, the runner snapshots the
disposable execution workspace without following symlinks. `result.json`
retains the deterministic relative-path diff, file kinds, sizes, digests, and
bounded UTF-8 text before the workspace is removed. A reviewer may describe
what the diff means, but an `external-state` pass is valid only when captured
state changes exist; reviewer prose cannot manufacture the evidence.

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

Use `build-record` to preview and `publish-reviewed` to construct this record
from the fixed current plan, raw target traces, v3 grades, and batch review.
The builder compares invocation classifications, reparses Tool trajectories,
recomputes isolation evidence, verifies declared external tools, localizes
failures, and redacts machine paths plus credential-like values. It does not
infer hidden reasoning. A missing or malformed measurement is `invalid`; a
required behavioral mismatch or observable Skill action that violates
isolation is `fail`. Host Skill contamination is an evaluator-boundary failure
and therefore `invalid`, not a failure attributed to the evaluated Skill.
Human-readable reports must preserve this distinction with separate
`ISOLATION INVALID` and `ISOLATION FAIL` labels.
Residual private paths, common personal identifiers, private keys, and token
formats fail closed instead of being marked sanitized. This scan covers the
entire prospective record, including prompts, expected outcomes, observations,
and review text. The record's
`sanitization.human_confirmed` field preserves the review confirmation. The
saved raw plan is the historical identity: a mismatch against the current plan
is invalid, while the record keeps the digest and inputs that were actually
tested.

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
