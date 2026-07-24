---
name: wiki-dedup
description: Audit or resolve page-level identity collisions in the configured Wiki. Use only when the user explicitly asks to find duplicates, compare two pages, or merge duplicate Wiki pages.
disable-model-invocation: true
---

# Wiki Dedup

Resolve the vault through `../llm-wiki/references/configuration.md`.

Without page arguments, perform a vault-wide read-only audit. Compare titles, aliases, tags,
categories, and summaries first; read bodies only for candidate pairs. Two named pages select
focused analysis. Report confidence and evidence without writing.

`--merge` presents each candidate's identity decision, canonical page, preserved content,
redirect, and link updates, then requires confirmation. An explicitly requested `--auto`
merges only source-threshold high-confidence pairs without per-pair prompts; uncertain pairs
remain untouched.

A merge preserves content and provenance, writes a redirect stub, rewrites inbound links, and
completes `../llm-wiki/references/post-write.md`. Report candidates, decisions, changes, and
post-merge health evidence.
