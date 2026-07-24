---
name: memory-bridge
description: Browse, search, compare, or map Wiki knowledge by recorded source-agent provenance. Use only when the user explicitly asks which AI source contributed knowledge or wants source-based Wiki comparison.
disable-model-invocation: true
---

# Memory Bridge

Resolve the vault through `../llm-wiki/references/configuration.md` and read `.manifest.json`.
Choose Browse, Search, Diff, or Map mode.

- Browse groups recorded source contributions by supported agent and topic.
- Search finds source-backed pages matching a topic.
- Diff computes page-source sets, intersections, and differences.
- Map summarizes contribution coverage and notable asymmetries.

Read only bounded matching page bodies after manifest selection. Missing or invalid provenance
is reported with repair guidance rather than inferred from prose. Describe contribution
coverage—not what an agent can know—because every configured agent may read the same Wiki.
Preserve the configured link format and append only the source workflow's activity-log entry.

Report counts, page links, asymmetries, gaps, and the manifest evidence used.
