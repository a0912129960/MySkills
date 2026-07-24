---
name: code-review
description: Review a Git change set along separate Standards and Spec axes. Use for branches, pull requests, staged or unstaged work, or changes since a supplied commit, branch, tag, or merge-base.
---

# Code Review

Keep Standards and Spec independent so correct behavior cannot hide poor
engineering and clean code cannot hide the wrong behavior.

## Fix the change set

Verify `git --version` before Git operations. If the user supplied a commit,
branch, tag, or other ref, resolve it and use it as the fixed baseline. Otherwise
review the current staged, unstaged, and untracked working-tree changes. Record
the exact commands and file list once so both review axes inspect the same set.

Stop with evidence if Git is unavailable, the ref is invalid, or the selected
change set is empty.

## Gather authority

Standards come from applicable `AGENTS.md`, `CLAUDE.md`,
`PROJECT_RULES.md`, architecture or ADR sources, validation configuration, and
nearby representative code. Repository rules override generic preferences.
Apply the judgement-only smell heuristics in
[references/standards-baseline.md](references/standards-baseline.md) where the
repository does not explicitly endorse the pattern.

Spec context comes only from a user-supplied source, the current conversation,
or a relevant artifact under `.scratch` or `.ai-dev`. Read an external issue or
pull request only when the user explicitly supplied it. If no spec exists, say
that the Spec axis is unavailable.

## Review

Run the axes independently, in parallel when agents are available:

- **Standards**: report concrete rule, convention, architecture-direction, and
  validation problems introduced by the change.
- **Spec**: report missing or partial requirements, incorrect behavior, and
  unrequested scope.

Every finding needs a file and line or hunk, the violated authority, its
consequence, and a practical correction. Do not report style already enforced
by passing automation. Treat documented-rule breaches as hard findings when
warranted; label baseline smells as judgement calls.

## Output

Present separate `Standards` and `Spec` sections, followed by the checks run and
their results. Rank findings within an axis by impact; do not merge the axes
into a single score.
