---
name: project-rules-init
description: Bootstrap or update concise local AI rules and an architecture baseline for a project. Use only when the user explicitly asks to initialize, restore, or revise project rules.
disable-model-invocation: true
---

# Project Rules Init

This workflow is local to the target project. It does not use the Wiki, global bootstrap files,
hooks, a remote identity store, or generated policy packs, and it never commits or pushes.

1. Read the target repository's applicable instruction hierarchy.
2. Sample representative code, build/test configuration, and architecture evidence.
3. Separate documented rules, observed conventions, and unapproved recommendations. Never
   present an ideal architecture as an existing rule.
4. Propose the complete contents of a concise canonical `PROJECT_RULES.md`, short managed
   pointers in `AGENTS.md` and `CLAUDE.md`, and an architecture baseline at the established
   documentation location or `docs/architecture.md`.
5. Show the full proposal and write only after explicit approval. Preserve unrelated content
   and existing instruction precedence.
6. Run every validation command declared by the approved rules.

Report files created or updated, evidence sampled, approval received, and validation results.
