# Phase Two Parallel File Ownership

This ownership map reserves non-overlapping write scopes for the three implementation agents.
It does not change the confirmed product decisions in
`docs/skill-consolidation-design.md`. The coordinating AI owns integration and every shared
file.

## Coordinating AI: shared and integration files

Only the coordinating AI may modify:

- repository-root files, `.claude-plugin/**`, and `docs/**`;
- `inventory/**`;
- `scripts/install.ps1`, `scripts/validate_repo.py`, `scripts/inventory_loader.py`, and
  `scripts/validate_inventory.py`;
- `package.json`, generated skill indexes, and other repository-wide manifests;
- `tests/test_inventory.py`, existing tests, and `tests/integration/**`.

Agents must report a requested shared-file change to the coordinator instead of editing one of
these paths. The coordinator applies accepted changes after checking all three workstreams.

## Agent 1: Engineering and Productivity workflows

Agent 1 exclusively owns:

- `skills/engineering/ask-myskills/**`;
- `skills/engineering/codebase-design/**`;
- `skills/engineering/code-review/**`;
- `skills/engineering/diagnosing-bugs/**`;
- `skills/engineering/domain-modeling/**`;
- `skills/engineering/grill-with-docs/**`;
- `skills/engineering/implement/**`;
- `skills/engineering/improve-codebase-architecture/**`;
- `skills/engineering/prototype/**`;
- `skills/engineering/spec-package-generator/**`;
- `skills/engineering/tdd/**`;
- `skills/engineering/to-spec/**`;
- `skills/productivity/**`;
- `tests/skills/engineering-workflows/**`;
- `tests/skills/productivity/**`.

`skills/engineering/skill-evaluator/**` is deliberately excluded from Agent 1.

## Agent 2: Wiki suite and repository-owned Wiki CLI

Agent 2 exclusively owns:

- `skills/wiki/**`;
- `tools/obsidian-wiki/**`;
- `tests/skills/wiki/**`;
- `tests/obsidian-wiki/**`.

Agent 2 may consume the inventory and dependency declarations but may not edit them.

## Agent 3: Skill evaluation, Obsidian, QMD, and dependency declarations

Agent 3 exclusively owns:

- `skills/engineering/skill-evaluator/**`;
- `skills/obsidian/**`;
- `skills/qmd/**`;
- `tools/skill-evaluator/**`;
- `requirements/skill-evaluator/**`;
- `manifests/dependencies.json` and `manifests/dependencies.schema.json`;
- `scripts/dependencies/**`;
- `tests/skill-evaluator/**`;
- `tests/skills/platform/**`;
- `tests/dependencies/**`.

Agent 3 owns dependency declaration and probing primitives. The coordinator retains
`scripts/install.ps1` so dependency actions, copy orchestration, and integration remain a
single-writer responsibility.

## Handoff rule

Each agent returns changed paths, verification commands and results, unresolved decisions, and
requested coordinator-owned edits. An agent must not stage, commit, or rewrite another
owner's files. The coordinator reviews and integrates work only after confirming that every
changed path belongs to that agent's scope.
