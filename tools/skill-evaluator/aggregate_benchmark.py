#!/usr/bin/env python3
"""Aggregate evaluator grading and timing files into a stable benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
from typing import Any


PENDING_EVIDENCE = "PENDING HUMAN REVIEW"


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _claude_evidence(stdout: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "final_response": "",
        "events": [],
        "metadata": {},
        "parse_errors": [],
    }
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as error:
        evidence["parse_errors"].append(f"Claude stdout is not JSON: {error}")
        return evidence
    if not isinstance(payload, dict):
        evidence["parse_errors"].append("Claude stdout JSON must be an object")
        return evidence
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
    evidence["metadata"] = {
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
    return evidence


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


def _model_evidence(target: str, result: dict[str, Any]) -> dict[str, Any]:
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
            "model_evidence": _model_evidence(str(target), result),
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
