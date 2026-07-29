#!/usr/bin/env python3
"""Aggregate evaluator grading and timing files into a stable benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import statistics
from typing import Any, Iterable


PENDING_EVIDENCE = "PENDING HUMAN REVIEW"
_COMMAND_NOT_AUDITED = object()
_ENVIRONMENT_NOT_AUDITED = object()


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


def claude_command_isolation_violations(
    command: object,
    execution_workspace: Path | str,
    *,
    allowed_commands: Iterable[str] = (),
    read_only: bool,
) -> list[str]:
    """Validate the observable Claude launch boundary."""

    if (
        not isinstance(command, (list, tuple))
        or not command
        or not all(isinstance(value, str) for value in command)
    ):
        return ["Claude command isolation evidence is malformed"]
    command_values = list(command)
    violations: list[str] = []
    value_options = {
        "-p",
        "--output-format",
        "--mcp-config",
        "--permission-mode",
        "--tools",
        "--allowedTools",
        "--model",
    }
    flag_options = {
        "--verbose",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--no-chrome",
        "--setting-sources=project,local",
    }
    parsed_values: dict[str, list[str]] = {
        option: [] for option in value_options
    }
    parsed_flags = {option: 0 for option in flag_options}
    shape_valid = command_values[0] == "claude"
    index = 1
    while shape_valid and index < len(command_values):
        token = command_values[index]
        if token in flag_options:
            parsed_flags[token] += 1
            index += 1
            continue
        if token not in value_options or index + 1 >= len(command_values):
            shape_valid = False
            break
        parsed_values[token].append(command_values[index + 1])
        index += 2

    normalized_workspace = Path(execution_workspace).resolve().as_posix()
    normalized_workspace = normalized_workspace.rstrip("/")
    if re.match(r"^[A-Za-z]:", normalized_workspace):
        normalized_workspace = (
            "/" + normalized_workspace[0].lower()
            + normalized_workspace[2:]
        )
    workspace_pattern = f"/{normalized_workspace}/**"
    declared_commands = tuple(allowed_commands)
    read_only_tools = (
        "Read,Glob,Grep,Bash"
        if declared_commands
        else "Read,Glob,Grep"
    )
    allowed_tool_entries = [
        f"Read({workspace_pattern})",
        *(f"Bash({name} *)" for name in declared_commands),
    ]
    expected_allowed_tools = ",".join(allowed_tool_entries)
    tools_values = parsed_values["--tools"]
    expected_permission_mode = ["dontAsk"] if read_only else []
    expected_tools = (
        [read_only_tools]
        if read_only
        else ["Read,Write,Edit,Glob,Grep,Bash"]
    )
    expected_allowed_tools_values = (
        [expected_allowed_tools] if read_only else []
    )
    shape_valid = shape_valid and (
        len(parsed_values["-p"]) == 1
        and bool(parsed_values["-p"][0])
        and parsed_values["--output-format"] == ["stream-json"]
        and parsed_flags["--verbose"] == 1
        and parsed_flags["--no-session-persistence"] == 1
        and parsed_flags["--setting-sources=project,local"] == 1
        and parsed_values["--mcp-config"] == ['{"mcpServers":{}}']
        and parsed_flags["--strict-mcp-config"] == 1
        and parsed_flags["--no-chrome"] == 1
        and parsed_values["--permission-mode"]
        == expected_permission_mode
        and tools_values == expected_tools
        and parsed_values["--allowedTools"]
        == expected_allowed_tools_values
        and len(parsed_values["--model"]) <= 1
        and all(
            value and not value.startswith("-")
            for value in parsed_values["--model"]
        )
    )
    if not shape_valid:
        violations.append(
            "Claude command shape permits undeclared capabilities"
        )
    setting_source_tokens = [
        token
        for token in command_values
        if token == "--setting-sources"
        or token.startswith("--setting-sources=")
    ]
    extra_settings = [
        token
        for token in command_values
        if token == "--settings" or token.startswith("--settings=")
    ]
    if (
        setting_source_tokens != ["--setting-sources=project,local"]
        or extra_settings
    ):
        violations.append(
            "Claude command does not exclude user settings"
        )
    mcp_tokens = [
        index
        for index, token in enumerate(command_values)
        if token == "--mcp-config" or token.startswith("--mcp-config=")
    ]
    if len(mcp_tokens) != 1:
        mcp_boundary_valid = False
    else:
        mcp_index = mcp_tokens[0]
        mcp_boundary_valid = (
            command_values[mcp_index] == "--mcp-config"
            and mcp_index + 2 < len(command_values)
            and command_values[mcp_index + 1]
            == '{"mcpServers":{}}'
            and command_values[mcp_index + 2].startswith("--")
            and command_values.count("--strict-mcp-config") == 1
        )
    if not mcp_boundary_valid:
        violations.append(
            "Claude command does not enforce an empty MCP configuration"
        )
    if (
        command_values.count("--no-chrome") != 1
        or "--chrome" in command_values
    ):
        violations.append(
            "Claude command does not disable Chrome integration"
        )
    return violations


def claude_environment_isolation_violations(
    evidence: object,
) -> list[str]:
    """Validate sanitized evidence for the Claude child environment."""

    expected_keys = {
        "USERPROFILE": "profile-root",
        "HOME": "profile-root",
        "CLAUDE_CONFIG_DIR": "profile-root",
        "APPDATA": "profile/AppData/Roaming",
    }
    if (
        not isinstance(evidence, dict)
        or set(evidence)
        != {
            "schema_version",
            "paths",
            "windows_home_matches_profile",
        }
        or evidence.get("schema_version") != 1
        or not isinstance(evidence.get("paths"), dict)
        or set(evidence["paths"])
        != {
            *expected_keys,
            "LOCALAPPDATA",
            "XDG_CONFIG_HOME",
            "XDG_CACHE_HOME",
        }
    ):
        return [
            (
                "Claude environment isolation evidence is missing or "
                "malformed"
            )
        ]
    violations = [
        f"Claude environment path is not isolated: {key}"
        for key, expected in expected_keys.items()
        if evidence["paths"].get(key) != expected
    ]
    if evidence["paths"].get("LOCALAPPDATA") not in {
        "profile/AppData/Local",
        "workspace/.runtime/localappdata",
    }:
        violations.append(
            "Claude environment path is not isolated: LOCALAPPDATA"
        )
    if evidence["paths"].get("XDG_CONFIG_HOME") not in {
        "profile/.config",
        "workspace/.runtime/qmd/xdg-config",
    }:
        violations.append(
            "Claude environment path is not isolated: XDG_CONFIG_HOME"
        )
    if evidence["paths"].get("XDG_CACHE_HOME") not in {
        "profile/.cache",
        "workspace/.runtime/qmd/cache",
    }:
        violations.append(
            "Claude environment path is not isolated: XDG_CACHE_HOME"
        )
    expected_home_match: bool | None = True if os.name == "nt" else None
    if evidence.get("windows_home_matches_profile") is not expected_home_match:
        violations.append(
            "Claude Windows home variables do not match the isolated profile"
        )
    return violations


def model_isolation_violations(
    target: str,
    evidence: dict[str, Any],
    execution_workspace: Path | str,
    *,
    allowed_commands: Iterable[str] = (),
    audit_undeclared_bash: bool = True,
    command: object = _COMMAND_NOT_AUDITED,
    environment_isolation: object = _ENVIRONMENT_NOT_AUDITED,
) -> list[str]:
    """Return successful Claude tool actions outside the declared boundary."""

    if target != "claude":
        return []
    workspace = Path(execution_workspace).resolve()
    violations = (
        []
        if command is _COMMAND_NOT_AUDITED
        else claude_command_isolation_violations(
            command,
            execution_workspace,
            allowed_commands=allowed_commands,
            read_only=audit_undeclared_bash,
        )
    )
    if environment_isolation is not _ENVIRONMENT_NOT_AUDITED:
        violations.extend(
            claude_environment_isolation_violations(
                environment_isolation
            )
        )
    violations.extend(
        [
            f"Claude evidence parse error: {error}"
            for error in evidence.get("parse_errors") or ()
            if isinstance(error, str) and error
        ]
    )
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
    terminal_turn_count = 0
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
            terminal_turn_count += 1
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
        elif item_type == "mcp_tool_call":
            evidence["events"].append(
                {
                    "type": "mcp_tool_call",
                    "server": item.get("server"),
                    "tool": item.get("tool"),
                    "arguments": item.get("arguments"),
                    "result": item.get("result"),
                    "error": item.get("error"),
                    "status": item.get("status"),
                }
            )
        elif item_type in {"web_search", "file_change"}:
            evidence["events"].append(
                {
                    "type": item_type,
                    "details": item,
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
    evidence["metadata"]["terminal_turn_count"] = terminal_turn_count
    if terminal_turn_count != 1:
        evidence["parse_errors"].append(
            "Codex evidence must contain exactly one completed turn"
        )
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


def _review_state(
    expectations: list[dict[str, Any]],
    observed_invocation: object = None,
    invocation_evidence: object = None,
) -> str:
    if not expectations:
        return "pending"
    if (
        observed_invocation == "unknown"
        or not isinstance(invocation_evidence, str)
        or not invocation_evidence.strip()
        or invocation_evidence.strip() == PENDING_EVIDENCE
    ):
        return "pending"
    if any(
        item.get("status") == "pending"
        or item.get("observation") == "pending"
        or not isinstance(item.get("evidence"), str)
        or not item["evidence"].strip()
        or item["evidence"].strip() == PENDING_EVIDENCE
        for item in expectations
    ):
        return "pending"
    return (
        "fail"
        if any(
            item.get("required") is True
            and item.get("status") != "pass"
            for item in expectations
        )
        else "pass"
    )


def aggregate_workspace(workspace: Path | str, skill_name: str) -> dict[str, Any]:
    """Aggregate public grading/timing artifacts below a run workspace."""

    root = Path(workspace)
    skill_root = root / skill_name
    if not skill_root.is_dir():
        skill_root = root
    retained_plans: dict[tuple[str, str, str], dict[str, Any]] = {}
    retained_plan_path = root / "plan.json"
    if retained_plan_path.is_file():
        retained_document = json.loads(
            retained_plan_path.read_text(encoding="utf-8")
        )
        retained_runs = (
            retained_document.get("runs")
            if isinstance(retained_document, dict)
            else None
        )
        if isinstance(retained_runs, list):
            retained_plans = {
                (
                    item.get("skill_name"),
                    item.get("case_id"),
                    item.get("target"),
                ): item
                for item in retained_runs
                if isinstance(item, dict)
                and isinstance(item.get("skill_name"), str)
                and isinstance(item.get("case_id"), str)
                and isinstance(item.get("target"), str)
            }
    cases: list[dict[str, Any]] = []
    grading_paths = sorted(skill_root.glob("*/*/grading.json"))
    if not grading_paths:
        raise ValueError(
            f"{skill_root}: no reviewed batch grading files were found"
        )

    for grading_path in grading_paths:
        run_dir = grading_path.parent
        result_path = run_dir / "result.json"
        case_name = run_dir.parent.name
        target = run_dir.name
        retained_plan = retained_plans.get(
            (skill_name, case_name, target)
        )
        record: dict[str, Any] = {}
        raw_result_state = "missing"
        if result_path.is_file():
            try:
                loaded_record = json.loads(
                    result_path.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError, json.JSONDecodeError):
                raw_result_state = "malformed"
            else:
                if isinstance(loaded_record, dict):
                    record = loaded_record
                    raw_result_state = "present"
                else:
                    raw_result_state = "malformed"
        raw_plan = record.get("plan")
        plan = raw_plan if isinstance(raw_plan, dict) else retained_plan
        if not isinstance(plan, dict):
            raise ValueError(
                f"{result_path}: batch plan is unavailable from raw or retained evidence"
            )
        if (
            plan.get("skill_name") != skill_name
            or case_name != run_dir.parent.name
            or target != run_dir.name
        ):
            raise ValueError(
                f"{result_path}: plan metadata does not match the batch path"
            )
        if retained_plan is not None and plan != retained_plan:
            raw_result_state = "plan-mismatch"
            plan = retained_plan
        grading = json.loads(grading_path.read_text(encoding="utf-8"))
        if not isinstance(grading, dict) or set(grading) != {
            "schema_version",
            "observed_invocation",
            "invocation_evidence",
            "observed_external_state",
            "expectations",
        }:
            raise ValueError(
                f"{grading_path} requires the v3 grading fields"
            )
        if grading.get("schema_version") != 3:
            raise ValueError(
                f"{grading_path} grading schema_version must be 3"
            )
        observed_invocation = grading.get("observed_invocation")
        invocation_evidence = grading.get("invocation_evidence")
        observed_external_state = grading.get("observed_external_state")
        if observed_invocation not in (
            "explicit",
            "implicit",
            "not-invoked",
            "unknown",
        ):
            raise ValueError(
                f"{grading_path} observed invocation is invalid"
            )
        if (
            not isinstance(invocation_evidence, str)
            or not invocation_evidence.strip()
        ):
            raise ValueError(
                f"{grading_path} invocation evidence is invalid"
            )
        if (
            observed_external_state is not None
            and (
                not isinstance(observed_external_state, str)
                or not observed_external_state.strip()
            )
        ):
            raise ValueError(
                f"{grading_path} observed external state is invalid"
            )
        expectations = grading.get("expectations", [])
        if not isinstance(expectations, list):
            raise ValueError(f"{grading_path} expectations must be an array")

        for item in expectations:
            if set(item) != {
                "assertion_id",
                "kind",
                "description",
                "required",
                "trajectory_observation",
                "status",
                "evidence",
                "observation",
            }:
                raise ValueError(
                    f"{grading_path} expectations require the v2 typed "
                    "grading fields"
                )
            if item.get("status") not in (
                "pending",
                "pass",
                "fail",
                "invalid",
            ):
                raise ValueError(
                    f"{grading_path} expectation status is invalid"
                )
            if (
                not isinstance(item.get("assertion_id"), str)
                or not item["assertion_id"].strip()
                or item.get("kind")
                not in ("deterministic", "human-rubric", "trajectory")
                or not isinstance(item.get("description"), str)
                or not item["description"].strip()
                or not isinstance(item.get("required"), bool)
                or item.get("trajectory_observation")
                not in (
                    "tool-trace",
                    "external-state",
                    "verified-absence",
                    "not-applicable",
                )
                or item.get("observation")
                not in (
                    "pending",
                    "final-output",
                    "tool-trace",
                    "external-state",
                    "verified-absence",
                    "invocation-trace",
                    "not-applicable",
                )
            ):
                raise ValueError(
                    f"{grading_path} expectation contract is invalid"
                )

        required_expectations = [
            item for item in expectations if item["required"] is True
        ]
        passed = sum(
            1
            for item in required_expectations
            if item["status"] == "pass"
        )
        total = len(required_expectations)
        warning_count = sum(
            1
            for item in expectations
            if item["required"] is False
            and item["status"] in ("fail", "invalid")
        )
        result = record.get("result")
        if not isinstance(result, dict):
            result = {}
            if raw_result_state == "present":
                raw_result_state = "malformed"
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
            command=result.get("command", []),
            environment_isolation=record.get(
                "environment_isolation"
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
            "target": target,
            "mode": plan.get("mode"),
            "prompt": plan.get("prompt"),
            "assertions": list(plan.get("assertions") or ()),
            "safety": plan.get("safety"),
            "expected_invocation": plan.get("expected_invocation"),
            "observed_invocation": observed_invocation,
            "invocation_evidence": invocation_evidence,
            "observed_external_state": observed_external_state,
            "explicit": plan.get("explicit"),
            "skill_path": plan.get("skill_path"),
            "skill_digest": plan.get("skill_digest"),
            "fixture_sets": list(plan.get("fixture_sets") or ()),
            "fixtures": list(plan.get("fixtures") or ()),
            "git_fixture": dict(plan.get("git_fixture") or {}),
            "runtime_tools": list(plan.get("runtime_tools") or ()),
            "external_tools": list(plan.get("external_tools") or ()),
            "external_tool_evidence": dict(
                record.get("external_tool_evidence") or {}
            ),
            "workspace_changes": (
                list(record.get("workspace_changes"))
                if isinstance(record.get("workspace_changes"), list)
                else []
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
            "raw_result_state": raw_result_state,
            "model_evidence": evidence,
            "execution_workspace": execution_workspace,
            "environment_isolation": record.get(
                "environment_isolation"
            ),
            "isolation_violations": list(isolation_violations),
            "isolation_audit_state": isolation_audit_state,
            "result_path": result_path.relative_to(skill_root).as_posix(),
            "grading_path": grading_path.relative_to(skill_root).as_posix(),
            "review_state": _review_state(
                expectations,
                observed_invocation,
                invocation_evidence,
            ),
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total else 0.0,
            "warning_count": warning_count,
            "total_tokens": result.get("total_tokens"),
            "duration_ms": result.get("duration_ms"),
            "expectations": expectations,
        }
        cases.append(case)

    bucket: dict[str, Any] = {
        "passed": 0,
        "total": 0,
        "tokens": [],
        "durations_ms": [],
        "review_states": {
            "pending": 0,
            "pass": 0,
            "fail": 0,
        },
    }
    for case in cases:
        bucket["passed"] += case["passed"]
        bucket["total"] += case["total"]
        bucket["review_states"][case["review_state"]] += 1
        if isinstance(case["total_tokens"], (int, float)):
            bucket["tokens"].append(case["total_tokens"])
        if isinstance(case["duration_ms"], (int, float)):
            bucket["durations_ms"].append(case["duration_ms"])

    summary = {
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
        "schema_version": 4,
        "skill_name": skill_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
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
