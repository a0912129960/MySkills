# Skill attestation workflow

Release validation requires one passing, source-controlled attestation for the
current directory digest of every Managed Skill. Raw model output stays under
`.scratch/skill-evals/` and is never committed.

1. Validate structure and print the current digest:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py validate skills/<bucket>/<name>
   python tools/skill-evaluator/skill_evaluator.py digest skills/<bucket>/<name>
   ```

2. Run isolated explicit and trigger cases on Claude and Codex:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py run skills/<bucket>/<name> `
     --mode explicit --prompt "<harmless required case>" `
     --allow-ephemeral-auth-copy
   python tools/skill-evaluator/skill_evaluator.py run skills/<bucket>/<name> `
     --mode trigger --prompt "<natural trigger or non-trigger case>" `
     --allow-ephemeral-auth-copy
   ```

   The authoritative batch cases are in `evaluations/cases.json`. Validate and
   preview them before spending model quota:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py validate-cases .
   python tools/skill-evaluator/skill_evaluator.py plan-batch . --skills qmd
   ```

   Required cases may declare reusable `fixture_sets`, case-local `fixtures`,
   a deterministic `git_fixture`, companion Skills, and allowlisted
   `runtime_tools`. The plan expands and digests those inputs before execution.
   Each run stages them in its isolated workspace; fixture content may use
   `{{WORKSPACE}}`, which is substituted only while staging. Git fixtures use a
   local identity, fixed commit timestamps, disabled signing, and an empty hook
   directory. Repository-owned runtime tools are copied into an isolated
   `LOCALAPPDATA` using only Git-tracked source files. Declared external tools
   use the verified host dependency with workspace-local state; QMD receives a
   local fixture index and a read-only command wrapper. The runner clears host
   index/config overrides before setup, pins QMD state below the workspace, and
   rejects command-line index overrides. It verifies the executable version
   against `manifests/dependencies.json` and records the identity and setup
   results in each raw run. Both kinds receive only declaration-scoped launcher
   permission in read-only Claude cases. The launchers reject mutating
   subcommands and paths outside the evaluation workspace.

   A complete 42-Skill run currently contains 336 target/configuration calls:
   Claude and Codex, with-Skill and no-Skill baseline, for one required and one
   trigger case per Skill. Execution is deliberately gated:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py run-batch . `
     --execute --allow-ephemeral-auth-copy
   ```

   The runner copies only the target CLI authentication file into an OS
   temporary directory and removes that directory after each call. The
   execution workspace is a second OS temporary directory outside the
   repository; only declared Skills and fixtures are staged there, and it is
   removed after its result is captured. For Codex the clean profile disables
   every discovered user Skill and contains evaluator-owned exec-policy rules
   that allow only case-declared guarded launcher names. Codex uses `untrusted`
   approval, so absolute host executables and undeclared commands are rejected
   by the non-interactive run. Claude read-only cases use `dontAsk` with only
   declared tools pre-approved inside the disposable execution workspace, plus
   evaluator-owned deny rules for the source repository and host Skill/config
   roots. Shell commands that Claude otherwise treats as implicitly safe are
   forced through the non-interactive permission gate in those cases. No user
   settings or user exec-policy rules are copied. Prompts, commands, machine
   isolation results, and model output are written under the ignored batch
   workspace; credentials are never written there.

3. Grade the raw results, compare required cases with a no-Skill or recorded
   previous-version baseline, and review the offline report. Claude evidence
   cannot substitute for Codex evidence or vice versa.

   Generate fail-closed grading templates without overwriting prior human work:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py prepare-review `
     .scratch/skill-evals/batch-<run-id>
   ```

   Generate the self-contained evidence report before asking a human to review:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py aggregate `
     .scratch/skill-evals/batch-<run-id> --skill-name <name> `
     --output .scratch/skill-evals/batch-<run-id>/<name>/benchmark.json
   python tools/skill-evaluator/skill_evaluator.py report `
     .scratch/skill-evals/batch-<run-id>/<name>/benchmark.json `
     --output .scratch/skill-evals/batch-<run-id>/<name>/review.html
   ```

   The report shows the declared prompt, exact logical launch command, ordinary
   and Git-backed fixtures, canonical Skill and baseline identities, target
   identity and process status, external-runtime identity/setup evidence,
   normalized final response, structured model/tool trace, raw streams, and
   current grading. Claude runs use verbose stream JSON so Bash/Read tool use
   and tool results remain reviewable rather than being collapsed into only the
   final answer. Each run also has a visible machine isolation PASS/FAIL badge;
   a successful out-of-workspace file tool, or an undeclared Bash command in a
   read-only case, blocks attestation. Missing or malformed audit data is a
   failure, not a pass. The
   report places With-Skill and Baseline runs side by side for each target. A
   process pass is not a behavior pass; the human records a specific reason for
   every assertion in the linked `grading.json`.

4. After completing every grading template, audit the reviewed evidence and
   create a pending draft:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py draft-attestation . `
     .scratch/skill-evals/batch-<run-id> <name> `
     --output attestations/skills/<name>.json
   ```

   The draft intentionally remains non-passing until a human records the final
   review fields required by `attestations/attestation.schema.json`. Do not mark
   an unavailable, failed, unreviewed, stale, or partially run target as
   passing. Draft audit reparses each raw model trace, recomputes its isolation
   result, and rejects a stored result that was removed or changed.

5. Verify the attestation and the release gate:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py verify-attestation `
     skills/<bucket>/<name> attestations/skills/<name>.json
   python scripts/validate_repo.py
   ```

Any change inside the Skill directory changes its digest and makes the previous
attestation stale. `python scripts/validate_repo.py --structural-only` is only
for authoring before evaluation; it is not a release pass.
