---
name: skill-evaluator
description: Evaluate an existing MySkills Skill for structure, cross-platform discovery, behavior, efficiency, trigger quality, and human review. Use only when the user explicitly asks to evaluate, benchmark, or attest a Skill; this workflow does not author or package Skills.
disable-model-invocation: true
---

# Skill Evaluator

Evaluate a completed Skill without editing it. A creator applies any accepted
recommendations and asks for a new evaluation of the resulting digest.

## Preconditions

- Resolve the canonical Skill directory and calculate its deterministic
  directory digest.
- Resolve the MySkills-managed evaluator launcher. Do not use a former source
  clone or a globally installed evaluator.
- Require the evaluator launcher and both `claude` and `codex` target
  capabilities declared by MySkills. Missing either target prevents a passing
  evaluation record.
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

After completing grading, create a record draft that satisfies
`evaluations/record.schema.json`, then use `publish-record` to write its
append-only `record.json` and `summary.md`. Do not commit credentials, personal
data, private machine paths, or unsanitized raw output.

Use `select-record` only when the published record passes for the exact current
Skill digest and both primary platforms. This writes the current release pointer
under `attestations/skills/`; `verify-attestation` validates the pointer, record
digest, Skill digest, and referenced evidence. Human review may classify a
failure or invalid evaluation but must not convert a platform failure directly
to a pass. A changed Skill digest requires a new evaluation.

An unchanged imported snapshot may use structural validation plus discovery and
explicit-invocation smoke tests. Any rename, shortening, Windows port, merge,
split, or behavioral change requires the full evaluation above.
