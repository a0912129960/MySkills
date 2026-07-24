---
name: wiki-research
description: Perform bounded multi-round external research and file sourced findings into the configured Wiki. Use only when the user explicitly invokes Wiki research or asks for research results to be written into the Wiki.
disable-model-invocation: true
---

# Wiki Research

Resolve the vault through `../llm-wiki/references/configuration.md`. A general research request
does not authorize a Wiki write.

Define the question, angles, round limit, stop condition, and source-quality criteria. Use the
active agent's native network search and retrieval, prioritizing primary and authoritative
sources. If network access is unavailable, stop and direct the user to provide sources to
`wiki-ingest`.

Across bounded rounds, capture sources, contradictions, gaps, and diminishing returns. Distill
supported reference, concept, entity, and synthesis pages with precise provenance; never hide
uncertainty or invent access dates. Complete `../llm-wiki/references/post-write.md`.

Report queries/rounds, sources accepted/rejected, pages changed, contradictions, gaps, halt
reason, and QMD status.
