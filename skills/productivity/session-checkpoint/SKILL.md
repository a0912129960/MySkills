---
name: session-checkpoint
description: Save a concise, non-delivered checkpoint so work can resume in a later session. Use only when the human explicitly requests a checkpoint or resumable summary.
argument-hint: "What should the next session resume?"
disable-model-invocation: true
---

# Session Checkpoint

Write `<current-project-root>/HANDOFF.md`. This is a saved summary, not a prompt
delivery: never contact, create, or select another AI session.

Capture the current goal, completion conditions, authoritative artifacts,
decisions, completed and remaining work, verification evidence, constraints,
risks, and a concrete next action. Reference specs, plans, ADRs, commits, diffs,
and source files instead of duplicating them. Redact secrets and unrelated
personal data. Tailor the checkpoint to any focus supplied by the human.

If `HANDOFF.md` exists, inspect it first. Update it automatically only when it
is an older checkpoint for the same goal. Do not overwrite a different goal or
a file serving another purpose without human direction.

Report the absolute path and a short summary of what the next session should do.
