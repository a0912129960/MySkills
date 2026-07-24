# Provenance and lifecycle

`.manifest.json` is the source-ingest ledger. Store canonical absolute source paths with user
and environment variables expanded. Preserve the earliest creation evidence and append or
update later contributions without erasing prior sources.

Lifecycle values describe knowledge maturity, not task progress:

- `seed`: useful but incomplete.
- `growing`: multiple supported observations or links.
- `evergreen`: stable and broadly reusable.
- `stale`: materially outdated and awaiting review.
- `superseded`: retained for traceability but replaced by a named page.

Confidence must follow the vault schema. Automated workflows may demote confidence when
evidence becomes stale; raising confidence requires evidence or an explicit reviewed record.
Superseded pages name their successor, and the successor links back.
