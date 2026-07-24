---
name: to-spec
description: Synthesize an already-discussed small change into one lightweight local specification without interviewing or publishing to a tracker. Use only when explicitly invoked.
disable-model-invocation: true
---

# To Spec

Use this for a small requirement that needs one synthesis pass. Use
`spec-package-generator` when the work needs gated PRD, EARS, BDD, technical
design, task, prompt, traceability, or readiness artifacts.

Do not interview the human. Read the current conversation, applicable project
rules, domain language, ADRs, architecture guidance, and representative code.
If missing information prevents an honest spec, record it as an open question
instead of inventing an answer.

Write `.scratch/<feature-slug>/spec.md` unless authoritative repository
instructions or an established repeated template defines a more specific
location. Do not infer a location from a generic `docs` or `specs` directory.

Include:

- problem and user-visible outcome;
- confirmed behavior and acceptance examples;
- implementation decisions already made;
- public test seams and validation expectations;
- constraints, dependencies, out of scope, risks, and open questions;
- authoritative sources read.

Do not create or mutate an issue, pull request, branch, commit, or external
tracker unless the human separately requests that action.
