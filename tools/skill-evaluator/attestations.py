#!/usr/bin/env python3
"""Create deterministic Skill digests and validate release record pointers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
from typing import Any

import evaluation_records


TARGETS = ("claude", "codex")
RELEASE_POINTER_SCHEMA_VERSION = 3
RELEASE_POINTER_FIELDS = {
    "$schema",
    "schema_version",
    "skill_name",
    "skill_digest",
    "record_path",
    "record_digest",
    "selected_at",
    "status",
}


def directory_digest(path: Path | str) -> str:
    """Match scripts/installer_core.psm1 Get-DirectoryDigest byte-for-byte."""

    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Skill directory does not exist: {root}")
    digest = hashlib.sha256()
    files = sorted(item for item in root.rglob("*") if item.is_file())
    for item in files:
        relative = item.relative_to(root).as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(struct.pack("<i", len(relative)))
        digest.update(relative)
        digest.update(struct.pack("<q", len(content)))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def file_digest(path: Path | str) -> str:
    """Return the SHA-256 digest of one exact evidence file."""

    return f"sha256:{hashlib.sha256(Path(path).read_bytes()).hexdigest()}"


def build_release_pointer(
    repo_root: Path | str,
    skill_path: Path | str,
    record_path: Path | str,
    *,
    selected_at: str | None = None,
) -> dict[str, Any]:
    """Build a release pointer for one passing current-digest record."""

    root = Path(repo_root).resolve()
    skill = Path(skill_path).resolve()
    record_file = Path(record_path).resolve()
    record = evaluation_records.load_record(root, record_file)
    errors = _record_release_errors(skill, record)
    if errors:
        raise ValueError("\n".join(errors))
    timestamp = selected_at or datetime.now(timezone.utc).isoformat()
    if not _is_datetime(timestamp):
        raise ValueError("release pointer selected_at must be ISO 8601")
    return {
        "$schema": "../attestation.schema.json",
        "schema_version": RELEASE_POINTER_SCHEMA_VERSION,
        "skill_name": skill.name,
        "skill_digest": directory_digest(skill),
        "record_path": record_file.relative_to(root).as_posix(),
        "record_digest": file_digest(record_file),
        "selected_at": timestamp,
        "status": "pass",
    }


def write_release_pointer(
    repo_root: Path | str,
    skill_path: Path | str,
    record_path: Path | str,
    *,
    selected_at: str | None = None,
) -> Path:
    """Atomically select one passing record as the current release evidence."""

    root = Path(repo_root).resolve()
    skill = Path(skill_path).resolve()
    try:
        skill.relative_to(root / "skills")
    except ValueError as error:
        raise ValueError("release Skill must be inside repository skills/") from error
    pointer = build_release_pointer(
        root,
        skill,
        record_path,
        selected_at=selected_at,
    )
    destination = root / "attestations" / "skills" / f"{skill.name}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{skill.name}-",
        dir=destination.parent,
        ignore_cleanup_errors=True,
    ) as temp_dir:
        temporary = Path(temp_dir) / destination.name
        temporary.write_text(
            json.dumps(pointer, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, destination)
    return destination


def validate_release_pointer(
    repo_root: Path | str,
    skill_path: Path | str,
    pointer_path: Path | str,
) -> list[str]:
    """Validate one v3 release pointer and its referenced Git evidence."""

    root = Path(repo_root).resolve()
    skill = Path(skill_path).resolve()
    pointer_file = Path(pointer_path)
    prefix = str(pointer_file)
    try:
        data: Any = json.loads(
            pointer_file.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return [f"{prefix}: invalid release pointer: {error}"]
    if not isinstance(data, dict) or set(data) != RELEASE_POINTER_FIELDS:
        return [f"{prefix}: release pointer fields are invalid"]

    errors: list[str] = []
    expected = {
        "$schema": "../attestation.schema.json",
        "schema_version": RELEASE_POINTER_SCHEMA_VERSION,
        "skill_name": skill.name,
        "skill_digest": directory_digest(skill),
        "status": "pass",
    }
    for field, value in expected.items():
        if data.get(field) != value:
            if field == "skill_digest":
                errors.append(
                    f"{prefix}: skill_digest does not match current Skill"
                )
            else:
                errors.append(
                    f"{prefix}: {field} must be {value!r}, "
                    f"got {data.get(field)!r}"
                )
    if not _is_datetime(data.get("selected_at")):
        errors.append(f"{prefix}: selected_at must be ISO 8601")
    record_relative = data.get("record_path")
    if (
        not isinstance(record_relative, str)
        or "\\" in record_relative
        or Path(record_relative).is_absolute()
    ):
        errors.append(f"{prefix}: record_path is invalid")
        return errors
    record_file = (root / record_relative).resolve()
    try:
        record_file.relative_to(root)
    except ValueError:
        errors.append(f"{prefix}: record_path escapes the repository")
        return errors
    try:
        record = evaluation_records.load_record(root, record_file)
    except ValueError as error:
        errors.append(f"{prefix}: referenced record is invalid: {error}")
        return errors
    errors.extend(
        f"{prefix}: {error}"
        for error in _record_release_errors(skill, record)
    )
    if data.get("record_path") != record_file.relative_to(root).as_posix():
        errors.append(f"{prefix}: record_path is not canonical")
    try:
        actual_record_digest = file_digest(record_file)
    except OSError as error:
        errors.append(f"{prefix}: cannot digest referenced record: {error}")
    else:
        if data.get("record_digest") != actual_record_digest:
            errors.append(f"{prefix}: record_digest does not match record.json")
    return errors


def _record_release_errors(
    skill: Path,
    record: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    digest = directory_digest(skill)
    if record.get("skill_name") != skill.name:
        errors.append("record skill_name does not match Skill")
    if record.get("skill_digest") != digest:
        errors.append("record skill_digest does not match current Skill")
    if record.get("status") != "pass":
        errors.append("release record status must be pass")
    targets = record.get("targets")
    if not isinstance(targets, dict) or any(
        not isinstance(targets.get(target), dict)
        or targets[target].get("status") != "pass"
        for target in TARGETS
    ):
        errors.append("release record requires passing Claude and Codex targets")
    return errors


def _is_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_attestation(
    skill_path: Path | str,
    attestation_path: Path | str,
) -> list[str]:
    """Validate the public v3 release pointer contract."""

    pointer = Path(attestation_path).resolve()
    if len(pointer.parents) < 3:
        return [f"{pointer}: cannot derive repository root"]
    return validate_release_pointer(pointer.parents[2], skill_path, pointer)


def validate_repository(repo_root: Path | str) -> list[str]:
    """Require one current passing attestation for every managed Skill."""

    root = Path(repo_root).resolve()
    inventory = json.loads(
        (root / "inventory" / "skills.json").read_text(encoding="utf-8")
    )
    errors: list[str] = []
    expected_names: set[str] = set()
    for item in inventory["skills"]:
        if item["state"] != "managed":
            continue
        name = item["managed_name"]
        expected_names.add(name)
        skill = root / "skills" / item["category"] / name
        attestation = root / "attestations" / "skills" / f"{name}.json"
        if not attestation.is_file():
            errors.append(
                f"{name}: missing passing current-digest release pointer"
            )
            continue
        errors.extend(validate_release_pointer(root, skill, attestation))

    actual_names = {
        item.stem
        for item in (root / "attestations" / "skills").glob("*.json")
    }
    for extra in sorted(actual_names - expected_names):
        errors.append(f"{extra}: release pointer does not name a managed Skill")
    return errors


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
