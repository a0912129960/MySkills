# Post-write maintenance

A successful mutating Wiki workflow is one complete transaction. Apply the effects relevant
to its write:

1. write or update the intended page, attachment, dashboard, or redirect;
2. preserve frontmatter, relationships, and source provenance;
3. reconcile `index.md`;
4. update `hot.md` when recency or importance changed;
5. append a concise `log.md` entry;
6. update `.manifest.json` for source-backed ingestion;
7. refresh QMD only when it is configured and available;
8. run the required structural or health check.

If a required write fails, do not mark its source ingested and do not claim completion.
