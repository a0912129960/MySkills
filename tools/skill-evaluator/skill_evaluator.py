#!/usr/bin/env python3
"""MySkills-managed entry point for structural and offline Skill evaluation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any

import yaml

import aggregate_benchmark
import attestations
import evaluation_cases
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

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("skill_path", type=Path)
    run_parser.add_argument("--prompt", required=True)
    run_parser.add_argument("--target", choices=["claude", "codex", "all"], default="all")
    run_parser.add_argument("--mode", choices=["explicit", "trigger"], required=True)
    run_parser.add_argument("--model")
    run_parser.add_argument("--timeout-seconds", type=float, default=300)
    run_parser.add_argument("--workspace", type=Path)

    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("workspace", type=Path)
    aggregate_parser.add_argument("--skill-name", required=True)
    aggregate_parser.add_argument("--output", type=Path)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("benchmark", type=Path)
    report_parser.add_argument("--output", type=Path, required=True)

    digest_parser = subparsers.add_parser("digest")
    digest_parser.add_argument("skill_path", type=Path)

    verify_parser = subparsers.add_parser("verify-attestation")
    verify_parser.add_argument("skill_path", type=Path)
    verify_parser.add_argument("attestation", type=Path)

    verify_repo_parser = subparsers.add_parser("verify-repository")
    verify_repo_parser.add_argument("repo_root", type=Path)

    validate_cases_parser = subparsers.add_parser("validate-cases")
    validate_cases_parser.add_argument("repo_root", type=Path)

    plan_parser = subparsers.add_parser("plan-batch")
    plan_parser.add_argument("repo_root", type=Path)
    plan_parser.add_argument("--skills", nargs="*", default=[])
    plan_parser.add_argument("--output", type=Path)

    batch_parser = subparsers.add_parser("run-batch")
    batch_parser.add_argument("repo_root", type=Path)
    batch_parser.add_argument("--skills", nargs="*", default=[])
    batch_parser.add_argument("--workspace", type=Path)
    batch_parser.add_argument("--output", type=Path)
    batch_parser.add_argument("--model")
    batch_parser.add_argument("--timeout-seconds", type=float, default=300)
    batch_parser.add_argument("--max-runs", type=int)
    batch_parser.add_argument("--execute", action="store_true")
    batch_parser.add_argument(
        "--allow-ephemeral-auth-copy",
        action="store_true",
    )

    prepare_review_parser = subparsers.add_parser("prepare-review")
    prepare_review_parser.add_argument("workspace", type=Path)
    prepare_review_parser.add_argument("--overwrite", action="store_true")
    prepare_review_parser.add_argument("--output", type=Path)

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

    if args.command == "run":
        skill = args.skill_path.resolve()
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        workspace = (
            args.workspace.resolve()
            if args.workspace
            else Path.cwd()
            / ".scratch"
            / "skill-evals"
            / skill.name
            / run_id
        )
        targets = runners.TARGETS if args.target == "all" else (args.target,)
        results: dict[str, Any] = {}
        for target in targets:
            target_workspace = runners.prepare_isolated_workspace(
                skill,
                target,
                workspace / target,
            )
            command = runners.build_command(
                target,
                args.prompt,
                skill,
                args.model,
                explicit=args.mode == "explicit",
            )
            result = runners.run_command(
                command,
                cwd=target_workspace,
                env=runners.evaluator_environment(),
                timeout_seconds=args.timeout_seconds,
            )
            result["mode"] = args.mode
            result["target"] = target
            result_path = target_workspace / "result.json"
            result_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            results[target] = {
                "returncode": result["returncode"],
                "timed_out": result["timed_out"],
                "result": str(result_path),
            }
        _write_json(
            {
                "skill_name": skill.name,
                "skill_digest": attestations.directory_digest(skill),
                "mode": args.mode,
                "workspace": str(workspace),
                "targets": results,
            }
        )
        return 0 if all(
            item["returncode"] == 0 and not item["timed_out"]
            for item in results.values()
        ) else 1

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

    if args.command == "digest":
        print(attestations.directory_digest(args.skill_path))
        return 0

    if args.command == "verify-attestation":
        errors = attestations.validate_attestation(
            args.skill_path,
            args.attestation,
        )
        _write_json({"valid": not errors, "errors": errors})
        return 0 if not errors else 1

    if args.command == "verify-repository":
        errors = attestations.validate_repository(args.repo_root)
        _write_json({"valid": not errors, "errors": errors})
        return 0 if not errors else 1

    if args.command == "validate-cases":
        try:
            document = evaluation_cases.load_cases(args.repo_root)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _write_json({"valid": False, "errors": [str(error)]})
            return 1
        _write_json(
            {
                "valid": True,
                "skill_count": len(document["skills"]),
                "errors": [],
            }
        )
        return 0

    if args.command == "plan-batch":
        try:
            document = evaluation_cases.load_cases(args.repo_root)
            plan = evaluation_cases.build_plan(
                args.repo_root,
                document,
                args.skills,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _write_json({"valid": False, "errors": [str(error)]}, args.output)
            return 1
        _write_json(evaluation_cases.summarize_plan(plan), args.output)
        return 0

    if args.command == "run-batch":
        try:
            document = evaluation_cases.load_cases(args.repo_root)
            plan = evaluation_cases.build_plan(
                args.repo_root,
                document,
                args.skills,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _write_json({"valid": False, "errors": [str(error)]}, args.output)
            return 1
        if args.max_runs is not None:
            if args.max_runs < 1:
                _write_json(
                    {"valid": False, "errors": ["--max-runs must be positive"]},
                    args.output,
                )
                return 1
            plan = plan[: args.max_runs]
        if not args.execute:
            preview = evaluation_cases.summarize_plan(plan)
            preview["executed"] = False
            preview["authorization_required"] = (
                "Rerun with --execute --allow-ephemeral-auth-copy; "
                "this spends Claude/Codex model quota."
            )
            _write_json(preview, args.output)
            return 0
        if not args.allow_ephemeral_auth_copy:
            _write_json(
                {
                    "valid": False,
                    "errors": [
                        "--execute also requires --allow-ephemeral-auth-copy"
                    ],
                },
                args.output,
            )
            return 1

        repo_root = args.repo_root.resolve()
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        workspace = (
            args.workspace.resolve()
            if args.workspace
            else repo_root / ".scratch" / "skill-evals" / f"batch-{run_id}"
        )
        results: list[dict[str, Any]] = []
        for item in plan:
            run_root = (
                workspace
                / item["skill_name"]
                / item["case_id"]
                / item["configuration"]
                / item["target"]
            )
            execution_root = run_root / "workspace"
            skill_path = Path(item["skill_path"])
            if item["configuration"] == "with_skill":
                runners.prepare_isolated_workspace(
                    skill_path,
                    item["target"],
                    execution_root,
                )
            else:
                execution_root.mkdir(parents=True, exist_ok=True)
            command = runners.build_command(
                item["target"],
                item["prompt"],
                skill_path,
                args.model,
                explicit=item["explicit"],
                baseline=item["configuration"] == "baseline",
                safety=item["safety"],
            )
            with runners.isolated_target_environment(
                item["target"],
                allow_ephemeral_auth_copy=True,
            ) as env:
                identity = runners.run_command(
                    [item["target"], "--version"],
                    cwd=execution_root,
                    env=env,
                    timeout_seconds=30,
                )
                result = runners.run_command(
                    command,
                    cwd=execution_root,
                    env=env,
                    timeout_seconds=args.timeout_seconds,
                )
            record = {
                "plan": item,
                "target_identity": identity["stdout"].strip(),
                "target_identity_returncode": identity["returncode"],
                "result": result,
            }
            result_path = run_root / "result.json"
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            results.append(
                {
                    "skill_name": item["skill_name"],
                    "case_id": item["case_id"],
                    "configuration": item["configuration"],
                    "target": item["target"],
                    "returncode": result["returncode"],
                    "timed_out": result["timed_out"],
                    "result_path": str(result_path),
                }
            )
        batch_result = {
            "schema_version": 1,
            "executed": True,
            "run_id": run_id,
            "workspace": str(workspace),
            "run_count": len(results),
            "passed_processes": sum(
                1
                for item in results
                if item["returncode"] == 0 and not item["timed_out"]
            ),
            "results": results,
        }
        _write_json(batch_result, args.output)
        return 0 if batch_result["passed_processes"] == len(results) else 1

    if args.command == "prepare-review":
        try:
            result = evaluation_cases.prepare_review_templates(
                args.workspace,
                overwrite=args.overwrite,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _write_json({"valid": False, "errors": [str(error)]}, args.output)
            return 1
        _write_json(result, args.output)
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
