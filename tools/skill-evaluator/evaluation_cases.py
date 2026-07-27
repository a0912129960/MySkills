#!/usr/bin/env python3
"""Validate evaluation cases and construct a deterministic batch run plan."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
from datetime import datetime
from typing import Any, Iterable

import aggregate_benchmark


TARGETS = ("claude", "codex")
RUNTIME_TOOLS = ("obsidian-wiki", "skill-evaluator")
EXTERNAL_TOOLS = ("qmd",)
KEBAB_CASE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FIXTURE_PATH = re.compile(
    r"[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*\Z"
)


def load_cases(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    path = root / "evaluations" / "cases.json"
    index = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    index_errors = _validate_case_index(index)
    if index_errors:
        raise ValueError("\n".join(index_errors))

    skills: list[dict[str, Any]] = []
    evaluations_root = path.parent.resolve()
    for relative in index["skill_case_files"]:
        source = (evaluations_root / relative).resolve()
        try:
            source.relative_to(evaluations_root)
        except ValueError as error:
            raise ValueError(
                f"evaluation case source escapes evaluations/: {relative}"
            ) from error
        try:
            entry = json.loads(
                source.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
        except OSError as error:
            raise ValueError(
                f"evaluation case source is unavailable: {relative}"
            ) from error
        expected_name = Path(relative).stem
        if (
            not isinstance(entry, dict)
            or entry.get("skill_name") != expected_name
        ):
            raise ValueError(
                f"{relative}: skill_name must match the source filename"
            )
        skills.append(entry)

    document = {
        "$schema": "./cases.schema.json",
        "schema_version": 4,
        "fixture_sets": index.get("fixture_sets", {}),
        "skills": skills,
    }
    errors = validate_cases(root, document)
    if errors:
        raise ValueError("\n".join(errors))
    return document


def _validate_case_index(document: object) -> list[str]:
    required = {"$schema", "schema_version", "skill_case_files"}
    optional = {"fixture_sets"}
    if (
        not isinstance(document, dict)
        or not required.issubset(document)
        or not set(document).issubset(required | optional)
    ):
        return ["evaluation case catalog fields are invalid"]
    errors: list[str] = []
    if document.get("$schema") != "./cases.schema.json":
        errors.append("evaluation case catalog $schema is invalid")
    if document.get("schema_version") != 4:
        errors.append("evaluation case catalog schema_version must be 4")
    fixture_errors = _validate_fixture_sets(document.get("fixture_sets", {}))
    errors.extend(fixture_errors)
    sources = document.get("skill_case_files")
    if not isinstance(sources, list) or not sources:
        errors.append(
            "evaluation case catalog skill_case_files are invalid, "
            "duplicated, or unsorted"
        )
    elif (
        not _unique_strings(sources)
        or sources != sorted(sources)
        or not all(
            isinstance(source, str)
            and re.fullmatch(
                r"cases/[a-z0-9]+(?:-[a-z0-9]+)*\.json",
                source,
            )
            for source in sources
        )
    ):
        errors.append(
            "evaluation case catalog skill_case_files are invalid, "
            "duplicated, or unsorted"
        )
    return errors


def validate_cases(repo_root: Path | str, document: object) -> list[str]:
    root = Path(repo_root).resolve()
    errors: list[str] = []
    required_root_fields = {
        "$schema",
        "schema_version",
        "skills",
    }
    optional_root_fields = {"fixture_sets"}
    if (
        not isinstance(document, dict)
        or not required_root_fields.issubset(document)
        or not set(document).issubset(
            required_root_fields | optional_root_fields
        )
    ):
        return ["evaluation cases root fields are invalid"]
    if document.get("$schema") != "./cases.schema.json":
        errors.append("evaluation cases $schema is invalid")
    if document.get("schema_version") != 4:
        errors.append("evaluation cases schema_version must be 4")
    skills = document.get("skills")
    if not isinstance(skills, list):
        return errors + ["evaluation cases skills must be an array"]
    fixture_sets = document.get("fixture_sets", {})
    fixture_set_errors = _validate_fixture_sets(fixture_sets)
    errors.extend(fixture_set_errors)
    if fixture_set_errors:
        fixture_sets = {}

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
        if not isinstance(entry, dict) or not {
            "skill_name",
            "invocation",
            "evaluation_level",
            "core_cases",
            "invocation_cases",
        }.issubset(entry) or not set(entry).issubset({
            "$schema",
            "schema_version",
            "skill_name",
            "invocation",
            "evaluation_level",
            "core_cases",
            "invocation_cases",
            "golden_cases",
        }):
            errors.append(f"{location} fields are invalid")
            continue
        if entry.get("$schema") != "../skill-case.schema.json":
            errors.append(f"{location}.$schema is invalid")
        if entry.get("schema_version") != 4:
            errors.append(f"{location}.schema_version must be 4")
        name = entry.get("skill_name")
        if not isinstance(name, str) or name not in managed:
            errors.append(f"{location}.skill_name is not a managed Skill")
            continue
        if name in seen:
            errors.append(f"{location}.skill_name is duplicated: {name}")
        seen.add(name)
        if entry.get("evaluation_level") != "full":
            errors.append(f"{name}: consolidated Skills require full evaluation")
        invocation = managed[name]["invocation"]
        if entry.get("invocation") != invocation:
            errors.append(
                f"{name}: invocation must match inventory value {invocation}"
            )
        errors.extend(
            _validate_core_cases(
                name,
                entry.get("core_cases"),
                set(managed),
                fixture_sets,
            )
        )
        errors.extend(
            _validate_invocation_cases(
                name,
                entry.get("invocation_cases"),
                invocation,
                set(managed),
                fixture_sets,
            )
        )
        errors.extend(
            _validate_golden_cases(
                name,
                entry.get("golden_cases", []),
                set(managed),
                fixture_sets,
            )
        )
        case_ids = [
            case.get("id")
            for field in ("core_cases", "invocation_cases", "golden_cases")
            for case in entry.get(field, [])
            if isinstance(case, dict) and isinstance(case.get("id"), str)
        ]
        if len(case_ids) != len(set(case_ids)):
            errors.append(f"{name}: case ids must be unique across all suites")
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
    runtime_digest_cache: dict[str, str] = {}

    def skill_digest(name: str) -> str:
        if name not in digest_cache:
            digest_cache[name] = _directory_digest(paths[name])
        return digest_cache[name]

    def runtime_source(name: str) -> Path:
        source = root / "tools" / name
        if not source.is_dir():
            raise ValueError(f"runtime tool source is unavailable: {source}")
        return source

    def runtime_digest(name: str) -> str:
        if name not in runtime_digest_cache:
            runtime_digest_cache[name] = _runtime_directory_digest(
                runtime_source(name),
                repo_root=root,
            )
        return runtime_digest_cache[name]

    plan: list[dict[str, Any]] = []
    fixture_sets = document.get("fixture_sets", {})
    for name in sorted(selected):
        entry = entries[name]
        for case in entry["core_cases"]:
            expanded_fixtures = _expanded_fixtures(case, fixture_sets)
            runtime_tools = case.get("runtime_tools", [])
            external_tools = case.get("external_tools", [])
            for target in TARGETS:
                plan.append(
                    _plan_item(
                        name,
                        paths[name],
                        case,
                        target,
                        evaluation_level=entry["evaluation_level"],
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
                        fixture_set_names=case.get("fixture_sets", []),
                        fixtures=expanded_fixtures,
                        runtime_tool_sources={
                            tool: runtime_source(tool)
                            for tool in runtime_tools
                        },
                        runtime_tool_digests={
                            tool: runtime_digest(tool)
                            for tool in runtime_tools
                        },
                        external_tools=external_tools,
                        mode="core",
                        explicit=True,
                    )
                )
        for case in entry["invocation_cases"]:
            expanded_fixtures = _expanded_fixtures(case, fixture_sets)
            external_tools = case.get("external_tools", [])
            companions = case.get("companion_skills", [])
            for target in TARGETS:
                plan.append(
                    _plan_item(
                        name,
                        paths[name],
                        case,
                        target,
                        evaluation_level=entry["evaluation_level"],
                        skill_digest=skill_digest(name),
                        companion_skill_paths={
                            companion: paths[companion]
                            for companion in companions
                        },
                        companion_skill_digests={
                            companion: skill_digest(companion)
                            for companion in companions
                        },
                        fixture_set_names=case.get("fixture_sets", []),
                        fixtures=expanded_fixtures,
                        runtime_tool_sources={},
                        runtime_tool_digests={},
                        external_tools=external_tools,
                        mode="invocation",
                        explicit=False,
                    )
                )
        for case in entry.get("golden_cases", []):
            expanded_fixtures = _expanded_fixtures(case, fixture_sets)
            runtime_tools = case.get("runtime_tools", [])
            external_tools = case.get("external_tools", [])
            companions = case.get("companion_skills", [])
            for target in TARGETS:
                plan.append(
                    _plan_item(
                        name,
                        paths[name],
                        case,
                        target,
                        evaluation_level=entry["evaluation_level"],
                        skill_digest=skill_digest(name),
                        companion_skill_paths={
                            companion: paths[companion]
                            for companion in companions
                        },
                        companion_skill_digests={
                            companion: skill_digest(companion)
                            for companion in companions
                        },
                        fixture_set_names=case.get("fixture_sets", []),
                        fixtures=expanded_fixtures,
                        runtime_tool_sources={
                            tool: runtime_source(tool)
                            for tool in runtime_tools
                        },
                        runtime_tool_digests={
                            tool: runtime_digest(tool)
                            for tool in runtime_tools
                        },
                        external_tools=external_tools,
                        mode="golden",
                        explicit=True,
                    )
                )
    return plan


def summarize_plan(plan: list[dict[str, Any]]) -> dict[str, Any]:
    skills = sorted({item["skill_name"] for item in plan})
    return {
        "schema_version": 4,
        "skill_count": len(skills),
        "model_run_count": len(plan),
        "targets": list(TARGETS),
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
    skill_roots: set[Path] = set()
    planned_runs: list[tuple[Path, dict[str, Any]]] = []
    plan_path = root / "plan.json"
    if plan_path.is_file():
        document = json.loads(
            plan_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        runs = document.get("runs") if isinstance(document, dict) else None
        if (
            not isinstance(document, dict)
            or document.get("schema_version") != 4
            or not isinstance(runs, list)
            or not all(isinstance(item, dict) for item in runs)
        ):
            raise ValueError(f"{plan_path}: retained batch plan is invalid")
        for item in runs:
            skill_name = item.get("skill_name")
            case_id = item.get("case_id")
            target = item.get("target")
            if (
                not isinstance(skill_name, str)
                or not skill_name
                or not isinstance(case_id, str)
                or not case_id
                or target not in TARGETS
            ):
                raise ValueError(
                    f"{plan_path}: retained run identity is invalid"
                )
            run_root = root / skill_name / case_id / target
            planned_runs.append((run_root, item))
    else:
        for result_path in results:
            record = json.loads(
                result_path.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
            plan = record.get("plan")
            if not isinstance(plan, dict):
                raise ValueError(f"{result_path}: missing batch plan")
            skill_name = plan.get("skill_name")
            if not isinstance(skill_name, str) or not skill_name:
                try:
                    skill_name = result_path.relative_to(root).parts[0]
                except (ValueError, IndexError) as error:
                    raise ValueError(
                        f"{result_path}: missing batch Skill name"
                    ) from error
            planned_runs.append((result_path.parent, plan))

    for run_root, plan in planned_runs:
        skill_name = plan.get("skill_name")
        if not isinstance(skill_name, str) or not skill_name:
            skill_name = run_root.relative_to(root).parts[0]
        skill_roots.add(root / skill_name)
        grading_path = run_root / "grading.json"
        if grading_path.exists() and not overwrite:
            preserved.append(str(grading_path))
            continue
        grading_path.parent.mkdir(parents=True, exist_ok=True)
        assertions = _grading_assertions(plan)
        grading = {
            "schema_version": 3,
            "observed_invocation": "unknown",
            "invocation_evidence": "PENDING HUMAN REVIEW",
            "observed_external_state": None,
            "expectations": [
                {
                    "assertion_id": assertion["id"],
                    "kind": assertion["kind"],
                    "description": assertion["description"],
                    "required": assertion["required"],
                    "trajectory_observation": assertion.get(
                        "trajectory_observation",
                        "not-applicable",
                    ),
                    "status": "pending",
                    "evidence": "PENDING HUMAN REVIEW",
                    "observation": "pending",
                }
                for assertion in assertions
            ]
        }
        grading_path.write_text(
            json.dumps(grading, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created.append(str(grading_path))
    created_reviews: list[str] = []
    preserved_reviews: list[str] = []
    for skill_root in sorted(skill_roots):
        review_path = skill_root / "review.json"
        if review_path.exists() and not overwrite:
            preserved_reviews.append(str(review_path))
            continue
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "pending",
                    "reviewer": None,
                    "reviewed_at": None,
                    "reason": None,
                    "corrective_action": None,
                    "sanitization_confirmed": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        created_reviews.append(str(review_path))
    index = {
        "schema_version": 3,
        "workspace": str(root),
        "planned_run_count": len(planned_runs),
        "raw_result_count": len(results),
        "created_grading_count": len(created),
        "preserved_grading_count": len(preserved),
        "created_review_count": len(created_reviews),
        "preserved_review_count": len(preserved_reviews),
        "created": created,
        "preserved": preserved,
        "created_reviews": created_reviews,
        "preserved_reviews": preserved_reviews,
        "status": "PENDING_HUMAN_REVIEW",
    }
    (root / "review-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index


def _dependency_minimum_versions(
    repo: Path,
    names: Iterable[str],
) -> dict[str, str]:
    requested = set(names)
    if not requested:
        return {}
    manifest_path = repo / "manifests" / "dependencies.json"
    document = json.loads(
        manifest_path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    dependencies = (
        document.get("dependencies")
        if isinstance(document, dict)
        else None
    )
    if not isinstance(dependencies, list):
        raise ValueError(f"{manifest_path}: dependencies must be an array")
    minimums: dict[str, str] = {}
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        name = dependency.get("id")
        if name not in requested:
            continue
        minimum = dependency.get("minimum_version")
        if (
            name in minimums
            or not isinstance(minimum, str)
            or not minimum
        ):
            raise ValueError(
                f"{manifest_path}: dependency {name!r} has invalid minimum"
            )
        minimums[name] = minimum
    if set(minimums) != requested:
        missing = ", ".join(sorted(requested - set(minimums)))
        raise ValueError(
            f"{manifest_path}: external dependencies are missing: {missing}"
        )
    return minimums


def _parsed_version(value: object) -> tuple[int, ...] | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)", value)
    if match is None:
        return None
    parts = tuple(int(part) for part in match.group(1).split("."))
    return parts + (0,) * (4 - len(parts))


def _audit_external_tool_evidence(
    result_path: Path,
    item: dict[str, Any],
    record: dict[str, Any],
    minimum_versions: dict[str, str],
    errors: list[str],
) -> None:
    declared = set(item["external_tools"])
    evidence = record.get("external_tool_evidence", {})
    if not isinstance(evidence, dict) or set(evidence) != declared:
        errors.append(
            f"{result_path}: external tool evidence keys do not match the plan"
        )
        return
    required_fields = {
        "minimum_version",
        "identity",
        "setup",
        "workspace_index",
        "fixture_root",
    }
    for name in sorted(declared):
        details = evidence.get(name)
        if not isinstance(details, dict) or set(details) != required_fields:
            errors.append(
                f"{result_path}: {name} external tool evidence is malformed"
            )
            continue
        minimum = minimum_versions[name]
        if details.get("minimum_version") != minimum:
            errors.append(
                f"{result_path}: {name} minimum version does not match "
                "the dependency manifest"
            )
        identity = details.get("identity")
        if (
            not isinstance(identity, dict)
            or identity.get("returncode") != 0
            or identity.get("timed_out") is not False
            or not _nonempty(identity.get("stdout"))
        ):
            errors.append(
                f"{result_path}: {name} external tool identity check "
                "did not pass"
            )
        else:
            actual_version = _parsed_version(identity["stdout"])
            required_version = _parsed_version(minimum)
            if (
                actual_version is None
                or required_version is None
                or actual_version < required_version
            ):
                errors.append(
                    f"{result_path}: {name} external tool version is invalid "
                    "or below the dependency minimum"
                )
        setup = details.get("setup")
        if (
            not isinstance(setup, list)
            or len(setup) < 2
            or any(
                not isinstance(step, dict)
                or step.get("returncode") != 0
                or step.get("timed_out") is not False
                for step in setup
            )
        ):
            errors.append(
                f"{result_path}: {name} external tool setup did not pass"
            )
        if (
            details.get("workspace_index") != ".qmd"
            or details.get("fixture_root") != "fixture/qmd-notes"
        ):
            errors.append(
                f"{result_path}: {name} external tool workspace evidence "
                "is invalid"
            )


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
    minimum_versions = _dependency_minimum_versions(
        repo,
        {
            name
            for item in expected
            for name in item["external_tools"]
        },
    )
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
        _audit_external_tool_evidence(
            result_path,
            item,
            record,
            minimum_versions,
            errors,
        )
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
        model_evidence = aggregate_benchmark.model_evidence(
            item["target"],
            result,
        )
        execution_workspace = record.get("execution_workspace")
        execution_path: Path | None = None
        if (
            not isinstance(execution_workspace, str)
            or not execution_workspace.strip()
            or not Path(execution_workspace).is_absolute()
        ):
            errors.append(
                f"{result_path}: execution workspace is missing or not absolute"
            )
        else:
            execution_path = Path(execution_workspace).resolve()
            try:
                execution_path.relative_to(repo)
            except ValueError:
                pass
            else:
                errors.append(
                    f"{result_path}: execution workspace is inside the repository"
                )

        isolation_violations = record.get("isolation_violations")
        stored_isolation_valid = (
            isinstance(isolation_violations, list)
            and all(
                isinstance(violation, str) and violation.strip()
                for violation in isolation_violations
            )
        )
        if not stored_isolation_valid:
            errors.append(f"{result_path}: model isolation audit is missing")
        elif isolation_violations:
            errors.append(
                f"{result_path}: model isolation did not pass: "
                + "; ".join(isolation_violations)
            )
        if execution_path is not None:
            recomputed_isolation = (
                aggregate_benchmark.model_isolation_violations(
                    item["target"],
                    model_evidence,
                    execution_path,
                    allowed_commands=[
                        *item["runtime_tools"],
                        *item["external_tools"],
                    ],
                    audit_undeclared_bash=(
                        item["safety"] == "read-only"
                    ),
                    command=result.get("command", []),
                    environment_isolation=record.get(
                        "environment_isolation"
                    ),
                )
            )
            if (
                stored_isolation_valid
                and isolation_violations != recomputed_isolation
            ):
                errors.append(
                    f"{result_path}: stored model isolation audit does not "
                    "match the raw trace"
                )
            if recomputed_isolation:
                errors.append(
                    f"{result_path}: model isolation did not pass: "
                    + "; ".join(recomputed_isolation)
                )
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
        if (
            not isinstance(grading, dict)
            or set(grading)
            != {
                "schema_version",
                "observed_invocation",
                "invocation_evidence",
                "observed_external_state",
                "expectations",
            }
            or grading.get("schema_version") != 3
        ):
            errors.append(f"{grading_path}: v3 grading fields are invalid")
            continue
        expected_invocation = (
            "explicit"
            if item["explicit"]
            else item["expected_invocation"]
        )
        observed_invocation = grading.get("observed_invocation")
        invocation_evidence = grading.get("invocation_evidence")
        observed_external_state = grading.get("observed_external_state")
        if observed_invocation == "unknown":
            errors.append(
                f"{grading_path}: observed invocation classification is required"
            )
        elif observed_invocation != expected_invocation:
            errors.append(
                f"{grading_path}: expected {expected_invocation} invocation "
                f"but observed {observed_invocation}"
            )
        if (
            not _nonempty(invocation_evidence)
            or invocation_evidence.strip() == "PENDING HUMAN REVIEW"
        ):
            errors.append(
                f"{grading_path}: invocation evidence is required"
            )
        if (
            observed_external_state is not None
            and not _nonempty(observed_external_state)
        ):
            errors.append(
                f"{grading_path}: observed external state is invalid"
            )
        if not isinstance(expectations, list) or len(expectations) != len(
            expected_assertions
        ):
            errors.append(f"{grading_path}: expectations do not match the plan")
            continue
        for expected_assertion, grade in zip(
            expected_assertions,
            expectations,
        ):
            if not isinstance(grade, dict) or set(grade) != {
                "assertion_id",
                "kind",
                "description",
                "required",
                "trajectory_observation",
                "status",
                "evidence",
                "observation",
            }:
                errors.append(f"{grading_path}: grading fields are invalid")
                continue
            immutable_fields = {
                "assertion_id": "id",
                "kind": "kind",
                "description": "description",
                "required": "required",
                "trajectory_observation": "trajectory_observation",
            }
            if any(
                grade.get(grade_field)
                != (
                    expected_assertion.get(assertion_field)
                    if assertion_field != "trajectory_observation"
                    else expected_assertion.get(
                        assertion_field,
                        "not-applicable",
                    )
                )
                for grade_field, assertion_field in immutable_fields.items()
            ):
                errors.append(
                    f"{grading_path}: assertion contract was changed"
                )
            status = grade.get("status")
            if status not in ("pending", "pass", "fail", "invalid"):
                errors.append(f"{grading_path}: grading status is invalid")
            elif status == "pending":
                errors.append(f"{grading_path}: reviewed status is required")
            if grade.get("required") is True and status != "pass":
                errors.append(
                    f"{grading_path}: every required expectation must pass"
                )
            evidence = grade.get("evidence")
            if (
                not _nonempty(evidence)
                or evidence.strip() == "PENDING HUMAN REVIEW"
            ):
                errors.append(f"{grading_path}: reviewed evidence is required")
            observation = grade.get("observation")
            if observation not in {
                "final-output",
                "tool-trace",
                "external-state",
                "verified-absence",
                "invocation-trace",
                "not-applicable",
            }:
                errors.append(
                    f"{grading_path}: reviewed observation is required"
                )
            expected_observation = expected_assertion.get(
                "trajectory_observation",
                "not-applicable",
            )
            if (
                expected_assertion["kind"] == "trajectory"
                and observation != expected_observation
            ):
                errors.append(
                    f"{grading_path}: trajectory observation must be "
                    f"{expected_observation}"
                )
            if (
                expected_assertion["kind"] == "trajectory"
                and status == "pass"
            ):
                tool_events = {
                    "tool_use",
                    "command_execution",
                    "mcp_tool_call",
                    "web_search",
                    "file_change",
                }
                if (
                    observation == "tool-trace"
                    and not any(
                        isinstance(event, dict)
                        and event.get("type") in tool_events
                        for event in model_evidence.get("events", [])
                    )
                ):
                    errors.append(
                        f"{grading_path}: tool-trace pass has no "
                        "observable Tool event"
                    )
                elif (
                    observation == "external-state"
                    and (
                        not _nonempty(observed_external_state)
                        or not _has_captured_workspace_change(raw)
                    )
                ):
                    errors.append(
                        f"{grading_path}: external-state pass has no "
                        "captured workspace change"
                    )
                elif observation not in {
                    "tool-trace",
                    "external-state",
                    "verified-absence",
                }:
                    errors.append(
                        f"{grading_path}: trajectory pass lacks "
                        "observable evidence"
                    )
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
        core_total = sum(
            1
            for item in expected
            if item["target"] == target
            and item["mode"] == "core"
        )
        invocation_total = sum(
            1
            for item in expected
            if item["target"] == target
            and item["mode"] == "invocation"
        )
        targets[target] = {
            "status": "pass",
            "discovery": True,
            "explicit_invocation": True,
            "isolation": True,
            "core_cases": {
                "passed": core_total,
                "total": core_total,
            },
            "invocation_cases": {
                "passed": invocation_total,
                "total": invocation_total,
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
        "raw_run_root": relative_root,
        "assertion_count": assertion_count,
        "target_identities": {
            target: next(iter(identities[target])) for target in TARGETS
        },
        "targets": targets,
        "efficiency": efficiency,
    }


def _grading_assertions(plan: dict[str, Any]) -> list[dict[str, Any]]:
    assertions = plan.get("assertions")
    base_fields = {"id", "kind", "description", "required"}
    if (
        not isinstance(assertions, list)
        or not assertions
        or not all(
            isinstance(assertion, dict)
            and set(assertion)
            == (
                base_fields | {"trajectory_observation"}
                if assertion.get("kind") == "trajectory"
                else base_fields
            )
            for assertion in assertions
        )
    ):
        raise ValueError("run plan assertions are missing or malformed")
    return [dict(assertion) for assertion in assertions]


def _plan_item(
    name: str,
    skill_path: Path,
    case: dict[str, Any],
    target: str,
    *,
    evaluation_level: str,
    skill_digest: str,
    companion_skill_paths: dict[str, Path],
    companion_skill_digests: dict[str, str],
    fixture_set_names: list[str],
    fixtures: list[dict[str, str]],
    runtime_tool_sources: dict[str, Path],
    runtime_tool_digests: dict[str, str],
    external_tools: list[str],
    mode: str,
    explicit: bool,
) -> dict[str, Any]:
    return {
        "skill_name": name,
        "skill_path": str(skill_path),
        "case_id": case["id"],
        "case_version": case["version"],
        "mode": mode,
        "case_role": case.get("role") or case.get("variant"),
        "target": target,
        "evaluation_level": evaluation_level,
        "max_attempts": 1,
        "skill_digest": skill_digest,
        "fixture_sets": list(fixture_set_names),
        "fixtures": [dict(fixture) for fixture in fixtures],
        "git_fixture": (
            {
                field: [dict(fixture) for fixture in case["git_fixture"][field]]
                for field in ("baseline_files", "working_tree_files")
            }
            if case.get("git_fixture") is not None
            else None
        ),
        "runtime_tools": list(runtime_tool_sources),
        "runtime_tool_sources": {
            name: str(path)
            for name, path in runtime_tool_sources.items()
        },
        "runtime_tool_digests": dict(runtime_tool_digests),
        "external_tools": list(external_tools),
        "companion_skills": list(companion_skill_paths),
        "companion_skill_paths": [
            str(path) for path in companion_skill_paths.values()
        ],
        "companion_skill_digests": dict(companion_skill_digests),
        "explicit": explicit,
        "prompt": case["prompt"],
        "expected_outcome": (
            case.get("oracle", {}).get("expected_outcome")
            if isinstance(case.get("oracle"), dict)
            else (
                f"Skill invocation classification is "
                f"{case.get('expected_invocation')}"
            )
        ),
        "assertions": (
            case.get("oracle", {}).get("assertions", [])
            if isinstance(case.get("oracle"), dict)
            else [
                {
                    "id": "invocation-classification",
                    "kind": "deterministic",
                    "description": (
                        "observed Skill invocation classification equals "
                        f"{case.get('expected_invocation')}"
                    ),
                    "required": True,
                }
            ]
        ),
        "safety": case.get("safety", "read-only"),
        "expected_invocation": case.get("expected_invocation"),
    }


def _validate_core_cases(
    name: str,
    value: object,
    managed_names: set[str],
    fixture_sets: dict[str, list[dict[str, str]]],
) -> list[str]:
    if not isinstance(value, list) or len(value) != 3:
        return [f"{name}: exactly 3 core_cases are required"]
    errors: list[str] = []
    seen: set[str] = set()
    roles: list[object] = []
    for case in value:
        required_fields = {
            "id",
            "version",
            "role",
            "prompt",
            "oracle",
            "safety",
        }
        optional_fields = {
            "fixtures",
            "fixture_sets",
            "companion_skills",
            "git_fixture",
            "runtime_tools",
            "external_tools",
        }
        if (
            not isinstance(case, dict)
            or not required_fields.issubset(case)
            or not set(case).issubset(required_fields | optional_fields)
        ):
            errors.append(f"{name}: required case fields are invalid")
            continue
        case_id = case.get("id")
        if (
            not isinstance(case_id, str)
            or KEBAB_CASE.fullmatch(case_id) is None
            or case_id in seen
        ):
            errors.append(f"{name}: core case id is invalid or duplicated")
        if isinstance(case_id, str):
            seen.add(case_id)
        if not _valid_version(case.get("version")):
            errors.append(f"{name}/{case_id}: version must be a positive integer")
        role = case.get("role")
        if role not in ("normal", "boundary", "safety-or-core"):
            errors.append(f"{name}/{case_id}: core role is invalid")
        else:
            roles.append(role)
        if not _nonempty(case.get("prompt")) or len(case["prompt"]) < 20:
            errors.append(f"{name}/{case_id}: prompt is too short")
        errors.extend(_validate_oracle(name, case_id, case.get("oracle")))
        if case.get("safety") not in ("read-only", "temporary-workspace"):
            errors.append(f"{name}/{case_id}: safety is invalid")
        fixtures = case.get("fixtures", [])
        fixtures_valid = isinstance(fixtures, list) and all(
            _valid_fixture(item) for item in fixtures
        )
        if not fixtures_valid:
            errors.append(f"{name}/{case_id}: fixtures are invalid")
        selected_fixture_sets = case.get("fixture_sets", [])
        fixture_sets_valid = (
            _unique_strings(selected_fixture_sets)
            and all(item in fixture_sets for item in selected_fixture_sets)
        )
        if not fixture_sets_valid:
            errors.append(f"{name}/{case_id}: fixture_sets are invalid")
        elif fixtures_valid:
            expanded = _expanded_fixtures(case, fixture_sets)
            paths = [fixture.get("path") for fixture in expanded]
            if len(paths) != len(set(paths)):
                errors.append(
                    f"{name}/{case_id}: duplicate fixture path"
                )
        git_fixture = case.get("git_fixture")
        if git_fixture is not None:
            errors.extend(
                _validate_git_fixture(name, case_id, git_fixture)
            )
            if fixtures_valid and isinstance(git_fixture, dict):
                regular_paths = {
                    fixture.get("path")
                    for fixture in _expanded_fixtures(case, fixture_sets)
                    if isinstance(fixture, dict)
                }
                git_files = [
                    fixture
                    for field in ("baseline_files", "working_tree_files")
                    if isinstance(git_fixture.get(field), list)
                    for fixture in git_fixture[field]
                ]
                git_paths = {
                    fixture.get("path")
                    for fixture in git_files
                    if isinstance(fixture, dict)
                }
                if regular_paths & git_paths:
                    errors.append(
                        f"{name}/{case_id}: duplicate fixture path across "
                        "fixtures and git_fixture"
                    )
        runtime_tools = case.get("runtime_tools", [])
        if (
            not _unique_strings(runtime_tools)
            or not all(tool in RUNTIME_TOOLS for tool in runtime_tools)
        ):
            errors.append(f"{name}/{case_id}: runtime_tools are invalid")
        external_tools = case.get("external_tools", [])
        if (
            not _unique_strings(external_tools)
            or not all(tool in EXTERNAL_TOOLS for tool in external_tools)
        ):
            errors.append(f"{name}/{case_id}: external_tools are invalid")
        companions = case.get("companion_skills", [])
        if (
            not _unique_strings(companions)
            or not all(
                item in managed_names
                and item != name
                for item in companions
            )
        ):
            errors.append(f"{name}/{case_id}: companion_skills are invalid")
    if set(roles) != {"normal", "boundary", "safety-or-core"}:
        errors.append(
            f"{name}: core_cases must contain normal, boundary, and "
            "safety-or-core roles exactly once"
        )
    return errors


def _valid_fixture(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {"path", "content"}:
        return False
    path = value.get("path")
    content = value.get("content")
    if (
        not _nonempty(path)
        or not isinstance(content, str)
        or FIXTURE_PATH.fullmatch(path) is None
    ):
        return False
    parts = path.split("/")
    return (
        all(
            part not in {"", ".", ".."}
            and not part.endswith((".", " "))
            for part in parts
        )
        and all(
            part.lower()
            not in {".agents", ".claude", ".codex", ".gemini", ".git"}
            for part in parts
        )
    )


def _validate_fixture_sets(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["evaluation fixture_sets must be an object"]
    errors: list[str] = []
    for name, fixtures in value.items():
        if (
            not isinstance(name, str)
            or KEBAB_CASE.fullmatch(name) is None
            or not isinstance(fixtures, list)
            or not fixtures
        ):
            errors.append("evaluation fixture_sets entry is invalid")
            continue
        if not all(_valid_fixture(fixture) for fixture in fixtures):
            errors.append(f"fixture_sets.{name} contains an invalid fixture")
            continue
        paths = [fixture["path"] for fixture in fixtures]
        if len(paths) != len(set(paths)):
            errors.append(
                f"fixture_sets.{name} contains a duplicate fixture path"
            )
    return errors


def _expanded_fixtures(
    case: dict[str, Any],
    fixture_sets: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    expanded: list[dict[str, str]] = []
    for name in case.get("fixture_sets", []):
        expanded.extend(dict(fixture) for fixture in fixture_sets.get(name, []))
    expanded.extend(dict(fixture) for fixture in case.get("fixtures", []))
    return expanded


def _validate_git_fixture(
    name: str,
    case_id: object,
    value: object,
) -> list[str]:
    if (
        not isinstance(value, dict)
        or set(value) != {"baseline_files", "working_tree_files"}
    ):
        return [f"{name}/{case_id}: git_fixture fields are invalid"]
    errors: list[str] = []
    for field in ("baseline_files", "working_tree_files"):
        fixtures = value.get(field)
        if (
            not isinstance(fixtures, list)
            or (field == "baseline_files" and not fixtures)
            or not all(_valid_fixture(fixture) for fixture in fixtures)
        ):
            errors.append(
                f"{name}/{case_id}: git_fixture.{field} is invalid"
            )
            continue
        paths = [fixture["path"] for fixture in fixtures]
        if len(paths) != len(set(paths)):
            errors.append(
                f"{name}/{case_id}: git_fixture.{field} has a duplicate path"
            )
    return errors


def _validate_oracle(
    name: str,
    case_id: object,
    value: object,
) -> list[str]:
    if not isinstance(value, dict) or set(value) != {
        "expected_outcome",
        "assertions",
    }:
        return [f"{name}/{case_id}: oracle fields are invalid"]
    errors: list[str] = []
    if not _nonempty(value.get("expected_outcome")):
        errors.append(f"{name}/{case_id}: expected_outcome is required")
    assertions = value.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        return errors + [f"{name}/{case_id}: assertions must be non-empty"]
    seen: set[str] = set()
    required_count = 0
    for assertion in assertions:
        base_fields = {"id", "kind", "description", "required"}
        if not isinstance(assertion, dict) or set(assertion) != (
            base_fields | {"trajectory_observation"}
            if isinstance(assertion, dict)
            and assertion.get("kind") == "trajectory"
            else base_fields
        ):
            errors.append(f"{name}/{case_id}: assertion fields are invalid")
            continue
        assertion_id = assertion.get("id")
        if (
            not isinstance(assertion_id, str)
            or KEBAB_CASE.fullmatch(assertion_id) is None
            or assertion_id in seen
        ):
            errors.append(
                f"{name}/{case_id}: assertion id is invalid or duplicated"
            )
        if isinstance(assertion_id, str):
            seen.add(assertion_id)
        if assertion.get("kind") not in (
            "deterministic",
            "human-rubric",
            "trajectory",
        ):
            errors.append(
                f"{name}/{case_id}/{assertion_id}: assertion kind is invalid"
            )
        if (
            assertion.get("kind") == "trajectory"
            and assertion.get("trajectory_observation")
            not in {"tool-trace", "external-state", "verified-absence"}
        ):
            errors.append(
                f"{name}/{case_id}/{assertion_id}: trajectory observation "
                "is invalid"
            )
        if not _nonempty(assertion.get("description")):
            errors.append(
                f"{name}/{case_id}/{assertion_id}: description is required"
            )
        if not isinstance(assertion.get("required"), bool):
            errors.append(
                f"{name}/{case_id}/{assertion_id}: required must be boolean"
            )
        elif assertion["required"]:
            required_count += 1
    if required_count == 0:
        errors.append(
            f"{name}/{case_id}: at least one assertion must be required"
        )
    return errors


def _validate_invocation_cases(
    name: str,
    value: object,
    invocation: str,
    managed_names: set[str],
    fixture_sets: dict[str, list[dict[str, str]]],
) -> list[str]:
    if not isinstance(value, list) or len(value) != 3:
        return [f"{name}: exactly 3 invocation_cases are required"]
    errors: list[str] = []
    seen: set[str] = set()
    variants: dict[object, object] = {}
    for case in value:
        required_fields = {
            "id",
            "version",
            "variant",
            "prompt",
            "expected_invocation",
        }
        optional_fields = {
            "fixtures",
            "fixture_sets",
            "companion_skills",
            "external_tools",
        }
        if (
            not isinstance(case, dict)
            or not required_fields.issubset(case)
            or not set(case).issubset(required_fields | optional_fields)
        ):
            errors.append(f"{name}: invocation case fields are invalid")
            continue
        case_id = case.get("id")
        if (
            not isinstance(case_id, str)
            or KEBAB_CASE.fullmatch(case_id) is None
            or case_id in seen
        ):
            errors.append(
                f"{name}: invocation case id is invalid or duplicated"
            )
        if isinstance(case_id, str):
            seen.add(case_id)
        if not _valid_version(case.get("version")):
            errors.append(f"{name}/{case_id}: version must be a positive integer")
        variant = case.get("variant")
        expected_invocation = case.get("expected_invocation")
        if variant not in ("direct", "paraphrase", "boundary"):
            errors.append(f"{name}/{case_id}: invocation variant is invalid")
        elif variant in variants:
            errors.append(
                f"{name}/{case_id}: invocation variant is duplicated"
            )
        else:
            variants[variant] = expected_invocation
        if not _nonempty(case.get("prompt")) or len(case["prompt"]) < 20:
            errors.append(f"{name}/{case_id}: invocation prompt is too short")
        if expected_invocation not in ("implicit", "not-invoked"):
            errors.append(
                f"{name}/{case_id}: expected_invocation is invalid"
            )
        fixtures = case.get("fixtures", [])
        fixtures_valid = isinstance(fixtures, list) and all(
            _valid_fixture(item) for item in fixtures
        )
        if not fixtures_valid:
            errors.append(f"{name}/{case_id}: fixtures are invalid")
        selected_fixture_sets = case.get("fixture_sets", [])
        fixture_sets_valid = (
            _unique_strings(selected_fixture_sets)
            and all(item in fixture_sets for item in selected_fixture_sets)
        )
        if not fixture_sets_valid:
            errors.append(f"{name}/{case_id}: fixture_sets are invalid")
        elif fixtures_valid:
            paths = [
                fixture.get("path")
                for fixture in _expanded_fixtures(case, fixture_sets)
            ]
            if len(paths) != len(set(paths)):
                errors.append(f"{name}/{case_id}: duplicate fixture path")
        external_tools = case.get("external_tools", [])
        if (
            not _unique_strings(external_tools)
            or not all(tool in EXTERNAL_TOOLS for tool in external_tools)
        ):
            errors.append(f"{name}/{case_id}: external_tools are invalid")
        companions = case.get("companion_skills", [])
        if (
            not _unique_strings(companions)
            or not all(
                item in managed_names
                and item != name
                for item in companions
            )
        ):
            errors.append(f"{name}/{case_id}: companion_skills are invalid")
    if set(variants) != {"direct", "paraphrase", "boundary"}:
        errors.append(
            f"{name}: invocation_cases must contain direct, paraphrase, "
            "and boundary variants exactly once"
        )
    if invocation == "explicit":
        if not variants or not all(
            value == "not-invoked" for value in variants.values()
        ):
            errors.append(
                f"{name}: explicit Skill invocation cases must all be "
                "not-invoked"
            )
    elif variants != {
        "direct": "implicit",
        "paraphrase": "implicit",
        "boundary": "not-invoked",
    }:
        errors.append(
            f"{name}: implicit Skill direct and paraphrase cases must invoke; "
            "boundary must be not-invoked"
        )
    return errors


def _validate_golden_cases(
    name: str,
    value: object,
    managed_names: set[str],
    fixture_sets: dict[str, list[dict[str, str]]],
) -> list[str]:
    if not isinstance(value, list):
        return [f"{name}: golden_cases must be an array"]
    errors: list[str] = []
    seen: set[str] = set()
    for case in value:
        required_fields = {
            "id",
            "version",
            "prompt",
            "oracle",
            "safety",
            "provenance",
            "approved_by",
            "approved_at",
            "deidentified",
        }
        optional_fields = {
            "fixtures",
            "fixture_sets",
            "companion_skills",
            "git_fixture",
            "runtime_tools",
            "external_tools",
        }
        if (
            not isinstance(case, dict)
            or not required_fields.issubset(case)
            or not set(case).issubset(required_fields | optional_fields)
        ):
            errors.append(f"{name}: golden case fields are invalid")
            continue
        case_id = case.get("id")
        if (
            not isinstance(case_id, str)
            or KEBAB_CASE.fullmatch(case_id) is None
            or case_id in seen
        ):
            errors.append(f"{name}: golden case id is invalid or duplicated")
        if isinstance(case_id, str):
            seen.add(case_id)
        if not _valid_version(case.get("version")):
            errors.append(f"{name}/{case_id}: version must be a positive integer")
        if not _nonempty(case.get("prompt")) or len(case["prompt"]) < 20:
            errors.append(f"{name}/{case_id}: golden prompt is too short")
        errors.extend(_validate_oracle(name, case_id, case.get("oracle")))
        if case.get("safety") not in ("read-only", "temporary-workspace"):
            errors.append(f"{name}/{case_id}: safety is invalid")
        for field in ("provenance", "approved_by"):
            if not _nonempty(case.get(field)):
                errors.append(f"{name}/{case_id}: {field} is required")
        if not _valid_datetime(case.get("approved_at")):
            errors.append(f"{name}/{case_id}: approved_at is invalid")
        if case.get("deidentified") is not True:
            errors.append(f"{name}/{case_id}: deidentified must be true")
        fixtures = case.get("fixtures", [])
        fixtures_valid = isinstance(fixtures, list) and all(
            _valid_fixture(item) for item in fixtures
        )
        if not fixtures_valid:
            errors.append(f"{name}/{case_id}: fixtures are invalid")
        selected_fixture_sets = case.get("fixture_sets", [])
        fixture_sets_valid = (
            _unique_strings(selected_fixture_sets)
            and all(
                isinstance(item, str) and item in fixture_sets
                for item in selected_fixture_sets
            )
        )
        if not fixture_sets_valid:
            errors.append(f"{name}/{case_id}: fixture_sets are invalid")
        elif fixtures_valid:
            paths = [
                fixture.get("path")
                for fixture in _expanded_fixtures(case, fixture_sets)
            ]
            if len(paths) != len(set(paths)):
                errors.append(f"{name}/{case_id}: duplicate fixture path")
        if case.get("git_fixture") is not None:
            errors.extend(
                _validate_git_fixture(name, case_id, case["git_fixture"])
            )
        runtime_tools = case.get("runtime_tools", [])
        if (
            not _unique_strings(runtime_tools)
            or not all(tool in RUNTIME_TOOLS for tool in runtime_tools)
        ):
            errors.append(f"{name}/{case_id}: runtime_tools are invalid")
        external_tools = case.get("external_tools", [])
        if (
            not _unique_strings(external_tools)
            or not all(tool in EXTERNAL_TOOLS for tool in external_tools)
        ):
            errors.append(f"{name}/{case_id}: external_tools are invalid")
        companions = case.get("companion_skills", [])
        if (
            not _unique_strings(companions)
            or not all(
                item in managed_names
                and item != name
                for item in companions
            )
        ):
            errors.append(f"{name}/{case_id}: companion_skills are invalid")
    return errors


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_captured_workspace_change(raw: dict[str, Any]) -> bool:
    changes = raw.get("workspace_changes")
    if not isinstance(changes, list) or not changes:
        return False
    for change in changes:
        if (
            not isinstance(change, dict)
            or set(change) != {"path", "change", "before", "after"}
            or not _nonempty(change.get("path"))
            or change.get("change")
            not in {"created", "modified", "deleted"}
        ):
            return False
        before = change.get("before")
        after = change.get("after")
        if (
            (
                change["change"] == "created"
                and (before is not None or after is None)
            )
            or (
                change["change"] == "deleted"
                and (before is None or after is not None)
            )
            or (
                change["change"] == "modified"
                and (before is None or after is None or before == after)
            )
        ):
            return False
    return True


def _valid_version(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _valid_datetime(value: object) -> bool:
    if not _nonempty(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _unique_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and len(value) == len(set(value))
    )


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


def _runtime_directory_digest(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> str:
    """Digest only source-controlled files in an allowlisted runtime."""

    root = path.resolve()
    repository = (
        repo_root.resolve()
        if repo_root is not None
        else root.parents[1]
    )
    files = _tracked_runtime_files(repository, root)
    digest = hashlib.sha256()
    for relative_path in files:
        item = root / relative_path
        relative = relative_path.as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(struct.pack("<i", len(relative)))
        digest.update(relative)
        digest.update(struct.pack("<q", len(content)))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _tracked_runtime_files(repo_root: Path, source: Path) -> list[Path]:
    repository = repo_root.resolve()
    runtime = source.resolve()
    try:
        relative_source = runtime.relative_to(repository)
    except ValueError as error:
        raise ValueError(
            f"runtime tool source escapes repository: {runtime}"
        ) from error
    env = os.environ.copy()
    for key in tuple(env):
        if key.upper().startswith("GIT_"):
            env.pop(key)
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            relative_source.as_posix(),
        ],
        cwd=repository,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"cannot enumerate runtime source files: {detail}")
    tracked: list[Path] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        candidate = (repository / raw.decode("utf-8")).resolve()
        try:
            relative = candidate.relative_to(runtime)
        except ValueError as error:
            raise ValueError(
                f"tracked runtime file escapes source: {candidate}"
            ) from error
        if not candidate.is_file():
            raise ValueError(f"tracked runtime file is unavailable: {candidate}")
        tracked.append(relative)
    if not tracked:
        raise ValueError(f"runtime tool has no source-controlled files: {runtime}")
    return sorted(tracked, key=lambda item: item.as_posix())


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
