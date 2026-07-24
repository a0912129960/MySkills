#!/usr/bin/env python3
"""Validate evaluation cases and construct a deterministic batch run plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
from typing import Any, Iterable


TARGETS = ("claude", "codex")
CONFIGURATIONS = ("with_skill", "baseline")


def load_cases(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    path = root / "evaluations" / "cases.json"
    document = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    errors = validate_cases(root, document)
    if errors:
        raise ValueError("\n".join(errors))
    return document


def validate_cases(repo_root: Path | str, document: object) -> list[str]:
    root = Path(repo_root).resolve()
    errors: list[str] = []
    if not isinstance(document, dict) or set(document) != {
        "$schema",
        "schema_version",
        "skills",
    }:
        return ["evaluation cases root fields are invalid"]
    if document.get("$schema") != "./cases.schema.json":
        errors.append("evaluation cases $schema is invalid")
    if document.get("schema_version") != 1:
        errors.append("evaluation cases schema_version must be 1")
    skills = document.get("skills")
    if not isinstance(skills, list):
        return errors + ["evaluation cases skills must be an array"]

    inventory = json.loads(
        (root / "inventory" / "skills.json").read_text(encoding="utf-8")
    )
    managed = {
        item["managed_name"]: item
        for item in inventory["skills"]
        if item["state"] == "managed"
    }
    seen: set[str] = set()
    for index, entry in enumerate(skills):
        location = f"skills[{index}]"
        if not isinstance(entry, dict) or set(entry) != {
            "skill_name",
            "evaluation_level",
            "baseline",
            "required_cases",
            "trigger_cases",
        }:
            errors.append(f"{location} fields are invalid")
            continue
        name = entry.get("skill_name")
        if not isinstance(name, str) or name not in managed:
            errors.append(f"{location}.skill_name is not a managed Skill")
            continue
        if name in seen:
            errors.append(f"{location}.skill_name is duplicated: {name}")
        seen.add(name)
        if entry.get("evaluation_level") != "full":
            errors.append(f"{name}: consolidated Skills require full evaluation")
        baseline = entry.get("baseline")
        if (
            not isinstance(baseline, dict)
            or set(baseline) != {"kind", "identity"}
            or baseline.get("kind") not in {"no-skill", "previous-version"}
            or not _nonempty(baseline.get("identity"))
        ):
            errors.append(f"{name}: baseline is invalid")
        errors.extend(
            _validate_required_cases(
                name,
                entry.get("required_cases"),
                set(managed),
            )
        )
        errors.extend(
            _validate_trigger_cases(
                name,
                entry.get("trigger_cases"),
                managed[name]["invocation"],
            )
        )
    missing = sorted(set(managed) - seen)
    extra = sorted(seen - set(managed))
    if missing:
        errors.append(f"missing evaluation cases: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected evaluation cases: {', '.join(extra)}")
    return errors


def build_plan(
    repo_root: Path | str,
    document: dict[str, Any],
    selected_skills: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    root = Path(repo_root).resolve()
    selected = set(selected_skills or ())
    entries = {
        entry["skill_name"]: entry
        for entry in document["skills"]
    }
    if selected:
        unknown = sorted(selected - set(entries))
        if unknown:
            raise ValueError(f"unknown evaluation Skill(s): {', '.join(unknown)}")
    else:
        selected = set(entries)

    inventory = json.loads(
        (root / "inventory" / "skills.json").read_text(encoding="utf-8")
    )
    paths = {
        item["managed_name"]: (
            root / "skills" / item["category"] / item["managed_name"]
        )
        for item in inventory["skills"]
        if item["state"] == "managed"
    }
    digest_cache: dict[str, str] = {}

    def skill_digest(name: str) -> str:
        if name not in digest_cache:
            digest_cache[name] = _directory_digest(paths[name])
        return digest_cache[name]

    plan: list[dict[str, Any]] = []
    for name in sorted(selected):
        entry = entries[name]
        for case in entry["required_cases"]:
            for configuration in CONFIGURATIONS:
                for target in TARGETS:
                    plan.append(
                        _plan_item(
                            name,
                            paths[name],
                            case,
                            target,
                            configuration,
                            evaluation_level=entry["evaluation_level"],
                            baseline=entry["baseline"],
                            skill_digest=skill_digest(name),
                            companion_skill_paths={
                                companion: paths[companion]
                                for companion in case.get(
                                    "companion_skills",
                                    [],
                                )
                            },
                            companion_skill_digests={
                                companion: skill_digest(companion)
                                for companion in case.get(
                                    "companion_skills",
                                    [],
                                )
                            },
                            mode="required",
                            explicit=configuration == "with_skill",
                        )
                    )
        for case in entry["trigger_cases"]:
            for configuration in CONFIGURATIONS:
                for target in TARGETS:
                    plan.append(
                        _plan_item(
                            name,
                            paths[name],
                            case,
                            target,
                            configuration,
                            evaluation_level=entry["evaluation_level"],
                            baseline=entry["baseline"],
                            skill_digest=skill_digest(name),
                            companion_skill_paths={},
                            companion_skill_digests={},
                            mode="trigger",
                            explicit=False,
                        )
                    )
    return plan


def summarize_plan(plan: list[dict[str, Any]]) -> dict[str, Any]:
    skills = sorted({item["skill_name"] for item in plan})
    return {
        "schema_version": 1,
        "skill_count": len(skills),
        "model_run_count": len(plan),
        "targets": list(TARGETS),
        "configurations": list(CONFIGURATIONS),
        "skills": skills,
        "runs": plan,
    }


def prepare_review_templates(
    workspace: Path | str,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create explicit failing-until-reviewed grading files for raw batch runs."""

    root = Path(workspace).resolve()
    results = sorted(root.rglob("result.json"))
    created: list[str] = []
    preserved: list[str] = []
    for result_path in results:
        record = json.loads(result_path.read_text(encoding="utf-8"))
        plan = record.get("plan")
        if not isinstance(plan, dict):
            raise ValueError(f"{result_path}: missing batch plan")
        grading_path = result_path.with_name("grading.json")
        if grading_path.exists() and not overwrite:
            preserved.append(str(grading_path))
            continue
        assertions = _grading_assertions(plan)
        grading = {
            "expectations": [
                {
                    "text": assertion,
                    "passed": False,
                    "evidence": "PENDING HUMAN REVIEW",
                }
                for assertion in assertions
            ]
        }
        grading_path.write_text(
            json.dumps(grading, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created.append(str(grading_path))
    index = {
        "schema_version": 1,
        "workspace": str(root),
        "raw_result_count": len(results),
        "created_grading_count": len(created),
        "preserved_grading_count": len(preserved),
        "created": created,
        "preserved": preserved,
        "status": "PENDING_HUMAN_REVIEW",
    }
    (root / "review-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index


def audit_reviewed_skill(
    repo_root: Path | str,
    workspace: Path | str,
    document: dict[str, Any],
    skill_name: str,
) -> dict[str, Any]:
    """Verify one complete batch slice before creating an attestation draft."""

    repo = Path(repo_root).resolve()
    root = Path(workspace).resolve()
    try:
        relative_root = root.relative_to(repo).as_posix()
    except ValueError as error:
        raise ValueError(
            f"{root}: review workspace must be inside the repository"
        ) from error
    if not relative_root.startswith(".scratch/skill-evals/"):
        raise ValueError(
            f"{root}: review workspace must be below .scratch/skill-evals/"
        )

    expected = build_plan(repo, document, [skill_name])
    skill_root = root / skill_name
    errors: list[str] = []
    identities: dict[str, set[str]] = {target: set() for target in TARGETS}
    durations: dict[str, list[int]] = {target: [] for target in TARGETS}
    token_counts: dict[str, list[int | None]] = {
        target: [] for target in TARGETS
    }
    assertion_count = 0
    expected_result_paths: set[Path] = set()

    for item in expected:
        run_root = (
            skill_root
            / item["case_id"]
            / item["configuration"]
            / item["target"]
        )
        result_path = run_root / "result.json"
        grading_path = run_root / "grading.json"
        if result_path in expected_result_paths:
            errors.append(f"{result_path}: evaluation case path is duplicated")
            continue
        expected_result_paths.add(result_path)
        if not result_path.is_file():
            errors.append(f"{result_path}: raw result is missing")
            continue
        if not grading_path.is_file():
            errors.append(f"{grading_path}: reviewed grading is missing")
            continue
        try:
            record = json.loads(
                result_path.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
            grading = json.loads(
                grading_path.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{run_root}: invalid review artifact: {error}")
            continue

        if not isinstance(record, dict) or record.get("plan") != item:
            errors.append(f"{result_path}: batch plan does not match the manifest")
            continue
        identity = record.get("target_identity")
        if (
            record.get("target_identity_returncode") != 0
            or not _nonempty(identity)
        ):
            errors.append(f"{result_path}: target identity check did not pass")
        else:
            identities[item["target"]].add(identity.strip())

        result = record.get("result")
        if not isinstance(result, dict):
            errors.append(f"{result_path}: process result is missing")
            continue
        if result.get("returncode") != 0 or result.get("timed_out") is not False:
            errors.append(f"{result_path}: model process did not pass")
        duration = result.get("duration_ms")
        if not isinstance(duration, int) or duration < 0:
            errors.append(f"{result_path}: duration_ms is invalid")
        else:
            durations[item["target"]].append(duration)
        tokens = result.get("total_tokens")
        if tokens is not None and (
            not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0
        ):
            errors.append(f"{result_path}: total_tokens is invalid")
        else:
            token_counts[item["target"]].append(tokens)

        expected_assertions = _grading_assertions(item)
        expectations = (
            grading.get("expectations")
            if isinstance(grading, dict)
            else None
        )
        if not isinstance(expectations, list) or len(expectations) != len(
            expected_assertions
        ):
            errors.append(f"{grading_path}: expectations do not match the plan")
            continue
        for expected_text, grade in zip(expected_assertions, expectations):
            if not isinstance(grade, dict) or set(grade) != {
                "text",
                "passed",
                "evidence",
            }:
                errors.append(f"{grading_path}: grading fields are invalid")
                continue
            if grade.get("text") != expected_text:
                errors.append(f"{grading_path}: expectation text was changed")
            if grade.get("passed") is not True:
                errors.append(f"{grading_path}: every expectation must pass")
            evidence = grade.get("evidence")
            if (
                not _nonempty(evidence)
                or evidence.strip() == "PENDING HUMAN REVIEW"
            ):
                errors.append(f"{grading_path}: reviewed evidence is required")
        assertion_count += len(expectations)

    actual_results = set(skill_root.rglob("result.json")) if skill_root.exists() else set()
    for extra in sorted(actual_results - expected_result_paths):
        errors.append(f"{extra}: raw result is not part of the current plan")
    for target, values in identities.items():
        if len(values) != 1:
            errors.append(
                f"{skill_name}: {target} target identity must be consistent"
            )
    if errors:
        raise ValueError("\n".join(errors))

    targets: dict[str, dict[str, Any]] = {}
    efficiency: dict[str, dict[str, int | None]] = {}
    for target in TARGETS:
        required_total = sum(
            1
            for item in expected
            if item["target"] == target
            and item["mode"] == "required"
            and item["configuration"] == "with_skill"
        )
        trigger_total = sum(
            1
            for item in expected
            if item["target"] == target
            and item["mode"] == "trigger"
            and item["configuration"] == "with_skill"
        )
        targets[target] = {
            "status": "pass",
            "discovery": True,
            "explicit_invocation": True,
            "isolation": True,
            "required_cases": {
                "passed": required_total,
                "total": required_total,
            },
            "trigger_results": {
                "passed": trigger_total,
                "total": trigger_total,
            },
            "summary": (
                f"{len(durations[target])} isolated processes and reviewed "
                "gradings passed."
            ),
        }
        observed_tokens = token_counts[target]
        efficiency[target] = {
            "duration_ms": sum(durations[target]),
            "total_tokens": (
                sum(item for item in observed_tokens if item is not None)
                if observed_tokens and all(item is not None for item in observed_tokens)
                else None
            ),
        }

    entry = next(
        item for item in document["skills"] if item["skill_name"] == skill_name
    )
    return {
        "skill_name": skill_name,
        "skill_path": expected[0]["skill_path"],
        "evaluation_level": entry["evaluation_level"],
        "baseline": dict(entry["baseline"]),
        "raw_run_root": relative_root,
        "assertion_count": assertion_count,
        "target_identities": {
            target: next(iter(identities[target])) for target in TARGETS
        },
        "targets": targets,
        "efficiency": efficiency,
    }


def _grading_assertions(plan: dict[str, Any]) -> list[str]:
    assertions = list(plan.get("assertions") or ())
    if plan.get("mode") == "trigger":
        expected = plan.get("expected_invocation")
        configuration = plan.get("configuration")
        if configuration == "with_skill":
            assertions = [
                f"Target behavior matches {expected} invocation policy"
            ]
        else:
            assertions = [
                "No-Skill baseline contains no evidence of the evaluated Skill"
            ]
    if not assertions:
        assertions = ["Run satisfies the declared case contract"]
    return assertions


def _plan_item(
    name: str,
    skill_path: Path,
    case: dict[str, Any],
    target: str,
    configuration: str,
    *,
    evaluation_level: str,
    baseline: dict[str, str],
    skill_digest: str,
    companion_skill_paths: dict[str, Path],
    companion_skill_digests: dict[str, str],
    mode: str,
    explicit: bool,
) -> dict[str, Any]:
    return {
        "skill_name": name,
        "skill_path": str(skill_path),
        "case_id": case["id"],
        "mode": mode,
        "target": target,
        "configuration": configuration,
        "evaluation_level": evaluation_level,
        "baseline": dict(baseline),
        "skill_digest": skill_digest,
        "fixtures": list(case.get("fixtures", [])),
        "companion_skills": list(companion_skill_paths),
        "companion_skill_paths": [
            str(path) for path in companion_skill_paths.values()
        ],
        "companion_skill_digests": dict(companion_skill_digests),
        "explicit": explicit,
        "prompt": case["prompt"],
        "assertions": case.get("assertions", []),
        "safety": case.get("safety", "read-only"),
        "expected_invocation": case.get("expected_invocation"),
    }


def _validate_required_cases(
    name: str,
    value: object,
    managed_names: set[str],
) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{name}: required_cases must be non-empty"]
    errors: list[str] = []
    seen: set[str] = set()
    for case in value:
        required_fields = {
            "id",
            "prompt",
            "assertions",
            "safety",
        }
        optional_fields = {"fixtures", "companion_skills"}
        if (
            not isinstance(case, dict)
            or not required_fields.issubset(case)
            or not set(case).issubset(required_fields | optional_fields)
        ):
            errors.append(f"{name}: required case fields are invalid")
            continue
        case_id = case.get("id")
        if not _nonempty(case_id) or case_id in seen:
            errors.append(f"{name}: required case id is invalid or duplicated")
        seen.add(case_id)
        if not _nonempty(case.get("prompt")) or len(case["prompt"]) < 20:
            errors.append(f"{name}/{case_id}: prompt is too short")
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions or not all(
            _nonempty(item) for item in assertions
        ):
            errors.append(f"{name}/{case_id}: assertions must be non-empty")
        if case.get("safety") not in {"read-only", "temporary-workspace"}:
            errors.append(f"{name}/{case_id}: safety is invalid")
        fixtures = case.get("fixtures", [])
        if not isinstance(fixtures, list) or not all(
            _valid_fixture(item) for item in fixtures
        ):
            errors.append(f"{name}/{case_id}: fixtures are invalid")
        companions = case.get("companion_skills", [])
        if (
            not isinstance(companions, list)
            or len(companions) != len(set(companions))
            or not all(
                isinstance(item, str)
                and item in managed_names
                and item != name
                for item in companions
            )
        ):
            errors.append(f"{name}/{case_id}: companion_skills are invalid")
    return errors


def _valid_fixture(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {"path", "content"}:
        return False
    path = value.get("path")
    content = value.get("content")
    if (
        not _nonempty(path)
        or not isinstance(content, str)
        or "\\" in path
        or path.startswith("/")
    ):
        return False
    parts = path.split("/")
    return (
        all(part not in {"", ".", ".."} for part in parts)
        and parts[0] not in {".agents", ".claude", ".codex", ".gemini"}
    )


def _validate_trigger_cases(
    name: str,
    value: object,
    invocation: str,
) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{name}: trigger_cases must be non-empty"]
    expected = "implicit" if invocation == "implicit" else "manual-only"
    errors: list[str] = []
    seen: set[str] = set()
    for case in value:
        if not isinstance(case, dict) or set(case) != {
            "id",
            "prompt",
            "expected_invocation",
        }:
            errors.append(f"{name}: trigger case fields are invalid")
            continue
        case_id = case.get("id")
        if not _nonempty(case_id) or case_id in seen:
            errors.append(f"{name}: trigger case id is invalid or duplicated")
        seen.add(case_id)
        if not _nonempty(case.get("prompt")) or len(case["prompt"]) < 20:
            errors.append(f"{name}/{case_id}: trigger prompt is too short")
        if case.get("expected_invocation") != expected:
            errors.append(
                f"{name}/{case_id}: expected_invocation must be {expected}"
            )
    return errors


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _directory_digest(path: Path) -> str:
    """Match the installer and attestation directory digest contract."""

    root = path.resolve()
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = item.relative_to(root).as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(struct.pack("<i", len(relative)))
        digest.update(relative)
        digest.update(struct.pack("<q", len(content)))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
