# MySkills

MySkills is a Windows-first, copy-only distribution of 42 Managed Agent Skills for Codex,
Claude Code, and Antigravity CLI. The canonical inventory is
[`inventory/skills.json`](inventory/skills.json); imported snapshots remain usable after their
former source repositories are archived.

## Managed Skills

Invocation policy is identical for Claude Code and Codex. **Explicit** skills run only when the
user names them; **implicit** skills may be selected by the model when their description
matches.

### Engineering

- Explicit: [`ask-myskills`](skills/engineering/ask-myskills/SKILL.md),
  [`grill-with-docs`](skills/engineering/grill-with-docs/SKILL.md),
  [`implement`](skills/engineering/implement/SKILL.md),
  [`improve-codebase-architecture`](skills/engineering/improve-codebase-architecture/SKILL.md),
  [`skill-evaluator`](skills/engineering/skill-evaluator/SKILL.md), and
  [`to-spec`](skills/engineering/to-spec/SKILL.md).
- Implicit: [`codebase-design`](skills/engineering/codebase-design/SKILL.md),
  [`code-review`](skills/engineering/code-review/SKILL.md),
  [`diagnosing-bugs`](skills/engineering/diagnosing-bugs/SKILL.md),
  [`domain-modeling`](skills/engineering/domain-modeling/SKILL.md),
  [`prototype`](skills/engineering/prototype/SKILL.md),
  [`spec-package-generator`](skills/engineering/spec-package-generator/SKILL.md), and
  [`tdd`](skills/engineering/tdd/SKILL.md).

### Productivity

- Explicit: [`ai-handoff`](skills/productivity/ai-handoff/SKILL.md),
  [`grill-me`](skills/productivity/grill-me/SKILL.md), and
  [`session-checkpoint`](skills/productivity/session-checkpoint/SKILL.md).
- Implicit: [`grilling`](skills/productivity/grilling/SKILL.md).

### Wiki

- Explicit: [`cross-linker`](skills/wiki/cross-linker/SKILL.md),
  [`graph-colorize`](skills/wiki/graph-colorize/SKILL.md),
  [`llm-wiki`](skills/wiki/llm-wiki/SKILL.md),
  [`memory-bridge`](skills/wiki/memory-bridge/SKILL.md),
  [`project-rules-init`](skills/wiki/project-rules-init/SKILL.md),
  [`tag-taxonomy`](skills/wiki/tag-taxonomy/SKILL.md),
  [`wiki-capture`](skills/wiki/wiki-capture/SKILL.md),
  [`wiki-context-pack`](skills/wiki/wiki-context-pack/SKILL.md),
  [`wiki-dashboard`](skills/wiki/wiki-dashboard/SKILL.md),
  [`wiki-dedup`](skills/wiki/wiki-dedup/SKILL.md),
  [`wiki-history-ingest`](skills/wiki/wiki-history-ingest/SKILL.md),
  [`wiki-ingest`](skills/wiki/wiki-ingest/SKILL.md),
  [`wiki-lint`](skills/wiki/wiki-lint/SKILL.md),
  [`wiki-rebuild`](skills/wiki/wiki-rebuild/SKILL.md),
  [`wiki-research`](skills/wiki/wiki-research/SKILL.md),
  [`wiki-setup`](skills/wiki/wiki-setup/SKILL.md),
  [`wiki-status`](skills/wiki/wiki-status/SKILL.md),
  [`wiki-synthesize`](skills/wiki/wiki-synthesize/SKILL.md), and
  [`wiki-update`](skills/wiki/wiki-update/SKILL.md).
- Implicit: [`wiki-query`](skills/wiki/wiki-query/SKILL.md), limited to questions about the
  user's Wiki or knowledge base.

### Obsidian and QMD

- Implicit: [`json-canvas`](skills/obsidian/json-canvas/SKILL.md),
  [`obsidian-bases`](skills/obsidian/obsidian-bases/SKILL.md),
  [`obsidian-cli`](skills/obsidian/obsidian-cli/SKILL.md),
  [`obsidian-markdown`](skills/obsidian/obsidian-markdown/SKILL.md), and
  [`qmd`](skills/qmd/qmd/SKILL.md).

## Install and manage

Windows PowerShell 5.1 or later is required. The installer performs a read-only preflight
before any mutation, installs only to detected Agent CLIs, and copies the same canonical
directory to each eligible target:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

The destinations are `%USERPROFILE%\.agents\skills` for Codex,
`%USERPROFILE%\.claude\skills` for Claude Code, and
`%USERPROFILE%\.gemini\antigravity-cli\skills` for Antigravity CLI. Junctions and symlinks are
not supported.

Common operations:

```powershell
# Preview without prompts or writes
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -DryRun

# Inspect or verify selected skills
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Action Status -Skills code-review,wiki-query
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Action Verify

# Remove only copies whose MySkills ownership can be proven
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Action Uninstall -Skills qmd
```

An existing same-name directory is never overwritten automatically. `-AdoptExact` records an
identical unowned copy after explicit review. `-BackupAndReplace` backs up and verifies a
drifted or different unowned copy before replacement. `-Yes` approves allowlisted pinned
dependency installs only; it does not bypass ownership or compatibility checks.

Machine-specific ownership and hashes live outside Git at
`%LOCALAPPDATA%\MySkills\state.json`. Backups live below
`%LOCALAPPDATA%\MySkills\backups`.

## Dependencies

MySkills detects user-provided runtimes and external CLIs but does not install them. It may,
after approval, install only allowlisted pinned dependencies declared in
[`manifests/dependencies.json`](manifests/dependencies.json). Missing prerequisites block only
affected skills; optional dependencies keep their complete declared fallback.

## Validate

```powershell
python .\scripts\validate_inventory.py
python .\scripts\validate_repo.py
python .\scripts\run_tests.py
```
