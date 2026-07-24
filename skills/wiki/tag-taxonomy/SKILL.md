---
name: tag-taxonomy
description: Audit or maintain the configured Wiki's canonical tag vocabulary. Use only when the user explicitly asks to audit, normalize, assign, or add Wiki tags.
disable-model-invocation: true
---

# Tag Taxonomy

Resolve the vault through `../llm-wiki/references/configuration.md`. Select audit, normalize,
tag-one-page, or add-canonical-tag mode.

Audit is read-only. Normalization automatically replaces known aliases, applies page tag
limits, and preserves reserved visibility tags. Unknown tags require the source workflow's
user decision before replacement or taxonomy expansion. Tag-one-page selects the smallest
canonical set supported by the page. Adding a canonical tag updates the vocabulary and rejects
duplicates or aliases that would make identity ambiguous.

For writes, preserve frontmatter and apply `../llm-wiki/references/post-write.md`. Report
canonical, aliased, unknown, over-tagged, untagged, and reserved-tag findings plus every change.
