# Skill Consolidation Design

This document records confirmed product behavior for consolidating personal skills into
MySkills. Domain language belongs in `CONTEXT.md`; hard-to-reverse architectural trade-offs
belong in ADRs.

## Confirmed scope

- MySkills is a private repository used by one person across multiple Windows computers.
- MySkills becomes the only editable source of truth for explicitly accepted Managed Skills.
- Discovery does not imply ownership: all valid discovered skills begin as Candidate Skills.
- Orca CLI artifacts and Codex system-managed skills are outside the inventory.
- The former source repositories remain untouched during migration. After verification, their
  remotes may be archived and their local folders retained temporarily; MySkills never deletes
  them.
- Skills are imported as file snapshots with Provenance, without merging former Git histories.

## Skill authoring principle

- Managed Skills are concise by default. `SKILL.md` contains only non-obvious triggering
  metadata, essential procedure, hard constraints, and the minimum completion evidence needed
  to control agent behavior; it does not teach general reasoning the agent already possesses.
- Brevity is judged by behavioral leverage rather than an arbitrary line limit. Every retained
  paragraph must change a decision or action that a capable agent would otherwise get wrong.
- Detailed schemas, variant-specific facts, and examples move to directly linked
  `references/` files and are loaded only when the active task needs them. Deterministic or
  repetitive mechanics belong in tested `scripts/` and reusable output material belongs in
  `assets/`.
- Information is not duplicated between `SKILL.md`, references, and central installer
  manifests. Dependency installation, platform targets, and machine-state policy remain
  central MySkills concerns rather than repeated prose in each Skill.
- Import review actively shortens verbose source Skills while preserving their behavioral
  invariants. A Skill is not expanded merely to encode every conceivable exception.
- Existing automation and confirmation boundaries are behavioral invariants. Shortening or
  reorganizing a Skill must not add confirmation prompts to an automatic source workflow,
  remove a source-required confirmation, or change a read-only default into a write mode.
  Such a change requires a separate explicit user decision.

## Inventory

- `inventory/skills.json` is the machine-readable authority.
- `docs/skill-inventory.md` is generated for human review.
- Candidate states are `pending`, `managed`, `deferred`, and `excluded`.
- Skill Origin records where a candidate was found; Skill Category controls its bucket in
  MySkills. For standalone and Matt-derived skills the category is functional. The LLM Wiki
  source suites deliberately preserve their package boundaries as categories.
- `engineering`, `productivity`, and `personal` are valid functional categories inherited from
  the Matt Pocock layout.
- Every skill sourced from `obsidian-wiki/.skills` belongs to `wiki`, including supporting
  policy, validation, skill-creation, graph, and layout workflows.
- Every skill sourced from `obsidian-skills/skills` belongs to `obsidian`, including `defuddle`.
- The QMD skill sourced from `qmd/skills/qmd` belongs to `qmd`.
- MySkills does not model a separate skill lifecycle. Former `in-progress` and `deprecated`
  folders are recorded only as part of Provenance and are not functional categories.
- Every Managed Skill is installable; installation eligibility is not controlled by a separate
  lifecycle flag.
- `misc` is not a valid category; candidates from that origin must receive a meaningful
  functional category before becoming Managed Skills.
- Duplicate installations with identical directory content represent one Candidate Skill.
- Same-name variants with different content are never merged or selected automatically.
- The `wiki` category has 20 Managed Skills. `impl-validator`, `daily-update`,
  `wiki-stage-commit`, `obsidian-layout-adjustment`, `vault-skill-factory`, and `wiki-agent`
  are excluded, as are the report-only `wiki-digest` and the external-format
  `wiki-export`/`wiki-import` pair. `wiki-narrate` is also excluded because its presentation
  modes are part of `wiki-query`; `wiki-switch` is excluded because the first version has one
  configured vault. Six provider-specific history Skills are replaced by one
  `wiki-history-ingest` Skill with only Claude, Codex, and Antigravity source adapters.
  `ai-policy-sync` and its central policy subsystem are not installed. The source
  `skill-creator` is transformed into the Engineering Skill `skill-evaluator`.
- In the `obsidian` category, `json-canvas`, `obsidian-bases`, `obsidian-cli`, and
  `obsidian-markdown` are Managed Skills; `defuddle` and `obsidian-vault` are excluded.
- The `qmd` skill is a Managed Skill.

## Windows management interface

- PowerShell is the only guaranteed management entry point.
- The single primary user entry point remains the existing installer:
  `powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1`.
- No `myskills.cmd` launcher or repository-root `myskills.ps1` command router is introduced.
- The command's `-ExecutionPolicy Bypass` applies only to that PowerShell process; the installer
  never calls `Set-ExecutionPolicy` or changes user/machine policy.
- Windows PowerShell 5.1 is the minimum supported management runtime. The installer also
  remains compatible with PowerShell 7 when invoked explicitly with `pwsh`, but PowerShell 7
  is not a prerequisite.
- Bash is not a Runtime Prerequisite for the Windows-only first version. Managed Skills that
  actually execute bundled `.sh` files—including `wiki-setup`—must be ported to PowerShell and
  pass Windows verification before they are considered fully usable.
- Bash fences that merely document source data, historical agent events, or commands belonging
  to a user's target project are not mechanically rewritten.
- Managed Skills must remain operational after the former source repositories are archived or
  removed. Runtime references to `$OBSIDIAN_WIKI_REPO`, its `scripts/` directory, or an absolute
  former clone path are prohibited even though source-repository references remain valid in
  Provenance and historical documentation.
- Wiki helper ownership is made explicit during import: `manifest.py` moves under
  `llm-wiki/scripts/`; `extract-jsonl.py` moves under
  `wiki-history-ingest/scripts/claude/`. The excluded `daily-update` Skill's shell helpers and macOS
  launchd plist are not imported into the Windows-only package.
- The first MySkills version consolidates repository ownership, installation, and dependency
  management without consolidating or redesigning existing Python behavior. Imported helpers
  remain separate, existing `obsidian-wiki` CLI commands retain their current responsibilities,
  and no helper is absorbed into the CLI merely to produce a uniform interface. Other than
  necessary Windows compatibility and removal of former-repository path assumptions,
  behavioral rewrites require a later explicit decision backed by parity fixtures.
- The excluded `vault-skill-factory` is not imported. Installer validation still rejects
  executable references from Managed Skills to the former source clone.
- Installation, dependency detection, prompts, copying, and post-install verification are
  orchestrated by `scripts\install.ps1`. Supporting diagnostic or test scripts may exist for
  maintainers and AI agents, but users are not expected to remember a separate command suite.
- Every installer run begins with a read-only preflight covering all Runtime Prerequisites,
  runtime managers, target Agent CLIs, required external CLIs, and dependency version probes
  for the requested Managed Skill set. No Skill copy, package installation, configuration
  edit, state-file write, or backup occurs until the complete preflight report has been shown.
- A Managed Skill is copied only when every capability required by its documented contract has
  passed its version and smoke checks. MySkills does not install a knowingly incomplete Skill
  under a `DEGRADED` label. A capability may be optional only when its absence preserves the
  complete primary workflow through an explicitly accepted fallback; optional absence is
  reported as capability information rather than a successful-but-degraded Skill.
- Each normal installer run also queries configured package sources for available dependency
  versions and prints a table containing the MySkills default, locally detected version,
  available version, Runtime Prerequisite constraint, and status.
- Package-source lookup is advisory and non-blocking. When offline or the registry is
  unavailable, the installer reports that update status could not be checked and continues
  using repository-recorded dependency data.
- An available version is never adopted automatically. The interactive installer asks before
  adopting it; declining does not block Skill installation or change the computer or
  repository.
- Dependency decisions compare three independent values: `D`, the MySkills default installation
  version; `L`, the locally detected version or absence; and `R`, the latest version reported by
  the configured package source. Detection alone never changes `D`.
- When `L` exists, is compatible, and no release newer than `L` is available, MySkills keeps
  using `L` and leaves `D` unchanged.
- When `L` is absent and no release newer than `D` is available, MySkills offers to install
  the verified default `D` and leaves `D` unchanged.
- When compatible `L` exists and `R` is newer, MySkills shows `L -> R` and asks whether to
  upgrade this computer and adopt `R` as the new default. Declining keeps both `L` and `D`;
  accepting changes `D` only after installation and verification of `R` succeed.
- When `L` is absent and `R` is newer than `D`, the prompt distinguishes installing verified
  default `D`, adopting and installing latest `R`, and declining installation. Installing `D`
  leaves the default unchanged; `R` becomes the default only after successful verification.
- A compatible local version newer than `D` is preserved and never downgraded, but is not
  silently adopted as the MySkills default.
- A local version below `minimum_version` remains incompatible and follows the required versus
  optional dependency outcome after the offered upgrade is declined or fails.
- Adopting `R` is transactional with respect to the observable pre-update state. MySkills does
  not change `D` until installation and all declared verification checks for `R` succeed.
- If adoption fails and `L` existed, MySkills attempts to reinstall and verify `L`. If no local
  dependency existed before the operation, it removes the failed package installed by that
  operation. Failure to restore the prior state is reported as `RECOVERY_REQUIRED` with a
  nonzero exit code and explicit repair commands.
- A failed dependency adoption does not stop installation of unrelated Skills.
- Normal `install` is interactive. For each missing or incompatible allowlisted dependency it
  displays the affected Skill, capability, detected/minimum/pinned versions, package source,
  and proposed action, then accepts `Y` (this dependency), `N` (decline), `A` (approve remaining
  allowlisted dependency actions for this run), or `Q` (stop further processing).
- `Q` preserves already completed independent items and returns `INCOMPLETE`.
- `-Yes` approves allowlisted installable dependency actions only; it does not install Runtime
  Prerequisites, adopt unrecorded dependency releases, bypass unowned Skill conflicts, or
  override compatibility failures.
