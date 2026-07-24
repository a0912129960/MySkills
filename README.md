# MySkills

Personal, installable Agent Skills for Codex, Claude Code, and compatible harnesses.

## Skills

### User-invoked

- [`ai-handoff`](skills/productivity/ai-handoff/SKILL.md) — create a controlled
  cross-session handoff or a reusable prompt for another AI.

### Model-invoked

None.

## Install

Install all skills into the standard local harness directories:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

The default mode copies skills to:

- `~\.agents\skills` for Codex and Agent Skills-compatible tools;
- `~\.claude\skills` for Claude Code.

Use development junctions instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Mode Junction
```

The repository can also be consumed by installers that understand the `skills` array in
`package.json`, or as a Claude Code plugin through `.claude-plugin/plugin.json`.

## Validate

```powershell
python .\scripts\validate_repo.py
python -m unittest discover -s .\tests -v
```

## Invoke

This first skill is intentionally human-controlled:

```text
$ai-handoff Create a prompt for another AI to audit C:\project\example.
```
