#!/usr/bin/env python3
"""Validate MySkills manifests, metadata, and invocation policy."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    skill_dirs = sorted(path.parent for path in SKILLS_ROOT.rglob("SKILL.md"))
    relative_skills = [f"./{path.relative_to(ROOT).as_posix()}" for path in skill_dirs]

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    plugin = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    for manifest_name, actual in (
        ("package.json", package.get("skills", [])),
        (".claude-plugin/plugin.json", plugin.get("skills", [])),
    ):
        if actual != relative_skills:
            fail(
                f"{manifest_name} skills do not match discovered skills: "
                f"expected {relative_skills}, got {actual}",
                errors,
            )

    names: set[str] = set()
    for skill_dir in skill_dirs:
        skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = skill_dir / "agents" / "openai.yaml"
        if not metadata.is_file():
            fail(f"Missing {metadata.relative_to(ROOT)}", errors)
            continue

        name_match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", skill_md)
        if not name_match:
            fail(f"Invalid or missing name in {skill_dir.relative_to(ROOT)}/SKILL.md", errors)
            continue

        name = name_match.group(1)
        if name != skill_dir.name:
            fail(f"Skill name {name!r} does not match folder {skill_dir.name!r}", errors)
        if name in names:
            fail(f"Duplicate skill name: {name}", errors)
        names.add(name)

        openai_yaml = metadata.read_text(encoding="utf-8")
        claude_manual = bool(
            re.search(r"(?m)^disable-model-invocation:\s*true\s*$", skill_md)
        )
        codex_manual = bool(
            re.search(
                r"(?ms)^policy:\s*\n(?:[ \t]+.*\n)*?"
                r"[ \t]+allow_implicit_invocation:\s*false\s*$",
                openai_yaml,
            )
        )
        if claude_manual != codex_manual:
            fail(
                f"Invocation policy mismatch for {name}: "
                f"Claude manual={claude_manual}, Codex manual={codex_manual}",
                errors,
            )
        if f"$" + name not in openai_yaml:
            fail(f"default_prompt does not explicitly mention ${name}", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(skill_dirs)} skill(s): {', '.join(sorted(names))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
