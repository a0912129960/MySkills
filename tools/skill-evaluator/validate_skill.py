#!/usr/bin/env python3
"""Validate a canonical MySkills Skill through its public file contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by installer preflight
    yaml = None


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((?!https?://|#)([^)]+)\)")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _load_yaml(text: str, source: str, errors: list[str]) -> dict[str, Any]:
    if yaml is None:
        errors.append("PyYAML is unavailable in the evaluator environment")
        return {}
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        errors.append(f"{source} is not valid YAML: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{source} must contain a YAML mapping")
        return {}
    return value


def validate_skill(skill_path: Path | str) -> dict[str, Any]:
    """Return a JSON-serializable structural validation result."""

    skill_dir = Path(skill_path).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skill_md_path = skill_dir / "SKILL.md"
    openai_path = skill_dir / "agents" / "openai.yaml"

    if not skill_md_path.is_file():
        errors.append("SKILL.md is missing")
        return {
            "skill_path": str(skill_dir),
            "skill_name": skill_dir.name,
            "valid": False,
            "errors": errors,
            "warnings": warnings,
        }

    skill_md = skill_md_path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(skill_md)
    metadata: dict[str, Any] = {}
    if not match:
        errors.append("SKILL.md is missing YAML frontmatter")
    else:
        metadata = _load_yaml(match.group(1), "SKILL.md frontmatter", errors)

    skill_name = metadata.get("name")
    if not isinstance(skill_name, str) or not NAME.fullmatch(skill_name):
        errors.append("SKILL.md name must be a kebab-case identifier")
        skill_name = skill_dir.name
    elif skill_name != skill_dir.name:
        errors.append(
            f"SKILL.md name {skill_name!r} does not match folder {skill_dir.name!r}"
        )

    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("SKILL.md description must be a non-empty string")

    openai: dict[str, Any] = {}
    if not openai_path.is_file():
        errors.append("agents/openai.yaml is missing")
    else:
        openai = _load_yaml(
            openai_path.read_text(encoding="utf-8"), "agents/openai.yaml", errors
        )

    interface = openai.get("interface")
    if not isinstance(interface, dict):
        errors.append("agents/openai.yaml interface must be a mapping")
    else:
        default_prompt = interface.get("default_prompt")
        if not isinstance(default_prompt, str) or f"${skill_name}" not in default_prompt:
            errors.append(
                f"agents/openai.yaml default_prompt must explicitly mention ${skill_name}"
            )

    claude_explicit = metadata.get("disable-model-invocation") is True
    policy = openai.get("policy", {})
    codex_explicit = (
        isinstance(policy, dict)
        and policy.get("allow_implicit_invocation") is False
    )
    if claude_explicit != codex_explicit:
        errors.append(
            "Claude and Codex invocation policies disagree "
            f"(Claude explicit={claude_explicit}, Codex explicit={codex_explicit})"
        )

    for link in MARKDOWN_LINK.findall(skill_md):
        relative = link.split("#", 1)[0]
        if relative and not (skill_dir / relative).is_file():
            errors.append(f"SKILL.md references a missing local file: {relative}")

    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".ps1"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"{path.relative_to(skill_dir)} is not valid UTF-8")
            continue
        if "C:\\project\\LLM Wiki" in text or "$OBSIDIAN_WIKI_REPO" in text:
            errors.append(
                f"{path.relative_to(skill_dir)} contains a former source runtime path"
            )

    return {
        "skill_path": str(skill_dir),
        "skill_name": skill_name,
        "invocation": "explicit" if claude_explicit else "implicit",
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    result = validate_skill(args.skill_path)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["valid"] else "FAIL"
        print(f"{status}: {result['skill_name']}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
