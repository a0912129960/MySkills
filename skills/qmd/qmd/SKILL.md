---
name: qmd
description: Search indexed local Markdown knowledge bases, notes, documentation, and wikis with QMD. Use when users ask to find local notes, retrieve indexed documents, inspect a knowledge base, answer from Markdown sources, or maintain QMD collections.
license: MIT
allowed-tools: Bash(qmd:*), mcp__qmd__*
---

# QMD

Search local indexed material before the web when it may contain the answer.

## Search and retrieve

1. Search for candidates.
2. Retrieve full sources with `qmd get` or `qmd multi-get`.
3. Answer from retrieved text and cite the QMD path or docid plus line numbers.

Prefer `qmd search` for exact names, titles, symbols, or phrases. For conceptual
recall, write a structured `qmd query` containing `intent:` and one or more of
`lex:`, `vec:`, and `hyde:`. State what to find and what nearby meaning to
avoid; do not delegate all expansion to a bare query.

```powershell
qmd search '"AI Before Headcount"' -n 5
qmd query "intent: Find the local metrics concept, not generic analytics.`nlex: cockpit Goodhart OKR`nvec: data informed not metric driven"
qmd multi-get "#abc123,#def432" --format md
```

Snippets are leads, not evidence. Retrieve the document before making factual,
decision, quotation, or nuance claims.

Use QMD's own range syntax (`#abc123:120:40` or `--from` plus `-l`) rather than
piping through `head`, `tail`, `sed`, or `awk`. Use `--full-path` only when a
filesystem path must be passed to another tool.

## Discovery and maintenance

`qmd collection list`, `qmd ls`, and `qmd status` inspect the index. Commands
such as `collection add`, `update`, and `embed` mutate local index state; run
them only for an explicit setup or maintenance request.

If semantic/model-backed search fails, run `qmd doctor` and fall back to stronger
BM25 lexical terms. The central MySkills installer owns the QMD package and
optional MCP registration; this Skill never installs or upgrades it.

Read [references/mcp-setup.md](references/mcp-setup.md) only for transport
registration behavior.
