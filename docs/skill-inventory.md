# Skill Inventory

Discovery snapshot for the first-stage MySkills consolidation interview. Duplicate
installations are listed once by skill name. The sections below currently group discovery
by Skill Origin; they do not determine the eventual functional Skill Category. All entries
remain Candidate Skills unless explicitly marked otherwise.

Current decisions classify 42 candidates as Managed Skills and 50 as excluded, with no
deferred or pending candidates.

The authoritative source for the LLM Wiki suite is
`C:\project\LLM Wiki\obsidian-wiki\.skills` at repository
`https://github.com/a0912129960/obsidian-wiki.git`. At discovery commit
`1260c9f4aadfe5a216b109288cfb94f936719b8b`, all corresponding copies under
`.agents`, `.claude`, and `.codex` have identical full-directory hashes.

## Origin summary

| Category | Count |
| --- | ---: |
| MySkills | 1 |
| Spec Package Generator | 1 |
| Matt / engineering | 17 |
| Matt / productivity | 5 |
| Matt / personal | 2 |
| Matt / misc | 4 |
| Matt / in-progress | 9 |
| Matt / deprecated | 4 |
| Installed / LLM Wiki suite | 36 |
| Installed / standalone | 6 |
| LLM Wiki / Obsidian third-party | 5 |
| LLM Wiki / QMD bundled | 2 |
| **Total** | **92** |

## Proposed MySkills classification

Matt and standalone candidates use functional categories. The LLM Wiki source suites preserve
their original package boundaries: `obsidian-wiki/.skills` maps to `wiki`,
`obsidian-skills/skills` maps to `obsidian`, and `qmd/skills/qmd` maps to `qmd`.

### Engineering (32)

- `code-review-expert`
- `karpathy-guidelines`
- `mermaid-diagram-renderer`
- `spec-package-generator`
- Matt engineering: `ask-matt`, `codebase-design`, `code-review`, `diagnosing-bugs`,
  `domain-modeling`, `grill-with-docs`, `implement`, `improve-codebase-architecture`,
  `prototype`, `research`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `tdd`,
  `to-spec`, `to-tickets`, `triage`, `wayfinder`
- Former Matt misc: `git-guardrails-claude-code`, `migrate-to-shoehorn`,
  `scaffold-exercises`, `setup-pre-commit`
- Former Matt in-progress: `setup-ts-deep-modules`
- Former Matt deprecated: `design-an-interface`, `qa`, `request-refactor-plan`,
  `ubiquitous-language`
- QMD project workflow: `release`
- Transformed LLM Wiki source: `skill-evaluator` — reworked from source candidate
  `skill-creator`

#### Engineering management decisions

Explicitly managed:

- `ask-myskills` — imported and rewritten from source candidate `ask-matt`
- `codebase-design`
- `code-review`
- `diagnosing-bugs`
- `domain-modeling`
- `grill-with-docs`
- `implement`
- `improve-codebase-architecture`
- `prototype`
- `tdd`
- `to-spec`
- `spec-package-generator`
- `skill-evaluator`

Explicitly excluded:

- `code-review-expert`
- `karpathy-guidelines`
- `setup-pre-commit`
- `setup-ts-deep-modules`
- `migrate-to-shoehorn`
- `scaffold-exercises`
- `design-an-interface`
- `qa`
- `request-refactor-plan`
- `ubiquitous-language`
- `release`
- `mermaid-diagram-renderer`
- `setup-matt-pocock-skills`
- `triage`
- `to-tickets`
- `wayfinder`
- `research`
- `resolving-merge-conflicts`
- `git-guardrails-claude-code`

### Productivity (15)

- `ai-handoff`
- Matt productivity: `grilling`, `grill-me`, `handoff`, `teach`, `writing-great-skills`
- Former Matt personal: `edit-article`
- Former Matt in-progress: `batch-grill-me`, `claude-handoff`, `loop-me`,
  `to-questionnaire`, `wizard`, `writing-beats`, `writing-fragments`, `writing-shape`

#### Productivity management decisions

Explicitly managed:

- `ai-handoff`
- `grilling`
- `grill-me`
- `session-checkpoint` — imported from source candidate `handoff`

Explicitly excluded:

- `batch-grill-me`
- `claude-handoff`
- `loop-me`
- `wizard`
- `writing-beats`
- `writing-fragments`
- `writing-shape`
- `teach`
- `writing-great-skills`
- `edit-article`
- `to-questionnaire`

### Wiki (38)

- `ai-policy-sync`
- `impl-validator`
- `project-rules-init`
- `graph-colorize`
- `obsidian-layout-adjustment`
- History ingestion: `claude-history-ingest`, `codex-history-ingest`,
  `copilot-history-ingest`, `hermes-history-ingest`, `openclaw-history-ingest`,
  `pi-history-ingest`, `wiki-history-ingest`
- `cross-linker`
- `daily-update`
- `llm-wiki`
- `memory-bridge`
- `tag-taxonomy`
- `vault-skill-factory`
- `wiki-agent`
- `wiki-capture`
- `wiki-context-pack`
- `wiki-dashboard`
- `wiki-dedup`
- `wiki-digest`
- `wiki-export`
- `wiki-import`
- `wiki-ingest`
- `wiki-lint`
- `wiki-narrate`
- `wiki-query`
- `wiki-rebuild`
- `wiki-research`
- `wiki-setup`
- `wiki-stage-commit`
- `wiki-status`
- `wiki-switch`
- `wiki-synthesize`
- `wiki-update`

#### Wiki management decisions

Explicitly managed:

