---
name: llm-wiki
description: The foundational model and routing contract for the user's Obsidian knowledge base. Use only when the user explicitly asks about the Wiki architecture, page model, provenance, lifecycle, relationships, retrieval, or configuration, or needs routing to the correct Wiki workflow.
disable-model-invocation: true
---

# LLM Wiki

Use this Skill as the concise theory and routing layer. It does not initialize or write the
vault.

## Route the request

- Setup or repair structure: `wiki-setup`.
- Ingest external material: `wiki-ingest`.
- Ingest Claude, Codex, or Antigravity history: `wiki-history-ingest`.
- Save the current conversation: `wiki-capture`.
- Ask an evidence-bounded question: `wiki-query`.
- Audit health: `wiki-lint`.
- Inspect source coverage or current state: `memory-bridge` or `wiki-status`.
- Maintain links, tags, duplicates, synthesis, dashboards, or project knowledge: invoke the
  matching explicit Wiki Skill.

Load only the contract needed by the active task:

- [architecture](references/architecture.md)
- [page schema](references/page-schema.md)
- [provenance and lifecycle](references/provenance-lifecycle.md)
- [typed relationships](references/relationships.md)
- [retrieval](references/retrieval.md)
- [configuration](references/configuration.md)
- [post-write maintenance](references/post-write.md)

## Completion evidence

State which operational Skill owns the request, which contract references it needs, and the
read/write boundary. Do not claim a vault operation was performed by this routing Skill.
