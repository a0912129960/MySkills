# Handoff prompt contract

Keep the default handoff as concise structured text. Reference authoritative
artifacts instead of copying conversation history or source files.

## Required information

```text
OBJECTIVE: <one concrete outcome>
TARGET: <project, session, or agent>
AUDIENCE: agent|human
FINAL_AUDIENCE: human              # only for multi-hop human delivery
AUTHORITATIVE_CONTEXT:
- <path, URL, commit, or observed fact>
DELIVERABLE: <verifiable output>
```

Also include constraints, authority boundaries, completed and remaining work,
non-goals, validation commands, and risks when they materially affect execution.
Separate observed facts from assumptions. Redact credentials, tokens, unrelated
personal data, and unnecessary transcript content.

## Language and transport

- Direct terminal transport text is ASCII-only.
- Aim for at most 6,000 characters; 10,000 is the hard ceiling. The builder
  requires `-AllowExtendedBudget` when further reduction would remove required
  handoff information.
- An agent-facing handoff does not constrain the receiver's working language.
- Add `Answer in Traditional Chinese (zh-TW).` only when `AUDIENCE` or
  `FINAL_AUDIENCE` is `human`.
- Put required non-ASCII or unsummarizable source material in an exceptional
  UTF-8 context file and reference its absolute path.

Validate the envelope with `scripts/build-handoff.ps1` before delivery. Live
delivery also requires destination inspection and read-back verification.
