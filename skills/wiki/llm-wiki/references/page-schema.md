# Page schema

Knowledge pages use YAML frontmatter followed by a short summary and evidence-backed body.
Preserve existing unknown frontmatter keys.

Required fields:

- `title`: human-readable identity.
- `summary`: one or two sentences suitable for retrieval.
- `tags`: canonical Wiki tags.
- `created`: ISO date.
- `updated`: ISO date.
- `status`: lifecycle value described in `provenance-lifecycle.md`.
- `confidence`: supported confidence value.
- `sources`: source identities sufficient to audit the page.

Prefer one durable concept per page. Use aliases for genuine alternate names, not related
concepts. Keep citations or source locations next to claims that need them. Do not invent
provenance, dates, or certainty.
