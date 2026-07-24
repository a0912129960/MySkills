---
name: wiki-context-pack
description: Build a token-bounded, provenance-preserving context pack from the configured Wiki for another task or agent. Use only when the user explicitly requests a Wiki context pack.
disable-model-invocation: true
---

# Wiki Context Pack

Resolve the vault through `../llm-wiki/references/configuration.md`. Clarify the target task
only when it cannot be inferred; otherwise use the user's stated goal and budget.

Retrieve candidates using `../llm-wiki/references/retrieval.md`. QMD is optional. Rank by task
relevance, lifecycle, confidence, recency, and tier; remove overlap before truncating. Preserve
page identity and provenance, distinguish facts from synthesis, and enforce the token budget
using deterministic size accounting.

Return structured Markdown with purpose, included sources, compact context, conflicts/gaps,
and excluded high-scoring items. Do not modify formal Wiki pages. Append only the source
workflow's activity-log record and report actual size versus budget.
