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
shared manifests. Every new or substantively changed Managed Skill must be evaluated with the
MySkills-managed `skill-evaluator`; do not report the work complete until the current directory
digest has a passing source-controlled attestation for both Claude Code and Codex. Raw
evaluation runs belong under ignored `.scratch/skill-evals/`.

Skill provenance and installation targets live only in `inventory/skills.json`; do not add
per-Skill provenance files or duplicate central dependency policy in `SKILL.md`.

Keep `README.md`, `.claude-plugin/plugin.json`, and `package.json` synchronized with all
installable skills. Run `python scripts/validate_inventory.py`,
`python scripts/validate_repo.py`, and `python scripts/run_tests.py` after changes.