- `-DryRun` performs detection and prints the planned prompts and actions without prompting
  or changing machine state.
- Installation is Copy-only. Junction and symlink modes are not supported.
- Managed Skills declare explicit installation targets rather than relying on installer-wide
  implicit copying.
- A repository-level `.agents/skills` installation is discoverable by Codex and Google
  Antigravity, but is not a documented Claude Code discovery location.
- User-wide installations use separate documented targets:
  `%USERPROFILE%\.agents\skills` for Codex, `%USERPROFILE%\.claude\skills` for Claude Code,
  and `%USERPROFILE%\.gemini\antigravity-cli\skills` for Antigravity CLI.
- All 42 currently accepted Managed Skills explicitly target all three user-wide
  installations: Codex, Claude Code, and Antigravity CLI. There are no target exceptions in
  the first version. The per-Skill manifest repeats these three targets so future compatibility
  exceptions are visible in review rather than inherited from a hidden default.
- Claude Code and Codex are the primary, behavior-certified platforms. Skill design,
  invocation-policy review, trigger tests, and passing evaluation
  attestations cover those two targets.
- Antigravity is a secondary compatibility-copy target. It receives the same unchanged
  canonical directory used by Codex, with no Antigravity-specific edition, overlay, creator
  requirement, or behavioral attestation in the first version. This lower support tier is
  reported explicitly and does not block Claude/Codex authoring or release.
- A Managed Skill may omit a target only through an explicit platform-compatibility
  declaration. The installation summary must identify every omitted target and its reason;
  an incompatible or unsupported target is never silently skipped.
- Antigravity CLI installations always target
  `%USERPROFILE%\.gemini\antigravity-cli\skills`. The broader Antigravity product path
  `%USERPROFILE%\.gemini\config\skills` is outside the current CLI-only scope and is not used
  as a fallback.
- Antigravity detection probes `agy` first and then the observed Windows installation at
  `%LOCALAPPDATA%\agy\bin\agy.exe`; the current CLI identifies itself through `agy --version`.
  When present, the installer verifies target-path ownership and copied hashes but does not
  run Antigravity model-based behavior evaluation. When absent, no compatibility copy is made.
- Claude, Codex, and Antigravity Agent CLIs have no MySkills minimum-version requirement.
  Installer eligibility depends only on resolving and starting the expected executable;
  reported versions are diagnostic information and are never compared with a threshold.
  A later operation that uses a CLI capability must execute that capability and report its
  actual failure rather than infer support from a version number.
- `.claude/skills` is the Claude Code project target, while `.codex/skills` is reserved for
  Codex-specific compatibility material rather than general skill discovery.
- `.codex/skills/.system` is never managed or modified.
- Sharing the Agent Skills directory format does not guarantee identical behavior:
  Claude-specific frontmatter and Codex `agents/openai.yaml` metadata may require
  platform-specific validation or overlays.
- Each Managed Skill has one canonical directory whose contents are copied unchanged to all
  compatible platform targets. MySkills does not maintain separate Claude, Codex, or
  Antigravity editions.
- Platform overlays are not part of the initial design. They may be introduced only after a
  reproducible compatibility failure proves that unchanged canonical content cannot work.
- Twenty-eight workflows are human-only and require the user to explicitly name or invoke the
  Skill:
  - Engineering: `ask-myskills`, `grill-with-docs`, `implement`,
    `improve-codebase-architecture`, `skill-evaluator`, and `to-spec`.
  - Productivity: `ai-handoff`, `grill-me`, and `session-checkpoint`.
  - Wiki: `project-rules-init`, `graph-colorize`, `wiki-history-ingest`, `cross-linker`,
    `llm-wiki`, `memory-bridge`, `tag-taxonomy`, `wiki-capture`, `wiki-context-pack`,
    `wiki-dashboard`, `wiki-dedup`, `wiki-ingest`, `wiki-lint`, `wiki-rebuild`,
    `wiki-research`, `wiki-setup`, `wiki-status`, `wiki-synthesize`, and `wiki-update`.
- Fourteen workflows allow implicit invocation:
  - Engineering: `codebase-design`, `code-review`, `diagnosing-bugs`, `domain-modeling`,
    `prototype`, `spec-package-generator`, and `tdd`.
  - Productivity: `grilling`.
  - Wiki: `wiki-query`.
  - Obsidian: `json-canvas`, `obsidian-bases`, `obsidian-cli`, and `obsidian-markdown`.
  - QMD: `qmd`.
- `wiki-query` is the only Wiki Skill that allows implicit invocation. Its trigger description
  must limit automatic selection to questions explicitly concerning the user's Wiki or
  knowledge base, not general knowledge questions.
- Functional parity takes precedence over minimizing implicit Skill exposure. Human-only
  metadata is permitted only when every accepted caller can still complete its original
  workflow without asking the user to issue an additional Skill command.
- An explicitly invoked Wiki workflow may load a declared internal contract, reference, helper,
  or deterministic script on demand. This is not assumed to work merely because both Skills are
  installed: every internal dependency must have an exact packaged path, be recorded in the
  machine-readable inventory, and be verified on both Claude and Codex.
- Release tests invoke each human-only Wiki entry point in a fresh Agent session and exercise
  every branch that depends on another Wiki workflow. The tests must prove equivalent results,
  write and confirmation boundaries, tracking updates, and failure behavior without preloading
  the dependency or asking the user for a second invocation.
- If a required workflow cannot be loaded reliably while hidden from implicit discovery,
  MySkills must expose the smallest necessary dependency to both Claude and Codex and report the
  resulting policy change for user approval. It must not preserve the 28/14 count by shipping a
  broken or incomplete workflow.
- The validator requires all 28 human-only Skills to set both Claude
  `disable-model-invocation: true` and Codex `policy.allow_implicit_invocation: false`.
  The remaining 14 Skills must not declare conflicting platform policies.
- A platform that can discover a human-only Skill but cannot enforce its invocation policy is
  reported with an explicit compatibility warning; MySkills does not silently claim equivalent
  behavior.
- The QMD Skill retains its Claude-style `allowed-tools` declaration in canonical content.
  Codex and Antigravity may ignore that field and use their own permission systems; this does
  not require a separate Skill edition.

### QMD CLI and MCP integration

- The `@tobilu/qmd` package provides both the `qmd` CLI and the `qmd mcp` server command; it is
  installed only once per computer.
- The `qmd` Managed Skill requires a working QMD CLI. If it is absent, MySkills offers the
  allowlisted package installation; declining or failing that installation blocks the Skill.
- QMD is optional for the Wiki suite. Missing QMD disables search-index acceleration and refresh
  steps but does not block Wiki Skill installation.
- MCP registration is an optional transport integration rather than a required QMD capability.
  An Agent with working CLI access but no QMD MCP registration is reported as `CLI_ONLY`, not
  `DEGRADED`.
- MySkills may register the same stdio server (`command = qmd`, arguments `mcp`) for Claude
  Code, Codex, and Antigravity CLI during the same interactive installation.
- Claude and Codex registration uses their supported MCP management interfaces when available.
  Antigravity registration is structurally merged into
  `%USERPROFILE%\.gemini\config\mcp_config.json`; this MCP location is independent of the
  CLI-specific Antigravity Skill target.
- An existing identical `qmd` registration is adopted without rewriting it. A missing
  registration is offered for addition. An existing same-name registration with different
  settings is reported as a conflict and never overwritten automatically.
- Registration preserves all unrelated MCP servers and settings. MySkills uses stdio and does
  not start QMD's optional persistent HTTP daemon.
- After registration, MySkills verifies QMD discovery separately for each installed Agent CLI.
- MySkills writes MCP configuration only for Agent CLIs that are installed and whose supported
  configuration mechanism can be verified. An absent Agent is
  `SKIPPED_NOT_INSTALLED`; MySkills does not pre-create or guess that Agent's MCP configuration.
  A later `install` run offers the missing registration after the Agent becomes available.
- Skill files follow the same verified-Agent boundary: MySkills does not copy Skills or write
  MCP configuration for an absent Agent CLI. A later installer run handles both after that
  Agent passes discovery and harmless smoke tests.

### Existing platform-copy audit

The 2026-07-23 discovery audit compared complete relative-file SHA-256 maps under the current
`.agents`, `.claude`, `.codex`, and Antigravity CLI skill directories.

- 61 skill names installed in at least two locations have identical complete content.
- Every multi-location Managed Skill is identical across `.agents`, `.claude`, and `.codex`.
- The only difference among those three locations is `code-review-expert/README.md`; that
  Candidate Skill is excluded and its `SKILL.md` is identical.
- Antigravity CLI contains older, materially different copies of `llm-wiki`,
  `project-rules-init`, and `wiki-switch`. These are version drift, not intentional
  platform-specific variants: the newer authoritative LLM Wiki source adds deterministic
  config resolution, vault-name validation, and the central project-policy workflow.
- Existing installation coverage differs by historical installer: `.agents` has 61,
  `.claude` has 68, `.codex` has 43 excluding `.system`, and Antigravity CLI has 42. A skill
  appearing in only one location is not evidence that its content was adapted for that
  platform.
- The source audit found 13 workflows that already declare Claude
  `disable-model-invocation: true`. Import applies the accepted 28-workflow human-only policy
  above and adds any missing matching Codex or Claude metadata.
- `qmd` declares Claude-style `allowed-tools`; its actual QMD CLI/MCP dependency remains
  portable, but permission metadata requires target-specific validation.
- Some workflows intentionally operate on provider data or configuration, including the
  Claude, Codex, and Antigravity adapters within `wiki-history-ingest` and `wiki-setup`.
  This is functional platform specialization inside one canonical Skill, not evidence of
  separately maintained platform copies.

