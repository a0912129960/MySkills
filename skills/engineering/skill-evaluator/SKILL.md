---
name: skill-evaluator
description: Evaluate an existing MySkills Skill for structure, cross-platform discovery, behavior, baseline improvement, efficiency, trigger quality, and human review. Use only when the user explicitly asks to evaluate, benchmark, or attest a Skill; this workflow does not author or package Skills.
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
  attestation.
- Place raw runs under
  `.scratch\skill-evals\<skill-name>\<run-id>\`; this location is disposable
  and ignored.

## Evaluate

1. Run structural validation for `SKILL.md`, `agents/openai.yaml`, directory
   naming, references, and matching invocation policy.
2. Run harmless isolated discovery and explicit-invocation smoke tests with
   Claude (`claude -p`) and Codex (`codex exec --ephemeral`) separately.
3. Exercise realistic cases against a no-Skill or recorded previous-version
   baseline. Keep target results separate.
4. Grade objective assertions, aggregate pass rate, duration, and token usage
   when the runners expose them.
5. Evaluate trigger cases for each primary target. Claude trigger results never
   stand in for Codex results.
6. Generate the offline static HTML review and present it for human inspection.
   Do not require a CDN, web server, or Node.js.

Read [references/evaluation-contract.md](references/evaluation-contract.md)
before constructing cases or recording results.

## Report and attest

Default evaluation is report-only. List failures, unavailable capabilities, and
recommendations without modifying the Skill.

After completing human grading, use the evaluator's `draft-attestation`
command. It must reject incomplete or failed raw evidence and leave report
review, reviewer identity, notes, and overall status pending.

Create a passing attestation only when structural checks, both primary target
runs, required cases, and human review pass for the exact current digest.
Record the digest, evaluator version, tested targets, result summary, and any
unavailable optional capability. A changed digest requires a new evaluation.

An unchanged imported snapshot may use structural validation plus discovery and
explicit-invocation smoke tests. Any rename, shortening, Windows port, merge,
split, or behavioral change requires the full evaluation above.
