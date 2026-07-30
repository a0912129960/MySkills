---
name: ask-myskills
description: Route a request to the Managed Skills and confirmed workflows in MySkills. Use only when the human explicitly asks which MySkills skill or flow fits the situation.
disable-model-invocation: true
---

# Ask MySkills

Route by outcome without inventing an uninstalled workflow.

## Engineering routes

- Sharpen a codebase-backed idea: `grill-with-docs`.
- Capture a small, already-discussed requirement: `to-spec`; use
  `spec-package-generator` for a gated, resumable formal package.
- Implement a small task or `to-spec` artifact: `implement`.
- Implement one human-confirmed Task from a formal
  `spec-package-generator` package: `implement-spec-task`.
- Build one observable behavior test-first: `tdd`.
- Diagnose a hard bug or regression: `diagnosing-bugs`.
- Review a change set against standards and a specification: `code-review`.
- Explore a runnable design question: `prototype`.
- Survey architecture health: `improve-codebase-architecture`.
- Design an interface or seam: `codebase-design`.
- Sharpen domain language or record a durable trade-off: `domain-modeling`.
- Evaluate a Managed Skill after authoring or substantive revision:
  `skill-evaluator`.

## Conversation routes

- Stress-test an idea without repository documentation: `grill-me`.
- Prepare a prompt or transfer ownership to another live AI session:
  `ai-handoff`.
- Save a non-delivered summary for resuming this project later:
  `session-checkpoint`.

## Wiki routes

- Initialize local project rules from approved architecture:
  `project-rules-init`.
- Understand the Wiki model: `llm-wiki`; initialize or repair a vault:
  `wiki-setup`.
- Ingest general sources: `wiki-ingest`; capture this conversation:
  `wiki-capture`; ingest supported agent history: `wiki-history-ingest`.
- Query existing knowledge: `wiki-query`; build a bounded downstream context:
  `wiki-context-pack`; compare source provenance: `memory-bridge`.
- Inspect state or quality: `wiki-status`, `wiki-lint`, or `wiki-dedup`.
- Maintain connections and vocabulary: `cross-linker`, `tag-taxonomy`, or
  `wiki-synthesize`.
- Research directly into the Wiki: `wiki-research`; sync durable learning from
  the current project: `wiki-update`.
- Create a persistent dashboard: `wiki-dashboard`; color the graph:
  `graph-colorize`; archive, rebuild, or restore: `wiki-rebuild`.

## Obsidian and search routes

- Work with Obsidian Canvas, Bases, Markdown, or the official CLI:
  `json-canvas`, `obsidian-bases`, `obsidian-markdown`, or `obsidian-cli`.
- Search local Markdown collections with QMD: `qmd`.

Ask one focused question only when the requested outcome cannot distinguish two
routes. Report the selected Skill by its managed name.
