# Standards smell baseline

Use these Fowler-inspired heuristics only when project rules do not override
them. Each is a judgement call, not a hard violation:

- **Mysterious Name**: a name does not reveal what the value or behavior means.
- **Duplicated Code**: the same logic shape appears in more than one changed
  location.
- **Feature Envy**: behavior reaches into another object's data more than its
  own.
- **Data Clumps**: the same fields or parameters repeatedly travel together.
- **Primitive Obsession**: a primitive stands in for a meaningful domain
  concept.
- **Repeated Switches**: the same type-based conditional recurs.
- **Shotgun Surgery**: one logical change requires scattered edits.
- **Divergent Change**: one module changes for unrelated reasons.
- **Speculative Generality**: abstraction or hooks serve no confirmed need.
- **Message Chains**: callers navigate a long internal object path.
- **Middle Man**: a module mainly delegates without hiding complexity.
- **Refused Bequest**: an inheritor ignores most of the inherited contract.

For each reported smell, quote the changed hunk, explain the concrete cost in
this change, and suggest the smallest correction. Suppress it when the project
documents the pattern as intentional or passing tooling already decides it.
