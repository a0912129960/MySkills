#!/usr/bin/env python3
"""Convert reviewed raw evaluator workspaces into sanitized Git records."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable

import aggregate_benchmark
import evaluation_cases
import evaluation_records


TARGETS = ("claude", "codex")
GRADING_SCHEMA_VERSION = 3
REVIEW_SCHEMA_VERSION = 1
Failure = tuple[str, str, str, str]
PENDING_REVIEW = {
    "status": "pending",
    "reviewer": None,
    "reviewed_at": None,
    "reason": None,
    "corrective_action": None,
}
SECRET_PATTERNS = (
    re.compile(
        r"(?i)\b(authorization\s*:\s*(?:bearer|basic)\s+)"
        r"[A-Za-z0-9._~+/=-]+"
    ),
    re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|secret[_-]?key|password)"
        r"(\s*[:=]\s*)[^\s,;]+"
    ),
)
PRIVATE_WINDOWS_PATH = re.compile(
    r"(?i)(?:"
    r"(?<=[\"'])(?:[A-Z]:[\\/]|\\\\)[^\r\n\"']+(?=[\"'])"
    r"|\b[A-Z]:[\\/][^\s\"']+"
    r"|(?<!\\)\\\\[^\s\"']+"
    r")"
)
PRIVATE_POSIX_ROOT = (
    r"(?:home|Users|tmp|var|root|opt|private|mnt|etc|usr|srv"
    r"|[A-Za-z]/(?:home|Users|tmp|project))"
)
PRIVATE_POSIX_PATH = re.compile(
    r"(?<=[\"'])//"
    r"[A-Za-z]/(?:home|Users|tmp|project)(?:/[^\r\n\"']*)?"
    r"(?=[\"'])"
    + r"|(?<![:/A-Za-z0-9.])//"
    r"[A-Za-z]/(?:home|Users|tmp|project)(?:/[^\s\"']*)?"
    + r"|(?<=[\"'])/"
    + PRIVATE_POSIX_ROOT
    + r"(?=/|[\s\"']|$)"
    + r"(?:/[^\r\n\"']*)?(?=[\"'])"
    + r"|(?<![:/A-Za-z0-9.])/"
    + PRIVATE_POSIX_ROOT
    + r"(?=/|[\s\"']|$)"
    + r"(?:/[^\s\"']*)?"
)
PRIVATE_PATH_REDACTIONS = (
    ("private Windows path", PRIVATE_WINDOWS_PATH),
    ("private POSIX path", PRIVATE_POSIX_PATH),
)
PRIVATE_ACCOUNT_IDENTIFIER = re.compile(
    r"(?i)(\b(?:account|accounts|user|owner)\s*[:=]\s*)"
    r"([A-Za-z0-9_.-]+(?:\+|\\)[A-Za-z0-9_.-]+)"
    r"(?![A-Za-z0-9_.-])"
)
REDACTED_WHOAMI_OUTPUT = "[REDACTED_WHOAMI_OUTPUT]"
REDACTED_MIXED_WHOAMI_OUTPUT = "[REDACTED_MIXED_WHOAMI_OUTPUT]"
WHOAMI_COMMAND_MARKER = "[WHOAMI_COMMAND]"
MIXED_WHOAMI_COMMAND_MARKER = "[MIXED_WHOAMI_COMMAND]"
SHELL_STAGE_SEPARATORS = {"&", "&&", "|", "||", ";", "("}
PRIVATE_POSIX_LISTING_IDENTIFIERS = re.compile(
    r"(?<!\S)"
    r"([bcdlps-][rwxStTs-]{9}\s+\d+\s+)"
    r"((?!\[REDACTED_ACCOUNT\])\S+)(\s+)"
    r"((?!\[REDACTED_ACCOUNT\])\S+)(\s+\d+\b)"
)
PRIVATE_POSIX_SINGLE_LISTING_IDENTIFIER = re.compile(
    r"(?<!\S)"
    r"([bcdlps-][rwxStTs-]{9}\s+\d+\s+)"
    r"((?!\[REDACTED_ACCOUNT\])\S+)(\s+\d+\b)"
)
RESIDUAL_SENSITIVE_PATTERNS = {
    "email address": re.compile(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    "government identifier": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "private key material": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "private Windows path": PRIVATE_WINDOWS_PATH,
    "private POSIX path": PRIVATE_POSIX_PATH,
    "account identifier": PRIVATE_ACCOUNT_IDENTIFIER,
    "directory listing account identifier": PRIVATE_POSIX_LISTING_IDENTIFIERS,
    "single directory listing account identifier": (
        PRIVATE_POSIX_SINGLE_LISTING_IDENTIFIER
    ),
    "SSH private path": re.compile(r"(?i)(?:^|[\\/])\.ssh[\\/]"),
    "known token format": re.compile(
        r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|"
        r"sk-[A-Za-z0-9_-]{20,})\b"
    ),
    "JSON Web Token": re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
        r"[A-Za-z0-9_-]{8,}\b"
    ),
}


def build_reviewed_record(
    repo_root: Path | str,
    workspace: Path | str,
    skill_name: str,
    run_id: str,
    *,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one current-manifest record from an ignored raw workspace."""

    repo = Path(repo_root).resolve()
    document = evaluation_cases.load_cases(repo)
    current_plan = evaluation_cases.build_plan(
        repo, document, [skill_name]
    )
    saved_plan = _saved_plan(workspace, skill_name)
    plan = saved_plan or current_plan
    return build_record_from_plan(
        repo,
        workspace,
        skill_name,
        run_id,
        plan,
        current_plan=current_plan,
        human_review=human_review,
    )


