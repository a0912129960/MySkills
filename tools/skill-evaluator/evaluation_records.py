#!/usr/bin/env python3
"""Validate source-controlled MySkills evaluation records."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


RECORD_SCHEMA_VERSION = 1
EVALUATOR_VERSION = "myskills-skill-evaluator/3"
TARGETS = ("claude", "codex")
KEBAB_CASE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")

ROOT_FIELDS = {
    "$schema",
    "schema_version",
    "run_id",
    "skill_name",
    "skill_digest",
    "case_manifest_digest",
    "evaluator_version",
    "started_at",
    "completed_at",
    "status",
    "targets",
    "human_review",
    "warnings",
    "sanitization",
}
TARGET_FIELDS = {
    "status",
    "runner",
    "duration_ms",
    "total_tokens",
    "cases",
}
CASE_FIELDS = {
    "case_id",
    "case_version",
    "kind",
    "prompt",
    "expected",
    "observed",
    "assertion_results",
    "status",
    "failure",
}
RESULT_STATUSES = {"pass", "fail", "invalid", "human-review-required"}


def read_record_document(record_path: Path | str) -> dict[str, Any]:
    """Read and validate a record document without imposing its final Git path."""

    path = Path(record_path)
    try:
        document: Any = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid evaluation record: {error}") from error
    errors = validate_record_document(document)
    if errors:
        raise ValueError("\n".join(errors))
    return document


def write_record(
    repo_root: Path | str,
    document: dict[str, Any],
) -> Path:
    """Atomically write one append-only machine and human evaluation record."""

    errors = validate_record_document(document)
    if errors:
        raise ValueError("\n".join(errors))
    root = Path(repo_root).resolve()
    parent = (
        root
        / "evaluations"
        / "records"
        / document["skill_name"]
    )
    destination = parent / document["run_id"]
    parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"evaluation record already exists: {destination}")
    with tempfile.TemporaryDirectory(
        prefix=f".{document['run_id']}-",
        dir=parent,
        ignore_cleanup_errors=True,
    ) as temp_dir:
        temporary = Path(temp_dir)
        (temporary / "record.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (temporary / "summary.md").write_text(
            render_summary(document),
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, destination)
    return destination


def render_summary(document: dict[str, Any]) -> str:
    """Render the concise, deterministic human review surface for a record."""

    lines = [
        f"# Skill evaluation: {document['skill_name']}",
        "",
        f"- Run: `{document['run_id']}`",
        f"- Skill digest: `{document['skill_digest']}`",
        f"- Status: **{document['status']}**",
        f"- Started: {document['started_at']}",
        f"- Completed: {document['completed_at']}",
        "",
        "## Platform results",
        "",
        "| Platform | Status | Passed cases | Duration | Tokens |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for target_name in TARGETS:
        target = document["targets"][target_name]
        cases = target["cases"]
        passed = sum(case["status"] == "pass" for case in cases)
        tokens = target["total_tokens"]["value"]
        token_text = (
            str(tokens)
            if tokens is not None
            else f"N/A ({_brief(target['total_tokens']['unavailable_reason'])})"
        )
        lines.append(
            f"| {target_name.title()} | {target['status']} | "
            f"{passed}/{len(cases)} | {target['duration_ms']} ms | "
            f"{token_text} |"
        )

    lines.extend(["", "## Case evidence", ""])
    for target_name in TARGETS:
        for case in document["targets"][target_name]["cases"]:
            lines.extend(
                [
                    f"### {target_name.title()} / {case['case_id']} "
                    f"({case['status']})",
                    "",
                    f"- Expected: {_brief(case['expected']['outcome'])}",
                    f"- Actual: {_brief(case['observed']['final_output'])}",
                ]
            )
            calls = case["observed"]["tool_calls"]
            if calls:
                trajectory = " -> ".join(
                    f"{call['sequence']}:{call['name']}[{call['status']}]"
                    for call in calls
                )
                lines.append(f"- Tool trajectory: {trajectory}")
            failure = case["failure"]
            if case["status"] in {"fail", "invalid"}:
                lines.extend(
                    [
                        f"- Failure point: {_brief(failure['stage'])}",
                        f"- Reason: {_brief(failure['reason'])}",
                        "- Corrective action: "
                        f"{_brief(failure['corrective_action'])}",
                    ]
                )
            lines.append("")

    review = document["human_review"]
    lines.extend(
        [
            "## Human review",
            "",
            f"- Status: {review['status']}",
            f"- Reviewer: {_brief(review['reviewer'])}",
            f"- Reason: {_brief(review['reason'])}",
            f"- Corrective action: {_brief(review['corrective_action'])}",
            "",
            "## Warnings",
            "",
        ]
    )
    if document["warnings"]:
        lines.extend(f"- {warning}" for warning in document["warnings"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def load_record(
    repo_root: Path | str,
    record_path: Path | str,
) -> dict[str, Any]:
    """Load and validate one record from its canonical source-controlled path."""

    root = Path(repo_root).resolve()
    path = Path(record_path).resolve()
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ValueError("evaluation record path is outside the repository") from error
    parts = relative.parts
    if (
        len(parts) != 5
        or parts[0:2] != ("evaluations", "records")
        or parts[4] != "record.json"
    ):
        raise ValueError(
            "evaluation record path must be "
            "evaluations/records/<skill>/<run-id>/record.json"
        )
    document = read_record_document(path)
    errors: list[str] = []
    if isinstance(document, dict):
        if document.get("skill_name") != parts[2]:
            errors.append("evaluation record path skill does not match skill_name")
        if document.get("run_id") != parts[3]:
            errors.append("evaluation record path run does not match run_id")
    if errors:
        raise ValueError("\n".join(errors))
    return document


def validate_record_document(document: object) -> list[str]:
    """Return contract violations for one machine-readable evaluation record."""

    if not isinstance(document, dict):
        return ["evaluation record root must be an object"]
    errors: list[str] = []
    if set(document) != ROOT_FIELDS:
        errors.append("evaluation record root fields are invalid")
    if document.get("$schema") != "../../../record.schema.json":
        errors.append("evaluation record $schema is invalid")
    if document.get("schema_version") != RECORD_SCHEMA_VERSION:
        errors.append(
            f"evaluation record schema_version must be {RECORD_SCHEMA_VERSION}"
        )
    if not _matches(document.get("run_id"), RUN_ID):
        errors.append("evaluation record run_id is invalid")
    if not _matches(document.get("skill_name"), KEBAB_CASE):
        errors.append("evaluation record skill_name is invalid")
    for field in ("skill_digest", "case_manifest_digest"):
        if not _matches(document.get(field), DIGEST):
            errors.append(f"evaluation record {field} is invalid")
    if document.get("evaluator_version") != EVALUATOR_VERSION:
        errors.append(
            f"evaluation record evaluator_version must be {EVALUATOR_VERSION!r}"
        )
    for field in ("started_at", "completed_at"):
        if not _is_datetime(document.get(field)):
            errors.append(f"evaluation record {field} must be ISO 8601")
    status = document.get("status")
    if status not in RESULT_STATUSES:
        errors.append("evaluation record status is invalid")
    targets = document.get("targets")
    if not isinstance(targets, dict) or set(targets) != set(TARGETS):
        errors.append("evaluation record targets must be exactly claude and codex")
    else:
        for target in TARGETS:
            errors.extend(_validate_target(target, targets[target]))
        if status == "pass" and any(
            targets[target].get("status") != "pass"
            for target in TARGETS
            if isinstance(targets[target], dict)
        ):
            errors.append("passing evaluation record requires both targets to pass")
    review = document.get("human_review")
    errors.extend(_validate_human_review(review))
    if (
        status == "pass"
        and _contains_human_rubric(targets)
        and (
            not isinstance(review, dict)
            or review.get("status") != "pass"
        )
    ):
        errors.append(
            "passing human-rubric record requires completed human review"
        )
    warnings = document.get("warnings")
    if not isinstance(warnings, list) or not all(
        isinstance(item, str) for item in warnings
    ):
        errors.append("evaluation record warnings must be a string array")
    errors.extend(_validate_sanitization(document.get("sanitization")))
    return errors


def _validate_sanitization(value: object) -> list[str]:
    prefix = "evaluation record sanitization"
    if not isinstance(value, dict) or set(value) != {"status", "redactions"}:
        return [f"{prefix} fields are invalid"]
    errors: list[str] = []
    if value.get("status") != "pass":
        errors.append(f"{prefix}.status must be 'pass'")
    redactions = value.get("redactions")
    if not isinstance(redactions, list) or not all(
        _nonempty(item) for item in redactions
    ):
        errors.append(f"{prefix}.redactions must be a string array")
    return errors


def _validate_human_review(value: object) -> list[str]:
    prefix = "evaluation record human_review"
    fields = {
        "status",
        "reviewer",
        "reviewed_at",
        "reason",
        "corrective_action",
    }
    if not isinstance(value, dict) or set(value) != fields:
        return [f"{prefix} fields are invalid"]
    errors: list[str] = []
    status = value.get("status")
    if status not in {"not-required", "pending", "pass"}:
        errors.append(f"{prefix}.status is invalid")
    if status == "pass":
        for field in ("reviewer", "reason"):
            if not _nonempty(value.get(field)):
                errors.append(f"{prefix}.{field} is required")
        if not _is_datetime(value.get("reviewed_at")):
            errors.append(f"{prefix}.reviewed_at must be ISO 8601")
    else:
        for field in ("reviewer", "reviewed_at", "reason"):
            if value.get(field) is not None:
                errors.append(f"{prefix}.{field} must be null when review is incomplete")
    corrective_action = value.get("corrective_action")
    if corrective_action is not None and not _nonempty(corrective_action):
        errors.append(f"{prefix}.corrective_action must be null or non-empty")
    return errors


def _contains_human_rubric(targets: object) -> bool:
    if not isinstance(targets, dict):
        return False
    for target in targets.values():
        if not isinstance(target, dict):
            continue
        cases = target.get("cases")
        if not isinstance(cases, list):
            continue
        for case in cases:
            if not isinstance(case, dict):
                continue
            expected = case.get("expected")
            if not isinstance(expected, dict):
                continue
            assertions = expected.get("assertions")
            if isinstance(assertions, list) and any(
                isinstance(assertion, dict)
                and assertion.get("kind") == "human-rubric"
                for assertion in assertions
            ):
                return True
    return False


def _validate_target(target: str, value: object) -> list[str]:
    prefix = f"targets.{target}"
    if not isinstance(value, dict) or set(value) != TARGET_FIELDS:
        return [f"{prefix} fields are invalid"]
    errors: list[str] = []
    status = value.get("status")
    if status not in RESULT_STATUSES:
        errors.append(f"{prefix}.status is invalid")
    errors.extend(
        _validate_availability(
            f"{prefix}.runner",
            value.get("runner"),
            value_type=str,
        )
    )
    duration = value.get("duration_ms")
    if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
        errors.append(f"{prefix}.duration_ms must be a non-negative integer")
    errors.extend(
        _validate_availability(
            f"{prefix}.total_tokens",
            value.get("total_tokens"),
            value_type=int,
            minimum=0,
        )
    )
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{prefix}.cases must be a non-empty array")
    else:
        for index, case in enumerate(cases):
            errors.extend(_validate_case(f"{prefix}.cases[{index}]", case))
        if status == "pass" and any(
            not isinstance(case, dict) or case.get("status") != "pass"
            for case in cases
        ):
            errors.append(f"{prefix}: passing target requires every case to pass")
    return errors


def _validate_case(prefix: str, value: object) -> list[str]:
    if not isinstance(value, dict) or set(value) != CASE_FIELDS:
        return [f"{prefix} fields are invalid"]
    errors: list[str] = []
    if not _matches(value.get("case_id"), KEBAB_CASE):
        errors.append(f"{prefix}.case_id is invalid")
    if (
        not isinstance(value.get("case_version"), int)
        or isinstance(value.get("case_version"), bool)
        or value["case_version"] < 1
    ):
        errors.append(f"{prefix}.case_version is invalid")
    if value.get("kind") not in {"core", "invocation", "golden"}:
        errors.append(f"{prefix}.kind is invalid")
    if not _nonempty(value.get("prompt")):
        errors.append(f"{prefix}.prompt is required")

    expected = value.get("expected")
    assertion_ids: set[str] = set()
    assertion_requirements: dict[str, bool] = {}
    if not isinstance(expected, dict) or set(expected) != {
        "invocation",
        "outcome",
        "assertions",
    }:
        errors.append(f"{prefix}.expected fields are invalid")
    else:
        if expected.get("invocation") not in {
            "explicit",
            "implicit",
            "not-invoked",
        }:
            errors.append(f"{prefix}.expected.invocation is invalid")
        if not _nonempty(expected.get("outcome")):
            errors.append(f"{prefix}.expected.outcome is required")
        assertions = expected.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(f"{prefix}.expected.assertions must be non-empty")
        else:
            for index, assertion in enumerate(assertions):
                assertion_prefix = f"{prefix}.expected.assertions[{index}]"
                if not isinstance(assertion, dict) or set(assertion) != {
                    "id",
                    "kind",
                    "description",
                    "required",
                }:
                    errors.append(f"{assertion_prefix} fields are invalid")
                    continue
                assertion_id = assertion.get("id")
                if not _matches(assertion_id, KEBAB_CASE):
                    errors.append(f"{assertion_prefix}.id is invalid")
                elif assertion_id in assertion_ids:
                    errors.append(f"{assertion_prefix}.id is duplicated")
                else:
                    assertion_ids.add(assertion_id)
                if assertion.get("kind") not in {
                    "deterministic",
                    "human-rubric",
                    "trajectory",
                }:
                    errors.append(f"{assertion_prefix}.kind is invalid")
                if not _nonempty(assertion.get("description")):
                    errors.append(f"{assertion_prefix}.description is required")
                if not isinstance(assertion.get("required"), bool):
                    errors.append(f"{assertion_prefix}.required must be boolean")
                elif isinstance(assertion_id, str):
                    assertion_requirements[assertion_id] = assertion["required"]

    observed = value.get("observed")
    if not isinstance(observed, dict) or set(observed) != {
        "invocation",
        "tool_calls",
        "final_output",
        "external_state",
        "unavailable",
    }:
        errors.append(f"{prefix}.observed fields are invalid")
    else:
        if observed.get("invocation") not in {
            "explicit",
            "implicit",
            "not-invoked",
            "unknown",
        }:
            errors.append(f"{prefix}.observed.invocation is invalid")
        errors.extend(
            _validate_tool_calls(
                f"{prefix}.observed.tool_calls",
                observed.get("tool_calls"),
            )
        )
        final_output = observed.get("final_output")
        if final_output is not None and not isinstance(final_output, str):
            errors.append(f"{prefix}.observed.final_output is invalid")
        external_state = observed.get("external_state")
        if external_state is not None and not isinstance(external_state, str):
            errors.append(f"{prefix}.observed.external_state is invalid")
        unavailable = observed.get("unavailable")
        if not isinstance(unavailable, list):
            errors.append(f"{prefix}.observed.unavailable must be an array")

    results = value.get("assertion_results")
    result_ids: set[str] = set()
    result_statuses: dict[str, object] = {}
    if not isinstance(results, list) or not results:
        errors.append(f"{prefix}.assertion_results must be non-empty")
    else:
        for index, result in enumerate(results):
            result_prefix = f"{prefix}.assertion_results[{index}]"
            if not isinstance(result, dict) or set(result) != {
                "assertion_id",
                "status",
                "evidence",
            }:
                errors.append(f"{result_prefix} fields are invalid")
                continue
            assertion_id = result.get("assertion_id")
            if not _matches(assertion_id, KEBAB_CASE):
                errors.append(f"{result_prefix}.assertion_id is invalid")
            else:
                result_ids.add(assertion_id)
                result_statuses[assertion_id] = result.get("status")
            if result.get("status") not in RESULT_STATUSES:
                errors.append(f"{result_prefix}.status is invalid")
            if not _nonempty(result.get("evidence")):
                errors.append(f"{result_prefix}.evidence is required")
    if assertion_ids and result_ids != assertion_ids:
        errors.append(f"{prefix}.assertion_results must cover every assertion")

    status = value.get("status")
    if status not in RESULT_STATUSES:
        errors.append(f"{prefix}.status is invalid")
    elif status == "pass" and any(
        required and result_statuses.get(assertion_id) != "pass"
        for assertion_id, required in assertion_requirements.items()
    ):
        errors.append(
            f"{prefix}: passing case requires all required assertions to pass"
        )
    failure = value.get("failure")
    if not isinstance(failure, dict) or set(failure) != {
        "stage",
        "reason",
        "corrective_action",
    }:
        errors.append(f"{prefix}.failure fields are invalid")
    elif status in {"fail", "invalid"}:
        if not _nonempty(failure.get("stage")) or not _nonempty(
            failure.get("reason")
        ):
            errors.append(
                f"{prefix}: failed or invalid case requires an observable "
                "stage and reason"
            )
    elif any(failure.get(field) is not None for field in failure):
        errors.append(f"{prefix}: non-failing case must not contain failure details")
    return errors


def _validate_tool_calls(prefix: str, value: object) -> list[str]:
    if not isinstance(value, list):
        return [f"{prefix} must be an array"]
    errors: list[str] = []
    sequences: list[int] = []
    expected_fields = {
        "sequence",
        "name",
        "arguments",
        "status",
        "result_summary",
    }
    for index, call in enumerate(value):
        call_prefix = f"{prefix}[{index}]"
        if not isinstance(call, dict) or set(call) != expected_fields:
            errors.append(f"{call_prefix} fields are invalid")
            continue
        sequence = call.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            errors.append(f"{call_prefix}.sequence must be an integer")
        else:
            sequences.append(sequence)
        if not _nonempty(call.get("name")):
            errors.append(f"{call_prefix}.name is required")
        if not isinstance(call.get("arguments"), dict):
            errors.append(f"{call_prefix}.arguments must be an object")
        if call.get("status") not in {"success", "failure"}:
            errors.append(f"{call_prefix}.status is invalid")
        if not isinstance(call.get("result_summary"), str):
            errors.append(f"{call_prefix}.result_summary must be a string")
    if sequences != list(range(1, len(value) + 1)):
        errors.append(f"{prefix} sequence must be contiguous and ordered")
    return errors


def _validate_availability(
    prefix: str,
    value: object,
    *,
    value_type: type,
    minimum: int | None = None,
) -> list[str]:
    if not isinstance(value, dict) or set(value) != {
        "value",
        "unavailable_reason",
    }:
        return [f"{prefix} fields are invalid"]
    actual = value.get("value")
    reason = value.get("unavailable_reason")
    if actual is None:
        if not _nonempty(reason):
            return [f"{prefix} null value requires unavailable_reason"]
        return []
    if not isinstance(actual, value_type) or isinstance(actual, bool):
        return [f"{prefix}.value has an invalid type"]
    if minimum is not None and actual < minimum:
        return [f"{prefix}.value must be at least {minimum}"]
    if reason is not None:
        return [f"{prefix}.unavailable_reason must be null when value is present"]
    return []


def _matches(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _brief(value: object, limit: int = 240) -> str:
    if value is None:
        return "N/A"
    normalized = " ".join(str(value).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _is_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
