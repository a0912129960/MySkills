#!/usr/bin/env python3
"""Validate evaluation cases and construct a deterministic batch run plan."""

from __future__ import annotations

import json
from pathlib import Path
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
        errors.extend(_validate_required_cases(name, entry.get("required_cases")))
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


def _plan_item(
    name: str,
    skill_path: Path,
    case: dict[str, Any],
    target: str,
    configuration: str,
    *,
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
        "explicit": explicit,
        "prompt": case["prompt"],
        "assertions": case.get("assertions", []),
        "safety": case.get("safety", "read-only"),
        "expected_invocation": case.get("expected_invocation"),
    }


def _validate_required_cases(name: str, value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{name}: required_cases must be non-empty"]
    errors: list[str] = []
    seen: set[str] = set()
    for case in value:
        if not isinstance(case, dict) or set(case) != {
            "id",
            "prompt",
            "assertions",
            "safety",
        }:
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
    return errors


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


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
