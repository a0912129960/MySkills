# Repository instructions

Skills live under `skills/<bucket>/<skill-name>/`.

Every skill must contain:

- `SKILL.md`;
- `agents/openai.yaml`;
- matching invocation policy for Claude Code and Codex.

A human-only skill uses both:

- `disable-model-invocation: true` in `SKILL.md`;
- `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.

Create a scaffold with `scripts/new-skill.ps1`, then add it to the authoritative inventory and
shared manifests. The model-evaluation architecture is preserved but disabled by default:
do not run Claude/Codex evaluation, require an evaluation record, or require a release pointer
unless the human explicitly requests that diagnostic workflow and its model-call budget.
Raw evaluation runs belong under ignored `.scratch/skill-evals/`; retained historical records
remain append-only.

Skill provenance and installation targets live only in `inventory/skills.json`; do not add
per-Skill provenance files or duplicate central dependency policy in `SKILL.md`.

Keep `README.md`, `.claude-plugin/plugin.json`, and `package.json` synchronized with all
installable skills. Run `python scripts/validate_inventory.py`,
`python scripts/validate_repo.py`, and `python scripts/run_tests.py` after changes.
`python scripts/validate_repo.py --require-evaluations` is an explicit opt-in diagnostic gate,
not a default completion or release requirement.