def build_record_from_plan(
    repo_root: Path | str,
    workspace: Path | str,
    skill_name: str,
    run_id: str,
    plan: list[dict[str, Any]],
    *,
    current_plan: list[dict[str, Any]] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build, sanitize, and validate a record from an explicit fixed plan."""

    repo = Path(repo_root).resolve()
    raw_root = Path(workspace).resolve()
    selected = [
        item
        for item in plan
        if item.get("skill_name") == skill_name
    ]
    if not selected:
        raise ValueError(f"evaluation plan has no runs for {skill_name}")
    if any(item.get("target") not in TARGETS for item in selected):
        raise ValueError("evaluation plan contains an unsupported target")
    plan_keys = [
        (item.get("case_id"), item.get("target"))
        for item in selected
    ]
    if len(plan_keys) != len(set(plan_keys)):
        raise ValueError("evaluation plan contains duplicate case targets")
    skill_digests = {
        item.get("skill_digest")
        for item in selected
        if isinstance(item.get("skill_digest"), str)
    }
    if len(skill_digests) != 1:
        raise ValueError("evaluation plan has inconsistent Skill digests")

    review, review_warnings, sanitization_confirmed = (
        _normalized_human_review(human_review)
    )
    if not sanitization_confirmed:
        raise ValueError(
            "human sanitization confirmation is required before "
            "building a source-controlled record"
        )
    redactions: set[str] = set()
    review = {
        key: (
            _sanitize_text(value, repo, {}, redactions)
            if isinstance(value, str)
            else value
        )
        for key, value in review.items()
    }
    warnings = list(review_warnings)
    current_selected = [
        item
        for item in (current_plan or selected)
        if item.get("skill_name") == skill_name
    ]
    current_by_key = {
        (item.get("case_id"), item.get("target")): item
        for item in current_selected
    }
    if set(plan_keys) != set(current_by_key):
        current_by_key = {}
        warnings.append(
            "saved raw plan case/target coverage differs from the current manifest"
        )
    target_documents: dict[str, dict[str, Any]] = {}
    observed_starts: list[str] = []
    observed_completions: list[str] = []

    for target in TARGETS:
        target_items = [
            item for item in selected if item["target"] == target
        ]
        if not target_items:
            raise ValueError(f"evaluation plan has no {target} runs")
        cases: list[dict[str, Any]] = []
        identities: set[str] = set()
        durations: list[int] = []
        token_counts: list[int | None] = []
        for item in target_items:
            case, metadata = _build_case(
                repo,
                raw_root,
                item,
                redactions,
                current_item=current_by_key.get(
                    (item.get("case_id"), item.get("target"))
                ),
            )
            cases.append(case)
            identity = metadata.get("identity")
            if isinstance(identity, str) and identity:
                identities.add(identity)
            duration = metadata.get("duration_ms")
            if isinstance(duration, int):
                durations.append(duration)
            token_counts.append(metadata.get("total_tokens"))
            if isinstance(metadata.get("started_at"), str):
                observed_starts.append(metadata["started_at"])
            if isinstance(metadata.get("completed_at"), str):
                observed_completions.append(metadata["completed_at"])
            warnings.extend(metadata.get("warnings", []))

        runner = (
            {
                "value": next(iter(identities)),
                "unavailable_reason": None,
            }
            if len(identities) == 1
            else {
                "value": None,
                "unavailable_reason": (
                    "runner identity is missing"
                    if not identities
                    else "runner identity differs between cases"
                ),
            }
        )
        target_documents[target] = {
            "status": _case_collection_status(cases),
            "runner": runner,
            "duration_ms": sum(durations),
            "total_tokens": (
                {
                    "value": sum(
                        value
                        for value in token_counts
                        if isinstance(value, int)
                    ),
                    "unavailable_reason": None,
                }
                if token_counts
                and all(isinstance(value, int) for value in token_counts)
                else {
                    "value": None,
                    "unavailable_reason": (
                        "one or more target runs did not expose token usage"
                    ),
                }
            ),
            "cases": cases,
        }

    status = _overall_status(target_documents, review)
    if status == "human-review-required" and review["status"] != "pass":
        review = dict(PENDING_REVIEW)
    record = {
        "$schema": "../../../record.schema.json",
        "schema_version": evaluation_records.RECORD_SCHEMA_VERSION,
        "run_id": run_id,
        "skill_name": skill_name,
        "skill_digest": next(iter(skill_digests)),
        "case_manifest_digest": _plan_digest(selected),
        "evaluator_version": evaluation_records.EVALUATOR_VERSION,
        "started_at": (
            min(observed_starts)
            if observed_starts
            else datetime.now(timezone.utc).isoformat()
        ),
        "completed_at": (
            max(observed_completions)
            if observed_completions
            else datetime.now(timezone.utc).isoformat()
        ),
        "status": status,
        "targets": target_documents,
        "human_review": review,
        "warnings": sorted(set(warnings)),
        "sanitization": {
            "status": "pass",
            "redactions": sorted(redactions),
            "human_confirmed": True,
        },
    }
    residual = _residual_sensitive_findings(record)
    if residual:
        raise ValueError(
            "sanitization failed; unresolved sensitive evidence: "
            + ", ".join(residual)
        )
    errors = evaluation_records.validate_record_document(record)
    if errors:
        raise ValueError("\n".join(errors))
    return record


def read_human_review(path: Path | str) -> dict[str, Any]:
    """Read a batch-level human-review decision."""

    review = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    _, warnings, _ = _normalized_human_review(review)
    if warnings:
        raise ValueError("\n".join(warnings))
    return dict(review)


def _saved_plan(
    workspace: Path | str,
    skill_name: str,
) -> list[dict[str, Any]]:
    """Load the exact plans retained by raw runs in stable path order."""

    root = Path(workspace).resolve()
    plan_path = root / "plan.json"
    if plan_path.is_file():
        try:
            document = json.loads(
                plan_path.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{plan_path}: retained batch plan is invalid: {error}"
            ) from error
        runs = document.get("runs") if isinstance(document, dict) else None
        if (
            not isinstance(document, dict)
            or document.get("schema_version") != 4
            or not isinstance(runs, list)
            or not all(isinstance(item, dict) for item in runs)
        ):
            raise ValueError(
                f"{plan_path}: retained batch plan contract is invalid"
            )
        selected = [
            item for item in runs if item.get("skill_name") == skill_name
        ]
        if not selected:
            raise ValueError(
                f"{plan_path}: retained plan has no runs for {skill_name}"
            )
        return selected

    skill_root = root / skill_name
    plans: list[dict[str, Any]] = []
    for result_path in sorted(skill_root.glob("*/*/result.json")):
        try:
            raw = json.loads(
                result_path.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
        ):
            continue
        plan = raw.get("plan") if isinstance(raw, dict) else None
        if not isinstance(plan, dict):
            continue
        if plan.get("skill_name") != skill_name:
            continue
        if (
            plan.get("case_id") != result_path.parent.parent.name
            or plan.get("target") != result_path.parent.name
        ):
            continue
        plans.append(plan)
    return plans


def _build_case(
    repo: Path,
    raw_root: Path,
    item: dict[str, Any],
    redactions: set[str],
    *,
    current_item: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    run_root = (
        raw_root
        / item["skill_name"]
        / item["case_id"]
        / item["target"]
    )
    expected_assertions = [
        dict(assertion) for assertion in item.get("assertions", [])
    ]
    expected_invocation = (
        "explicit" if item.get("explicit") else item.get("expected_invocation")
    )
    case = {
        "case_id": item["case_id"],
        "case_version": item["case_version"],
        "kind": item["mode"],
        "prompt": item["prompt"],
        "expected": {
            "invocation": expected_invocation,
            "outcome": item["expected_outcome"],
            "assertions": expected_assertions,
        },
        "observed": {
            "invocation": "unknown",
            "invocation_evidence": (
                "Observable invocation evidence is unavailable."
            ),
            "tool_calls": [],
            "final_output": None,
            "external_state": None,
            "environment_isolation": None,
            "unavailable": [
                {
                    "field": "external_state",
                    "reason": "external state is not captured by this case",
                }
            ],
        },
        "assertion_results": _invalid_assertion_results(
            expected_assertions,
            "Reviewed grading evidence is unavailable.",
        ),
        "status": "invalid",
        "failure": {
            "stage": "raw-result",
            "reason": "Raw result is unavailable.",
            "corrective_action": "Run this exact case once and retain result.json.",
        },
    }
    metadata: dict[str, Any] = {"warnings": []}
    result_path = run_root / "result.json"
    grading_path = run_root / "grading.json"
    if not result_path.is_file():
        return case, metadata
    try:
        raw = json.loads(
            result_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        case["failure"]["reason"] = f"Raw result cannot be parsed: {error}"
        return case, metadata
    if not isinstance(raw, dict) or raw.get("plan") != item:
        case["failure"]["reason"] = (
            "Raw result plan does not match the current case manifest."
        )
        return case, metadata

    raw_environment = raw.get("environment_isolation")
    if (
        item["target"] == "claude"
        and not aggregate_benchmark.claude_environment_isolation_violations(
            raw_environment
        )
    ):
        case["observed"]["environment_isolation"] = raw_environment

    metadata["started_at"] = _valid_datetime(raw.get("started_at"))
    metadata["completed_at"] = _valid_datetime(raw.get("completed_at"))
    technical_failure: Failure | None = None
    if (
        current_item is None
        or _portable_plan_item(item) != _portable_plan_item(current_item)
    ):
        technical_failure = (
            "invalid",
            "case-manifest",
            (
                "Saved raw plan does not match the current case manifest; "
                "the record retains the plan that was actually tested."
            ),
            "Evaluate the current Skill and case manifest in a new run.",
        )
        metadata["warnings"].append(
            f"{item['target']}/{item['case_id']}: saved plan is stale"
        )
    if metadata["started_at"] is None or metadata["completed_at"] is None:
        technical_failure = technical_failure or (
            "invalid",
            "raw-result",
            "Run timestamps are missing, timezone-free, or malformed.",
            "Run a new evaluation with the current evaluator.",
        )
    identity = raw.get("target_identity")
    if (
        raw.get("target_identity_returncode") == 0
        and isinstance(identity, str)
        and identity.strip()
    ):
        metadata["identity"] = _sanitize_text(
            identity.strip(), repo, raw, redactions
        )
    else:
        technical_failure = technical_failure or (
            "invalid",
            "runner-identity",
            "Target runner identity check is missing or failed.",
            "Repair the target CLI and run a new evaluation.",
        )

    result = raw.get("result")
    evidence: dict[str, Any] | None = None
    if not isinstance(result, dict):
        technical_failure = technical_failure or (
            "invalid",
            "raw-result",
            "Model process result is missing or malformed.",
            "Run a new evaluation and retain the complete process result.",
        )
    else:
        duration = result.get("duration_ms")
        if (
            isinstance(duration, int)
            and not isinstance(duration, bool)
            and duration >= 0
        ):
            metadata["duration_ms"] = duration
        else:
            technical_failure = technical_failure or (
                "invalid",
                "raw-result",
                "Model duration is missing or malformed.",
                "Run a new evaluation with the current evaluator.",
            )
        tokens = result.get("total_tokens")
        if tokens is None or (
            isinstance(tokens, int)
            and not isinstance(tokens, bool)
            and tokens >= 0
        ):
            metadata["total_tokens"] = tokens
        else:
            technical_failure = technical_failure or (
                "invalid",
                "raw-result",
                "Model token usage is malformed.",
                "Run a new evaluation with the current evaluator.",
            )
        if result.get("returncode") != 0 or result.get("timed_out") is not False:
            technical_failure = technical_failure or (
                "invalid",
                "model-process",
                "Model process failed or timed out.",
                "Resolve the runner failure and execute a new evaluation.",
            )
        evidence = aggregate_benchmark.model_evidence(item["target"], result)
        parse_errors = [
            error
            for error in evidence.get("parse_errors", [])
            if isinstance(error, str) and error
        ]
        if parse_errors:
            technical_failure = technical_failure or (
                "invalid",
                "raw-result",
                "; ".join(parse_errors),
                "Run a new evaluation that emits parseable structured output.",
            )
        final_response = evidence.get("final_response")
        if isinstance(final_response, str) and final_response:
            case["observed"]["final_output"] = _sanitize_text(
                final_response, repo, raw, redactions
            )
        else:
            case["observed"]["unavailable"].append(
                {
                    "field": "final_output",
                    "reason": "target trace contains no final response",
                }
            )
        case["observed"]["tool_calls"] = _tool_calls(
            item["target"], evidence, repo, raw, redactions
        )

    stored_isolation = raw.get("isolation_violations")
    execution_workspace = raw.get("execution_workspace")
    if (
        not isinstance(stored_isolation, list)
        or not all(
            isinstance(value, str) and value.strip()
            for value in stored_isolation
        )
    ):
        technical_failure = technical_failure or (
            "invalid",
            "isolation",
            "Stored model isolation audit is missing or malformed.",
            "Run a new evaluation with isolation auditing enabled.",
        )
    elif evidence is not None and isinstance(execution_workspace, str):
        raw_result = raw.get("result")
        command = (
            raw_result.get("command", [])
            if isinstance(raw_result, dict)
            else []
        )
        command_violations = (
            aggregate_benchmark.claude_command_isolation_violations(
                command,
                execution_workspace,
                allowed_commands=[
                    *item["runtime_tools"],
                    *item["external_tools"],
                ],
                read_only=item.get("safety", "read-only") == "read-only",
            )
            if item["target"] == "claude"
            else []
        )
        environment_isolation = raw.get("environment_isolation")
        environment_violations = (
            aggregate_benchmark.claude_environment_isolation_violations(
                environment_isolation
            )
            if item["target"] == "claude"
            else []
        )
        skill_discovery_violations = (
            aggregate_benchmark.claude_skill_discovery_violations(
                evidence,
                aggregate_benchmark.declared_skill_names(item),
                raw.get("host_skill_names"),
            )
            if item["target"] == "claude"
            else []
        )
        recomputed = aggregate_benchmark.model_isolation_violations(
            item["target"],
            evidence,
            execution_workspace,
            allowed_commands=[
                *list(item.get("runtime_tools") or ()),
                *list(item.get("external_tools") or ()),
            ],
            audit_undeclared_bash=(
                item.get("safety", "read-only") == "read-only"
            ),
            command=command,
            environment_isolation=environment_isolation,
            allowed_skills=aggregate_benchmark.declared_skill_names(item),
            host_skill_names=raw.get("host_skill_names"),
        )
        if recomputed:
            if (
                command_violations
                or environment_violations
                or skill_discovery_violations
            ):
                technical_failure = technical_failure or (
                    "invalid",
                    "isolation",
                    "; ".join(recomputed),
                    (
                        "Fix the evaluator isolation boundary and run a new "
                        "evaluation."
                    ),
                )
            else:
                technical_failure = technical_failure or (
                    "fail",
                    "isolation",
                    "; ".join(recomputed),
                    "Restrict the Skill trajectory and run a new evaluation.",
                )
        elif stored_isolation != recomputed:
            technical_failure = technical_failure or (
                "invalid",
                "isolation",
                "Stored isolation audit does not match the observable trace.",
                "Investigate the evaluator and run a new evaluation.",
            )
    else:
        technical_failure = technical_failure or (
            "invalid",
            "isolation",
            "Execution workspace is unavailable for isolation verification.",
            "Run a new evaluation with the current evaluator.",
        )

    declared_external_tools = list(item.get("external_tools") or ())
    external_errors: list[str] = []
    try:
        minimum_versions = evaluation_cases._dependency_minimum_versions(
            repo,
            declared_external_tools,
        )
        evaluation_cases._audit_external_tool_evidence(
            result_path,
            item,
            raw,
            minimum_versions,
            external_errors,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        external_errors.append(str(error))
    if external_errors:
        technical_failure = technical_failure or (
            "invalid",
            "external-tool-evidence",
            "; ".join(external_errors),
            "Repair the external-tool fixture and run a new evaluation.",
        )

    workspace_changes, workspace_change_error = _validated_workspace_changes(
        raw.get("workspace_changes")
    )
    if workspace_change_error:
        technical_failure = technical_failure or (
            "invalid",
            "external-state",
            workspace_change_error,
            "Run a new evaluation with workspace state capture enabled.",
        )

    grading_failure: Failure | None = None
    grading = _read_grading(grading_path)
    if isinstance(grading, str):
        grading_failure = (
            "invalid",
            "grading-evidence",
            grading,
            "Complete the v3 grading template from the raw evidence.",
        )
    else:
        observed_invocation = grading["observed_invocation"]
        case["observed"]["invocation"] = observed_invocation
        invocation_evidence = grading.get("invocation_evidence")
        if (
            isinstance(invocation_evidence, str)
            and invocation_evidence.strip()
            and invocation_evidence.strip()
            != aggregate_benchmark.PENDING_EVIDENCE
        ):
            case["observed"]["invocation_evidence"] = _sanitize_text(
                invocation_evidence.strip(),
                repo,
                raw,
                redactions,
            )
        else:
            grading_failure = (
                "invalid",
                "grading-evidence",
                "Observable invocation evidence is incomplete.",
                "Describe the trace evidence used for invocation classification.",
            )
        reviewed_external_state = grading.get("observed_external_state")
        if workspace_changes:
            case["observed"]["external_state"] = _workspace_change_summary(
                workspace_changes,
                (
                    reviewed_external_state.strip()
                    if isinstance(reviewed_external_state, str)
                    and reviewed_external_state.strip()
                    else None
                ),
                repo,
                raw,
                redactions,
            )
            case["observed"]["unavailable"] = [
                unavailable
                for unavailable in case["observed"]["unavailable"]
                if unavailable.get("field") != "external_state"
            ]
        grades = grading["expectations"]
        contract_error = _grading_contract_error(
            grades, expected_assertions
        )
        if contract_error:
            grading_failure = (
                "invalid",
                "grading-evidence",
                contract_error,
                "Regenerate and complete the grading template.",
            )
        else:
            case["assertion_results"] = [
                {
                    "assertion_id": grade["assertion_id"],
                    "status": (
                        grade["status"]
                        if grade["status"] in {"pass", "fail", "invalid"}
                        else "invalid"
                    ),
                    "evidence": (
                        _sanitize_text(
                            grade["evidence"].strip(),
                            repo,
                            raw,
                            redactions,
                        )
                        if isinstance(grade.get("evidence"), str)
                        and grade["evidence"].strip()
                        and grade["evidence"].strip()
                        != aggregate_benchmark.PENDING_EVIDENCE
                        else "Reviewed grading evidence is incomplete."
                    ),
                    "observation": (
                        grade["observation"]
                        if grade.get("observation")
                        in {
                            "final-output",
                            "tool-trace",
                            "external-state",
                            "verified-absence",
                            "invocation-trace",
                            "not-applicable",
                        }
                        else "not-applicable"
                    ),
                }
                for grade in grades
            ]
            if any(
                grade["status"] == "pending"
                or grade.get("observation") == "pending"
                or not isinstance(grade.get("evidence"), str)
                or not grade["evidence"].strip()
                or grade["evidence"].strip()
                == aggregate_benchmark.PENDING_EVIDENCE
                for grade in grades
            ):
                grading_failure = (
                    "invalid",
                    "grading-evidence",
                    "One or more assertion grades are still pending.",
                    "Complete every assertion grade before publishing.",
                )
            trajectory_error = _trajectory_observation_error(
                expected_assertions,
                case["assertion_results"],
                case["observed"],
            )
            if trajectory_error:
                grading_failure = grading_failure or (
                    "invalid",
                    "trajectory-evidence",
                    trajectory_error,
                    "Record observable Tool, external-state, or "
                    "verified-absence evidence.",
                )

    invocation_failure: Failure | None = None
    if case["observed"]["invocation"] == "unknown":
        grading_failure = grading_failure or (
            "invalid",
            "grading-evidence",
            "Observed Skill invocation was not classified.",
            "Classify invocation from the observable target trace.",
        )
    elif case["observed"]["invocation"] != expected_invocation:
        invocation_failure = (
            "fail",
            "invocation",
            (
                f"Expected {expected_invocation} invocation but observed "
                f"{case['observed']['invocation']}."
            ),
            "Clarify the Skill boundary or invocation policy and run a new evaluation.",
        )
        for index, assertion in enumerate(expected_assertions):
            if assertion["id"] == "invocation-classification":
                case["assertion_results"][index] = {
                    "assertion_id": assertion["id"],
                    "status": "fail",
                    "evidence": invocation_failure[2],
                    "observation": "invocation-trace",
                }

    failure = technical_failure or grading_failure or invocation_failure
    required = {
        assertion["id"]: assertion["required"]
        for assertion in expected_assertions
    }
    required_invalid = [
        result["assertion_id"]
        for result in case["assertion_results"]
        if required.get(result["assertion_id"]) is True
        and result["status"] == "invalid"
    ]
    required_failed = [
        result["assertion_id"]
        for result in case["assertion_results"]
        if required.get(result["assertion_id"]) is True
        and result["status"] == "fail"
    ]
    if failure is not None:
        case["status"] = failure[0]
        case["failure"] = {
            "stage": failure[1],
            "reason": _sanitize_text(
                failure[2], repo, raw, redactions
            ),
            "corrective_action": _sanitize_text(
                failure[3], repo, raw, redactions
            ),
        }
    elif required_invalid:
        case["status"] = "invalid"
        case["failure"] = {
            "stage": "assertion",
            "reason": "Invalid required assertion(s): " + ", ".join(required_invalid),
            "corrective_action": "Repair the evidence and run a new evaluation.",
        }
    elif required_failed:
        case["status"] = "fail"
        case["failure"] = {
            "stage": "assertion",
            "reason": "Failed required assertion(s): " + ", ".join(required_failed),
            "corrective_action": "Improve the Skill behavior and run a new evaluation.",
        }
    else:
        case["status"] = "pass"
        case["failure"] = {
            "stage": None,
            "reason": None,
            "corrective_action": None,
        }

    for assertion, result_item in zip(
        expected_assertions, case["assertion_results"]
    ):
        if not assertion["required"] and result_item["status"] != "pass":
            metadata["warnings"].append(
                f"{item['target']}/{item['case_id']}: optional assertion "
                f"{assertion['id']} is {result_item['status']}"
            )
    return case, metadata


def _read_grading(path: Path) -> dict[str, Any] | str:
    if not path.is_file():
        return "Reviewed grading file is missing."
    try:
        grading = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return f"Reviewed grading file cannot be parsed: {error}"
    if not isinstance(grading, dict) or set(grading) != {
        "schema_version",
        "observed_invocation",
        "invocation_evidence",
        "observed_external_state",
        "expectations",
    }:
        return "Reviewed grading must use the v3 fields."
    if grading.get("schema_version") != GRADING_SCHEMA_VERSION:
        return "Reviewed grading schema_version must be 3."
    if grading.get("observed_invocation") not in {
        "explicit",
        "implicit",
        "not-invoked",
        "unknown",
    }:
        return "Reviewed grading invocation classification is invalid."
    if not isinstance(grading.get("invocation_evidence"), str):
        return "Reviewed grading invocation evidence is invalid."
    external_state = grading.get("observed_external_state")
    if external_state is not None and (
        not isinstance(external_state, str)
        or not external_state.strip()
    ):
        return "Reviewed grading external-state evidence is invalid."
    if not isinstance(grading.get("expectations"), list):
        return "Reviewed grading expectations must be an array."
    return grading


def _grading_contract_error(
    grades: list[object],
    assertions: list[dict[str, Any]],
) -> str | None:
    if len(grades) != len(assertions):
        return "Reviewed grading expectations do not match the plan."
    immutable = {
        "assertion_id": "id",
        "kind": "kind",
        "description": "description",
        "required": "required",
        "trajectory_observation": "trajectory_observation",
    }
    fields = {
        "assertion_id",
        "kind",
        "description",
        "required",
        "trajectory_observation",
        "status",
        "evidence",
        "observation",
    }
    for grade, assertion in zip(grades, assertions):
        if not isinstance(grade, dict) or set(grade) != fields:
            return "Reviewed grading expectation fields are invalid."
        if any(
            grade.get(grade_field)
            != (
                assertion.get(assertion_field)
                if assertion_field != "trajectory_observation"
                else assertion.get(
                    assertion_field,
                    "not-applicable",
                )
            )
            for grade_field, assertion_field in immutable.items()
        ):
            return "Reviewed grading changed the assertion contract."
        if grade.get("status") not in {"pending", "pass", "fail", "invalid"}:
            return "Reviewed grading assertion status is invalid."
        if grade.get("observation") not in {
            "pending",
            "final-output",
            "tool-trace",
            "external-state",
            "verified-absence",
            "invocation-trace",
            "not-applicable",
        }:
            return "Reviewed grading assertion observation is invalid."
    return None


def _invalid_assertion_results(
    assertions: Iterable[dict[str, Any]],
    evidence: str,
) -> list[dict[str, str]]:
    return [
        {
            "assertion_id": assertion["id"],
            "status": "invalid",
            "evidence": evidence,
            "observation": "not-applicable",
        }
        for assertion in assertions
    ]


def _trajectory_observation_error(
    assertions: list[dict[str, Any]],
    results: list[dict[str, Any]],
    observed: dict[str, Any],
) -> str | None:
    assertion_contracts = {
        assertion["id"]: assertion
        for assertion in assertions
    }
    for result in results:
        assertion = assertion_contracts.get(result["assertion_id"], {})
        if (
            assertion.get("kind") != "trajectory"
            or result["status"] != "pass"
        ):
            continue
        observation = result["observation"]
        expected_observation = assertion.get("trajectory_observation")
        if observation != expected_observation:
            return (
                f"{result['assertion_id']} requires "
                f"{expected_observation} evidence, not {observation}."
            )
        if observation == "tool-trace":
            if observed["tool_calls"]:
                continue
            return (
                f"{result['assertion_id']} claims tool-trace evidence "
                "but no Tool call was observed."
            )
        if observation == "external-state":
            if (
                isinstance(observed["external_state"], str)
                and observed["external_state"].strip()
            ):
                continue
            return (
                f"{result['assertion_id']} claims external-state evidence "
                "but no external state was observed."
            )
        if observation == "verified-absence":
            continue
        return (
            f"{result['assertion_id']} requires an observable trajectory "
            "classification."
        )
    return None


def _validated_workspace_changes(
    value: object,
) -> tuple[list[dict[str, Any]], str | None]:
    if value is None:
        return [], None
    if not isinstance(value, list):
        return [], "Captured workspace changes are malformed."
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, change in enumerate(value):
        prefix = f"workspace_changes[{index}]"
        if not isinstance(change, dict) or set(change) != {
            "path",
            "change",
            "before",
            "after",
        }:
            return [], f"{prefix} has invalid fields."
        path = change.get("path")
        if (
            not isinstance(path, str)
            or not path
            or "\\" in path
            or path.startswith("/")
            or any(part in ("", ".", "..") for part in path.split("/"))
            or path in seen
        ):
            return [], f"{prefix}.path is invalid."
        seen.add(path)
        kind = change.get("change")
        before = change.get("before")
        after = change.get("after")
        if kind not in {"created", "modified", "deleted"}:
            return [], f"{prefix}.change is invalid."
        if (
            (kind == "created" and (before is not None or after is None))
            or (kind == "deleted" and (before is None or after is not None))
            or (kind == "modified" and (before is None or after is None))
        ):
            return [], f"{prefix} before/after state is inconsistent."
        for label, state in (("before", before), ("after", after)):
            if state is None:
                continue
            if not _valid_workspace_state(state):
                return [], f"{prefix}.{label} is invalid."
        if before == after:
            return [], f"{prefix} does not describe a state change."
        validated.append(dict(change))
    return validated, None


def _valid_workspace_state(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "kind",
        "sha256",
        "size",
        "text",
    }:
        return False
    kind = value.get("kind")
    digest = value.get("sha256")
    size = value.get("size")
    text = value.get("text")
    if kind == "directory":
        return digest is None and size is None and text is None
    return (
        kind in {"file", "symlink"}
        and isinstance(digest, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None
        and isinstance(size, int)
        and not isinstance(size, bool)
        and size >= 0
        and (text is None or isinstance(text, str))
    )


def _workspace_change_summary(
    changes: list[dict[str, Any]],
    review_note: str | None,
    repo: Path,
    raw: dict[str, Any],
    redactions: set[str],
) -> str:
    descriptions: list[str] = []
    for change in changes:
        state = change["after"] or change["before"]
        digest = state.get("sha256")
        detail = f"{change['change']} {change['path']} ({state['kind']}"
        if digest:
            detail += f", {digest}"
        detail += ")"
        descriptions.append(detail)
    summary = (
        f"Captured workspace changes ({len(changes)}): "
        + "; ".join(descriptions)
    )
    if review_note:
        summary += f". Reviewer observation: {review_note}"
    return _sanitize_text(summary, repo, raw, redactions)


def _tool_calls(
    target: str,
    evidence: dict[str, Any],
    repo: Path,
    raw: dict[str, Any],
    redactions: set[str],
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    events = [
        event
        for event in evidence.get("events", [])
        if isinstance(event, dict)
    ]
    if target == "claude":
        results = {
            event.get("tool_use_id"): event
            for event in events
            if event.get("type") == "tool_result"
        }
        for event in events:
            if event.get("type") != "tool_use":
                continue
            result = results.get(event.get("id"))
            failed = not isinstance(result, dict) or result.get("is_error") is True
            inputs = (
                event.get("input")
                if isinstance(event.get("input"), dict)
                else {}
            )
            command = str(inputs.get("command") or "")
            arguments = _sanitize_value(
                inputs,
                repo,
                raw,
                redactions,
            )
            if _is_whoami_command(command):
                arguments["command"] = WHOAMI_COMMAND_MARKER
            elif _has_whoami_stage(command):
                arguments["command"] = (
                    MIXED_WHOAMI_COMMAND_MARKER
                    + " "
                    + str(arguments["command"])
                )
            calls.append(
                {
                    "sequence": len(calls) + 1,
                    "name": str(event.get("name") or "unknown"),
                    "arguments": arguments,
                    "status": "failure" if failed else "success",
                    "result_summary": _brief(
                        _sanitize_command_output(
                            command,
                            str(result.get("content") if result else "no result"),
                            repo,
                            raw,
                            redactions,
                        )
                    ),
                }
            )
    else:
        for event in events:
            event_type = str(event.get("type") or "")
            if event_type == "command_execution":
                exit_code = event.get("exit_code")
                status = event.get("status")
                failed = exit_code != 0 or status in {"failed", "error"}
                command = str(event.get("command") or "")
                calls.append(
                    {
                        "sequence": len(calls) + 1,
                        "name": "command_execution",
                        "arguments": {
                            "command": (
                                WHOAMI_COMMAND_MARKER
                                if _is_whoami_command(command)
                                else (
                                    (
                                        MIXED_WHOAMI_COMMAND_MARKER
                                        + " "
                                    )
                                    if _has_whoami_stage(command)
                                    else ""
                                )
                                + _sanitize_text(
                                    command,
                                    repo,
                                    raw,
                                    redactions,
                                )
                            )
                        },
                        "status": "failure" if failed else "success",
                        "result_summary": _brief(
                            _sanitize_command_output(
                                command,
                                str(event.get("output") or ""),
                                repo,
                                raw,
                                redactions,
                            )
                        ),
                    }
                )
            elif event_type == "mcp_tool_call":
                failed = (
                    event.get("error") is not None
                    or event.get("status") in {"failed", "error"}
                )
                server = str(event.get("server") or "mcp")
                tool = str(event.get("tool") or "unknown")
                calls.append(
                    {
                        "sequence": len(calls) + 1,
                        "name": f"{server}.{tool}",
                        "arguments": _sanitize_value(
                            event.get("arguments")
                            if isinstance(event.get("arguments"), dict)
                            else {},
                            repo,
                            raw,
                            redactions,
                        ),
                        "status": "failure" if failed else "success",
                        "result_summary": _brief(
                            _sanitize_text(
                                str(
                                    event.get("error")
                                    if failed
                                    else event.get("result") or ""
                                ),
                                repo,
                                raw,
                                redactions,
                            )
                        ),
                    }
                )
            elif (
                "tool" in event_type
                or event_type in {"web_search", "file_change"}
            ) and isinstance(event.get("details"), dict):
                failed = event.get("status") in {"failed", "error"}
                calls.append(
                    {
                        "sequence": len(calls) + 1,
                        "name": event_type,
                        "arguments": _sanitize_value(
                            event["details"], repo, raw, redactions
                        ),
                        "status": "failure" if failed else "success",
                        "result_summary": "",
                    }
                )
    return calls


def _is_whoami_command(command: str) -> bool:
    tokens = _split_command(command)
    if tokens is None:
        return False
    if _is_direct_whoami(tokens):
        return True
    if len(tokens) < 3:
        return False
    executable = _command_basename(tokens[0])
    if executable in {"cmd", "cmd.exe"}:
        options = {"/c", "/k"}
    elif executable in {
        "powershell",
        "powershell.exe",
        "pwsh",
        "pwsh.exe",
    }:
        options = {"-command", "-c"}
    else:
        return False
    for index, token in enumerate(tokens[1:], start=1):
        if token.casefold() in options:
            return _is_whoami_payload(tokens[index + 1 :])
    return False


def _is_whoami_payload(tokens: list[str]) -> bool:
    return _is_direct_whoami(_payload_tokens(tokens))


def _payload_tokens(tokens: list[str]) -> list[str]:
    if len(tokens) != 1:
        return tokens
    nested = _split_command(tokens[0])
    return nested if nested is not None else tokens


def _split_command(command: str) -> list[str] | None:
    try:
        normalized = (
            command.replace("\r\n", ";")
            .replace("\n", ";")
            .replace("\r", ";")
        )
        lexer = shlex.shlex(
            normalized,
            posix=False,
            punctuation_chars="&|;<>()",
        )
        lexer.whitespace_split = True
        return [
            token.strip("\"'")
            for token in lexer
        ]
    except ValueError:
        return None


def _is_direct_whoami(tokens: list[str]) -> bool:
    if (
        not tokens
        or _command_basename(tokens[0]) not in {"whoami", "whoami.exe"}
    ):
        return False
    index = 1
    while index < len(tokens):
        token = tokens[index].casefold()
        if any(character in token for character in "&|;<>"):
            return False
        if not token.startswith(("/", "-")):
            return False
        if token in {"/fo", "/format"}:
            index += 1
            if (
                index >= len(tokens)
                or tokens[index].casefold() not in {"csv", "list", "table"}
            ):
                return False
        index += 1
    return True


def _has_whoami_stage(command: str) -> bool:
    tokens = _split_command(command)
    if not tokens:
        return False
    executable = _command_basename(tokens[0])
    if executable in {"cmd", "cmd.exe"}:
        options = {"/c", "/k"}
    elif executable in {
        "powershell",
        "powershell.exe",
        "pwsh",
        "pwsh.exe",
    }:
        options = {"-command", "-c"}
    else:
        return _tokens_have_whoami_stage(tokens)
    for index, token in enumerate(tokens[1:], start=1):
        if token.casefold() in options:
            return _tokens_have_whoami_stage(
                _payload_tokens(tokens[index + 1 :])
            )
    return False


def _tokens_have_whoami_stage(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if _command_basename(token) not in {"whoami", "whoami.exe"}:
            continue
        if index == 0 or tokens[index - 1] in SHELL_STAGE_SEPARATORS:
            return True
    return False


def _command_basename(token: str) -> str:
    return token.replace("\\", "/").rsplit("/", 1)[-1].casefold()


def _sanitize_command_output(
    command: str,
    value: str,
    repo: Path,
    raw: dict[str, Any],
    redactions: set[str],
) -> str:
    sanitized = _sanitize_text(value, repo, raw, redactions)
    if _is_whoami_command(command):
        sanitized = REDACTED_WHOAMI_OUTPUT
        redactions.add("account identifier")
    elif _has_whoami_stage(command):
        sanitized = REDACTED_MIXED_WHOAMI_OUTPUT
        redactions.add("account identifier")
    return sanitized


def _sanitize_value(
    value: Any,
    repo: Path,
    raw: dict[str, Any],
    redactions: set[str],
) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _sanitize_value(item, repo, raw, redactions)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _sanitize_value(item, repo, raw, redactions)
            for item in value
        ]
    if isinstance(value, str):
        return _sanitize_text(value, repo, raw, redactions)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _sanitize_text(
    value: str,
    repo: Path,
    raw: dict[str, Any],
    redactions: set[str],
) -> str:
    sanitized = value
    replacements = [
        (str(repo), "[REDACTED_REPO_PATH]", "repository path"),
    ]
    execution_workspace = raw.get("execution_workspace")
    if isinstance(execution_workspace, str) and execution_workspace:
        replacements.insert(
            0,
            (
                execution_workspace,
                "[REDACTED_EXECUTION_PATH]",
                "execution workspace path",
            ),
        )
    for original, replacement, label in replacements:
        variants = {
            original,
            original.replace("\\", "/"),
            original.replace("/", "\\"),
        }
        changed = False
        for variant in sorted(variants, key=len, reverse=True):
            if variant and variant in sanitized:
                sanitized = sanitized.replace(variant, replacement)
                changed = True
        if changed:
            redactions.add(label)
    for label, pattern in PRIVATE_PATH_REDACTIONS:
        if pattern.search(sanitized):
            sanitized = pattern.sub("[REDACTED_PRIVATE_PATH]", sanitized)
            redactions.add(label)
    if PRIVATE_ACCOUNT_IDENTIFIER.search(sanitized):
        sanitized = PRIVATE_ACCOUNT_IDENTIFIER.sub(
            r"\1[REDACTED_ACCOUNT]",
            sanitized,
        )
        redactions.add("account identifier")
    if PRIVATE_POSIX_LISTING_IDENTIFIERS.search(sanitized):
        sanitized = PRIVATE_POSIX_LISTING_IDENTIFIERS.sub(
            r"\1[REDACTED_ACCOUNT]\3[REDACTED_ACCOUNT]\5",
            sanitized,
        )
        redactions.add("account identifier")
    if PRIVATE_POSIX_SINGLE_LISTING_IDENTIFIER.search(sanitized):
        sanitized = PRIVATE_POSIX_SINGLE_LISTING_IDENTIFIER.sub(
            r"\1[REDACTED_ACCOUNT]\3",
            sanitized,
        )
        redactions.add("account identifier")
    for pattern in SECRET_PATTERNS:
        if pattern.search(sanitized):
            if pattern.groups >= 2:
                sanitized = pattern.sub(
                    lambda match: (
                        f"{match.group(1)}{match.group(2)}[REDACTED_SECRET]"
                        if pattern.groups >= 2
                        else f"{match.group(1)}[REDACTED_SECRET]"
                    ),
                    sanitized,
                )
            else:
                sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
            redactions.add("credential-like value")
    return sanitized


def _residual_sensitive_findings(
    record: dict[str, Any],
) -> list[str]:
    findings = {
        label
        for label, pattern in RESIDUAL_SENSITIVE_PATTERNS.items()
        if any(pattern.search(text) for text in _iter_text(record))
    }
    if _has_unsanitized_whoami_output(record):
        findings.add("whoami output")
    return sorted(findings)


def _has_unsanitized_whoami_output(value: Any) -> bool:
    if isinstance(value, dict):
        arguments = value.get("arguments")
        command = (
            arguments.get("command")
            if isinstance(arguments, dict)
            else None
        )
        summary = value.get("result_summary")
        if (
            isinstance(command, str)
            and isinstance(summary, str)
        ):
            if (
                (
                    command == WHOAMI_COMMAND_MARKER
                    or _is_whoami_command(command)
                )
                and summary != REDACTED_WHOAMI_OUTPUT
            ):
                return True
            if (
                _has_whoami_stage(command)
                and summary != REDACTED_MIXED_WHOAMI_OUTPUT
            ):
                return True
            if (
                command.startswith(MIXED_WHOAMI_COMMAND_MARKER)
                and summary != REDACTED_MIXED_WHOAMI_OUTPUT
            ):
                return True
        return any(
            _has_unsanitized_whoami_output(item)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_has_unsanitized_whoami_output(item) for item in value)
    return False


def _iter_text(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_text(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_text(item)
    elif isinstance(value, str):
        yield value


def _normalized_human_review(
    value: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str], bool]:
    if value is None:
        return dict(PENDING_REVIEW), [], False
    fields = {
        "schema_version",
        "status",
        "reviewer",
        "reviewed_at",
        "reason",
        "corrective_action",
        "sanitization_confirmed",
    }
    if not isinstance(value, dict) or set(value) != fields:
        return dict(PENDING_REVIEW), [
            "human review decision is malformed; review remains pending"
        ], False
    if value.get("schema_version") != REVIEW_SCHEMA_VERSION:
        return dict(PENDING_REVIEW), [
            "human review schema_version is invalid; review remains pending"
        ], False
    sanitization_confirmed = value.get("sanitization_confirmed") is True
    if not isinstance(value.get("sanitization_confirmed"), bool):
        return dict(PENDING_REVIEW), [
            "human review sanitization confirmation must be boolean"
        ], False
    status = value.get("status")
    if status == "pending":
        if any(
            value.get(field) is not None
            for field in ("reviewer", "reviewed_at", "reason")
        ):
            return dict(PENDING_REVIEW), [
                "pending human review contains completion fields"
            ], sanitization_confirmed
        return {
            field: value[field]
            for field in PENDING_REVIEW
        }, [], sanitization_confirmed
    if (
        status != "pass"
        or not _nonempty(value.get("reviewer"))
        or _valid_datetime(value.get("reviewed_at")) is None
        or not _nonempty(value.get("reason"))
        or (
            value.get("corrective_action") is not None
            and not _nonempty(value.get("corrective_action"))
        )
    ):
        return dict(PENDING_REVIEW), [
            "human review decision is incomplete; review remains pending"
        ], sanitization_confirmed
    return {
        field: value[field]
        for field in PENDING_REVIEW
    }, [], sanitization_confirmed


def _case_collection_status(cases: list[dict[str, Any]]) -> str:
    statuses = {case["status"] for case in cases}
    if "human-review-required" in statuses:
        return "human-review-required"
    if "invalid" in statuses:
        return "invalid"
    if "fail" in statuses:
        return "fail"
    return "pass"


def _overall_status(
    targets: dict[str, dict[str, Any]],
    review: dict[str, Any],
) -> str:
    statuses = [targets[target]["status"] for target in TARGETS]
    passed = statuses.count("pass")
    if "human-review-required" in statuses:
        return "human-review-required"
    if passed == 1:
        if review["status"] != "pass":
            return "human-review-required"
        other = next(status for status in statuses if status != "pass")
        return other
    if passed == 2:
        contains_human_rubric = any(
            assertion["kind"] == "human-rubric"
            for target in TARGETS
            for case in targets[target]["cases"]
            for assertion in case["expected"]["assertions"]
        )
        if contains_human_rubric and review["status"] != "pass":
            return "human-review-required"
        return "pass"
    if "invalid" in statuses:
        return "invalid"
    return "fail"


def _plan_digest(plan: list[dict[str, Any]]) -> str:
    portable = [_portable_plan_item(item) for item in plan]
    payload = json.dumps(
        portable,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _portable_plan_item(item: dict[str, Any]) -> dict[str, Any]:
    path_fields = {
        "skill_path",
        "companion_skill_paths",
        "runtime_tool_sources",
    }
    return {
        key: value
        for key, value in item.items()
        if key not in path_fields
    }


def _valid_datetime(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return value


def _brief(value: str, limit: int = 240) -> str:
    normalized = " ".join(value.split())
    return (
        normalized
        if len(normalized) <= limit
        else normalized[: limit - 3].rstrip() + "..."
    )


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