- `project-rules-init`

Explicitly excluded:

- `impl-validator`
- `daily-update`
- `wiki-stage-commit`
- `obsidian-layout-adjustment`
- `vault-skill-factory`
- `wiki-agent`
- `wiki-digest`
- `wiki-export`
- `wiki-import`
- `wiki-narrate`
- `wiki-switch`
- `claude-history-ingest` (source adapter absorbed into `wiki-history-ingest`)
- `codex-history-ingest` (source adapter absorbed into `wiki-history-ingest`)
- `copilot-history-ingest`
- `hermes-history-ingest`
- `openclaw-history-ingest`
- `pi-history-ingest`
- `ai-policy-sync`

All remaining Wiki candidates are explicitly managed, for a total of 20 Managed Skills in the
`wiki` category.

### Obsidian (6)

- `defuddle`
- `json-canvas`
- `obsidian-bases`
- `obsidian-cli`
- `obsidian-markdown`
- `obsidian-vault`

#### Obsidian management decisions

Explicitly managed:

- `json-canvas`
- `obsidian-bases`
- `obsidian-cli` — requires a working official Obsidian CLI; MySkills verifies it with
  `obsidian help` but does not install or register it. Obsidian Desktop 1.12.7+ is installation
  guidance, not a separately compared version gate
- `obsidian-markdown`

The other three managed Obsidian Skills operate on Obsidian file formats and do not require
the Obsidian CLI.

Explicitly excluded:

- `defuddle`
- `obsidian-vault`

### QMD (1)

- `qmd`

#### QMD management decision

- `qmd` is explicitly managed.

### Personal (0)

No current Candidate Skill requires this category under the proposed functional
classification. The category remains available for future private workflows.

## Origin: MySkills

- `ai-handoff` — proposed Skill Category: `productivity`

## Origin: Spec Package Generator

- `spec-package-generator`

## Origin: Matt / engineering

- `ask-matt`
- `codebase-design`
- `code-review`
- `diagnosing-bugs`
- `domain-modeling`
- `grill-with-docs`
- `implement`
- `improve-codebase-architecture`
- `prototype`
- `research`
- `resolving-merge-conflicts`
- `setup-matt-pocock-skills`
- `tdd`
- `to-spec`
- `to-tickets`
- `triage`
- `wayfinder`

## Origin: Matt / productivity

- `grilling`
- `grill-me`
- `session-checkpoint` — imported from source candidate `handoff`
- `teach`
- `writing-great-skills`

## Origin: Matt / personal

- `edit-article`
- `obsidian-vault`

## Origin: Matt / misc

- `git-guardrails-claude-code`
- `migrate-to-shoehorn`
- `scaffold-exercises`
- `setup-pre-commit`

## Origin: Matt / in-progress

- `batch-grill-me`
- `claude-handoff`
- `loop-me`
- `setup-ts-deep-modules`
- `to-questionnaire`
- `wizard`
- `writing-beats`
- `writing-fragments`
- `writing-shape`

## Origin: Matt / deprecated

- `design-an-interface`
- `qa`
- `request-refactor-plan`
- `ubiquitous-language`

## Origin: LLM Wiki / obsidian-wiki

- `ai-policy-sync`
- `claude-history-ingest`
- `codex-history-ingest`
- `copilot-history-ingest`
- `cross-linker`
- `daily-update`
- `graph-colorize`
- `hermes-history-ingest`
- `llm-wiki`
- `memory-bridge`
- `obsidian-layout-adjustment`
- `openclaw-history-ingest`
- `pi-history-ingest`
- `tag-taxonomy`
- `vault-skill-factory`
- `wiki-agent`
- `wiki-capture`
- `wiki-context-pack`
- `wiki-dashboard`
- `wiki-dedup`
- `wiki-digest`
- `wiki-export`
- `wiki-history-ingest`
- `wiki-import`
- `wiki-ingest`
- `wiki-lint`
- `wiki-narrate`
- `wiki-query`
- `wiki-rebuild`
- `wiki-research`
- `wiki-setup`
- `wiki-stage-commit`
- `wiki-status`
- `wiki-switch`
- `wiki-synthesize`
- `wiki-update`

## Origin: installed / standalone

- `code-review-expert`
- `karpathy-guidelines`
- `mermaid-diagram-renderer`

The following candidates previously grouped as installed/standalone are actually sourced
from `C:\project\LLM Wiki\obsidian-wiki\.skills`:

- `impl-validator`
- `project-rules-init`
- `skill-creator`

Management rename:

- Source candidate `ask-matt` becomes Managed Skill `ask-myskills` because it routes only the
  Skills and workflows managed by this private repository.
- Source candidate `skill-creator` becomes the human-only Engineering Skill
  `skill-evaluator`. Platform-native creators or the MySkills scaffolder own authoring; the
  transformed Skill owns structural, behavioral, baseline, efficiency, and trigger
  evaluation.
- Source candidate `handoff` becomes Managed Skill `session-checkpoint` to distinguish a
  saved, non-delivered session summary from an active `ai-handoff`.

## Origin: LLM Wiki / Obsidian third-party

- `defuddle`
- `json-canvas`
- `obsidian-bases`
- `obsidian-cli`
- `obsidian-markdown`

## Origin: LLM Wiki / QMD bundled

- `qmd`
- `release`

## Explicit exclusions from discovery

These directories are not Candidate Skills and are not included in the count:

- Orca CLI artifacts: `computer-use`, `find-skills`, `orca-cli`, `orchestration`
- Codex system-managed directory: `.codex/skills/.system`
