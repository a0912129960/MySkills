---
name: wiki-dashboard
description: Create or modify a persistent Obsidian Wiki dashboard using Bases by default or Dataview when explicitly needed. Use only when the user explicitly asks for a Wiki dashboard or dynamic view.
disable-model-invocation: true
---

# Wiki Dashboard

Resolve the vault through `../llm-wiki/references/configuration.md`. Prefer Obsidian Bases.
Use Dataview only when requested or when the required grouping/computation cannot be expressed
suitably with Bases, and only after verifying that the plugin is installed and enabled.

Define the dashboard's audience, filters, grouping, sort order, displayed properties, and
empty-state behavior. Create `.base` and, when needed, a Markdown embedding page in the
source-defined location. Before modifying an existing note or dashboard, show the proposed
change and obtain confirmation. Preserve unrelated content.

Apply the relevant steps from `../llm-wiki/references/post-write.md`. Report paths, engine,
query/filter contract, confirmation, and verification in Obsidian-compatible syntax.
