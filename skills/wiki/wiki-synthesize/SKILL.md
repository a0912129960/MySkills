---
name: wiki-synthesize
description: Discover and create evidence-backed cross-cutting synthesis pages in the configured Wiki. Use only when the user explicitly asks the Wiki to synthesize connections or create synthesis pages.
disable-model-invocation: true
---

# Wiki Synthesize

Resolve the vault through `../llm-wiki/references/configuration.md`. Use co-occurrence, typed
graph evidence, CLI graph analysis, and optional QMD to find unsupported synthesis gaps.

Once explicitly invoked, score candidates and automatically create the highest-value bounded
syntheses without per-page confirmation. Each page must cite source pages, distinguish
evidence from inference, include ambiguity and the strongest objection, and avoid restating an
existing page. Add source-page backlinks.

Skip weak or redundant candidates and explain why. Complete
`../llm-wiki/references/post-write.md`. Report candidates considered, scores, pages/backlinks
created, objections, skipped cases, and health/QMD evidence.
