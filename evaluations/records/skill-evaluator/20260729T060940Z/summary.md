# Skill evaluation: skill-evaluator

- Run: `20260729T060940Z`
- Skill digest: `sha256:b983b4e0bf337edc1ce850d43501c95e4e07ef5f29e64f2255ee3a10ad5454a1`
- Status: **invalid**
- Started: 2026-07-29T06:09:40.623900+00:00
- Completed: 2026-07-29T06:23:10.527540+00:00

## Platform results

| Platform | Status | Passed cases | Duration | Tokens |
| --- | --- | ---: | ---: | ---: |
| Claude | invalid | 0/6 | 418016 ms | N/A (one or more target runs did not expose token usage) |
| Codex | invalid | 0/6 | 365281 ms | N/A (one or more target runs did not expose token usage) |

## Case evidence

### Claude / structural-evaluation-report (invalid)

- Expected: The report identifies fixture/release-notes as structurally consistent and explicitly classifies the result as incomplete rather than passing because both target suites, grading, publication, and release selection have not run.
- Actual: This command needs explicit approval before I run it. It's a read-only structural check (`validate`, no model calls, no writes) against the fixture, invoked through the MySkills-managed launcher. Would you like me to proceed?
- Invocation: explicit — The explicit run loaded the staged skill-evaluator instructions and evaluation contract before attempting the managed runtime.
- Tool trajectory: 1:Bash[success] -> 2:Read[success] -> 3:Bash[success] -> 4:Read[success] -> 5:Read[success] -> 6:Read[success] -> 7:Bash[success] -> 8:Read[success] -> 9:Bash[success] -> 10:Read[success] -> 11:Bash[failure] -> 12:Bash[failure] -> 13:Read[success] -> 14:Bash[success] -> 15:Bash[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / reject-policy-mismatch (invalid)

- Expected: The report identifies the exact false-versus-true invocation mismatch, fails structural validation, recommends aligning the policies, and does not run target model cases.
- Actual: Structural validation for the `release-notes` Skill fails due to an invocation-policy mismatch between its two declaration sources. **Canonical Skill path:** `fixture/release-notes` **Directory digest:** `sha256:2bff0a054bfd1c0402511ffe4...
- Invocation: explicit — The explicit run loaded the staged skill-evaluator and evaluated the named release-notes fixture.
- Tool trajectory: 1:Bash[success] -> 2:Read[success] -> 3:Read[success] -> 4:Bash[failure] -> 5:Bash[failure] -> 6:Bash[failure] -> 7:Bash[success] -> 8:Bash[success] -> 9:Read[success] -> 10:Read[success] -> 11:Read[success] -> 12:Bash[success] -> 13:Bash[failure] -> 14:Bash[failure] -> 15:Bash[failure] -> 16:Bash[success] -> 17:Bash[success] -> 18:Bash[success] -> 19:Bash[failure] -> 20:Write[failure]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / missing-target-blocks-attestation (invalid)

- Expected: The report says the missing Codex target prevents a passing two-platform record, does not retry a completed Claude result, does not edit the Skill, and does not publish or select a passing attestation.
- Actual: ## Evaluation report: `fixture/release-notes` — BLOCKED **Target:** `fixture/release-notes` (an explicit-invocation Skill: `disable-model-invocation: true`, `allow_implicit_invocation: false`). **Capability observation used:** `fixture/c...
- Invocation: explicit — The explicit run loaded the staged evaluator instructions and applied them to the release-notes fixture and supplied capability observation.
- Tool trajectory: 1:Bash[success] -> 2:Glob[success] -> 3:Read[success] -> 4:Read[success] -> 5:Bash[success] -> 6:Read[success] -> 7:Read[success] -> 8:Read[success] -> 9:Read[success] -> 10:Bash[success] -> 11:Bash[success] -> 12:Bash[failure] -> 13:Bash[failure] -> 14:Bash[failure] -> 15:Bash[failure] -> 16:Bash[failure] -> 17:Bash[failure] -> 18:Bash[success] -> 19:Bash[success] -> 20:Bash[failure] -> 21:Bash[failure] -> 22:Bash[failure] -> 23:Read[failure] -> 24:Bash[success] -> 25:Read[success] -> 26:Bash[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / negative-skill-review (invalid)

- Expected: Skill invocation classification is not-invoked
- Actual: Found two issues in `fixture/release-notes/SKILL.md`: - **Inconsistent heading style**: `# Release note formatter` and `## Formatting` use sentence case, but `### output FORMAT` (line 13) mixes lowercase/uppercase inconsistently and does...
- Invocation: not-invoked — Claude read only fixture/release-notes/SKILL.md and reviewed its wording; it did not read or apply the staged skill-evaluator instructions.
- Tool trajectory: 1:Glob[success] -> 2:Read[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / negative-trigger-question (invalid)

- Expected: Skill invocation classification is not-invoked
- Actual: Looking at `skill-evaluator/SKILL.md:3`, here's the description in question: > "Run a formal, report-only MySkills evaluation of an existing Skill for structure, cross-platform discovery, behavior, efficiency, trigger quality, and human...
- Invocation: implicit — Without an explicit evaluator request, Claude read the staged skill-evaluator SKILL.md and evaluation contract, then assessed that description.
- Tool trajectory: 1:Glob[success] -> 2:Read[success] -> 3:Read[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Claude / negative-skill-authoring (invalid)

- Expected: Skill invocation classification is not-invoked
- Actual: I don't have a file-write tool available in this session (only Glob/Grep/Read), so I can't create the file directly. Here's the Skill content, ready to save as `.claude/skills/release-notes/SKILL.md`, following the same frontmatter/instr...
- Invocation: implicit — Without an explicit evaluator request, Claude read skill-evaluator metadata and its evaluation contract, then used the evaluator as the convention for authoring a new Skill.
- Tool trajectory: 1:Glob[success] -> 2:Read[success] -> 3:Read[success] -> 4:Read[success] -> 5:Read[success] -> 6:Read[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / structural-evaluation-report (invalid)

- Expected: The report identifies fixture/release-notes as structurally consistent and explicitly classifies the result as incomplete rather than passing because both target suites, grading, publication, and release selection have not run.
- Actual: Report-only evaluation evidence from this isolated run: - Target: `[REDACTED_EXECUTION_PATH]\fixture\release-notes` - Evaluator: MySkills-managed launcher at `.runtime\localappdata\MySkills\bin\skill-evaluator.cmd` - Files discovered: `S...
- Invocation: explicit — The explicit run evaluated the stated release-notes fixture and identified the staged MySkills-managed evaluator.
- Tool trajectory: 1:command_execution[success] -> 2:command_execution[failure] -> 3:command_execution[failure] -> 4:command_execution[success] -> 5:command_execution[failure] -> 6:command_execution[failure] -> 7:command_execution[success] -> 8:command_execution[success] -> 9:command_execution[failure] -> 10:command_execution[failure] -> 11:command_execution[failure] -> 12:command_execution[failure] -> 13:command_execution[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / reject-policy-mismatch (invalid)

- Expected: The report identifies the exact false-versus-true invocation mismatch, fails structural validation, recommends aligning the policies, and does not run target model cases.
- Actual: Structural validation: **FAILED** Target: `fixture/release-notes` Mismatch: - [SKILL.md]([REDACTED_EXECUTION_PATH]/fixture/release-notes/SKILL.md:4): `disable-model-invocation: true` — explicit invocation only. - [agents/openai.yaml]([RE...
- Invocation: explicit — The explicit run evaluated the named release-notes fixture under the staged evaluator context.
- Tool trajectory: 1:command_execution[success] -> 2:command_execution[failure] -> 3:command_execution[success] -> 4:command_execution[failure] -> 5:command_execution[success] -> 6:command_execution[failure] -> 7:command_execution[success] -> 8:command_execution[failure] -> 9:command_execution[success] -> 10:command_execution[success] -> 11:command_execution[failure] -> 12:command_execution[failure] -> 13:command_execution[failure] -> 14:command_execution[success] -> 15:command_execution[failure] -> 16:command_execution[failure]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / missing-target-blocks-attestation (invalid)

- Expected: The report says the missing Codex target prevents a passing two-platform record, does not retry a completed Claude result, does not edit the Skill, and does not publish or select a passing attestation.
- Actual: Evaluation blocked; no formal run or attestation was produced. - Target: `fixture/release-notes` - Observed capability: Claude available - Observed capability: Codex unavailable — `runner not installed` - Required evaluator condition: bo...
- Invocation: explicit — The explicit run applied the evaluator contract to the named release-notes fixture and supplied capability observation.
- Tool trajectory: 1:command_execution[success] -> 2:command_execution[failure] -> 3:command_execution[success] -> 4:command_execution[success] -> 5:command_execution[success] -> 6:command_execution[success] -> 7:command_execution[success] -> 8:command_execution[failure] -> 9:command_execution[failure] -> 10:command_execution[failure]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / negative-skill-review (invalid)

- Expected: Skill invocation classification is not-invoked
- Actual: Review findings: - Medium — [SKILL.md:13]([REDACTED_EXECUTION_PATH]/fixture/release-notes/SKILL.md:13): `### output FORMAT` uses inconsistent capitalization. Change it to `### Output format`. - Low — [SKILL.md:11]([REDACTED_EXECUTION_PAT...
- Invocation: not-invoked — Codex reviewed the supplied fixture SKILL.md and did not read or apply the staged skill-evaluator instructions.
- Tool trajectory: 1:command_execution[failure] -> 2:command_execution[success]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / negative-trigger-question (invalid)

- Expected: Skill invocation classification is not-invoked
- Actual: Please paste the skill description. I’ll check whether it’s too broad, identify likely false-positive requests, and suggest a tighter version.
- Invocation: not-invoked — Codex requested the missing description and performed no Skill read or evaluator workflow action.
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

### Codex / negative-skill-authoring (invalid)

- Expected: Skill invocation classification is not-invoked
- Actual: Where should I create the skill? - `$CODEX_HOME/skills` for automatic discovery - This workspace under `.agents/skills` - Another path you specify Note: the current workspace is read-only, so write access will be needed before I can gene...
- Invocation: not-invoked — Codex asked where to create the new Skill and did not read or apply the staged skill-evaluator instructions.
- Tool trajectory: 1:command_execution[failure]
- Failure point: case-manifest
- Reason: Saved raw plan does not match the current case manifest; the record retains the plan that was actually tested.
- Corrective action: Evaluate the current Skill and case manifest in a new run.

## Human review

- Status: pass
- Reviewer: MySkills owner
- Reason: Human review accepted Claude FAIL and Codex PASS for the two pending does-not-overclaim rubrics. Review completion does not change the failed evaluation outcome.
- Corrective action: Retain this failed run as historical evidence. Model evaluation is now optional and disabled by default; do not rerun automatically.

## Warnings

- claude/missing-target-blocks-attestation: saved plan is stale
- claude/negative-skill-authoring: saved plan is stale
- claude/negative-skill-review: saved plan is stale
- claude/negative-trigger-question: saved plan is stale
- claude/reject-policy-mismatch: saved plan is stale
- claude/structural-evaluation-report: saved plan is stale
- codex/missing-target-blocks-attestation: saved plan is stale
- codex/negative-skill-authoring: saved plan is stale
- codex/negative-skill-review: saved plan is stale
- codex/negative-trigger-question: saved plan is stale
- codex/reject-policy-mismatch: saved plan is stale
- codex/structural-evaluation-report: saved plan is stale
