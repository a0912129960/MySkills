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
        checks["codex_command"] = codex[:4] == [
            "codex",
            "--ask-for-approval",
            "untrusted",
            "exec",
        ]

        workspace = root / "workspace"
        run_dir = (
            workspace
            / "fixture-skill"
            / "case"
            / "with_skill"
            / "claude"
        )
        run_dir.mkdir(parents=True)
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "plan": {
                        "skill_name": "fixture-skill",
                        "case_id": "case",
                        "configuration": "with_skill",
                        "target": "claude",
                    },
                    "result": {
                        "returncode": 0,
                        "timed_out": False,
                        "duration_ms": 0,
                        "total_tokens": 0,
                    },
                }
            ),
            encoding="utf-8",
        )
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


def _execute_batch_item(
    item: dict[str, Any],
    repo_root: Path,
    *,
    model: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Execute one plan item in a disposable workspace outside the repository."""

    skill_path = Path(item["skill_path"])
    staged_skills = [
        Path(path) for path in item["companion_skill_paths"]
    ]
    if item["configuration"] == "with_skill":
        staged_skills.insert(0, skill_path)
    with runners.isolated_execution_workspace(repo_root) as execution_root:
        runners.prepare_evaluation_workspace(
            staged_skills,
            item["target"],
            execution_root,
            fixtures=item["fixtures"],
            git_fixture=item["git_fixture"],
        )
        command = runners.build_command(
            item["target"],
            item["prompt"],
            skill_path,
            model,
            explicit=item["explicit"],
            baseline=item["configuration"] == "baseline",
            safety=item["safety"],
            runtime_tools=item["runtime_tools"],
            external_tools=item["external_tools"],
            execution_workspace=execution_root,
        )
        external_tool_evidence = {}
        with runners.isolated_target_environment(
            item["target"],
            allow_ephemeral_auth_copy=True,
            allowed_commands=(
                [
                    *item["runtime_tools"],
                    *item["external_tools"],
                ]
                if item["target"] == "codex"
                else ()
            ),
            denied_read_roots=(
                [repo_root] if item["target"] == "claude" else ()
            ),
            restrict_implicit_shell=(
                item["target"] == "claude"
                and item["safety"] == "read-only"
            ),
        ) as env:
            if item["runtime_tools"] or item["external_tools"]:
                preparation = runners.prepare_runtime_environment(
                    execution_root,
                    item["runtime_tool_sources"],
                    item["runtime_tool_digests"],
                    repo_root=repo_root,
                    safety=item["safety"],
                    base_env=env,
                    external_tools=item["external_tools"],
                )
                env = preparation.environment
                external_tool_evidence = (
                    preparation.external_tool_evidence
                )
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
                timeout_seconds=timeout_seconds,
            )
        execution_workspace = str(execution_root)
        evidence = aggregate_benchmark.model_evidence(
            item["target"],
            result,
        )
        isolation_violations = (
            aggregate_benchmark.model_isolation_violations(
                item["target"],
                evidence,
                execution_root,
                allowed_commands=[
                    *item["runtime_tools"],
                    *item["external_tools"],
                ],
                audit_undeclared_bash=(
                    item["safety"] == "read-only"
                ),
            )
        )
    return {
        "plan": item,
        "target_identity": identity["stdout"].strip(),
        "target_identity_returncode": identity["returncode"],
        "external_tool_evidence": external_tool_evidence,
        "execution_workspace": execution_workspace,
        "isolation_violations": isolation_violations,
        "result": result,
    }


def _write_json(value: Any, output: Path | None = None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if output:
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _source_boundary(skill_path: Path) -> Path:
    """Return the nearest repository root, or the Skill directory itself."""

    skill = skill_path.resolve()
    for candidate in (skill, *skill.parents):
        if (candidate / ".git").exists():
            return candidate
    return skill


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
    commands_parser.add_argument("--workspace", type=Path, default=Path.cwd())

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("skill_path", type=Path)
    run_parser.add_argument("--prompt", required=True)
    run_parser.add_argument("--target", choices=["claude", "codex", "all"], default="all")
    run_parser.add_argument("--mode", choices=["explicit", "trigger"], required=True)
    run_parser.add_argument("--model")
    run_parser.add_argument("--timeout-seconds", type=float, default=300)
    run_parser.add_argument("--workspace", type=Path)
    run_parser.add_argument(
        "--allow-ephemeral-auth-copy",
        action="store_true",
    )

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

    draft_parser = subparsers.add_parser("draft-attestation")
    draft_parser.add_argument("repo_root", type=Path)
    draft_parser.add_argument("workspace", type=Path)
    draft_parser.add_argument("skill_name")
    draft_parser.add_argument("--output", type=Path, required=True)

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
                target,
                args.prompt,
                args.skill_path,
                args.model,
                execution_workspace=args.workspace.resolve(),
            )
            for target in targets
        }
        _write_json(result)
        return 0

    if args.command == "run":
        if not args.allow_ephemeral_auth_copy:
            _write_json(
                {
                    "valid": False,
                    "errors": [
                        "run requires --allow-ephemeral-auth-copy"
                    ],
                }
            )
            return 1
        skill = args.skill_path.resolve()
        source_boundary = _source_boundary(skill)
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
            with runners.isolated_execution_workspace(
                source_boundary
            ) as execution_root:
                runners.prepare_isolated_workspace(
                    skill,
                    target,
                    execution_root,
                )
                command = runners.build_command(
                    target,
                    args.prompt,
                    skill,
                    args.model,
                    explicit=args.mode == "explicit",
                    execution_workspace=execution_root,
                )
                with runners.isolated_target_environment(
                    target,
                    allow_ephemeral_auth_copy=True,
                    denied_read_roots=(
                        [source_boundary]
                        if target == "claude"
                        else ()
                    ),
                    restrict_implicit_shell=target == "claude",
                ) as env:
                    result = runners.run_command(
                        command,
                        cwd=execution_root,
                        env=env,
                        timeout_seconds=args.timeout_seconds,
                    )
                execution_workspace = str(execution_root)
                evidence = aggregate_benchmark.model_evidence(
                    target,
                    result,
                )
                isolation_violations = (
                    aggregate_benchmark.model_isolation_violations(
                        target,
                        evidence,
                        execution_root,
                    )
                )
            record = {
                "mode": args.mode,
                "target": target,
                "execution_workspace": execution_workspace,
                "isolation_violations": isolation_violations,
                "result": result,
            }
            result_path = workspace / target / "result.json"
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
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
            record = _execute_batch_item(
                item,
                repo_root,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
            result = record["result"]
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

    if args.command == "draft-attestation":
        try:
            repo_root = args.repo_root.resolve()
            document = evaluation_cases.load_cases(repo_root)
            review = evaluation_cases.audit_reviewed_skill(
                repo_root,
                args.workspace,
                document,
                args.skill_name,
            )
            skill_path = Path(review["skill_path"])
            structural = validate_skill.validate_skill(skill_path)
            if not structural["valid"]:
                raise ValueError(
                    "structural validation failed: "
                    + "; ".join(structural["errors"])
                )
            skill_review_root = args.workspace.resolve() / args.skill_name
            benchmark = aggregate_benchmark.aggregate_workspace(
                args.workspace,
                args.skill_name,
            )
            benchmark_path = skill_review_root / "benchmark.json"
            _write_json(benchmark, benchmark_path)
            report_path = skill_review_root / "review.html"
            generate_report.write_static_report(benchmark, report_path)
            relative_report = report_path.relative_to(repo_root).as_posix()
            draft = attestations.build_pending_draft(
                skill_path,
                review,
                static_review_path=relative_report,
                structural_summary=(
                    "MySkills structural validation passed for the current "
                    "Skill directory."
                ),
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _write_json({"valid": False, "errors": [str(error)]}, args.output)
            return 1
        _write_json(draft, args.output)
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
