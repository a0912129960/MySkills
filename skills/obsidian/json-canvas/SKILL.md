---
name: json-canvas
description: Create and edit JSON Canvas (.canvas) files with text, file, link, and group nodes plus validated edges. Use whenever the user works with Obsidian Canvas files, mind maps, visual boards, or JSON Canvas data.
---

# JSON Canvas

Create or edit a `.canvas` file through its JSON document.

## Workflow

1. Parse the existing file when editing; a new canvas starts with `nodes` and
   `edges` arrays.
2. Give every node and edge a unique lowercase 16-character hexadecimal ID.
3. Place nodes with non-overlapping integer `x`, `y`, `width`, and `height`
   values. Preserve unrelated existing layout and styling.
4. Add edges only after their `fromNode` and `toNode` IDs exist.
5. Serialize valid JSON and validate the complete graph after every edit.

Read [references/json-canvas-contract.md](references/json-canvas-contract.md)
when choosing node fields, edge anchors, colors, or group layout.

## Completion evidence

- JSON parses successfully.
- IDs are unique across nodes and edges.
- Every edge endpoint resolves to a node.
- Each node type has its required payload field.
- Enum and color values satisfy the contract.

Use real newline characters encoded as `\n` inside JSON strings; do not insert
the literal two-character sequence `\\n` when a rendered line break is wanted.
