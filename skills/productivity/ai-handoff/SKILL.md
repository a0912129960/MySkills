---
name: ai-handoff
description: Construct and validate a prompt for another AI session, then either return it for manual copy or explicitly deliver it live. Use only when the human explicitly requests a cross-session prompt or transfer.
disable-model-invocation: true
---

# AI Handoff

Transfer intent, evidence, and authority without silently expanding the task.

## Select delivery

- **Manual**: print the validated prompt for the human to copy.
- **Live**: use an available transport only when the human explicitly requested
  delivery. Prefer a matching session in the target project; reuse it only when
  blank or demonstrably for the same goal. If none exists, a request to hand the
  work to that project authorizes creation of a new session for the named agent
  or configured project default. If neither is available, ask the human rather
  than guessing an agent.

Do not write to the clipboard. A file is an exceptional fallback only when
required source material cannot be represented safely in the text envelope.

## Build and validate

Follow [references/prompt-contract.md](references/prompt-contract.md). Include
the objective, completion conditions, target, authoritative artifacts and
observed state, completed and remaining work, constraints, permissions,
non-goals, and expected deliverable. Reference existing artifacts rather than
copying conversations or source files. Redact secrets and unrelated personal
data.

Use `scripts/build-handoff.ps1` for deterministic validation. Direct terminal
transport text must be ASCII, should remain within 6,000 characters, and must
not exceed 10,000. An agent-facing handoff has no forced response language. A
human-facing final delivery adds `Answer in Traditional Chinese (zh-TW).`;
multi-hop work carries the corresponding final-audience fields.

## Deliver and finish

For live delivery, inspect the destination before sending, send exactly once,
then read receiver state. Mojibake, truncation, or a wrong destination is a
failure; diagnose before any corrected resend.

A normal live handoff transfers ownership. After verified delivery, stop work
and monitoring unless the human explicitly requested coordination. Report the
mode, destination, payload or exceptional artifact, verification result, and
anything intentionally omitted or still required.
