---
name: wiki-status
description: Report the configured Wiki's source coverage, pending work, health, graph insights, and ranked next actions. Use only when the user explicitly asks for Wiki status, freshness, delta, or insights.
disable-model-invocation: true
---

# Wiki Status

Resolve the vault through `../llm-wiki/references/configuration.md`. Select Status/Delta or
Insights mode.

Status/Delta compares configured source identities and `.manifest.json`; reports ingest
coverage, changed sources, raw work, visibility, token footprint, health signals, and ranked
next actions. It does not modify formal pages.

Insights uses the MySkills-managed CLI graph analysis for hubs, bridges, clusters, surprising
connections, dead ends, graph delta, tier suggestions, and questions worth asking. Skip
unsupported conclusions for small vaults. Its only writes are the regenerable `_insights.md`
artifact and the source workflow's activity-log entry.

QMD is optional and manifest fallbacks remain valid. Report mode, counts, graph limitations,
ranked actions, and any permitted artifact writes.
