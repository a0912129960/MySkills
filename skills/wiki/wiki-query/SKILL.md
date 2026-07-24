---
name: wiki-query
description: Answer questions by searching the user's configured Obsidian Wiki or knowledge base, with vault-page citations and evidence limits. Invoke implicitly only when the request explicitly concerns the user's Wiki, vault, notes, or knowledge base—not for general knowledge questions.
---

# Wiki Query

This is the only implicitly invokable Wiki Skill. Resolve the vault through
`../llm-wiki/references/configuration.md`.

Use `../llm-wiki/references/retrieval.md` and the MySkills-managed CLI query/graph commands.
QMD may add candidates but is optional. Search metadata before bodies, then traverse typed
neighbors only as needed.

Answer in the requested presentation style, including briefing, plain-language, or progressive
teaching. Cite vault-relative pages, warn about stale or superseded evidence, surface
contradictions and gaps, and distinguish evidence from inference.

Do not modify formal knowledge pages or create derived readout files. The only permitted write
is the source workflow's bounded query-log append. Report insufficient evidence rather than
answering from unrelated general knowledge.
