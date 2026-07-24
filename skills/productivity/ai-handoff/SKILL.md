---
name: ai-handoff
description: Prepare and deliver a controlled handoff to another AI session or generate a reusable prompt for another AI. Use only when the human explicitly invokes this skill to cross sessions, cross projects, delegate work, or create a prompt for another agent.
disable-model-invocation: true
---

# AI Handoff

Transfer intent, evidence, and authority without silently expanding the task.

## Choose the mode

1. **Prompt only** — return a self-contained prompt for the user to copy.
2. **Handoff document** — write a UTF-8 Markdown artifact and return its path.
3. **Live session** — deliver the prompt through an available session tool such as Orca.

Do not create or contact another session unless the user requested live delivery.

## Build the handoff

Extract only what the receiver needs:

- objective and completion conditions;
- target repo, branch, session, or agent;
- authoritative files, commands, URLs, and observed state;
- completed work and remaining work;
- constraints, permissions, destructive-action boundaries, and explicit non-goals;
- required output language and expected deliverables.

Reference existing artifacts instead of duplicating them. Redact credentials, tokens,
personal data, and unrelated conversation content.

For a stable prompt contract and examples, read
[references/prompt-contract.md](references/prompt-contract.md).

## Use a safe transport

When sending through Orca or another Windows PTY:

1. Write the transport prompt in ASCII English.
2. End with `Answer in Traditional Chinese (zh-TW).`
3. Put non-ASCII or long source material in a UTF-8 file accessible to the receiver.
4. Send the file path and an English description instead of embedding the material.
5. Use `scripts/build_handoff.py` to generate and validate the transport prompt.

Example:

```powershell
python scripts/build_handoff.py `
  --objective "Audit the repository and recommend changes. Do not edit files." `
  --target "C:\project\example" `
  --context-file "C:\temp\handoff-context.md" `
  --deliverable "A prioritized plan with file and line evidence." `
  --output "C:\temp\handoff-prompt.txt"
```

In ASCII mode, stop if the builder rejects non-ASCII input. Do not bypass the check.

## Deliver a live handoff

1. Use the tool or model-invoked skill that owns the destination runtime.
2. Confirm the destination exists and is reachable.
3. Read the target session before sending so active work is not overwritten.
4. Send the generated prompt exactly once.
5. Read back the receiver state.
6. Treat the handoff as failed if the prompt contains `�`, obvious mojibake, truncation,
   or was delivered to the wrong target. Rebuild using an ASCII prompt plus UTF-8 context
   file and resend only after identifying the failed attempt.

For Orca-managed sessions, use the `orca-cli` workflow rather than raw PTY automation.
Follow Orca's full-handoff rule: after verified delivery, report the destination and stop
monitoring unless the user explicitly asked for supervision.

## Output

Report:

- selected mode and destination;
- prompt or artifact path;
- whether delivery and read-back verification succeeded;
- any information intentionally omitted or still required.

Never claim another agent accepted or understood a handoff based only on a successful byte
write.
