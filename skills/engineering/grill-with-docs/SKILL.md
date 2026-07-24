---
name: grill-with-docs
description: Relentlessly interview the human to sharpen a codebase-backed plan while maintaining its domain glossary and durable decisions. Use only when explicitly invoked.
disable-model-invocation: true
---

# Grill With Docs

Run the `grilling` one-question-at-a-time decision loop. Read applicable
`CONTEXT.md`, `CONTEXT-MAP.md`, architecture guidance, and ADRs before asking
questions; inspect the environment instead of asking for discoverable facts.

Use `domain-modeling` throughout:

- update the applicable `CONTEXT.md` as domain terms are resolved;
- surface contradictions between the discussion, glossary, and code;
- offer an ADR only for a hard-to-reverse, surprising, real trade-off.

Do not implement the plan. Finish when the human confirms shared understanding,
then summarize confirmed decisions, recorded artifacts, and unresolved items.
