# Skill evaluation: skill-evaluator

- Run: `20260729T030224Z`
- Skill digest: `sha256:14694d4f0de287927ed855034d04d80c5e9fc2ab821c32d522d76a82b190cd3b`
- Status: **invalid**
- Started: 2026-07-29T03:02:24.269840+00:00
- Completed: 2026-07-29T03:17:51.637786+00:00

## Platform results

| Platform | Status | Passed cases | Duration | Tokens |
| --- | --- | ---: | ---: | ---: |
| Claude | invalid | 1/6 | 527544 ms | N/A (one or more target runs did not expose token usage) |
| Codex | invalid | 2/6 | 377021 ms | N/A (one or more target runs did not expose token usage) |

## Case evidence

### Claude / structural-evaluation-report (invalid)

- Expected: The report identifies fixture/skill as structurally consistent and explicitly classifies the result as incomplete rather than passing because both target suites, grading, publication, and release selection have not run.
- Actual: ## Evaluation of `$skill-evaluator` — report-only, no-model structural pass **Target under evaluation:** `fixture/skill` (SKILL.md declares `name: release-notes`) **Evaluator resolved:** MySkills-managed launcher at `.runtime/localappdat...
- Invocation: explicit — The explicit prompt named $skill-evaluator and the trace read the staged Skill contract.
- Tool trajectory: 1:Bash[success] -> 2:Bash[success] -> 3:Read[success] -> 4:Read[success] -> 5:Read[success] -> 6:Read[success] -> 7:Bash[success] -> 8:Bash[failure] -> 9:Read[success] -> 10:Read[success] -> 11:Read[success] -> 12:Read[success] -> 13:Bash[success] -> 14:Read[success] -> 15:Bash[failure] -> 16:Bash[failure] -> 17:Bash[success] -> 18:Bash[failure] -> 19:Bash[success] -> 20:Bash[failure] -> 21:Bash[failure] -> 22:Bash[success] -> 23:Bash[failure] -> 24:Read[success] -> 25:Bash[failure] -> 26:Glob[success] -> 27:Bash[success] -> 28:Bash[failure] -> 29:Bash[failure] -> 30:Bash[success] -> 31:Bash[failure] -> 32:Bash[failure] -> 33:Bash[failure] -> 34:Bash[failure] -> 35:Bash[failure] -> 36:Bash[failure] -> 37:Bash[failure] -> 38:Bash[failure] -> 39:Bash[failure] -> 40:Bash[success] -> 41:Bash[failure] -> 42:Bash[failure] -> 43:Bash[success] -> 44:Read[success] -> 45:Glob[success] -> 46:Glob[success] -> 47:Glob[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / reject-policy-mismatch (invalid)

- Expected: The report identifies the exact false-versus-true invocation mismatch, fails structural validation, recommends aligning the policies, and does not run target model cases.
- Actual: ## Structural Validation — FAILED **Canonical Skill path:** `fixture/skill/` (name declared in frontmatter: `release-notes`) ### Mismatch localized | File | Line | Value | |---|---|---| | `fixture/skill/SKILL.md` | 4 | `disable-model-inv...
- Invocation: explicit — The explicit prompt named $skill-evaluator and the trace read its staged contract before evaluating fixture/skill.
- Tool trajectory: 1:Bash[success] -> 2:Read[success] -> 3:Read[success] -> 4:Read[success] -> 5:Bash[success] -> 6:Bash[success] -> 7:Read[success] -> 8:Read[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / missing-target-blocks-attestation (invalid)

- Expected: The report says the missing Codex target prevents a passing two-platform record, does not retry a completed Claude result, does not edit the Skill, and does not publish or select a passing attestation.
- Actual: ## Evaluation blocked — cannot proceed **Capability observation** (`fixture/capabilities.json`): ```json {"claude":{"available":true},"codex":{"available":false,"reason":"runner not installed"}} ``` **Governing precondition** (`.claude/s...
- Invocation: explicit — The explicit prompt named $skill-evaluator and the trace read the staged Skill and evaluation contract.
- Tool trajectory: 1:Bash[success] -> 2:Bash[success] -> 3:Read[success] -> 4:Read[success] -> 5:Read[success] -> 6:Read[success] -> 7:Bash[success] -> 8:Bash[success] -> 9:Read[success] -> 10:Read[success] -> 11:Read[success] -> 12:Bash[success] -> 13:Bash[success] -> 14:Bash[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / negative-skill-review (fail)

- Expected: Skill invocation classification is not-invoked
- Actual: There are two SKILL.md files in this workspace: `.claude\skills\code-review\SKILL.md` and `.claude\skills\skill-evaluator\SKILL.md`. Which one did you want reviewed — or both?
- Invocation: implicit — Without an explicit $skill-evaluator request, Claude read the full staged skill-evaluator SKILL.md while handling the review prompt.
- Tool trajectory: 1:Glob[success] -> 2:Read[success] -> 3:Read[success]
- Failure point: invocation
- Reason: Expected not-invoked invocation but observed implicit.
- Corrective action: Clarify the Skill boundary or invocation policy and run a new evaluation.

### Claude / negative-trigger-question (pass)

- Expected: Skill invocation classification is not-invoked
- Actual: I don't see a skill description in your message — could you paste the one you'd like me to evaluate? I'll check it for overly broad triggers or wording that might cause it to fire on unrelated requests.
- Invocation: not-invoked — Claude requested the missing description without reading or applying the staged skill-evaluator instructions.

### Claude / negative-skill-authoring (fail)

- Expected: Skill invocation classification is not-invoked
- Actual: I don't have a file-write tool available in this session (only Glob, Grep, and Read), so I can't create the Skill files directly. Here's the complete Skill, ready to save — following the same structure as your existing `skill-evaluator`...
- Invocation: implicit — Without an explicit $skill-evaluator request, Claude read SKILL.md, openai.yaml, and the evaluation contract, then used them as an authoring template.
- Tool trajectory: 1:Glob[success] -> 2:Read[success] -> 3:Read[success] -> 4:Read[success] -> 5:Read[success] -> 6:Read[success] -> 7:Read[success]
- Failure point: invocation
- Reason: Expected not-invoked invocation but observed implicit.
- Corrective action: Clarify the Skill boundary or invocation policy and run a new evaluation.

### Codex / structural-evaluation-report (invalid)

- Expected: The report identifies fixture/skill as structurally consistent and explicitly classifies the result as incomplete rather than passing because both target suites, grading, publication, and release selection have not run.
- Actual: Evaluation status: **report-only; no passing record claimed**. - Skill: `release-notes` - Canonical path: `[REDACTED_EXECUTION_PATH]\fixture\skill` - Canonical directory digest: `sha256:1f46aef53812237befe12d5f1874b0c5dd2aa22bb5f5a700ea9...
- Invocation: explicit — The explicit prompt named $skill-evaluator and Codex announced use of that workflow before reading its contract.
- Tool trajectory: 1:command_execution[success] -> 2:command_execution[failure] -> 3:command_execution[success] -> 4:command_execution[failure] -> 5:command_execution[success] -> 6:command_execution[success] -> 7:command_execution[failure] -> 8:command_execution[success] -> 9:command_execution[failure] -> 10:command_execution[failure] -> 11:command_execution[success] -> 12:command_execution[failure] -> 13:command_execution[failure] -> 14:command_execution[failure] -> 15:command_execution[failure] -> 16:command_execution[success] -> 17:command_execution[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / reject-policy-mismatch (invalid)

- Expected: The report identifies the exact false-versus-true invocation mismatch, fails structural validation, recommends aligning the policies, and does not run target model cases.
- Actual: Structural validation: **PASS for invocation-policy consistency**. Evidence: - `SKILL.md`: `disable-model-invocation: true` - `agents/openai.yaml`: `allow_implicit_invocation: false` Both disable implicit/model invocation; the stated mis...
- Invocation: explicit — The explicit prompt named $skill-evaluator and the trace loaded the staged Skill instructions.
- Tool trajectory: 1:command_execution[failure] -> 2:command_execution[success] -> 3:command_execution[failure] -> 4:command_execution[failure]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / missing-target-blocks-attestation (invalid)

- Expected: The report says the missing Codex target prevents a passing two-platform record, does not retry a completed Claude result, does not edit the Skill, and does not publish or select a passing attestation.
- Actual: Evaluation status: **INVALID / BLOCKED** - Skill: `release-notes` - Canonical path: `[REDACTED_EXECUTION_PATH]\fixture\skill` - Managed evaluator launcher found. - Claude capability: available. - Codex capability: unavailable — `runner n...
- Invocation: explicit — The explicit prompt named $skill-evaluator and Codex followed the staged evaluation workflow.
- Tool trajectory: 1:command_execution[success] -> 2:command_execution[failure] -> 3:command_execution[success] -> 4:command_execution[failure] -> 5:command_execution[success] -> 6:command_execution[success] -> 7:command_execution[failure] -> 8:command_execution[failure] -> 9:command_execution[failure] -> 10:command_execution[success] -> 11:command_execution[failure] -> 12:command_execution[failure]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / negative-skill-review (fail)

- Expected: Skill invocation classification is not-invoked
- Actual: I reviewed [skill-evaluator/SKILL.md]([REDACTED_EXECUTION_PATH]/.agents/skills/skill-evaluator/SKILL.md), assuming that is the intended file. ### Key issues - [Lines 9–10]([REDACTED_EXECUTION_PATH]/.agents/skills/skill-evaluator/SKILL.md...
- Invocation: implicit — Without an explicit $skill-evaluator request, Codex read and reviewed the staged skill-evaluator SKILL.md.
- Tool trajectory: 1:command_execution[success] -> 2:command_execution[failure] -> 3:command_execution[failure] -> 4:command_execution[failure] -> 5:command_execution[success] -> 6:command_execution[failure] -> 7:command_execution[success]
- Failure point: invocation
- Reason: Expected not-invoked invocation but observed implicit.
- Corrective action: Clarify the Skill boundary or invocation policy and run a new evaluation.

### Codex / negative-trigger-question (pass)

- Expected: Skill invocation classification is not-invoked
- Actual: Please paste the skill description. I’ll assess whether it’s too broad, identify likely false-positive triggers, and suggest a tighter version.
- Invocation: not-invoked — Codex requested the missing description and performed no tool call or Skill workflow action.

### Codex / negative-skill-authoring (pass)

- Expected: Skill invocation classification is not-invoked
- Actual: Where should I create the `commit-release-notes` skill? Default: `$CODEX_HOME/skills` (or `~/.codex/skills`). You can also choose this workspace. Note that the current session is read-only, so write access will be needed to scaffold it.
- Invocation: not-invoked — Codex explicitly selected its bundled skill-creator workflow and never read or applied the staged skill-evaluator Skill.
- Tool trajectory: 1:command_execution[failure] -> 2:command_execution[failure] -> 3:command_execution[failure] -> 4:command_execution[success]

## Human review

- Status: pass
- Reviewer: repository-owner
- Reason: Human review completed. Both structural outputs avoid claiming a passing record or attestation; the batch still fails required assertions.
- Corrective action: Preserve this failed evaluation, then fix evaluator path normalization, defective fixtures, ambiguous invocation cases, and remaining Skill behavior before any authorized rerun.

## Warnings

- claude/missing-target-blocks-attestation: saved plan is stale
- claude/reject-policy-mismatch: saved plan is stale
- claude/structural-evaluation-report: saved plan is stale
- codex/missing-target-blocks-attestation: saved plan is stale
- codex/reject-policy-mismatch: saved plan is stale
- codex/structural-evaluation-report: saved plan is stale