### Local-first engineering workflow

- `codebase-design` is retained as the shared deep-module, interface, seam, testability, and
  locality vocabulary used by `tdd` and `improve-codebase-architecture`. Its core guidance is
  imported unchanged, it has no third-party CLI or Runtime Prerequisite, and it receives only
  the metadata required for discovery and invocation-policy validation across the three
  supported agent targets.
- `project-rules-init` is retained as an explicit, human-only, one-time or occasional project
  bootstrap. It creates or updates a concise canonical `PROJECT_RULES.md`, short managed
  `AGENTS.md` and `CLAUDE.md` entry blocks that direct supported agents to that canonical
  file, and an architecture baseline at the repository's established documentation location
  or `docs/architecture.md` when no convention exists.
- For an existing project, it distinguishes documented rules, observed implementation
  conventions, and unapproved recommendations. It samples representative code, build and test
  configuration, and architecture evidence, presents the complete proposed rules and baseline,
  and writes only after user approval. It never represents inferred ideal architecture as an
  existing rule.
- For a greenfield formal package, `spec-package-generator` records the user-confirmed Gate 2
  architecture and creates a first bootstrap task that explicitly invokes
  `project-rules-init` with that approved design before feature implementation begins.
- `project-rules-init` is local-only: it does not use a central Wiki policy record,
  `.ai-policy`, pack/lock files, Git remote identity, global agent bootstrap, hooks, tool
  installation, commits, or pushes. It has no third-party dependency.
- `code-review` retains its separate Standards and Spec review axes but removes the
  `setup-matt-pocock-skills` and configured-issue-tracker assumptions. A user-supplied commit,
  branch, or tag is used as the Git baseline when present; otherwise the workflow reviews
  staged, unstaged, and untracked working-tree changes. Specification context comes from an
  explicitly supplied source, the current conversation, `.scratch`, or `.ai-dev`; an external
  issue or pull request is read only when the user explicitly supplies it.
- Git is a required Runtime Prerequisite for `code-review`, not a MySkills-installed
  dependency. Its manifest uses the shared successful `git --version` probe with no initial
  minimum version. Without Git, the Skill is not copied because it cannot perform its complete
  fixed-point change-set review.
- `diagnosing-bugs` is retained as a tool-agnostic debugging discipline whose invariant is to
  establish a tight, red-capable reproduction loop before forming and testing hypotheses.
  Tests, HTTP requests, CLI probes, browser automation, replay fixtures, bisection, and timing
  harnesses are project-selected techniques rather than MySkills-installed dependencies.
  Its human-in-the-loop Bash fallback is ported to PowerShell for the Windows-only package.
- It declares no fixed Runtime Prerequisite or Installable Dependency. At runtime it selects
  an already available project seam; PowerShell `Invoke-WebRequest`, direct CLI execution,
  existing tests, instrumentation, fixtures, or a structured human-operated loop remain valid
  alternatives. A project-local dependency is proposed only when the current bug requires it
  and no equivalent is available.
- If no executable loop can capture the reported symptom, the Skill reports the minimum
  missing capability and cannot claim that diagnosis or root-cause validation completed.
- `improve-codebase-architecture` is retained as a manually invoked architecture-health scan.
  It reports deepening opportunities and then discusses only the user-selected candidate; it
  never schedules scans, runs in the background, or implements a refactor by itself. Git
  history may help identify hot spots but is optional when the user supplies a scope.
- Its visual report must remain usable without network access: packaged local styling replaces
  Tailwind CDN use. It is a second optional consumer of the same centrally managed
  `@mermaid-js/mermaid-cli` 11.16.0 dependency used by `spec-package-generator`; the dependency
  is detected, offered, installed, owned, and updated only once. Its absence falls back to a
  basic HTML/CSS/SVG report and does not block or degrade the architecture analysis.
