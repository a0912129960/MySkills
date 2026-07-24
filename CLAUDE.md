# Repository instructions

Skills live under `skills/<bucket>/<skill-name>/`.

Every skill must contain:

- `SKILL.md`;
- `agents/openai.yaml`;
- matching invocation policy for Claude Code and Codex.

A human-only skill uses both:

- `disable-model-invocation: true` in `SKILL.md`;
- `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.

Keep `README.md`, `.claude-plugin/plugin.json`, and `package.json` synchronized with all
installable skills. Run `python scripts/validate_repo.py` and the unit tests after changes.
