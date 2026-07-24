---
name: wiki-update
description: Sync durable knowledge from the current project into the configured Obsidian Wiki. Use only when the user explicitly asks to update or synchronize the Wiki from a project.
disable-model-invocation: true
---

# Wiki Update

Resolve the destination vault through `../llm-wiki/references/configuration.md`. Read applicable
project rules and architecture before selecting durable knowledge.

Detect source-project delta with local Git history when available. Do not infer an issue
tracker from the remote host. Without Git, use the MySkills-managed CLI's deterministic
managed-file SHA-256 snapshot path. Resolve computer-specific project paths from local Wiki
configuration; keep stable identity and shared sync state in the vault manifest.

Distill durable architecture, decisions, abstractions, and reusable lessons. Classify
project-specific versus global knowledge, preserve provenance, merge by identity, and add
useful cross-links. Apply `../llm-wiki/references/post-write.md`.

Change only Wiki files and tracking artifacts. Never commit or push unless separately
requested. Report delta basis, files considered, pages changed, manifest checkpoint, skipped
ephemeral material, and validation/QMD status.
