---
name: obsidian-bases
description: Create and edit Obsidian Bases (.base) files with scoped views, filters, formulas, properties, and summaries. Use whenever the user mentions Bases, database-like note views, .base files, cards, tables, filters, or Obsidian formulas.
---

# Obsidian Bases

Create valid YAML in a `.base` file.

## Workflow

1. Define the note scope with a global filter.
2. Add formulas only for values that must be computed.
3. Configure display metadata under `properties`.
4. Add one or more `table`, `cards`, `list`, or `map` views with explicit
   property order and any view-specific filters, grouping, or summaries.
5. Parse the YAML, verify every `formula.<name>` reference is defined, then ask
   Obsidian to render the Base when that runtime is available.

Read [references/bases-contract.md](references/bases-contract.md) for filter,
formula, view, quoting, and duration rules.

## Safety

Preserve unrelated views and properties when editing. Ask before replacing an
existing view whose identity is ambiguous. A map view additionally depends on
the user's chosen map capability; do not claim that `.base` alone supplies it.

## Completion evidence

- YAML parses without errors.
- Filters use one valid recursive operator at each object level.
- Formula and property references resolve.
- Every view has a supported type, name, and useful order.
- The result renders in Obsidian when rendering was available.
