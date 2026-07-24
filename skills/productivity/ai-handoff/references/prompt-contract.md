# Prompt contract

Use this structure for prompts handed to another AI:

```text
ROLE
You are the receiving agent working in <target>.

OBJECTIVE
<one concrete outcome>

AUTHORITATIVE CONTEXT
- Read <path or URL>.
- Current observed state: <facts only>.

CONSTRAINTS
- <authority and non-goals>
- Do not modify files unless explicitly authorized.

DELIVERABLES
- <verifiable outputs>

VERIFICATION
- Inspect the current state before relying on this handoff.
- Cite files and line numbers when making repository claims.

RESPONSE
Answer in Traditional Chinese (zh-TW).
```

## Rules

- Write one objective, not a backlog of unrelated requests.
- Separate observed facts from assumptions.
- Preserve the user's authority boundaries.
- Name the evidence that proves completion.
- Prefer paths and identifiers over pasted transcripts.
- Never include secrets.
- For ASCII transport, keep every character in the prompt within ASCII. A referenced
  UTF-8 context file may contain any language.

## Prompt-only example

```text
ROLE
You are the receiving agent working in C:\project\example.

OBJECTIVE
Audit the skill installation flow and recommend changes. Do not edit files.

AUTHORITATIVE CONTEXT
- Read C:\temp\skill-policy-context.md.
- Inspect the repository before accepting claims in that document.

CONSTRAINTS
- Analysis only.
- Do not change files or external state.

DELIVERABLES
- A prioritized recommendation.
- File and line evidence.
- Tests needed for each proposed change.

VERIFICATION
- Distinguish proven behavior from inference.

RESPONSE
Answer in Traditional Chinese (zh-TW).
```
