# Skill attestation workflow

This is a preserved, optional diagnostic workflow. It is disabled by default and is not a
creation, installation, completion, or release requirement. Do not execute its Claude/Codex
commands unless a human explicitly requests model evaluation and approves the target
platforms, case scope, and model-call budget. Raw model output stays under
`.scratch/skill-evals/` and is never committed.

Default deterministic repository validation is:

```powershell
python scripts/validate_repo.py
```

Only a human-requested diagnostic uses the workflow below. Its historical record can be
retained without becoming a default release gate. To explicitly check the preserved
record/release-pointer contract, use:

```powershell
python scripts/validate_repo.py --require-evaluations
```

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

   `evaluations/cases.json` is the authoritative v4 catalog and each
   `evaluations/cases/<skill>.json` file is the independently owned case source
   for one Managed Skill. Validate and preview the merged plan before spending
   model quota:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py validate-cases .
   python tools/skill-evaluator/skill_evaluator.py plan-batch . --skills qmd
   ```

   Core and approved Golden cases may declare reusable `fixture_sets`, case-local `fixtures`,
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

   With the current 42 configured Skill case sources, a full-catalog run contains
   504 target calls: three core cases and three invocation cases, each run once
   on Claude and once on Codex. Explicit
   Skills use three negative implicit-selection cases. Implicit Skills use a
   direct positive, paraphrased positive, and nearest-boundary negative case.
   The plan fixes `max_attempts` to `1`; a rerun is a new explicitly authorized
   evaluation, never an automatic retry. Execution is deliberately gated:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py run-batch . `
      --execute --allow-ephemeral-auth-copy
   ```

   Before the first target call, `run-batch` writes the complete fixed
   `plan.json` at the batch root and refuses to reuse an existing plan. If the
   batch is interrupted, the retained plan still identifies every intended
   call; missing or malformed results are published as `invalid` evidence
   instead of disappearing from the record. `prepare-review` creates
   fail-closed grading and review files for every planned run even when its raw
   result is missing or malformed, and the offline report labels that raw state
   rather than aborting the whole review.

   The runner copies only the target CLI authentication file into an OS
   temporary directory and removes that directory after each call. The
   execution workspace is a second disposable directory outside the repository.
   Before staging, none of its external parent directories may contain
   `.claude/skills`; only declared Skills and fixtures are then staged inside
   the workspace, and it is removed after its result is captured.
   For Codex the clean profile disables
   every discovered user Skill and contains evaluator-owned exec-policy rules
   that allow only case-declared guarded launcher names. Codex uses `untrusted`
   approval, so absolute host executables and undeclared commands are rejected
   by the non-interactive run. Claude read-only cases use `dontAsk` with only
   declared tools pre-approved inside the disposable execution workspace, plus
   evaluator-owned deny rules for the source repository and host Skill/config
   roots. Shell commands that Claude otherwise treats as implicitly safe are
   forced through the non-interactive permission gate in those cases. No user
   settings or user exec-policy rules are copied. Claude runs explicitly load
   only project/local setting sources; the evaluator writes its deny and ask
   rules into the disposable workspace's project settings so those rules are
   part of the actual launch boundary. Runs require a strict MCP configuration
   file owned by the evaluator inside the disposable workspace. That file
   contains only an empty `mcpServers` object, avoiding Windows launcher
   argument rewriting while preserving an empty MCP boundary. Runs also disable
   Chrome integration and isolate Windows home, AppData, and XDG paths in the
   ephemeral profile. The isolation audit rejects raw Claude commands that omit
   or override those controls. Each Claude result also retains a sanitized
   environment manifest that classifies relevant paths relative to the
   ephemeral profile or execution workspace (including QMD's workspace-local
   XDG directories) and records the empty MCP file's fixed path and content
   digest after the target process exits. The project settings also set
   `disableBundledSkills: true`, and the manifest records that value after the
   target process exits; missing, malformed, changed, or external-path evidence
   invalidates the measurement. Version 1 and version 2 environment evidence
   remain readable only in append-only historical records. Every new run emits
   version 3 with the MCP and project-settings evidence, and publication rejects
   older evidence as a new record. A new non-invalid Claude case must contain
   version 3 evidence; `null` is reserved for a case already classified invalid
   because isolation evidence was unavailable. Prompts,
   commands, machine
   isolation results, and model output are written under the ignored batch
   workspace; credentials are never written there. Immediately before and
   after the target call, the evaluator snapshots the disposable execution
   workspace without following symlinks. The retained raw result includes a
   deterministic created/modified/deleted diff with relative paths, content
   digests, sizes, and bounded UTF-8 text for human inspection before cleanup.
   The `commands` subcommand is a read-only command preview and does not stage
   the referenced execution workspace; only `run` and `run-batch --execute`
   create the evaluator-owned MCP file before launch.

   Before staging a Claude execution workspace, no external parent may contain
   `.claude/skills`; otherwise Claude can discover host Skills even when its
   profile is isolated. The workspace-local `.claude/skills` root is then
   populated only with evaluator-staged Skills. Before launch, the evaluator
   records the names of installed host Skills. Claude's bundled Skills are
   disabled for isolated single-Skill and batch evaluations; Claude's documented
   `doctor` exception may remain visible. After launch, the evaluator parses the
   single `system/init.skills` list and requires it to contain the staged Skills
   and no undeclared Skill other than `doctor`. The raw result retains the
   name-only host inventory so later aggregation and publication can distinguish
   host contamination from other undeclared discovery and recompute the check.
   If that host inventory also contains `doctor`, the name-only evidence cannot
   prove which copy Claude loaded, so the measurement is invalid. Missing or
   contradictory Skill-discovery evidence is also an invalid measurement.

3. Grade the raw results and review the offline report. Claude evidence cannot
   substitute for Codex evidence or vice versa.

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
   and Git-backed fixtures, canonical Skill identity, target identity and
   process status, external-runtime identity/setup evidence,
   normalized final response, structured model/tool trace, raw streams, and
   current grading. Claude runs use verbose stream JSON so Bash/Read tool use
   and tool results remain reviewable rather than being collapsed into only the
   final answer. Each run also has a visible machine isolation PASS/FAIL badge;
   a successful out-of-workspace file tool, or an undeclared Bash command in a
   read-only case, blocks attestation. Missing or malformed audit data is a
   failure, not a pass. The report labels observable Skill trajectory
   violations as `ISOLATION FAIL`, while evaluator-boundary contamination and
   missing, malformed, or contradictory evidence are `ISOLATION INVALID`. The
   report places Claude and Codex runs in separate target sections. A process
   pass is not a behavior pass; the human records a specific reason for every
   assertion in the linked `grading.json`. The v3 grading contract preserves
   each assertion's ID, kind, description, and required/optional flag. Optional
   failures remain visible warnings; required failures block acceptance. It
   also requires `observed_invocation`: `explicit`, `implicit`, `not-invoked`,
   or `unknown`, plus a concise `invocation_evidence` explanation. Templates
   always begin as `unknown`, including explicit runs. The reviewer classifies
   them from the observable trace; the evaluator compares the result with the
   predeclared expectation. Each trajectory assertion also predeclares exactly
   one acceptable observable evidence class in the source case. The grade must
   match that class: Tool trace, external state, or verified absence from a
   complete trace. A positive Tool-call requirement cannot pass by claiming
   verified absence. An external-state pass requires an actual captured
   workspace change; reviewer prose alone is insufficient. Non-trajectory
   assertions use final output, invocation trace, or not applicable as
   appropriate, and no completed grade may retain a pending observation.

   `prepare-review` also creates `<name>/review.json`. After checking the HTML
   and every grading file, set its status to `pass` and record the reviewer,
   timezone-qualified review time, reason, and any corrective action. Here
   `pass` means review was completed; it cannot change a failed platform result
   into a pass. Set `sanitization_confirmed` only after inspecting the retained
   evidence for credentials, personal data, private paths, and other secrets.
   The builder also scans the entire prospective record—including prompts,
   expected outcomes, observations, and review text—and fails closed on
   residual sensitive values.

4. Build a sanitized preview directly from the raw results, grading files, and
   review decision:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py build-record . `
     .scratch/skill-evals/batch-<run-id> <name> <run-id> `
     --output .scratch/skill-evals/batch-<run-id>/<name>/record-draft.json
   ```

   Then publish from the same fixed plan without hand-copying evidence:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py publish-reviewed . `
     .scratch/skill-evals/batch-<run-id> <name> <run-id>
   ```

   The command writes
   `evaluations/records/<name>/<run-id>/record.json` and `summary.md`. Every
   completed pass, failure, and invalid run is retained. Missing or malformed
   measurement evidence is `invalid`, not a Skill failure. If exactly one
   platform passes, the preview is `human-review-required`; after review it
   remains `fail` or `invalid`, never `pass`. Private paths and credential-like
   values are redacted; raw streams remain ignored. Publishing is append-only.
   A residual sensitive-data scan fails closed even after human confirmation.
   Observable actions by the evaluated Skill that violate isolation or
   authorization are Skill failures. Evaluator-boundary failures such as host
   Skill contamination, and missing or contradictory audit evidence, are
   invalid measurements.

   The builder reads the fixed plans stored in each raw result. If the Skill or
   case manifest has changed, the invalid record retains the digest, prompt, and
   case manifest that were actually tested; it does not relabel old evidence as
   a test of current content.

   `publish-record` remains available for a separately constructed compatible
   record; the normal workflow is `publish-reviewed`.

5. If and only if the explicitly requested diagnostic needs a selected passing record, and the
   published record passes for both platforms and the exact current Skill digest, select it
   and verify the optional evaluation gate:

   ```powershell
   python tools/skill-evaluator/skill_evaluator.py select-record . `
     skills/<bucket>/<name> `
     evaluations/records/<name>/<run-id>/record.json
   python tools/skill-evaluator/skill_evaluator.py verify-attestation `
     skills/<bucket>/<name> attestations/skills/<name>.json
   python scripts/validate_repo.py --require-evaluations
   ```

Any change inside the Skill directory changes its digest and makes a previous optional release
pointer stale. Changing a selected `record.json` also invalidates its record digest. Default
repository validation remains deterministic and does not inspect those optional pointers.
