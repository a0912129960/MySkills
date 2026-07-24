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
     --mode explicit --prompt "<harmless required case>"
   python tools/skill-evaluator/skill_evaluator.py run skills/<bucket>/<name> `
     --mode trigger --prompt "<natural trigger or non-trigger case>"
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
   directory. Runtime tools are copied from the repository into an isolated
   `LOCALAPPDATA` using only Git-tracked source files, use workspace-local
   configuration, and receive only declaration-scoped launcher permission in
   read-only Claude cases. The launcher also rejects mutating subcommands and
   paths outside the evaluation workspace for those cases.

   A complete 42-Skill run currently contains 336 target/configuration calls:
   Claude and Codex, with-Skill and no-Skill baseline, for one required and one
   trigger case per Skill. Execution is deliberately gated:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py run-batch . `
     --execute --allow-ephemeral-auth-copy
   ```

   The runner copies only the target CLI authentication file into an OS
   temporary directory, loads no user settings or user-wide Skills, and removes
   that directory after each call. Prompts, commands, and results are written
   under the ignored batch workspace; credentials are never written there.

3. Grade the raw results, compare required cases with a no-Skill or recorded
   previous-version baseline, and review the offline report. Claude evidence
   cannot substitute for Codex evidence or vice versa.

   Generate fail-closed grading templates without overwriting prior human work:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py prepare-review `
     .scratch/skill-evals/batch-<run-id>
   ```

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
   passing.

5. Verify the attestation and the release gate:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py verify-attestation `
     skills/<bucket>/<name> attestations/skills/<name>.json
   python scripts/validate_repo.py
   ```

Any change inside the Skill directory changes its digest and makes the previous
attestation stale. `python scripts/validate_repo.py --structural-only` is only
for authoring before evaluation; it is not a release pass.
