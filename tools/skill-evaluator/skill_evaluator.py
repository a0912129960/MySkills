#!/usr/bin/env python3
"""MySkills-managed entry point for structural and offline Skill evaluation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import yaml

import aggregate_benchmark
import attestations
import evaluation_cases
import evaluation_records
import generate_report
import runners
import validate_skill


_WORKSPACE_TEXT_LIMIT = 64 * 1024
_HASH_CHUNK_SIZE = 1024 * 1024


def _workspace_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    """Capture a non-following, reviewable snapshot of a disposable workspace."""

    snapshot: dict[str, dict[str, Any]] = {}
    for current, directories, filenames in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current)
        entries = sorted([*directories, *filenames])
        for name in entries:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                target = os.readlink(path)
                payload = target.encode("utf-8", errors="surrogatepass")
                snapshot[relative] = {
                    "kind": "symlink",
                    "sha256": f"sha256:{hashlib.sha256(payload).hexdigest()}",
                    "size": len(payload),
                    "text": target,
                }
                if name in directories:
                    directories.remove(name)
                continue
            if path.is_dir():
                snapshot[relative] = {
                    "kind": "directory",
                    "sha256": None,
                    "size": None,
                    "text": None,
                }
                continue
            if not path.is_file():
                continue
            reported_size = path.stat().st_size
            preview = (
                bytearray()
                if reported_size <= _WORKSPACE_TEXT_LIMIT
                else None
            )
            digest = hashlib.sha256()
            actual_size = 0
            with path.open("rb") as stream:
                while chunk := stream.read(_HASH_CHUNK_SIZE):
                    digest.update(chunk)
                    actual_size += len(chunk)
                    if preview is not None:
                        if actual_size <= _WORKSPACE_TEXT_LIMIT:
                            preview.extend(chunk)
                        else:
                            preview = None
            text: str | None = None
            if preview is not None and b"\x00" not in preview:
                try:
                    text = bytes(preview).decode("utf-8")
                except UnicodeDecodeError:
                    text = None
            snapshot[relative] = {
                "kind": "file",
                "sha256": f"sha256:{digest.hexdigest()}",
                "size": actual_size,
                "text": text,
            }
    return snapshot


def _workspace_changes(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a deterministic before/after diff for retained raw evidence."""

    changes: list[dict[str, Any]] = []
    for relative in sorted(set(before) | set(after)):
        prior = before.get(relative)
        current = after.get(relative)
        if prior == current:
            continue
        change = (
            "created"
            if prior is None
            else "deleted"
            if current is None
            else "modified"
        )
        changes.append(
            {
                "path": relative,
                "change": change,
                "before": prior,
                "after": current,
            }
        )
    return changes


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
        run_dir = workspace / "fixture-skill" / "case" / "claude"
        run_dir.mkdir(parents=True)
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "plan": {
                        "skill_name": "fixture-skill",
                        "case_id": "case",
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
                    "schema_version": 3,
                    "observed_invocation": "explicit",
                    "invocation_evidence": "Fixture invokes the Skill explicitly.",
                    "observed_external_state": None,
                    "expectations": [
                        {
                            "assertion_id": "fixture",
                            "kind": "deterministic",
                            "description": "fixture",
                            "required": True,
                            "trajectory_observation": "not-applicable",
                            "status": "pass",
                            "evidence": "smoke",
                            "observation": "final-output",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        benchmark = aggregate_benchmark.aggregate_workspace(workspace, "fixture-skill")
        checks["benchmark"] = benchmark["summary"]["pass_rate"] == 1.0
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

    started_at = datetime.now(timezone.utc).isoformat()
    skill_path = Path(item["skill_path"])
    staged_skills = [
        skill_path,
        *(Path(path) for path in item["companion_skill_paths"]),
    ]
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
            workspace_before = _workspace_snapshot(execution_root)
            result = runners.run_command(
                command,
                cwd=execution_root,
                env=env,
                timeout_seconds=timeout_seconds,
            )
            workspace_after = _workspace_snapshot(execution_root)
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
    completed_at = datetime.now(timezone.utc).isoformat()
    return {
        "plan": item,
        "started_at": started_at,
        "completed_at": completed_at,
        "target_identity": identity["stdout"].strip(),
        "target_identity_returncode": identity["returncode"],
        "external_tool_evidence": external_tool_evidence,
        "workspace_changes": _workspace_changes(
            workspace_before,
            workspace_after,
        ),
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

    build_record_parser = subparsers.add_parser("build-record")
    build_record_parser.add_argument("repo_root", type=Path)
    build_record_parser.add_argument("workspace", type=Path)
    build_record_parser.add_argument("skill_name")
    build_record_parser.add_argument("run_id")
    build_record_parser.add_argument("--review", type=Path)
    build_record_parser.add_argument("--output", type=Path)

    publish_reviewed_parser = subparsers.add_parser("publish-reviewed")
    publish_reviewed_parser.add_argument("repo_root", type=Path)
    publish_reviewed_parser.add_argument("workspace", type=Path)
    publish_reviewed_parser.add_argument("skill_name")
    publish_reviewed_parser.add_argument("run_id")
    publish_reviewed_parser.add_argument("--review", type=Path)

    publish_record_parser = subparsers.add_parser("publish-record")
    publish_record_parser.add_argument("repo_root", type=Path)
    publish_record_parser.add_argument("record_draft", type=Path)

    select_record_parser = subparsers.add_parser("select-record")
    select_record_parser.add_argument("repo_root", type=Path)
    select_record_parser.add_argument("skill_path", type=Path)
    select_record_parser.add_argument("record_path", type=Path)
    select_record_parser.add_argument("--selected-at")

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
        plan_path = workspace / "plan.json"
        if plan_path.exists():
            _write_json(
                {
                    "valid": False,
                    "errors": [
                        f"batch plan already exists: {plan_path}"
                    ],
                },
                args.output,
            )
            return 1
        workspace.mkdir(parents=True, exist_ok=True)
        retained_plan = evaluation_cases.summarize_plan(plan)
        retained_plan["run_id"] = run_id
        retained_plan["created_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        plan_path.write_text(
            json.dumps(
                retained_plan,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        results: list[dict[str, Any]] = []
        for item in plan:
            run_root = (
                workspace
                / item["skill_name"]
                / item["case_id"]
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

    if args.command in {"build-record", "publish-reviewed"}:
        import reviewed_records

        review_path = (
            args.review
            if args.review is not None
            else args.workspace / args.skill_name / "review.json"
        )
        try:
            review = (
                reviewed_records.read_human_review(review_path)
                if review_path.is_file()
                else None
            )
            document = reviewed_records.build_reviewed_record(
                args.repo_root,
                args.workspace,
                args.skill_name,
                args.run_id,
                human_review=review,
            )
            if args.command == "build-record":
                _write_json(document, args.output)
                return 0
            output = evaluation_records.write_record(
                args.repo_root,
                document,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"ERROR: {error}")
            return 1
        print(output)
        return 0

    if args.command == "publish-record":
        try:
            document = evaluation_records.read_record_document(args.record_draft)
            output = evaluation_records.write_record(args.repo_root, document)
        except (OSError, ValueError) as error:
            print(f"ERROR: {error}")
            return 1
        print(output)
        return 0

    if args.command == "select-record":
        try:
            output = attestations.write_release_pointer(
                args.repo_root,
                args.skill_path,
                args.record_path,
                selected_at=args.selected_at,
            )
        except (OSError, ValueError) as error:
            print(f"ERROR: {error}")
            return 1
        print(output)
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
