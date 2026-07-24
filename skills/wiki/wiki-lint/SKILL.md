---
name: wiki-lint
description: Audit the configured Wiki's structure, links, provenance, lifecycle, confidence, tags, and synthesis health. Use only when the user explicitly asks to lint, audit, check, or repair Wiki health.
disable-model-invocation: true
---

# Wiki Lint

Resolve the vault through `../llm-wiki/references/configuration.md`. Invoke the
MySkills-managed CLI for deterministic checks and load
`references/semantic-checks.md` only for findings requiring semantic judgment.

Default lint is report-only. Cover orphaned pages, broken links, required frontmatter and
summaries, stale content, contradictions, index consistency, provenance drift, fragmented
tags, visibility tags, misc promotion, lifecycle/confidence, supersession, trust integrity,
typed relationships, and synthesis gaps. Exclude `.obsidian/`, `_raw/`, and `_archives/`.

For repairs, show a dry-run plan and obtain explicit confirmation before writes. Support the
source repair classes: links, orphan references, lifecycle correction, tier demotion, tag
normalization, contradiction callouts, and consolidation reporting. Apply
`../llm-wiki/references/post-write.md` after repairs.

Report every check's count and severity, proposed/applied repairs, skipped semantic findings,
and post-repair verification.