- `prototype` is retained for throwaway logic, UI, and feasibility experiments. It does not
  create branches, commits, or issue-tracker records. Logic and feasibility prototypes default
  to `.scratch\<prototype-slug>\`; a clearly marked temporary project route is used only when
  a UI question cannot be answered outside the application's routing environment.
- A prototype uses only the target project's existing runtimes and tools, so it declares no
  repository-wide installable development dependency. The learned decision is retained, while
  prototype-file deletion requires the user's direction rather than happening automatically.
- `tdd` is retained as a concise red-green discipline using the target project's existing test
  tools. Before editing, it states whether the task changes observable behavior. A behavior
  change testable through a public seam requires red-green TDD; small size, difficulty, or time
  cost are not exceptions. Otherwise it gives one sentence explaining why TDD does not apply
  and names the alternative verification. Completion requires red-green evidence or evidence
  from that alternative verification.
- Clear existing test seams do not require a user interruption. The workflow asks only when
  materially different seam choices would change architecture or testing cost, and it does not
  install a test framework into a project that lacks one.
- The Matt `research` candidate is excluded. Its background-agent, primary-source, and
  Markdown-report defaults do not add a distinct capability or guarantee exhaustive results.
  Durable external research belongs to `wiki-research`, while ordinary project code searches
  remain direct agent work. A strict `project-usage-audit` may be designed later only if a
  recurring need for exhaustive reference inventories emerges.
- `resolving-merge-conflicts` is excluded. An occasional Git merge or rebase conflict is
  handled as direct project work under the user's current instructions rather than through a
  dedicated workflow that manages staging, commits, continuation, or abort behavior.
- `git-guardrails-claude-code` is excluded. Its Bash hook modifies Claude-specific settings,
  does not protect Codex or Antigravity, blocks even explicitly authorized Git commands, and
  would require security-sensitive Windows command parsing that MySkills will not maintain.
- `teach` is excluded. Ordinary explanations remain direct AI work; MySkills does not maintain
  its large, specialized workflow for converting the current directory into a persistent
  multi-session course with missions, HTML lessons, references, learning records, resources,
  notes, and assets.
- `writing-great-skills` is excluded as an installed workflow. Its useful concision,
  single-source, triggering, and progressive-disclosure guidance belongs to MySkills repository
  authoring rules and validation review, while general Skill creation uses the platform's
  `skill-creator` capability.
- `edit-article` is excluded. Ordinary article revision follows the current request's audience,
  tone, structure, and length instead of a dedicated workflow with a fixed 240-character
  paragraph limit.
- `to-questionnaire` is excluded. A questionnaire for an external person is generated directly
  from the current recipient and information gap when requested, without maintaining a
  dedicated installed workflow.
- `impl-validator` is excluded. Its generic AI second-opinion review overlaps the accepted
  review model without adding deterministic Wiki validation. `memory-bridge` removes its call
  to it; Wiki structure and health use the repository-owned CLI and `wiki-lint`, while
  implementation changes use `code-review`.
- `daily-update` is excluded. MySkills does not install its scheduler, freshness helper, or
  terminal reminder. `wiki-status` owns on-demand source delta and next-action reporting,
  `wiki-lint` owns health checks, and each writing Skill owns its own post-write maintenance.
- `wiki-stage-commit` is excluded because the current configuration does not enable
  `WIKI_STAGED_WRITES` and the user does not want routine per-page approval. The initial
  MySkills package does not offer staged-write configuration; imported Wiki writers use their
  direct-write branches and `wiki-status` omits staged-review recommendations.
- `obsidian-layout-adjustment` is excluded. Its source workflow is personalized to another
  user's visual language and depends on macOS AppleScript and screenshot mechanics. MySkills
  does not maintain a Windows visual-automation rewrite for occasional Obsidian CSS edits.
- `setup-matt-pocock-skills` is excluded. Managed engineering workflows do not require a
  repository-wide setup step.
- `to-tickets` is excluded because this MySkills workflow does not use its ticket-decomposition
  or ticket-publishing behavior.
- Git hosting, branch strategy, and issue tracking are independent concepts. A Bitbucket,
  GitHub, or GitLab remote never implies that the corresponding issue tracker is used, and a
  branch name is not assumed to identify an issue.
- `to-spec` writes the lightweight working artifact
  `.scratch\<feature-slug>\spec.md` by default.
- `to-spec` is retained for small requirements that need only a single synthesis of an
  already-discussed change. It does not interview the user, publish to an issue tracker, or
  apply triage labels. Requirements needing gated PRD, EARS, BDD, technical-design, task,
  prompt, traceability, and readiness artifacts use `spec-package-generator` instead.
- `implement` is the lightweight execution workflow only for a `to-spec` artifact or a small
  task stated directly by the user. It does not execute or wrap a formal
  `spec-package-generator` package.
- Before editing, `implement` verifies applicable project rules, reads the referenced
  architecture guidance, and samples nearby representative implementations. When the task
  creates or changes a module interface, seam, adapter, dependency direction, or architectural
  responsibility, it loads `codebase-design`; ordinary local edits do not.
- `implement` uses applicable project validation and ends with `code-review`. The Standards
  axis checks documented project rules, nearby conventions, architecture direction, and
  available test/lint/type-check/build evidence. A failed required check prevents a successful
  completion report. The workflow does not create a branch or commit unless the user
  explicitly requests that Git mutation. Git is not required when the project provides
  non-Git verification.
- `spec-package-generator` alone owns the formal AI-ready package under
  `.ai-dev\features\<feature-name>\`; `to-spec` does not create a competing `docs\specs`
  convention.
- Large efforts are implemented task-by-task from the prompts generated by
  `spec-package-generator`. The generator itself remains specification-only and does not edit
  downstream production code.
- Existing-project Gate 2 treats applicable `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`,
  architecture/ADR sources, representative implementations, and validation commands as
  grounding inputs. Generated task prompts require the executor to re-read the current project
  rules and conditionally load `codebase-design` under the same architectural-change test used
  by `implement`; they do not embed a stale duplicate of the rules.
- `triage` is excluded because MySkills does not maintain an unclassified request inbox or
  issue-tracker triage workflow.
- `wayfinder` is excluded because its parent/child issues, labels, assignments, native
  blocking relationships, and subagent workflow would require a substantial rewrite for
  local files. `grill-with-docs` already owns iterative decision clarification,
  `spec-package-generator` owns resumable formal specification, and the future
  multi-project coordinator will separately own executable task coordination.
- `code-review` accepts an explicit diff baseline and local specification.
- A repository-specific output location overrides these defaults only when authoritative
  repository instructions, an established repeated template, or a managed tool explicitly
  defines that artifact's location. The mere presence of a generically named `docs` or
  `specs` directory is insufficient.
- External issue creation or mutation occurs only when the user explicitly requests a named
  tracker. Any required CLI, authentication, and project-specific workflow are checked at
  that time rather than during MySkills installation.
- Domain documentation remains self-initializing: an existing `CONTEXT-MAP.md` selects
  multi-context behavior, otherwise `CONTEXT.md` and ADR directories are created lazily when
  the workflow first has durable domain information to record.

### Cross-session handoff transport

- `ai-handoff` owns construction and validation of every prompt intended for another AI
  session. Its two first-class delivery modes are manual copy/paste by the user and explicit
  live delivery through an available transport. Live delivery is never inferred merely
  because a transport is available.
- A transport CLI may deliver the validated payload but must not independently assemble or
  rewrite it.
- The Skill and its contract remain transport-neutral and do not name or depend on a specific
  session-management CLI.
- The default handoff is a concise, structured text prompt rather than a file. It references
  authoritative repository artifacts instead of copying conversations, source files, or
  already-recorded decisions.
- Manual copy/paste mode prints the validated prompt for the user to copy. `ai-handoff` has no
  clipboard-writing feature and never calls `Set-Clipboard`.
- Text placed directly in a terminal transport must be ASCII-only and must not
  contain emoji, full-width punctuation, or other non-ASCII characters.
- The default transport budget is 6,000 ASCII characters and the hard ceiling is 10,000 ASCII
  characters. A prompt over the default budget is reduced again; it may approach the hard
  ceiling only when further reduction would remove required handoff information. Character
  counting is used instead of a model-specific tokenizer.
- A file is an exceptional fallback only when required source material cannot be safely
  summarized or represented in ASCII; no fixed shared handoff directory is assumed.
- Every handoff declares `audience: agent` or `audience: human`. Agent-to-agent exchanges do
  not constrain the agents' working language and do not translate source material merely for
  transport. The ASCII-only envelope rule still applies.
- A human-facing delivery declares `response_language: zh-TW`; its final response is
  Traditional Chinese while code, commands, paths, and proper names remain in their original
  form.
- A multi-hop agent exchange that will eventually produce a human-facing answer carries
  `final_audience: human` and `final_response_language: zh-TW`. Intermediate agent responses
  need not be translated; the language constraint applies at final human delivery.
- `Answer in Traditional Chinese (zh-TW).` is therefore added only for a human-facing final
  delivery, not unconditionally to every transport envelope.
- Validation checks encoding, allowed characters, length, and required fields before
  delivery. Post-delivery verification reads receiver state and treats mojibake, truncation,
  or delivery to the wrong session as failure; the same uncorrected payload is not blindly
  resent.
- The current Python payload builder is ported to Windows PowerShell so the core handoff
  protocol does not acquire a Python dependency.
- Direct use of an external transport outside `ai-handoff` is outside MySkills' enforcement
  boundary and cannot be claimed as compliant.
- The Matt source candidate `handoff` is imported as `session-checkpoint`. It creates a
  non-delivered summary for resuming work later and never contacts another session;
  `ai-handoff` prepares a prompt for another AI now. Both remain human-only workflows.
- `session-checkpoint` writes `<current-project-root>\HANDOFF.md` by default, rather than using
  the operating-system temporary directory. When that path already exists, it updates the
  current goal's prior checkpoint only after confirming that the file is in fact an older
  checkpoint; a file serving another purpose is not overwritten without user direction.
- A request equivalent to "hand the discussion to project X to execute" selects
  `ai-handoff` live-delivery mode and authorizes delivery to the resolved target session or
  project. A request equivalent to "turn the discussion into a prompt for Claude" selects
  prompt-only mode and returns text without contacting or creating another session.
- Live delivery prefers an available session in the target project. If none is available, the
  request to hand work to that project for execution also authorizes creation of a new
  session. An explicitly named agent such as Claude or Codex is used; otherwise the target
  project's configured default agent is used. If neither is available, `ai-handoff` asks the
  user rather than guessing an agent.
- An existing session is automatically reused only when it is blank or demonstrably belongs
  to the same goal or task. Idle status alone is insufficient because unrelated context may
  remain. If no matching session exists, a new session is created. A user-selected session is
  inspected before delivery, and a conflict with active unrelated work is reported before
  sending.
- A normal live `ai-handoff` is a full transfer of ownership. After verified delivery, the
  originating session stops working on and monitoring that task. Waiting, supervision,
  progress tracking, or result aggregation occurs only when the user explicitly requests
  coordination.
- Future multi-project coordination is a separate `multi-project-coordinator` concern rather
  than another mode hidden inside `ai-handoff`. The coordinator will decompose a goal into a
  task dependency graph, use `ai-handoff` as its delivery primitive, track idempotent task
  IDs, collect compact worker reports, apply human gates to consequential actions, and
  produce the final Traditional Chinese report.
- Worker reports use the fields `TASK`, `STATUS`, `CHANGES`, `VERIFICATION`, `ARTIFACTS`,
  `DECISIONS NEEDED`, `RISKS`, and `NEXT`; they reference commits, paths, tests, and
  specifications instead of returning complete conversations or logs.
- The coordinator is deliberately outside the initial Managed Skill inventory. The initial
  `ai-handoff` contract must remain usable as its future transport primitive without taking
  on coordinator state or monitoring responsibilities.

## Dependencies

The first-stage dependency registry is closed with these declarations:

| Capability or package | Consumers | Minimum accepted | MySkills install version | Management |
| --- | --- | --- | --- | --- |
| Windows PowerShell | Installer | 5.1 | Not installed | Required host runtime |
| Python | All 20 Wiki Skills; `skill-evaluator` | 3.10 | Not installed | User-provided runtime |
| PyYAML | `skill-evaluator` | 6.0.3 | 6.0.3 | Private evaluator venv |
| Node.js | `qmd` | 22.0.0 | Not installed | User-provided runtime |
| `@tobilu/qmd` | `qmd`; optional Wiki acceleration | 2.5.3 | 2.5.3 | Managed Node CLI |
| Node.js | Mermaid rendering | `^18.19` or `>=20.0` | Not installed | User-provided runtime |
| `@mermaid-js/mermaid-cli` | `spec-package-generator`; `improve-codebase-architecture` | 11.16.0 | 11.16.0 | Optional managed Node CLI with complete `.mmd` fallback |
| Git | `code-review`; optional task-specific consumers | No numeric minimum | Not installed | Require successful `git --version` where contractually required |
| Official Obsidian CLI | `obsidian-cli` | No numeric minimum | Not installed | Require successful `obsidian help` |
| Dataview | Optional `wiki-dashboard` mode | No numeric minimum | Not installed | Require installed-and-enabled vault plugin only for Dataview requests |
| Claude, Codex, Antigravity CLIs | Platform installation targets | No numeric minimum | Not installed | Require executable startup; Antigravity remains compatibility-only |

The repository-owned `obsidian-wiki` CLI is versioned with MySkills rather than treated as a
PyPI dependency. QMD is required by the `qmd` Skill but optional for Wiki acceleration.
Remaining Managed Skills have no fixed third-party installation dependency; project-local
tools are selected only when required by the task and project.

- PowerShell, Git, Node.js, and Python are Runtime Prerequisites. MySkills detects them and
  validates the declared version constraint or capability probe but does not install them.
- Missing Git blocks a Skill whose complete contract requires Git, including fixed-point
  `code-review`; a workflow with a previously accepted non-Git complete path may remain
  eligible. Each workflow verifies Git again immediately before performing a Git operation.
  Diagnostics identify Git as the unavailable capability and provide Git for Windows guidance.
- The initial design assigns Git no repository-wide minimum version. Detection requires a
  successful `git --version`; an individual Skill may declare a minimum version later if it
  adopts a feature that demonstrably requires one.
- Runtime versions are evaluated per dependency instead of imposing the highest requirement
  globally. A computer may therefore satisfy Mermaid CLI while remaining ineligible for QMD.
- Missing-runtime guidance recommends a version manager rather than a standalone runtime
  installer. On Windows, Node.js guidance uses Volta and Python guidance uses the official
  Python Install Manager. MySkills prints their official WinGet commands and the compatible
  runtime-version command, but never executes either manager or runtime installation.
- The initial guidance is:
  `winget install Volta.Volta` followed by `volta install node@22`, and
  `winget install 9NQ7512CXL7T -e` followed by `py install 3.12`.
  The authoritative references are `https://docs.volta.sh/guide/getting-started` and
  `https://docs.python.org/3/using/windows.html`.
- A compatible existing Node.js or Python runtime installed without the recommended manager is
  accepted as `COMPATIBLE_UNMANAGED` after executable, version, package-manager, architecture,
  and smoke probes pass. It is not replaced or adopted by a manager automatically. Guidance
  for a missing or incompatible runtime always uses the recommended manager.
- Node-based Installable Dependencies require both a compatible `node --version` result and a
  working `npm --version` result. Preflight also detects Volta, fnm, NVM for Windows, and
  unmanaged installations without switching the user's active Node version or persistently
  modifying `PATH`.
