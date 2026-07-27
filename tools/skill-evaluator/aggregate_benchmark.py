#!/usr/bin/env python3
"""Aggregate evaluator grading and timing files into a stable benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
from typing import Any, Iterable


PENDING_EVIDENCE = "PENDING HUMAN REVIEW"


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _record_claude_result(
    payload: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    if isinstance(payload.get("result"), str):
        evidence["final_response"] = payload["result"]
    permission_denials = payload.get("permission_denials")
    if permission_denials is not None:
        if isinstance(permission_denials, list):
            for denial in permission_denials:
                evidence["events"].append(
                    {
                        "type": "permission_denial",
                        "details": denial,
                    }
                )
        else:
            evidence["parse_errors"].append(
                "Claude permission_denials must be an array"
            )
    evidence["metadata"].update(
        {
            key: payload.get(key)
            for key in (
                "subtype",
                "is_error",
                "num_turns",
                "stop_reason",
                "terminal_reason",
                "total_cost_usd",
                "usage",
                "modelUsage",
            )
            if key in payload
        }
    )


def _claude_message_blocks(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    message = payload.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def _claude_evidence(stdout: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "final_response": "",
        "events": [],
        "metadata": {},
        "parse_errors": [],
    }
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    if isinstance(payload, dict):
        _record_claude_result(payload, evidence)
        evidence["metadata"]["raw_event_count"] = 1
        evidence["metadata"]["terminal_result_count"] = (
            1
            if payload.get("type") == "result"
            or isinstance(payload.get("result"), str)
            else 0
        )
        return evidence
    if payload is not None:
        evidence["parse_errors"].append(
            "Claude stdout JSON must be an object"
        )
        return evidence

    event_count = 0
    terminal_result_count = 0
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            evidence["parse_errors"].append(
                f"Claude stdout line {line_number} is not JSON: {error}"
            )
            continue
        if not isinstance(event, dict):
            evidence["parse_errors"].append(
                f"Claude stdout line {line_number} must be an object"
            )
            continue
        event_count += 1
        event_type = event.get("type")
        if event_type == "result":
            terminal_result_count += 1
            _record_claude_result(event, evidence)
            continue
        if event_type == "assistant":
            for block in _claude_message_blocks(event):
                block_type = block.get("type")
                if block_type == "text" and isinstance(
                    block.get("text"),
                    str,
                ):
                    evidence["events"].append(
                        {
                            "type": "agent_message",
                            "text": block["text"],
                        }
                    )
                elif block_type == "tool_use":
                    evidence["events"].append(
                        {
                            "type": "tool_use",
                            "id": block.get("id"),
                            "name": block.get("name"),
                            "input": block.get("input"),
                        }
                    )
            continue
        if event_type == "user":
            for block in _claude_message_blocks(event):
                if block.get("type") == "tool_result":
                    evidence["events"].append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.get("tool_use_id"),
                            "content": block.get("content"),
                            "is_error": block.get("is_error"),
                        }
                    )
            continue
        if event_type == "system":
            evidence["metadata"]["system_subtype"] = event.get("subtype")
            continue
        evidence["events"].append(
            {
                "type": str(event_type or "unknown"),
                "details": event,
            }
        )
    evidence["metadata"]["raw_event_count"] = event_count
    evidence["metadata"]["terminal_result_count"] = terminal_result_count
    if event_count == 0 and not evidence["parse_errors"]:
        evidence["parse_errors"].append("Claude stdout contains no JSON events")
    return evidence


def _successful_claude_tool_uses(
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    tool_uses: dict[str, dict[str, Any]] = {}
    successful_ids: set[str] = set()
    for event in evidence.get("events") or ():
        if not isinstance(event, dict):
            continue
        if event.get("type") == "tool_use" and isinstance(
            event.get("id"),
            str,
        ):
            tool_uses[event["id"]] = event
        if (
            event.get("type") == "tool_result"
            and isinstance(event.get("tool_use_id"), str)
            and event.get("is_error") is not True
        ):
            successful_ids.add(event["tool_use_id"])
    return [
        tool_uses[tool_use_id]
        for tool_use_id in tool_uses
        if tool_use_id in successful_ids
    ]


def _claude_trace_errors(evidence: dict[str, Any]) -> list[str]:
    tool_use_ids: list[str] = []
    tool_result_ids: list[str] = []
    errors: list[str] = []
    metadata = evidence.get("metadata")
    terminal_result_count = (
        metadata.get("terminal_result_count")
        if isinstance(metadata, dict)
        else None
    )
    if terminal_result_count != 1:
        errors.append(
            "Claude evidence must contain exactly one terminal result event"
        )
    for event in evidence.get("events") or ():
        if not isinstance(event, dict):
            errors.append("Claude evidence contains a malformed event")
            continue
        if event.get("type") == "tool_use":
            tool_id = event.get("id")
            if not isinstance(tool_id, str) or not tool_id:
                errors.append("Claude tool use is missing a non-empty id")
            else:
                tool_use_ids.append(tool_id)
        elif event.get("type") == "tool_result":
            tool_id = event.get("tool_use_id")
            if not isinstance(tool_id, str) or not tool_id:
                errors.append("Claude tool result is missing a non-empty id")
            else:
                tool_result_ids.append(tool_id)
    duplicate_uses = sorted(
        {
            tool_id
            for tool_id in tool_use_ids
            if tool_use_ids.count(tool_id) > 1
        }
    )
    duplicate_results = sorted(
        {
            tool_id
            for tool_id in tool_result_ids
            if tool_result_ids.count(tool_id) > 1
        }
    )
    if duplicate_uses:
        errors.append(
            "Claude evidence contains duplicate tool use id(s): "
            + ", ".join(duplicate_uses)
        )
    if duplicate_results:
        errors.append(
            "Claude evidence contains duplicate tool result id(s): "
            + ", ".join(duplicate_results)
        )
    unmatched_uses = sorted(set(tool_use_ids) - set(tool_result_ids))
    unmatched_results = sorted(set(tool_result_ids) - set(tool_use_ids))
    if unmatched_uses:
        errors.append(
            "Claude evidence has tool use without result: "
            + ", ".join(unmatched_uses)
        )
    if unmatched_results:
        errors.append(
            "Claude evidence has result without tool use: "
            + ", ".join(unmatched_results)
        )
    return errors


def _inside_workspace(path: Path, workspace: Path) -> bool:
    try:
        path.resolve().relative_to(workspace.resolve())
    except ValueError:
        return False
    return True


def _declared_command(
    command: str,
    allowed_commands: Iterable[str],
) -> bool:
    if (
        re.search(r"[;&|<>\r\n`]", command)
        or "$(" in command
        or "\x00" in command
    ):
        return False
    normalized = command.lstrip().casefold()
    return any(
        normalized == name.casefold()
        or normalized.startswith(name.casefold() + " ")
        or normalized.startswith(name.casefold() + "\t")
        for name in allowed_commands
    )


def model_isolation_violations(
    target: str,
    evidence: dict[str, Any],
    execution_workspace: Path | str,
    *,
    allowed_commands: Iterable[str] = (),
    audit_undeclared_bash: bool = True,
) -> list[str]:
    """Return successful Claude tool actions outside the declared boundary."""

    if target != "claude":
        return []
    workspace = Path(execution_workspace).resolve()
    violations = [
        f"Claude evidence parse error: {error}"
        for error in evidence.get("parse_errors") or ()
        if isinstance(error, str) and error
    ]
    violations.extend(_claude_trace_errors(evidence))
    file_fields = {
        "Read": ("file_path",),
        "Glob": ("path", "pattern"),
        "Grep": ("path",),
        "Write": ("file_path",),
        "Edit": ("file_path",),
        "NotebookEdit": ("notebook_path",),
    }
    for event in _successful_claude_tool_uses(evidence):
        tool = event.get("name")
        tool_input = event.get("input")
        if not isinstance(tool_input, dict):
            violations.append(
                f"{tool or 'unknown'} returned success with malformed input"
            )
            continue
        if tool in file_fields:
            malformed_fields = [
                field
                for field in file_fields[tool]
                if field in tool_input
                and (
                    not isinstance(tool_input[field], str)
                    or not tool_input[field]
                )
            ]
            if malformed_fields:
                violations.append(
                    f"{tool} returned success with malformed path field(s): "
                    + ", ".join(malformed_fields)
                )
            values = [
                tool_input.get(field)
                for field in file_fields[tool]
                if isinstance(tool_input.get(field), str)
                and tool_input[field]
            ]
            if not values and tool not in {"Grep"}:
                violations.append(
                    f"{tool} returned success without an auditable path"
                )
                continue
            for value in values:
                candidate = Path(value).expanduser()
                if not candidate.is_absolute():
                    candidate = workspace / candidate
                if not _inside_workspace(candidate, workspace):
                    violations.append(
                        f"{tool} accessed {value} outside {workspace}"
                    )
        elif tool == "Bash":
            if not audit_undeclared_bash:
                continue
            command = tool_input.get("command")
            if not isinstance(command, str) or not command.strip():
                violations.append(
                    "Bash returned success without an auditable command"
                )
            elif not _declared_command(
                command,
                allowed_commands,
            ):
                violations.append(
                    f"Bash executed undeclared command: {command}"
                )
        else:
            violations.append(
                f"Successful unsupported tool use cannot be audited: {tool}"
            )
    return violations


def _codex_evidence(stdout: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "final_response": "",
        "events": [],
        "metadata": {},
        "parse_errors": [],
    }
    messages: list[str] = []
    event_count = 0
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            evidence["parse_errors"].append(
                f"Codex stdout line {line_number} is not JSON: {error}"
            )
            continue
        if not isinstance(event, dict):
            continue
        event_count += 1
        if event.get("type") == "turn.completed":
            evidence["metadata"]["usage"] = event.get("usage")
            continue
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "agent_message":
            text = item.get("text")
            if isinstance(text, str):
                messages.append(text)
                evidence["events"].append(
                    {"type": "agent_message", "text": text}
                )
        elif item_type == "command_execution":
            evidence["events"].append(
                {
                    "type": "command_execution",
                    "command": item.get("command"),
                    "output": item.get("aggregated_output"),
                    "exit_code": item.get("exit_code"),
                    "status": item.get("status"),
                }
            )
        elif item_type == "error":
            evidence["events"].append(
                {
                    "type": "error",
                    "message": item.get("message"),
                }
            )
        else:
            evidence["events"].append(
                {
                    "type": str(item_type or "unknown"),
                    "details": item,
                }
            )
    if messages:
        evidence["final_response"] = messages[-1]
    evidence["metadata"]["raw_event_count"] = event_count
    return evidence


def model_evidence(target: str, result: dict[str, Any]) -> dict[str, Any]:
    stdout = result.get("stdout")
    stderr = result.get("stderr")
    stdout_text = stdout if isinstance(stdout, str) else ""
    if target == "claude":
        evidence = _claude_evidence(stdout_text)
    elif target == "codex":
        evidence = _codex_evidence(stdout_text)
    else:
        evidence = {
            "final_response": "",
            "events": [],
            "metadata": {},
            "parse_errors": [f"Unsupported target: {target}"],
        }
    evidence["raw_stdout"] = stdout_text
    evidence["raw_stderr"] = stderr if isinstance(stderr, str) else ""
    return evidence


def _review_state(expectations: list[dict[str, Any]]) -> str:
    if not expectations:
        return "pending"
    if any(
        not isinstance(item.get("evidence"), str)
        or not item["evidence"].strip()
        or item["evidence"].strip() == PENDING_EVIDENCE
        for item in expectations
    ):
        return "pending"
    return (
        "pass"
        if all(item.get("passed") is True for item in expectations)
        else "fail"
    )


def aggregate_workspace(workspace: Path | str, skill_name: str) -> dict[str, Any]:
    """Aggregate public grading/timing artifacts below a run workspace."""

    root = Path(workspace)
    skill_root = root / skill_name
    if not skill_root.is_dir():
        skill_root = root
    configurations: dict[str, dict[str, Any]] = {}
    cases: list[dict[str, Any]] = []
    grading_paths = sorted(skill_root.glob("*/*/*/grading.json"))
    if not grading_paths:
        raise ValueError(
            f"{skill_root}: no reviewed batch grading files were found"
        )

    for grading_path in grading_paths:
        run_dir = grading_path.parent
        result_path = run_dir / "result.json"
        if not result_path.is_file():
            raise ValueError(f"{run_dir}: result.json is required")
        record = json.loads(result_path.read_text(encoding="utf-8"))
        plan = record.get("plan")
        if not isinstance(plan, dict):
            raise ValueError(f"{result_path}: batch plan is required")
        case_name = plan.get("case_id")
        configuration = plan.get("configuration")
        target = plan.get("target")
        if (
            plan.get("skill_name") != skill_name
            or case_name != run_dir.parents[1].name
            or configuration != run_dir.parent.name
            or target != run_dir.name
        ):
            raise ValueError(
                f"{result_path}: plan metadata does not match the batch path"
            )
        grading = json.loads(grading_path.read_text(encoding="utf-8"))
        expectations = grading.get("expectations", [])
        if not isinstance(expectations, list):
            raise ValueError(f"{grading_path} expectations must be an array")

        for item in expectations:
            if set(item) != {"text", "passed", "evidence"}:
                raise ValueError(
                    f"{grading_path} expectations require text/passed/evidence"
                )

        passed = sum(1 for item in expectations if item["passed"] is True)
        total = len(expectations)
        result = record.get("result")
        if not isinstance(result, dict):
            raise ValueError(f"{result_path}: process result is required")
        evidence = model_evidence(str(target), result)
        execution_workspace = record.get("execution_workspace")
        if not isinstance(execution_workspace, str) or not execution_workspace:
            execution_workspace = str(run_dir / "workspace")
        stored_isolation = record.get("isolation_violations")
        stored_isolation_valid = (
            isinstance(stored_isolation, list)
            and all(
                isinstance(violation, str) and violation.strip()
                for violation in stored_isolation
            )
        )
        recomputed_isolation = model_isolation_violations(
            str(target),
            evidence,
            execution_workspace,
                allowed_commands=[
                    *list(plan.get("runtime_tools") or ()),
                    *list(plan.get("external_tools") or ()),
                ],
                audit_undeclared_bash=(
                    plan.get("safety", "read-only") == "read-only"
                ),
            )
        if stored_isolation_valid:
            isolation_violations = list(stored_isolation)
            isolation_audit_state = (
                "fail" if isolation_violations else "pass"
            )
            if isolation_violations != recomputed_isolation:
                isolation_audit_state = "mismatch"
                isolation_violations = (
                    recomputed_isolation or list(stored_isolation)
                )
        else:
            isolation_violations = recomputed_isolation
            isolation_audit_state = (
                "missing"
                if "isolation_violations" not in record
                else "malformed"
            )
        case = {
            "case": case_name,
            "configuration": configuration,
            "target": target,
            "mode": plan.get("mode"),
            "prompt": plan.get("prompt"),
            "assertions": list(plan.get("assertions") or ()),
            "safety": plan.get("safety"),
            "expected_invocation": plan.get("expected_invocation"),
            "explicit": plan.get("explicit"),
            "skill_path": plan.get("skill_path"),
            "skill_digest": plan.get("skill_digest"),
            "baseline": dict(plan.get("baseline") or {}),
            "fixture_sets": list(plan.get("fixture_sets") or ()),
            "fixtures": list(plan.get("fixtures") or ()),
            "git_fixture": dict(plan.get("git_fixture") or {}),
            "runtime_tools": list(plan.get("runtime_tools") or ()),
            "external_tools": list(plan.get("external_tools") or ()),
            "external_tool_evidence": dict(
                record.get("external_tool_evidence") or {}
            ),
            "companion_skills": list(plan.get("companion_skills") or ()),
            "target_identity": record.get("target_identity"),
            "target_identity_returncode": record.get(
                "target_identity_returncode"
            ),
            "process": {
                key: result.get(key)
                for key in (
                    "command",
                    "returncode",
                    "timed_out",
                    "duration_ms",
                    "total_tokens",
                )
            },
            "model_evidence": evidence,
            "execution_workspace": execution_workspace,
            "isolation_violations": list(isolation_violations),
            "isolation_audit_state": isolation_audit_state,
            "result_path": result_path.relative_to(skill_root).as_posix(),
            "grading_path": grading_path.relative_to(skill_root).as_posix(),
            "review_state": _review_state(expectations),
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total else 0.0,
            "total_tokens": result.get("total_tokens"),
            "duration_ms": result.get("duration_ms"),
            "expectations": expectations,
        }
        cases.append(case)

        bucket = configurations.setdefault(
            configuration,
            {
                "passed": 0,
                "total": 0,
                "tokens": [],
                "durations_ms": [],
                "review_states": {
                    "pending": 0,
                    "pass": 0,
                    "fail": 0,
                },
            },
        )
        bucket["passed"] += passed
        bucket["total"] += total
        bucket["review_states"][case["review_state"]] += 1
        if isinstance(case["total_tokens"], (int, float)):
            bucket["tokens"].append(case["total_tokens"])
        if isinstance(case["duration_ms"], (int, float)):
            bucket["durations_ms"].append(case["duration_ms"])

    summary: dict[str, dict[str, Any]] = {}
    for name, bucket in configurations.items():
        summary[name] = {
            "passed": bucket["passed"],
            "total": bucket["total"],
            "pass_rate": (
                bucket["passed"] / bucket["total"] if bucket["total"] else 0.0
            ),
            "mean_tokens": _mean(bucket["tokens"]),
            "mean_duration_ms": _mean(bucket["durations_ms"]),
            "review_states": dict(bucket["review_states"]),
        }

    return {
        "schema_version": 3,
        "skill_name": skill_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "configurations": summary,
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    benchmark = aggregate_workspace(args.workspace, args.skill_name)
    text = json.dumps(benchmark, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
