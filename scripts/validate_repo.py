#!/usr/bin/env python3
"""Validate repository-wide Managed Skill packaging contracts."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

from inventory_loader import InventoryValidationError, load_inventory


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".jsonl",
    ".ps1",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
FORMER_RUNTIME_REFERENCES = (
    "$OBSIDIAN_WIKI_REPO",
    "%OBSIDIAN_WIKI_REPO%",
)


def _relative_skill_path(root: Path, category: str, name: str) -> str:
    return f"./{(Path('skills') / category / name).as_posix()}"


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"Cannot load {path.relative_to(path.parents[1])}: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name} must contain a JSON object")
        return {}
    return value


def _validate_attestations(root: Path) -> list[str]:
    module_path = root / "tools" / "skill-evaluator" / "attestations.py"
    spec = importlib.util.spec_from_file_location(
        "myskills_attestations",
        module_path,
    )
    if spec is None or spec.loader is None:
        return [f"Cannot load attestation validator: {module_path}"]
    module = importlib.util.module_from_spec(spec)
    tool_path = str(module_path.parent)
    sys.path.insert(0, tool_path)
    try:
        spec.loader.exec_module(module)
    finally:
        if sys.path[0] == tool_path:
            sys.path.pop(0)
    return module.validate_repository(root)


def validate_repository(
    root: Path = ROOT,
    *,
    require_attestations: bool = True,
) -> list[str]:
    """Return all repository contract violations."""

    errors: list[str] = []
    try:
        inventory = load_inventory(root / "inventory" / "skills.json")
    except InventoryValidationError as error:
        return [f"Invalid inventory: {message}" for message in error.errors]

    managed = sorted(
        (skill for skill in inventory["skills"] if skill["state"] == "managed"),
        key=lambda skill: (skill["category"], skill["managed_name"]),
    )
    expected_paths = [
        _relative_skill_path(root, skill["category"], skill["managed_name"])
        for skill in managed
    ]
    expected_by_name = {skill["managed_name"]: skill for skill in managed}

    skills_root = root / "skills"
    skill_dirs = sorted(path.parent for path in skills_root.rglob("SKILL.md"))
    discovered_paths = [
        f"./{path.relative_to(root).as_posix()}" for path in skill_dirs
    ]
    if discovered_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(discovered_paths))
        unexpected = sorted(set(discovered_paths) - set(expected_paths))
        if missing:
            errors.append(f"Missing Managed Skill directories: {', '.join(missing)}")
        if unexpected:
            errors.append(f"Unexpected installable Skill directories: {', '.join(unexpected)}")

    package = _load_json(root / "package.json", errors)
    plugin = _load_json(root / ".claude-plugin" / "plugin.json", errors)
    for manifest_name, actual in (
        ("package.json", package.get("skills", [])),
        (".claude-plugin/plugin.json", plugin.get("skills", [])),
    ):
        if actual != expected_paths:
            errors.append(
                f"{manifest_name} skills do not match the Managed Skill inventory: "
                f"expected {expected_paths}, got {actual}"
            )

    try:
        readme = (root / "README.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"Cannot read README.md: {error}")
        readme = ""
    for expected_path in expected_paths:
        skill_link = f"{expected_path.removeprefix('./')}/SKILL.md"
        if skill_link not in readme:
            errors.append(f"README.md does not link Managed Skill {skill_link}")

    names: set[str] = set()
    for skill_dir in skill_dirs:
        relative_dir = skill_dir.relative_to(root)
        skill_md_path = skill_dir / "SKILL.md"
        try:
            skill_md = skill_md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"Cannot read {relative_dir.as_posix()}/SKILL.md: {error}")
            continue

        name_match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", skill_md)
        description_match = re.search(r"(?m)^description:\s*.+$", skill_md)
        if not name_match:
            errors.append(f"Invalid or missing name in {relative_dir.as_posix()}/SKILL.md")
            continue
        if not description_match:
            errors.append(
                f"Invalid or missing description in {relative_dir.as_posix()}/SKILL.md"
            )

        name = name_match.group(1)
        if name != skill_dir.name:
            errors.append(f"Skill name {name!r} does not match folder {skill_dir.name!r}")
        if name in names:
            errors.append(f"Duplicate skill name: {name}")
        names.add(name)

        record = expected_by_name.get(name)
        if record is None:
            continue
        expected_dir = Path("skills") / record["category"] / name
        if relative_dir != expected_dir:
            errors.append(
                f"Skill {name} is in {relative_dir.as_posix()}, expected "
                f"{expected_dir.as_posix()}"
            )

        metadata_path = skill_dir / "agents" / "openai.yaml"
        if not metadata_path.is_file():
            errors.append(f"Missing {metadata_path.relative_to(root).as_posix()}")
            continue
        try:
            openai_yaml = metadata_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(
                f"Cannot read {metadata_path.relative_to(root).as_posix()}: {error}"
            )
            continue

        claude_manual = bool(
            re.search(r"(?m)^disable-model-invocation:\s*true\s*$", skill_md)
        )
        policy_match = re.search(
            r"(?m)^\s*allow_implicit_invocation:\s*(true|false)\s*$",
            openai_yaml,
        )
        if not policy_match:
            errors.append(f"Missing Codex invocation policy for {name}")
        else:
            codex_implicit = policy_match.group(1) == "true"
            expected_implicit = record["invocation"] == "implicit"
            if codex_implicit != expected_implicit:
                errors.append(
                    f"Codex invocation policy for {name} is "
                    f"{'implicit' if codex_implicit else 'explicit'}, expected "
                    f"{record['invocation']}"
                )
        expected_manual = record["invocation"] == "explicit"
        if claude_manual != expected_manual:
            errors.append(
                f"Claude invocation policy for {name} is "
                f"{'explicit' if claude_manual else 'implicit'}, expected "
                f"{record['invocation']}"
            )
        if f"${name}" not in openai_yaml:
            errors.append(f"default_prompt does not explicitly mention ${name}")

        for path in skill_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            for forbidden in FORMER_RUNTIME_REFERENCES:
                if forbidden in content:
                    errors.append(
                        f"Former source runtime reference {forbidden!r} remains in "
                        f"{path.relative_to(root).as_posix()}"
                    )

    imported_dates = {
        skill.get("imported_on")
        for skill in managed
    }
    if None in imported_dates:
        errors.append("Every Managed Skill must record imported_on provenance")

    if require_attestations:
        errors.extend(_validate_attestations(root))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="Skip the release attestation gate while authoring.",
    )
    args = parser.parse_args()
    errors = validate_repository(require_attestations=not args.structural_only)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    inventory = load_inventory(ROOT / "inventory" / "skills.json")
    names = sorted(
        skill["managed_name"]
        for skill in inventory["skills"]
        if skill["state"] == "managed"
    )
    scope = "structural contracts" if args.structural_only else "release contracts"
    print(
        f"Validated {len(names)} Managed Skill(s) ({scope}): "
        f"{', '.join(names)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
