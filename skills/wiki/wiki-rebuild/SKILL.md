---
name: wiki-rebuild
description: Archive, rebuild, or restore the configured Wiki with verified backups and destructive-action safeguards. Use only when the user explicitly requests Wiki archive, rebuild, reset, or restore.
disable-model-invocation: true
---

# Wiki Rebuild

Resolve and validate the vault through `../llm-wiki/references/configuration.md`. Select Archive
Only, Archive + Rebuild, or Restore. Show exact targets and obtain the source-required explicit
confirmation before any destructive step.

Every clear or restore first creates a timestamped archive of the current live Wiki and
verifies its inventory and digest. Archives are never deleted automatically. Never include or
delete `.obsidian/`. Archive + Rebuild clears only validated live Wiki targets and does not
re-ingest sources. Restore first archives current state, validates the selected archive, then
restores it.

Use `scripts/manage-wiki.ps1` for archive, verification, clear, and restore mechanics. After a
write, record the operation, refresh QMD when configured, and run health validation. Report
confirmation, archive paths/digests, exact changed targets, and recovery guidance.
