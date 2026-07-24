#!/usr/bin/env python3
"""Create deterministic Skill digests and validate compact attestations."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
from typing import Any


EVALUATOR_VERSION = "myskills-skill-evaluator/1"
TARGETS = ("claude", "codex")


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
    """Return release-blocking errors for one current Skill/attestation pair."""

    skill = Path(skill_path).resolve()
    attestation = Path(attestation_path)
    errors: list[str] = []
    try:
        data: Any = json.loads(
            attestation.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{attestation}: invalid attestation: {exc}"]
    if not isinstance(data, dict):
        return [f"{attestation}: root must be an object"]

    expected_keys = {
        "$schema",
        "schema_version",
        "skill_name",
        "skill_digest",
        "source_digest",
        "evaluation_level",
        "evaluator_version",
        "evaluated_at",
        "targets",
        "human_review",
        "unavailable_capabilities",
        "status",
    }
    if set(data) != expected_keys:
        errors.append(
            f"{attestation}: fields must be exactly {sorted(expected_keys)}"
        )
    expected_digest = directory_digest(skill)
    expected_values = {
        "$schema": "../attestation.schema.json",
        "schema_version": 1,
        "skill_name": skill.name,
        "skill_digest": expected_digest,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "pass",
    }
    for field, expected in expected_values.items():
        if data.get(field) != expected:
            errors.append(
                f"{attestation}: {field} must be {expected!r}, "
                f"got {data.get(field)!r}"
            )
    if data.get("evaluation_level") not in {"snapshot-smoke", "full"}:
        errors.append(f"{attestation}: evaluation_level must be recognized")
    source_digest = data.get("source_digest")
    if source_digest is not None and not _is_digest(source_digest):
        errors.append(f"{attestation}: source_digest must be null or sha256")
    if not _is_datetime(data.get("evaluated_at")):
        errors.append(f"{attestation}: evaluated_at must be ISO 8601")

    targets = data.get("targets")
    if not isinstance(targets, dict) or set(targets) != set(TARGETS):
        errors.append(f"{attestation}: targets must be exactly claude and codex")
    else:
        for target in TARGETS:
            errors.extend(_validate_target(attestation, target, targets[target]))

    review = data.get("human_review")
    if not isinstance(review, dict):
        errors.append(f"{attestation}: human_review must be an object")
    else:
        if set(review) != {"status", "reviewer", "reviewed_at", "notes"}:
            errors.append(f"{attestation}: human_review fields are invalid")
        if review.get("status") != "pass":
            errors.append(f"{attestation}: human review must pass")
        for field in ("reviewer", "notes"):
            if not isinstance(review.get(field), str) or not review[field].strip():
                errors.append(f"{attestation}: human_review.{field} is required")
        if not _is_datetime(review.get("reviewed_at")):
            errors.append(f"{attestation}: human_review.reviewed_at must be ISO 8601")

    unavailable = data.get("unavailable_capabilities")
    if not isinstance(unavailable, list) or not all(
        isinstance(item, str) and item.strip() for item in unavailable
    ):
        errors.append(
            f"{attestation}: unavailable_capabilities must be a string array"
        )
    return errors


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
            errors.append(f"{name}: missing passing current-digest attestation")
            continue
        errors.extend(validate_attestation(skill, attestation))

    actual_names = {
        item.stem
        for item in (root / "attestations" / "skills").glob("*.json")
    }
    for extra in sorted(actual_names - expected_names):
        errors.append(f"{extra}: attestation does not name a managed Skill")
    return errors


def _validate_target(path: Path, target: str, value: object) -> list[str]:
    errors: list[str] = []
    prefix = f"{path}: targets.{target}"
    expected = {
        "status",
        "discovery",
        "explicit_invocation",
        "isolation",
        "required_cases",
        "trigger_results",
        "summary",
    }
    if not isinstance(value, dict) or set(value) != expected:
        return [f"{prefix} fields are invalid"]
    for field in ("status", "discovery", "explicit_invocation", "isolation"):
        required = "pass" if field == "status" else True
        if value.get(field) != required:
            errors.append(f"{prefix}.{field} must be {required!r}")
    for field in ("required_cases", "trigger_results"):
        count = value.get(field)
        if not isinstance(count, dict) or set(count) != {"passed", "total"}:
            errors.append(f"{prefix}.{field} must contain passed and total")
            continue
        passed, total = count.get("passed"), count.get("total")
        if (
            not isinstance(passed, int)
            or not isinstance(total, int)
            or total < 1
            or passed != total
        ):
            errors.append(f"{prefix}.{field} must be a non-empty full pass")
    if not isinstance(value.get("summary"), str) or not value["summary"].strip():
        errors.append(f"{prefix}.summary is required")
    return errors


def _is_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(char in "0123456789abcdef" for char in suffix)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
