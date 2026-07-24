---
name: wiki-capture
description: Distill the current conversation into durable Wiki knowledge or a bounded raw draft. Use only when the user explicitly asks to save or capture this conversation in the Wiki.
disable-model-invocation: true
---

# Wiki Capture

Resolve the vault through `../llm-wiki/references/configuration.md`. Use full mode unless the
user explicitly requests quick/raw capture.

In full mode, distill durable claims, decisions, concepts, entities, and relationships into one
appropriately classified page. Do not copy hidden reasoning or the conversation verbatim.
Preserve uncertainty and identify conversation provenance, then perform the complete
post-write transaction in `../llm-wiki/references/post-write.md`.

In quick mode, write one bounded draft under `_raw/` using
`references/raw-format.md`. Quick mode does not update formal knowledge pages or claim that the
draft has been ingested.

No hook or end-of-response automation is part of this workflow. Report the mode, written path,
knowledge retained, and maintenance evidence.
