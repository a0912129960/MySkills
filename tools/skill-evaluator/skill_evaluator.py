#!/usr/bin/env python3
"""MySkills-managed entry point for structural and offline Skill evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any

import yaml

import aggregate_benchmark
import generate_report
import runners
import validate_skill


def smoke_contract() -> dict[str, Any]:
    """Exercise installer-safe core capabilities without spending model tokens."""

    checks: dict[str, bool] = {}
    checks["pyyaml"] = yaml.safe_load("ok: true") == {"ok": True}

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        fixture = root / "fixture-skill"
        (fixture / "agents").mkdir(parents=True)
        (fixture / "SKILL.md").write_text(
            "---\n"
            "name: fixture-skill\n"
            "description: Validate the evaluator smoke contract.\n"
            "---\n\n"
            "# Fixture\n",
            encoding="utf-8",
        )
        (fixture / "agents" / "openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Fixture"\n'
            '  short_description: "Fixture"\n'
            '  default_prompt: "Use $fixture-skill for this fixture."\n'
            "policy:\n"
            "  allow_implicit_invocation: true\n",
            encoding="utf-8",
        )
        checks["fixture_validation"] = validate_skill.validate_skill(fixture)["valid"]

        claude = runners.build_command("claude", "Smoke test.", fixture)
        codex = runners.build_command("codex", "Smoke test.", fixture)
        checks["claude_command"] = claude[:2] == ["claude", "-p"]
        checks["codex_command"] = codex[:3] == ["codex", "exec", "--ephemeral"]

        workspace = root / "workspace"
        run_dir = workspace / "case" / "with_skill"
        run_dir.mkdir(parents=True)
        (run_dir / "grading.json").write_text(
            json.dumps(
                {
                    "expectations": [
                        {"text": "fixture", "passed": True, "evidence": "smoke"}
                    ]
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "timing.json").write_text(
            json.dumps(
                {
                    "total_tokens": 0,
                    "duration_ms": 0,
                    "total_duration_seconds": 0,
                }
            ),
            encoding="utf-8",
        )
        benchmark = aggregate_benchmark.aggregate_workspace(workspace, "fixture-skill")
        checks["benchmark"] = (
            benchmark["configurations"]["with_skill"]["pass_rate"] == 1.0
        )
        report_path = workspace / "review.html"
        generate_report.write_static_report(benchmark, report_path)
        checks["static_report"] = (
            report_path.is_file()
            and "https://" not in report_path.read_text(encoding="utf-8")
        )

    return {"passed": all(checks.values()), "checks": checks}


def _write_json(value: Any, output: Path | None = None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if output:
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("skill_path", type=Path)
    validate_parser.add_argument("--json", action="store_true", dest="as_json")

    commands_parser = subparsers.add_parser("commands")
    commands_parser.add_argument("skill_path", type=Path)
    commands_parser.add_argument("--prompt", default="Run a harmless Skill smoke test.")
    commands_parser.add_argument("--target", choices=["claude", "codex", "all"], default="all")
    commands_parser.add_argument("--model")

    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("workspace", type=Path)
    aggregate_parser.add_argument("--skill-name", required=True)
    aggregate_parser.add_argument("--output", type=Path)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("benchmark", type=Path)
    report_parser.add_argument("--output", type=Path, required=True)

    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args(argv)
    if args.command == "validate":
        result = validate_skill.validate_skill(args.skill_path)
        if args.as_json:
            _write_json(result)
        else:
            print("PASS" if result["valid"] else "FAIL")
            for error in result["errors"]:
                print(f"ERROR: {error}")
        return 0 if result["valid"] else 1

    if args.command == "commands":
        targets = runners.TARGETS if args.target == "all" else (args.target,)
        result = {
            target: runners.build_command(
                target, args.prompt, args.skill_path, args.model
            )
            for target in targets
        }
        _write_json(result)
        return 0

    if args.command == "aggregate":
        result = aggregate_benchmark.aggregate_workspace(
            args.workspace, args.skill_name
        )
        _write_json(result, args.output)
        return 0

    if args.command == "report":
        data = json.loads(args.benchmark.read_text(encoding="utf-8"))
        generate_report.write_static_report(data, args.output)
        print(args.output)
        return 0

    result = smoke_contract()
    if args.as_json:
        _write_json(result)
    else:
        for name, passed in result["checks"].items():
            print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
