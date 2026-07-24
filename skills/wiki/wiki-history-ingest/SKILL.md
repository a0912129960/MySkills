---
name: wiki-history-ingest
description: Ingest or query durable knowledge from Claude, Codex, or Antigravity conversation history into the configured Wiki. Use only when the user explicitly requests history ingestion or names one of those agents' history as a Wiki source.
disable-model-invocation: true
---

# Wiki History Ingest

Resolve the vault through `../llm-wiki/references/configuration.md`. Select exactly one source:
Claude, Codex, or Antigravity. If it is ambiguous, infer only from a named agent or an
unambiguous source path; otherwise ask.

Load the matching data contract:

- [Claude](references/claude-data-format.md)
- [Codex](references/codex-data-format.md)
- [Antigravity](references/antigravity-data-format.md)

Support append, full, and targeted-topic modes. Validate and sample source records before
processing. Apply privacy filtering, cluster topics, distill durable knowledge, and avoid
transcript dumps. Targeted mode returns an immediately usable synthesis as well as any durable
page changes.

Use the packaged parser only for its matching source; fail safely on an unknown record shape
and retain that source's documented fallback. Complete
`../llm-wiki/references/post-write.md` after successful writes. Report sessions considered,
records accepted/skipped, privacy exclusions, pages changed, source checkpoint, and QMD status.
