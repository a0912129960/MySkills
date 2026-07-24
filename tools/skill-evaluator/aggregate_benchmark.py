#!/usr/bin/env python3
"""Aggregate evaluator grading and timing files into a stable benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
from typing import Any


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


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
            {"passed": 0, "total": 0, "tokens": [], "durations_ms": []},
        )
        bucket["passed"] += passed
        bucket["total"] += total
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
        }

    return {
        "schema_version": 1,
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
