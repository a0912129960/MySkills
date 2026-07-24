---
name: obsidian-cli
description: Use the official Obsidian CLI to read, create, search, and manage vault notes, tasks, properties, plugins, themes, screenshots, errors, and DOM state. Use when a request requires live Obsidian vault or plugin operations rather than direct file-format editing.
---

# Obsidian CLI

Use the official `obsidian` command against a running Obsidian Desktop
instance. Before any task, run `obsidian help`; if it fails, report the
prerequisite and stop this workflow.

Parameters use `name=value`; boolean flags have no value. Quote values
containing spaces. `file=<name>` resolves like a wikilink, while
`path=<vault-relative-path>` targets an exact file. Put `vault=<name>` first
when selecting a vault other than the most recently focused one.

Examples:

```powershell
obsidian read file="My Note"
obsidian create name="New Note" content="# Hello" silent
obsidian search query="search term" limit=10
obsidian property:set name="status" value="done" file="My Note"
```

For plugin or theme development, reload the component, inspect
`obsidian dev:errors`, verify through a screenshot or DOM query, then inspect
console errors. Use `obsidian help` for the current developer command surface.

Require the official Obsidian CLI capability declared by MySkills. Its
verification may launch Obsidian because the CLI communicates with the desktop
application.