- If Node.js is compatible but npm is absent or broken, MySkills reports repair guidance and
  does not attempt to repair or reinstall Node.js. Every Skill requiring a Node-installed
  capability remains `BLOCKED`.
- On a Volta-managed runtime, a Node CLI is installed and updated through
  `volta install <package>@<version>`. On an accepted unmanaged runtime, MySkills may use
  `npm install --global <package>@<version>` after normal dependency confirmation and records
  the resulting ownership. Existing fnm or NVM for Windows environments use the active
  compatible Node version and receive manager-specific persistence warnings rather than an
  automatic version switch.
- A compatible existing CLI installed through Bun, pnpm, another manager, or an unknown source
  is classified as `preexisting` and preserved.
- Automatic dependency upgrade and rollback are allowed only when MySkills can prove that the
  relevant installation is npm-managed. For another or unknown manager, MySkills reports the
  available release and manager-appropriate manual guidance but does not overlay an npm global
  package that could create ambiguous `PATH` resolution.
- Functional tools such as QMD or Mermaid CLI may be Installable Dependencies.
- A skill declares the dependencies it needs; a central allowlisted registry owns detection,
  installation, and verification recipes.
- Each registry entry records a `minimum_version` used to accept an already-installed tool and
  an `install_version` pinned to the version MySkills has verified and installs.
- Dependency update checks are not scheduled and are not delegated to GitHub automation in the
  first version.
- MySkills does not replace an existing dependency whose version satisfies
  `minimum_version` merely because it differs from `install_version`.
- Finding an executable on `PATH` is insufficient: dependency detection must run its
  allowlisted version probe. A command that exists but cannot complete that probe is a broken
  installation, and MySkills offers to reinstall the pinned version. Declining has the same
  required/optional outcome as any other unavailable dependency.
- An installed dependency below `minimum_version` is treated as incompatible. MySkills reports
  the current, minimum, and pinned installation versions and offers an in-place package-manager
  upgrade to `install_version`.
- If that upgrade is declined or fails, every Skill requiring that dependency remains
  `BLOCKED`. MySkills does not manually delete the old tool before invoking its package
  manager.
- Dependencies are classified as `required` or `optional`.
- A missing required dependency blocks its Skill after the authorized installation attempt
  fails or is declined.
- A missing optional dependency is offered for installation when its Runtime Prerequisites are
  compatible. It may be absent only when the manifest names an explicitly accepted complete
  fallback; the Skill remains fully installed and the summary identifies which optional
  implementation was not selected.
- Missing or incompatible Runtime Prerequisites block only affected installations and report
  the required minimum version.
- Installable Dependencies require interactive confirmation by default.
- `-DryRun` previews dependency actions; `-Yes` permits allowlisted non-interactive actions.
- Removing a Managed Skill removes only its MySkills-managed platform copies and never
  automatically removes shared runtimes or third-party dependencies.
- A separate dependency-cleanup report may list installed tools no longer referenced by any
  Managed Skill. Removing one requires a distinct explicit confirmation.
- Machine state records each detected dependency as `preexisting` or
  `installed_by_myskills`.
- A `preexisting` dependency is report-only and MySkills never removes it. Only an
  `installed_by_myskills` dependency with no remaining Managed Skill references may become an
  executable cleanup candidate.

### Mermaid rendering

- The installed `mermaid-diagram-renderer` Candidate Skill is excluded because its upstream
  repository, author, and license could not be established.
- `spec-package-generator` remains responsible for generating Mermaid `.mmd` source files and
  will be revised to invoke the official `@mermaid-js/mermaid-cli` directly.
- Node.js is a Runtime Prerequisite for diagram rendering. Mermaid CLI 11.16.0 accepts
  Node.js `^18.19 || >=20.0`; this constraint is evaluated only when Mermaid CLI is needed.
- `@mermaid-js/mermaid-cli` is an Installable Dependency managed through the central dependency
  registry, initially pinned to `11.16.0`, and is optional for `spec-package-generator`.
- When Mermaid CLI is missing, MySkills offers to install it after confirming a compatible
  Node.js runtime. If Node.js is unavailable or incompatible, MySkills does not install Node.js
  or Mermaid CLI. The previously accepted authoritative-`.mmd` fallback remains a complete
  primary workflow rather than a degraded installation; the summary explicitly reports that
  optional SVG rendering was not selected.
- Mermaid `.mmd` files remain authoritative; SVG files are reproducible review artifacts.

### QMD

- The `qmd` Managed Skill requires a working `@tobilu/qmd` CLI. The package also supplies the
  `qmd mcp` stdio server; one machine-level package installation supports both interfaces.
- The initial pinned QMD installation version is `2.5.3`.
- QMD requires Node.js 22.0.0 or later. This requirement blocks only QMD installation and does
  not raise the Node.js requirement of Mermaid CLI or unrelated Skills.
- QMD is optional for the Wiki suite: without it, accelerated indexing, refresh, and search
  features are unavailable, but Wiki Skills remain installable.
- MCP registration is optional and tracked independently for each installed agent. A working
  CLI without MCP registration is reported as `CLI_ONLY`, not `DEGRADED`.

### Skill evaluation

- The normative evaluation model is defined in
  [`skill-evaluation-design.md`](skill-evaluation-design.md). This section retains the
  repository-level integration constraints; the attestation runbook documents execution
  steps rather than acceptance policy.
- The LLM Wiki source candidate `skill-creator` is transformed into the human-only
  Engineering Skill `skill-evaluator`. It does not author or package Skills. A platform
  creator or the repository-owned `scripts\new-skill.ps1` scaffolder creates or edits the
  Skill; `skill-evaluator` then performs structural, behavioral, efficiency, trigger,
  and human-review evaluation.
- Every MySkills creation path has an explicit creator-to-evaluator handoff. After authoring
  and basic structural validation, the creator invokes `skill-evaluator` against the new
  Managed Skill and does not report creation as complete until the evaluator has produced a
  passing attestation for the current Skill digest. If evaluation recommends changes, the
  creator applies only the accepted changes and evaluates the new digest again. If evaluation
  cannot run or still fails, creation is reported as incomplete rather than silently accepted.
  Repository instructions enforce this final creator step for platform-native creators; the
  deterministic scaffolder also prints the same required next action but does not pretend that
  an empty scaffold has been evaluated.
