---
name: graph-colorize
description: Color-code or restore the configured Obsidian Wiki graph by tag, category, visibility, combined rules, or a custom mapping. Use only when the user explicitly asks to change Wiki graph colors.
disable-model-invocation: true
---

# Graph Colorize

Resolve the vault through `../llm-wiki/references/configuration.md`. Warn that an open Obsidian
instance may overwrite graph settings.

Select exactly one mode: by tag, category, visibility, combined, custom, clear, or restore.
Inventory the needed tags/categories before applying a mode. Invoke
`scripts/set-graph-colors.ps1` with the resolved vault and selected mode.

The script must back up `.obsidian\graph.json`, replace only `colorGroups`, preserve unrelated
settings, apply stable palette ordering and visibility precedence, and verify the written JSON.
If `.obsidian` exists but `graph.json` does not, initialize the retained source default before
colorizing it. If `.obsidian` does not exist, report the missing prerequisite. Restore reuses a
named backup; it never guesses among multiple backups.

Report the mode, backup path, number of groups, verification result, and exact undo command.
