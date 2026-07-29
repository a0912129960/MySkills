---
name: skill-evaluator
description: Run a formal, report-only MySkills evaluation of an existing Skill for structure, cross-platform discovery, behavior, efficiency, trigger quality, and human review. Use only when the user explicitly invokes $skill-evaluator or explicitly asks to evaluate, benchmark, or attest an existing Skill. Never use it for general review, authoring, or editing.
disable-model-invocation: true
---

# Skill Evaluator

Use this workflow only for a formal evaluation of an existing Skill. Never use
it for general review, authoring, editing, or advice about trigger wording.
This is a preserved optional diagnostic, not a default creation, installation,
completion, or release gate. Never launch Claude, Codex, or another model
unless the human explicitly approves the targets, cases, and model-call budget.

Evaluate a completed Skill without editing it. A creator applies any accepted
recommendations and asks for a new evaluation of the resulting digest.

## Preconditions

- Resolve the canonical Skill directory and calculate its deterministic
  directory digest.
- Resolve the MySkills-managed evaluator launcher. Do not use a former source
  clone or a globally installed evaluator.
- For an explicitly requested two-platform diagnostic, require the evaluator
  launcher and both `claude` and `codex` target capabilities declared by
  MySkills. Missing either target prevents that optional diagnostic record
  from passing but does not block ordinary repository work.
- Place raw runs under
  `.scratch\skill-evals\<skill-name>\<run-id>\`; this location is disposable
  and ignored.

## Evaluate

1. Run structural validation for `SKILL.md`, `agents/openai.yaml`, directory
   naming, references, and matching invocation policy.
2. Run harmless isolated discovery and explicit-invocation smoke tests with
   Claude (`claude -p`) and Codex (`codex exec --ephemeral`) separately.
3. Run the three predeclared core cases once per target: normal use, boundary
   or invalid input, and safety/authorization or another core capability.
4. Run the three predeclared invocation cases once per target. Explicit Skills
   must remain unselected in all three negative cases. Implicit Skills must
   pass direct-positive, paraphrase-positive, and nearest-boundary-negative
   classification.
5. Grade every required assertion without averaging away a failed case. Record
   duration and token usage when the runners expose them. Never automatically
   retry a completed result.
6. Generate the offline static HTML review and present it for human inspection.
   Do not require a CDN, web server, or Node.js.
7. Produce a sanitized machine-readable record and concise Markdown summary for
   every run, including failed and invalid runs.

Read [references/evaluation-contract.md](references/evaluation-contract.md)
before constructing cases or recording results.

## Report and release

Default evaluation is report-only. List failures, unavailable capabilities, and
recommendations without modifying the Skill.

After completing every v3 grading file and the batch `review.json`, use
`build-record` to preview the sanitized record, then `publish-reviewed` to write
its append-only `record.json` and `summary.md` directly from the fixed raw
workspace. Do not infer hidden reasoning or copy raw streams into the record.
Do not commit credentials, personal data, private machine paths, or unsanitized
raw output.

Do not pre-answer invocation classification, even for an explicit run. Record
the reviewed trace evidence. Each trajectory assertion predeclares one
acceptable observation; the grade must match it and the actual Tool trace,
captured before/after workspace change, or complete-trace verified absence.
Reviewer prose alone cannot satisfy external-state evidence. Confirm
sanitization separately in `review.json`; the builder scans the entire
prospective record for residual sensitive data and fails closed.

If the human explicitly requests the preserved evaluation gate, use
`select-record` only when the published record passes for the exact current
Skill digest and both primary platforms. This writes an optional release pointer
under `attestations/skills/`; `verify-attestation` validates the pointer, record
digest, Skill digest, and referenced evidence. Human review may classify a
failure or invalid evaluation but must not convert a platform failure directly
to a pass. A changed Skill digest requires a new evaluation only for a new
optional pointer.

When a human activates model diagnostics, an unchanged imported snapshot may
use structural validation plus discovery and explicit-invocation smoke tests.
Any broader model scope remains an explicit human decision; it is never started
automatically because of a rename, shortening, Windows port, merge, split, or
behavioral change.
