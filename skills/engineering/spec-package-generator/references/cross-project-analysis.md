# Cross-Project Analysis Reference

Use this reference when a feature may affect more than one project, repository, service, database, report, shared library, or external integration.

## Inventory-Derived Rule

The projects-involved list must be derived from `00-context-inventory.md`, never inferred from the requirement text alone.

- A project may only appear in `20-gate2-project-impact.md` or in a cross-project diagram when its inventory status is `verified`, or when the user explicitly accepted it with status `accepted-unverified`.
- Accepted unverified projects must be tagged `UNVERIFIED`.
- A project whose architecture was never read is a context gap, not a diagram node. Record the gap and ask the user for the source.
- Systems whose behavior is being removed by the requirement still belong in the analysis; verifying the current integration is required to specify its removal.

## Questions To Answer

- Which projects are involved?
- Which project provides data, APIs, contracts, files, or events?
- Which project consumes them?
- Which projects should be modified?
- Which projects should remain read-only references?
- What integration points exist?
- What shared contracts exist?
- What release order is required?
- Can provider and consumer be released independently?
- Should the feature be split into multiple project-level tasks?

## Provider And Consumer Rule

Provider-side contracts usually need to be defined or implemented before consumer-side work.

Examples:

- Backend API before frontend integration.
- Shared DTO package before API and UI updates.
- Data project query before report rendering.
- External PDF/report project before calling service integration.

## Risk Signals

Mark cross-project risk higher when:

- Multiple repositories must release together.
- Contracts are unclear.
- A verified released contract or active consumer requires compatibility handling.
- A database or shared schema changes.
- External services are involved.
- Verified active consumers may be affected.

## Single-Project Handling

Do not delete the cross-project review file for single-project work.

State explicitly:

```text
Single-project feature. No cross-project implementation required.
```
