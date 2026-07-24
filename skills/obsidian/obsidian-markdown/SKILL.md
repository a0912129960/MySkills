---
name: obsidian-markdown
description: Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, tags, block IDs, comments, and Obsidian-specific formatting. Use whenever the user works with Obsidian notes or asks for Obsidian-specific Markdown syntax.
---

# Obsidian Flavored Markdown

Use standard Markdown normally and add only the Obsidian extensions the note
needs.

## Workflow

1. Preserve or add valid YAML properties at the top of the note.
2. Use `[[wikilinks]]` for vault notes and Markdown links for external URLs.
3. Prefix a wikilink with `!` to embed its target.
4. Use `> [!type]` callouts for highlighted blocks.
5. Preserve block IDs, comments, tags, and existing Obsidian syntax when
   editing.
6. Verify YAML parses and internal target spelling is consistent; render in
   Obsidian when available.

Read the relevant reference only when needed:

- [references/properties.md](references/properties.md)
- [references/embeds.md](references/embeds.md)
- [references/callouts.md](references/callouts.md)

Common forms:

```markdown
[[Note|Label]]
[[Note#Heading]]
[[Note#^block-id]]
![[image.png|300]]
> [!warning] Review needed
```

Do not rewrite wikilinks as filesystem paths. Preserve standard Markdown
content that does not require an Obsidian-specific change.