- MySkills repository instructions require every newly authored Managed Skill to run
  `skill-evaluator` before completion. The evaluator writes raw runs under the ignored
  `.scratch\skill-evals\<skill>\<run-id>\` and records a compact, source-controlled attestation
  containing the evaluated Skill digest, evaluator version, test targets, results, and
  unavailable capabilities. Repository validation rejects a new Managed Skill whose current
  digest lacks a passing attestation.
- Provenance alone does not exempt an import from behavioral evaluation. A snapshot whose
  complete directory digest is unchanged from its recorded source receives structural
  validation plus Claude and Codex discovery and explicit-invocation smoke tests. Any import
  that is shortened, Windows-ported, renamed, merged, split, or behaviorally changed is treated
  as a substantive revision and requires the same full Claude-and-Codex evaluation as a newly
  authored Skill. Repository validation records the source and current digests so this
  distinction is mechanical rather than judgment-based.
- Default evaluation is report-only. It validates the MySkills structure and metadata, runs
  realistic cases with the Skill installed, evaluates explicit assertions, measures time and
  tokens when exposed by the runner, and renders an offline static HTML review. Applying
  recommendations is a separate creator/editing action.
- Trigger results are target-specific. Claude results never stand in for Codex. A passing
  attestation requires both the Claude `claude -p` runner and Codex `codex exec --ephemeral`
  runner to pass discovery, isolation, and harmless smoke tests and then pass the Skill's
  required cases. Antigravity is outside the behavioral attestation in the first version.
  Claude description optimization uses `claude -p` only when explicitly requested for the
  Claude target and proposes, rather than silently applies, the winning description.
- Claude and Codex evaluation scores are calculated independently and cannot offset each
  other. When exactly one platform reaches its required threshold, the evaluation is marked
  as requiring human review rather than receiving an automatic pass. A completed platform
  suite is not automatically retried to seek a better score; any later rerun is a new,
  explicitly authorized evaluation so nondeterministic retries cannot consume tokens merely
  to obtain a favorable result.
- Automated evaluation requires Python 3.10 or later. MySkills never installs or upgrades
  Python; missing or incompatible Python blocks `skill-evaluator` from being copied because it
  cannot produce the required automated attestation.
- With compatible Python, the installer creates
  `%LOCALAPPDATA%\MySkills\venvs\skill-evaluator` and installs pinned PyYAML 6.0.3 there. Python
  detection prefers a compatible runtime reported by the official Python Install Manager,
  then tries the legacy `py` launcher and `python`, executing the exact candidate to verify
  version and architecture. The user's global Python environment is never modified.
- The evaluator dependency manifest declares Python 3.10 or later as its only Runtime
  Prerequisite and PyYAML 6.0.3 as its only Python Installable Dependency. Installation uses
  the selected interpreter's `-m venv` and the private environment's `python -m pip` with a
  repository-owned hash-locked requirements file covering supported Windows Python builds.
  MySkills builds a replacement environment separately, runs all core smoke tests, and swaps
  it into place only after success; a failed install or update leaves the last working
  evaluator environment intact.
- Claude and Codex CLIs are required evaluation targets, not packages secretly installed by
  `skill-evaluator`. If either executable is absent, `skill-evaluator` is not installed.
  Installer preflight does not infer or gate runner support by Agent version; each real
  evaluation proves the required Claude and Codex commands and fails without an attestation
  when either cannot run. The offline report requires no Node.js package, CDN asset, local web
  server, or additional browser installation.
- Source helpers are reduced to validation, result aggregation, target runners,
  description testing, and static report generation. `package_skill.py`, general creator
  teaching, and Claude/Cowork-only presentation instructions are removed. Pipe reading is
  ported from `select.select` to a Windows-compatible reader thread and queue; the viewer uses
  packaged CSS/system fonts and no CDN or local web server.
- Installer smoke tests import PyYAML, validate a fixture Skill, aggregate fixture benchmark
  data, generate the static HTML report, and validate Claude/Codex command construction without
  spending model tokens. A core failure blocks evaluator installation; actual isolated
  discovery and trigger behavior is proven by each evaluation run.

### Foundational Wiki contract

- `llm-wiki` is retained as the concise theory and routing Skill for the shared Wiki model. It
  does not write the vault, initialize it, or duplicate operational workflows; setup routes to
  `wiki-setup` and source ingestion routes to `wiki-ingest`.
- Its source 609-line monolith is split into directly routed references for architecture,
  page schema, provenance/lifecycle, typed relationships, retrieval, and configuration.
  Operational Skills load only the specific contract they require rather than the complete
  foundation on every invocation.
- Deterministic schema, path, and configuration validation live in the managed
  `obsidian-wiki` CLI. Staged writes, named-vault/`@name` behavior, former repository paths,
  and the excluded policy system are removed from the contract.
- `llm-wiki` itself invokes no third-party package, but it follows the accepted Wiki-suite
  installation gate: it is copied only when Python and the operational CLI/helper smoke tests
  for all 20 managed Wiki Skills pass.

### `obsidian-wiki` CLI

- The legacy LLM Wiki repository's `obsidian_wiki` Python package is imported into MySkills as
  the repository-owned `obsidian-wiki` CLI. It is not a Skill, is not updated from PyPI, and
  no runtime reference to the former repository remains.
- `wiki-ingest`, `wiki-lint`, `wiki-query`, `wiki-setup`, `wiki-status`, and `wiki-update` may
  invoke the CLI commands that already exist in the source implementation. This does not move
  their other Python helpers or AI-driven behavior into the CLI, and a desired command that
  does not exist is not treated as an available capability.
- It requires Python 3.10 or later and is installed into
  `%LOCALAPPDATA%\MySkills\venvs\obsidian-wiki`. MySkills does not install or upgrade Python
  and does not persistently modify `PATH`.
- Managed Wiki Skills invoke the explicit MySkills-managed launcher rather than assuming that
  `obsidian-wiki` is globally discoverable. The installed tool source and launcher are
  versioned and hashed as part of the MySkills desired state.
- The CLI does not retain the former repository's independent CalVer. Its human-readable
  version is `myskills-<MySkills-version>+<content-hash-prefix>`, while installer drift
  detection compares the full SHA-256. The CLI is released and updated only with MySkills.
- The stable Windows launcher is
  `%LOCALAPPDATA%\MySkills\bin\obsidian-wiki.cmd`. It delegates to
  `%LOCALAPPDATA%\MySkills\venvs\obsidian-wiki\Scripts\python.exe` and the installed
  repository-owned CLI source. The six Skills resolve this absolute launcher through
  a shared PowerShell helper; they do not invoke a bare `obsidian-wiki` command.
- Installer verification executes the launcher itself, including its version and doctor
  probes, so the presence of files alone is not treated as a working installation.
- A globally installed or editable `obsidian-wiki` package that predates MySkills remains
  `preexisting`. After the private launcher verifies successfully, the installer reports the
  old executable, its source, and a manual uninstall command, but neither interactive install
  nor `-Yes` removes it. Managed Skills always use the private launcher's absolute path.
- The initial `obsidian-wiki` CLI uses only Python's standard library. Optional upstream
  enhancements such as `tree-sitter`, `tree-sitter-languages`, `leidenalg`, and `igraph` are
  not installed; their existing pure-Python fallbacks remain active.
- The imported CLI retains Wiki configuration, query, doctor, lint, cache, batching, AST,
  graph, and trust commands. The excluded central policy subsystem and its `rules` commands
  are not imported. Its `setup` command initializes Wiki and vault state but
  no longer installs Skills. Legacy `install-skills` and `update-skills` commands are removed;
  `scripts\install.ps1` is the only Skill installation and update entry point.
- The first version does not add history-ingest, manifest-normalize/delta, provenance-set, or
  synthesis-specific commands to the CLI. Existing standalone helpers remain callable from
  their MySkills-owned locations and are removed only after a separately approved,
  fixture-proven replacement.
- Python 3.10 or later and successful CLI/helper smoke tests are a suite-level installation
  gate for all 20 Managed Skills in the `wiki` category. If the gate fails, none of those
  Skills is copied; the installer reports the exact failing prerequisite and leaves unrelated
  categories eligible.

### Wiki setup

- `wiki-setup` is retained as an explicit, human-only workflow for creating a new vault,
  connecting an existing synchronized vault on another computer, or repairing missing Wiki
  structure. It configures Wiki state; it does not install Skills or third-party programs.
- On an installer run with no resolved Wiki configuration, `scripts\install.ps1` may offer to
  launch this setup flow. Declining does not block Skill installation. Per-computer
  configuration is stored at `%USERPROFILE%\.obsidian-wiki\config`.
- The initial version supports one configured vault and excludes `wiki-switch`. Imported Wiki
  Skills remove named-profile and inline `@name` routing; multiple projects remain namespaces
  inside the one vault. A future multi-vault design must use an explicit Windows-compatible
  profile registry rather than symbolic links.
- The Windows workflow delegates deterministic initialization and validation to the managed
  `obsidian-wiki` CLI. It removes staged-write directories and configuration, the Claude Stop
  hook, Bash commands, and generic community-plugin recommendations from the source workflow.
- Existing vault and `.obsidian` content is preserved. Setup creates missing safe defaults,
  reports incompatible existing values, and requires an explicit user decision before
  replacing any configuration. QMD collections may be configured, but QMD installation and
  version management remain owned by `scripts\install.ps1`.

### Excluded central project policy system

- The standalone `ai-policy-sync` Skill, central Wiki policy records, `.ai-policy` pack/lock
  artifacts, global agent bootstrap, Codex policy hook, and corresponding
  `obsidian-wiki rules` commands are excluded.
- Project rules and architecture baselines are owned by the target project through the
  local-only `project-rules-init` workflow described under the engineering workflow. This
  supersedes the earlier diagnostic-absorption design.

### Wiki lint migration

- `wiki-lint` remains the user-facing Wiki health-check Skill, but its installed `SKILL.md` is
  reduced to config resolution, CLI invocation, result interpretation, repair authorization,
  and conditional pointers for semantic checks. Concision changes context loading, not
  supported behavior.
- Migration requires parity with every current check: orphaned pages, broken wikilinks,
  missing frontmatter, missing summaries, stale content, contradictions, index consistency,
  provenance drift, fragmented tag clusters, visibility-tag consistency, misc promotion
  candidates, lifecycle and confidence schema, supersession and confidence-review integrity,
  typed relationships, and synthesis gaps. Scope exclusions for archives, raw material,
  readouts, and Obsidian configuration are also preserved.
- Default lint remains report-only. Consolidation preserves dry-run preview and explicit
  confirmation before writes, then supports broken-link repair, orphan cross-references,
  lifecycle correction, tier demotion, tag normalization, contradiction callouts, the
  consolidation report, activity logging, and QMD refresh after vault writes.
- Existing deterministic CLI checks are reused unchanged. Checks and repairs that are not
  already implemented by the CLI remain in their original Skill workflow or imported helper;
  semantic checks remain in directly linked references loaded only for those findings. No
  behavior is dropped merely to centralize implementation.
- The verbose source workflow is not retired until fixture vaults cover every check and repair
  class, report-only runs prove no writes, consolidation authorization is tested, and
  before/after reports demonstrate equivalent classifications and outcomes.

### Wiki deduplication

- `wiki-dedup` is retained as the semantic identity-resolution workflow distinct from the
  broad structural health checks in `wiki-lint`.
- Invoking it without arguments resolves the current vault and performs a vault-wide,
  read-only audit. It first searches titles, aliases, tags, categories, and summaries, then
  reads full bodies only for candidate pairs. It reports candidates and confidence without
  changing files or refreshing QMD.
- The user may instead name two pages for focused analysis. Before any merge, the workflow
  presents whether the pages represent one concept, the proposed canonical page, content to
  preserve, redirect behavior, and links requiring updates.
- The source modes and their authorization boundaries are preserved: the default audit is
  read-only; `--merge` presents and confirms each candidate pair; and an explicitly requested
  `--auto` mode merges only high-confidence pairs at the source threshold without per-pair
  prompts. Uncertain pairs remain unmerged and are reported.
- A merge preserves content and provenance, writes the redirect stub, updates vault links and
  tracking state, and finishes with Wiki health validation.
- Its installed `SKILL.md` remains concise, while candidate scoring and merge details use the
  repository-owned CLI or conditional references. The shorter entry point must preserve the
  current detection, report, merge, redirect, link-rewrite, logging, and post-write QMD
  behavior, verified with duplicate and non-duplicate fixture pairs.

### Wiki cross-linking

- `cross-linker` retains its original automatic write behavior. It scans for missing
  cross-references, scores candidates, applies the source workflow's actionable confidence
  classes, updates typed relationships and Wiki tracking artifacts, refreshes QMD after
  writes, and reports what changed.
- MySkills does not add a confirmation prompt to each link. Candidates outside the source
  workflow's actionable confidence classes remain skipped or reported according to the
  original behavior.

### Wiki tag taxonomy

- `tag-taxonomy` is retained as the owner of the vault's canonical tag vocabulary, distinct
  from the broad issue reporting performed by `wiki-lint`.
- Its four source modes remain intact: read-only tag audit, normalization, canonical tagging
  of a new page, and addition of a new canonical tag. Known aliases are normalized
  automatically; unknown tags retain the source-required user decision before replacement or
  taxonomy expansion.
- The concise entry point preserves canonical and reserved-tag rules, page tag limits,
  taxonomy updates, activity logging, `hot.md` maintenance, and QMD refresh after writes.
  Fixture coverage includes canonical tags, aliases, unknowns, over-tagged and untagged pages,
  and reserved visibility tags.

### Wiki status and insights

- `wiki-status` is retained with both source modes. Status/delta reports ingest coverage,
  source changes, pending staging and raw work, visibility, token footprint, health signals,
  and ranked next actions without modifying formal Wiki pages.
- Insights mode retains graph analysis for hubs, bridges, tag-cluster cohesion, surprising
  connections, dead ends, graph delta, tier suggestions, and questions worth asking. Its only
  writes are the regenerable `_insights.md` artifact and activity log defined by the source
  workflow.
- The concise Skill delegates deterministic source comparison and graph analysis to the
  repository-owned CLI and loads mode-specific presentation rules only when needed. It does
  not change the source read/write boundaries, small-vault skip behavior, manifest fallbacks,
  or report content.

### Wiki post-write maintenance

- A successful Managed Wiki write is self-contained and does not require a subsequent
  `daily-update` run. Each mutating Skill preserves its applicable source behavior for
  reconciling `index.md`, updating `hot.md` and `log.md`, recording source-backed ingest state
  in `.manifest.json`, and refreshing QMD after vault Markdown changes.
- Import validation inventories every mutating Wiki Skill and tests its declared post-write
  effects. A missing applicable index, activity, manifest, or QMD update is fixed in that
  owning Skill or the shared CLI rather than delegated to a catch-all maintenance Skill.
- Direct manual vault edits remain visible through `wiki-status` and `wiki-lint`; MySkills
  does not run a background watcher, scheduled repair, or automatic knowledge ingest.

### General Wiki ingest

- `wiki-ingest` is retained as the catch-all workflow that distills documents, structured and
  conversational data, folders, images, URLs, and `_raw/` drafts into integrated Wiki pages.
  Source content remains untrusted data and can never supply executable agent instructions.
- The MySkills version removes all staged-write and `wiki-stage-commit` branches. Successful
  writes go directly to the configured vault and preserve deduplication, provenance,
  relationships, asset safety, manifest/index/log/hot maintenance, and optional QMD refresh.
- URL ingest does not depend on the excluded Defuddle CLI. It uses an agent's native web
  retrieval capability when available; otherwise it asks the user to save the source locally
  and ingests that file.
- PageIndex, PyMuPDF, Poppler, and other unmanaged optional source-repository tools are not
  dependencies of the initial MySkills version. PDF and image handling uses the active
  agent's native document and vision capabilities and reports unsupported content explicitly.
  The MySkills-managed `obsidian-wiki` CLI remains the deterministic helper, and QMD remains
  optional.
- The concise `SKILL.md` retains modes, trust boundary, write contract, and failure behavior.
  Format-specific reading, long-document, asset, and academic-paper procedures move to
  directly routed references or Windows-compatible helpers.

### Autonomous Wiki research

- `wiki-research` is retained as an explicit, human-only workflow that performs bounded
  multi-round web research and writes sourced reference, concept, entity, and synthesis pages
  into the Wiki. A general request to research a topic does not imply permission to write the
  vault; the user must name `wiki-research` or explicitly request that results be filed there.
- Research uses the active agent's native network search and retrieval tools, prioritizes
  primary and authoritative sources, and does not depend on the excluded Defuddle CLI. If the
  active agent lacks suitable network access, the workflow stops and directs the user to
  provide sources to `wiki-ingest`.
- The Skill preserves its bounded-round halt condition, contradiction and gap reporting,
  source provenance, Wiki tracking maintenance, and optional QMD refresh. Search recipes and
  filing templates move to directly routed references so the installed `SKILL.md` remains
  concise.

### Agent history ingest

- `wiki-history-ingest` is the sole installed history-ingest Skill. The source candidates
  `claude-history-ingest` and `codex-history-ingest` are not installed independently; their
  format-specific behavior is preserved in directly routed source-workflow references rather
  than merged into one parser. `copilot-history-ingest`,
  `hermes-history-ingest`, `openclaw-history-ingest`, and `pi-history-ingest` and their source
  adapters are excluded because those CLIs are not in the user's supported tool set.
- The supported sources are Claude, Codex, and Antigravity. Common append/full selection,
  privacy filtering, topic clustering, knowledge distillation, Wiki tracking maintenance, and
  optional QMD refresh are stated once only where the source behaviors are equivalent. The
  entry point routes to one source workflow, which retains that source's discovery, validation,
  extraction, sampling, and fallback behavior.
- Claude defaults to `%USERPROFILE%\.claude`; Codex defaults to
  `%USERPROFILE%\.codex`; Antigravity defaults to
  `%USERPROFILE%\.gemini\antigravity-cli`. Per-computer overrides
  `CLAUDE_HISTORY_PATH`, `CODEX_HISTORY_PATH`, and `ANTIGRAVITY_HISTORY_PATH` live in the local
  Wiki configuration.
- The Antigravity adapter indexes conversations through `conversation_summaries.db` and reads
  validated `brain\<conversation-id>\.system_generated\logs\transcript.jsonl` records. The
  initial adapter does not parse the internal `.pb`/per-conversation `.db` files or rely on
  the observed format-unstable `history.jsonl`. SQLite access uses Python's standard library.
  Its new helper remains isolated under `wiki-history-ingest/scripts/antigravity/`; it is not
  added to `obsidian-wiki` CLI. Because this is an internal Antigravity format, table and JSONL
  field validation must fail safely when an Antigravity update changes the source shape.
- The Claude workflow retains the imported
  `wiki-history-ingest/scripts/claude/extract-jsonl.py` optimization and its raw-JSONL fallback.
  The Codex workflow retains direct Agent parsing of its session index and rollout JSONL and
  receives no new Python parser in the first version.
- The standalone `wiki-agent` Skill remains excluded. `wiki-history-ingest` retains its
  targeted mode: the user may name one supported agent and a topic, and the workflow selects
  relevant sessions, extracts only useful context, writes or updates durable Wiki pages,
  maintains tracking artifacts, and returns an immediately usable synthesis.
- Agent-specific natural-language invocation remains supported without separate Skill or
  slash-command implementations. Platform history paths and extraction live in directly
  routed references and Windows-compatible helpers rather than the concise `SKILL.md`.

### Conversation capture

- `wiki-capture` is retained as a manually invoked workflow for distilling the current
  conversation into durable Wiki knowledge. Full mode writes a classified page and maintains
  the applicable Wiki tracking artifacts; quick mode stages a bounded draft under `_raw/` for
  later promotion by `wiki-ingest`.
- MySkills does not import, port, or install the source repository's Claude Code Stop hook.
  No installer action modifies global agent hook configuration, and ending an agent response
  never triggers conversation capture automatically.
- Users invoke capture directly with intent such as "save this conversation to the Wiki" or
  explicitly request quick staging. This preserves the useful capture modes without hidden
  follow-up turns, additional token use, or platform-specific Bash, Python, and `awk`
  dependencies.

### Bounded Wiki context

- `wiki-context-pack` is retained as the reusable, token-bounded retrieval workflow for
  downstream agents and tasks. It is distinct from `wiki-query`, which answers a question,
  and from `ai-handoff`, which communicates task state and instructions.
- QMD may contribute semantic search candidates when available, but the Skill remains
  responsible for relevance and tier ordering, overlap reduction, budget enforcement, source
  identity, and a structured Markdown context-pack contract. Missing QMD falls back to the
  vault index and frontmatter.
- The installed `SKILL.md` contains only invocation, budget, read/write boundary, and output
  requirements. Deterministic ranking, compression, and size accounting move to a
  Windows-compatible helper or directly referenced specification without changing the
  source workflow's results or activity logging.

### Wiki answers and presentation

- The standalone `wiki-narrate` Skill and its `_readouts/` derived-output feature are
  excluded. `wiki-query` handles evidence-bounded answers and accepts natural-language
  requests for briefing, plain-language, or progressive-teaching presentation without
  creating a separate persisted artifact.
- `wiki-query` remains the primary read-only Wiki question-answering workflow. It uses the
  MySkills-managed `obsidian-wiki` CLI and optional QMD to select evidence, preserves
  citations, lifecycle/freshness warnings, typed-edge traversal, gaps, and its single
  permitted query-log append, and never modifies formal knowledge pages.
- Human-facing answers follow the MySkills Chinese response policy. The concise `SKILL.md`
  retains the read-only boundary, retrieval escalation, evidence, and answer contracts;
  deterministic ranking and graph traversal live in the CLI or directly routed references.

### Wiki source provenance comparison

- `memory-bridge` is retained with Browse, Search, Diff, and Map modes over source provenance
  recorded in `.manifest.json`. It removes the excluded `impl-validator` call and retains its
  direct manifest-based source maps, sets, intersections, and differences; the first version
  does not add a provenance-comparison command to the CLI.
- Reports describe source contribution coverage rather than claiming that an AI tool can or
  cannot know a shared Wiki page. All configured agents may read the same Wiki; labels such as
  "only from Codex sources" mean only that Codex-originated inputs are recorded as creating or
  updating the page.
- The concise Skill preserves source-type mappings, bounded reads, counts, notable-asymmetry
  reporting, link-format handling, missing-manifest guidance, and the source workflow's
  activity log behavior.

### Wiki synthesis

- `wiki-synthesize` is retained as an explicit, human-only write workflow that discovers
  unsupported synthesis gaps through co-occurrence and graph evidence, creates bounded
  cross-cutting synthesis pages, and adds source-page backlinks.
- Once explicitly invoked, it preserves the source workflow's automatic creation of the
  highest-value candidates without adding per-page confirmation. Inferences, ambiguity,
  strongest objections, skipped candidates, tracking-file maintenance, and optional QMD
  refresh remain part of the output contract.
- The workflow may use the CLI's existing `graph-analyse` output and optional QMD as evidence,
  but candidate discovery, scoring, and semantic judgment retain the source Skill behavior.
  The first version adds no synthesis-specific CLI command or third-party dependency.

### Project-to-Wiki synchronization

- `wiki-update` is retained as the cross-project workflow that distills durable architecture,
  decisions, abstractions, and reusable lessons from the current source project into the
  configured Wiki. It runs only when the user explicitly asks to update or sync the Wiki.
- Source-project delta detection prefers local Git history when available; the remote host may
  be GitHub, Bitbucket, another provider, or absent. Projects without Git use deterministic
  managed-file SHA-256 snapshots through the `obsidian-wiki` CLI. Git hosting APIs and issue
  trackers are not dependencies.
- The destination Wiki keeps its existing Git/GitHub version control, but `wiki-update` only
  changes Wiki files and tracking artifacts. It never commits or pushes unless the user makes
  a separate explicit request.
- Stable project identity and shared synchronization data live in the vault manifest.
  Computer-specific absolute source paths are resolved from
  `%USERPROFILE%\.obsidian-wiki\config` so different computers do not overwrite one another's
  local paths.
- The concise Skill preserves project/global classification, merge and cross-link behavior,
  provenance, manifest/index/log/hot maintenance, and optional QMD refresh. Deterministic
  scanning, exclusions, Git ancestry checks, and hash fallback use existing CLI commands or
  retained imported helpers only where those capabilities already exist; the first version
  does not rewrite them solely for consolidation.

### Wiki archive, rebuild, and restore

- `wiki-rebuild` is retained with its Archive Only, Archive + Rebuild, and Restore modes and
  the source workflow's confirmation boundaries.
- Every destructive clear or restore first creates a timestamped archive of the current live
  Wiki and verifies its inventory and digest before changing live content. Existing archives
  are never removed automatically, and `.obsidian\` is never included in a destructive target.
- Archive + Rebuild clears only the validated live Wiki targets and does not automatically
  re-ingest sources. Restore first archives the current state, restores the selected archive,
  records the operation, refreshes QMD when configured, and recommends a health check.
- Fragile archive, validation, clear, and restore mechanics belong in a deterministic
  repository-owned PowerShell or CLI implementation. The concise Skill selects the mode,
  obtains the source-required confirmation, invokes the operation, and reports evidence.

### Wiki dashboards

- `wiki-dashboard` is retained to create and modify persistent, dynamically evaluated
  Obsidian dashboard views. A created dashboard does not require repeated Skill execution;
  Obsidian Bases or Dataview reevaluates it when viewed.
- Obsidian Bases is the default because it is native to supported Obsidian versions. Dataview
  is an optional capability used only when requested or when the required grouping or computed
  query cannot be expressed suitably with Bases.
- Missing Dataview does not block `wiki-dashboard` installation: Bases is its complete primary
  workflow. MySkills assigns Dataview no minimum version and does not create a Dataview query
  unless the current vault has the plugin installed and enabled.
- The currently detected Dataview installation is `preexisting`; MySkills does not install,
  update, or remove Obsidian community plugins. On another vault without Dataview, the Skill
  uses Bases when possible or provides the in-app Community Plugins installation path and
  asks the user to rerun the Dataview-specific request.
- The concise entry point preserves `.base` and Markdown dashboard output locations, the
  source-required confirmation before modifying an existing note, embedding guidance,
  activity logging, and post-write QMD behavior. Bases and Dataview schema and recipe details
  move to separate conditional references.

### Obsidian graph coloring

- `graph-colorize` is retained with its by-tag, by-category, by-visibility, combined, custom,
  clear, and restore behaviors.
- The concise Skill chooses the mode and surfaces the source warning about Obsidian
  overwriting an open vault's graph settings. A deterministic PowerShell script inventories
  tags or categories, builds color groups, backs up the current file, replaces only
  `colorGroups`, preserves JSON style and all unrelated settings, verifies the result, and
  records the operation.
- It requires no third-party CLI. Source fallback, palette, stable category ordering,
  visibility precedence, manual-color handling, backup reuse, undo, and missing `.obsidian`
  behavior remain covered by fixtures.

### Obsidian CLI

- The official Obsidian CLI is a required Runtime Prerequisite only for the managed
  `obsidian-cli` Skill. `json-canvas`, `obsidian-bases`, and `obsidian-markdown` describe file
  formats and do not require the executable.
- Obsidian Desktop 1.12.7 or later is the documented source of the official CLI, but MySkills
  does not parse or compare the Desktop version. Installation eligibility is determined by
  resolving the registered command and successfully running `obsidian help`.
- MySkills does not install Obsidian Desktop, enable its **Command line interface** setting, or
  modify the user's persistent `PATH`. When the prerequisite is unavailable, it reports the
  official download, enablement, and terminal-restart instructions, blocks only
  `obsidian-cli`, and tells the user to rerun installation afterward.
- Verification may launch Obsidian because the official CLI communicates with the running
  desktop application.

## Installation safety and outcomes

- Desired state lives in the version-controlled MySkills manifests. Observed machine-specific
  installation state lives outside the repository at
  `%LOCALAPPDATA%\MySkills\state.json`.
- Machine state records installed Skill targets and hashes, dependency versions and paths,
  dependency ownership, verification results, and the last successful operation needed to
  detect drift. It must not contain credentials or other secrets.
- `state.json` is never committed or copied between computers. If it is missing or invalid,
  MySkills reconstructs observable state through read-only detection; ownership that cannot be
  proven is conservatively classified as `preexisting`.
- For each Skill target, MySkills computes a deterministic SHA-256 digest over relative file
  paths and file contents. Timestamps and other filesystem metadata do not affect the digest.
- `source_hash` is computed from the canonical repository directory, `recorded_hash` is the
  last successfully installed digest in machine state, and `actual_hash` is computed from the
  current target directory.
- `actual_hash == recorded_hash == source_hash` is `CURRENT`;
  `actual_hash == recorded_hash != source_hash` is `UPDATE_AVAILABLE`;
  `actual_hash != recorded_hash` is `DRIFTED`; an absent target is `MISSING`; and a present
  target without ownership state is `UNOWNED`.
- `install`, `status`, `verify`, and `uninstall` perform this detection. MySkills runs no
  background watcher or service, and no AI agent participates in ownership or drift decisions.
- A `DRIFTED` target is never automatically overwritten or removed. It requires an explicit
  diff review and backup-and-replace action, and `-Yes` cannot bypass that protection.
- If machine state is lost, an exact target/source match may be explicitly adopted; a
  nonmatching target remains unowned until an explicit backup-and-replace action.
- Backup-and-replace applies only after explicit approval for a `DRIFTED` or differing
  `UNOWNED` target; normal installation and clean updates create no backup.
- Before replacement, MySkills copies the complete existing Skill directory to
  `%LOCALAPPDATA%\MySkills\backups\<timestamp>\<platform>\<skill-name>` and verifies its
  digest. Replacement begins only after that verification succeeds.
- Backup metadata is recorded in machine state and backups are never committed to the
  repository. The initial implementation does not delete backups automatically; cleanup is a
  separate explicit operation.
- Installation is atomic per Managed Skill within each eligible platform target. An absent
  target Agent receives no copy and does not prevent installation to other eligible targets.
- MySkills validates and, when authorized, installs all required dependencies before copying
  any platform copy. If a required dependency remains unavailable, that Skill is copied to no
  target, while unrelated Skills in the batch continue.
- Every installation verifies copied file integrity against the Managed Skill source.
- MySkills copies a Skill to Claude or Codex after preflight confirms that the target
  executable exists, then verifies after copying that the CLI discovers the installed Skill.
  Antigravity follows the explicitly lower compatibility-copy policy: its CLI/version and
  target path must be validated, and copied hashes must match, but model behavior is not a
  release gate.
- An absent or unverifiable target CLI receives no Skill files and is reported as
  `SKIPPED_NOT_INSTALLED` or `BLOCKED` with installation or repair guidance. Other verified
  platform targets remain eligible and do not receive an `UNVERIFIED` copy.
- When a verified CLI cannot discover a copied Skill, that platform installation is rolled
  back, the result is `BLOCKED`, the overall result is `INCOMPLETE`, and the command returns a
  nonzero exit code.
- An existing same-name target not recorded as MySkills-managed is never overwritten.
- Identical unowned installations may be explicitly adopted.
- Different unowned installations require comparison and an explicit backup-and-replace action.
- `-Yes` does not bypass an unowned same-name conflict.
- Batch operations continue independent installations after an item is blocked.
- Any blocked requested item makes the final result `INCOMPLETE` and returns a nonzero exit code.
- Summaries must visibly report requested, installed, skipped, and blocked counts plus next
  actions for every blocked item.
- Important governance rules must be enforced through manifests, CLI guards, validators, or
  automated tests whenever they are mechanically checkable.

## Managed renames

- The Matt source candidate `ask-matt` is imported as `ask-myskills`. Its routing content is
  rewritten to include only Managed Skills and to remove assumptions about
  `setup-matt-pocock-skills`, issue trackers, and excluded workflows. Lightweight
  specification routes to `to-spec`, formal or resumable specification routes to
  `spec-package-generator`, and cross-session requests route to `ai-handoff` or
  `session-checkpoint` according to whether delivery is intended.
- The LLM Wiki source candidate `skill-creator` is transformed into `skill-evaluator`.
  Provenance records the source name, while creator guidance and packaging are removed and
  internal references are updated to the evaluator's narrower responsibility.

## Open decisions

No open decisions remain for the first-stage consolidation design.
