# Skill evaluation case authoring ownership

This file defines the non-overlapping edit boundary for the parallel case-authoring
slice. Agents may read the complete repository but edit only their assigned files.
They do not stage or commit; the coordinator reviews and commits each ownership group
separately.

## Coordinator-owned shared files

Only the coordinator edits:

- `evaluations/cases.json`
- `evaluations/*.schema.json`
- `evaluations/records/**`
- `attestations/**`
- `tools/skill-evaluator/**`
- `tests/**`
- `scripts/**`
- `CLAUDE.md`, `CONTEXT.md`, and `docs/**`

## Agent A: engineering and productivity cases

- `evaluations/cases/ai-handoff.json`
- `evaluations/cases/ask-myskills.json`
- `evaluations/cases/code-review.json`
- `evaluations/cases/codebase-design.json`
- `evaluations/cases/diagnosing-bugs.json`
- `evaluations/cases/domain-modeling.json`
- `evaluations/cases/grill-me.json`
- `evaluations/cases/grill-with-docs.json`
- `evaluations/cases/grilling.json`
- `evaluations/cases/implement.json`
- `evaluations/cases/improve-codebase-architecture.json`
- `evaluations/cases/project-rules-init.json`
- `evaluations/cases/prototype.json`
- `evaluations/cases/session-checkpoint.json`

## Agent B: platform and evaluation cases

- `evaluations/cases/cross-linker.json`
- `evaluations/cases/graph-colorize.json`
- `evaluations/cases/json-canvas.json`
- `evaluations/cases/llm-wiki.json`
- `evaluations/cases/memory-bridge.json`
- `evaluations/cases/obsidian-bases.json`
- `evaluations/cases/obsidian-cli.json`
- `evaluations/cases/obsidian-markdown.json`
- `evaluations/cases/qmd.json`
- `evaluations/cases/skill-evaluator.json`
- `evaluations/cases/spec-package-generator.json`
- `evaluations/cases/tag-taxonomy.json`
- `evaluations/cases/tdd.json`
- `evaluations/cases/to-spec.json`

## Agent C: operational Wiki cases

- `evaluations/cases/wiki-capture.json`
- `evaluations/cases/wiki-context-pack.json`
- `evaluations/cases/wiki-dashboard.json`
- `evaluations/cases/wiki-dedup.json`
- `evaluations/cases/wiki-history-ingest.json`
- `evaluations/cases/wiki-ingest.json`
- `evaluations/cases/wiki-lint.json`
- `evaluations/cases/wiki-query.json`
- `evaluations/cases/wiki-rebuild.json`
- `evaluations/cases/wiki-research.json`
- `evaluations/cases/wiki-setup.json`
- `evaluations/cases/wiki-status.json`
- `evaluations/cases/wiki-synthesize.json`
- `evaluations/cases/wiki-update.json`

## Case-authoring acceptance boundary

Each owner replaces mechanical scaffold prompts with concrete, Skill-specific cases
that can support a black-box correctness decision:

- normal, boundary/invalid-input, and safety/authorization-or-core cases are distinct
  and supply enough fixture context to produce an observable result;
- Explicit Skills have three realistic negative implicit-selection prompts that do
  not name or explicitly invoke the Skill;
- Implicit Skills have an independent direct prompt, genuine paraphrase, and
  nearest-Skill non-invoking boundary prompt;
- every expected outcome and assertion was defined before execution, is observable,
  and uses `deterministic`, `human-rubric`, or `trajectory` according to what is
  actually graded;
- trajectory assertions cover only mandatory correctness, authorization, safety, or
  side-effect constraints;
- no baseline comparison, automatic retry, Red Team, Shadow, or Canary behavior is
  introduced.
