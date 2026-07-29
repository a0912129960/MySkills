from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = ROOT / "tools" / "skill-evaluator"
ENTRY_POINT = TOOLS_ROOT / "skill_evaluator.py"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS_ROOT / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_plan(skill_path: Path) -> list[dict[str, object]]:
    digest = "sha256:" + ("a" * 64)
    base = {
        "skill_name": "fixture-skill",
        "skill_path": str(skill_path),
        "case_id": "normal-use",
        "case_version": 1,
        "mode": "core",
        "case_role": "normal",
        "evaluation_level": "full",
        "max_attempts": 1,
        "skill_digest": digest,
        "fixture_sets": [],
        "fixtures": [],
        "git_fixture": None,
        "runtime_tools": [],
        "runtime_tool_sources": {},
        "runtime_tool_digests": {},
        "external_tools": [],
        "companion_skills": [],
        "companion_skill_paths": [],
        "companion_skill_digests": {},
        "explicit": True,
        "prompt": "Use the fixture Skill to return the requested result.",
        "expected_outcome": "The requested result is correct.",
        "assertions": [
            {
                "id": "correct-result",
                "kind": "human-rubric",
                "description": "The requested result is correct.",
                "required": True,
            },
            {
                "id": "concise-style",
                "kind": "human-rubric",
                "description": "The result is concise.",
                "required": False,
            },
        ],
        "safety": "read-only",
        "expected_invocation": None,
    }
    return [
        {**copy.deepcopy(base), "target": target}
        for target in ("claude", "codex")
    ]


def reviewed_grading(
    *,
    required_status: str = "pass",
    optional_status: str = "fail",
) -> dict[str, object]:
    return {
        "schema_version": 3,
        "observed_invocation": "explicit",
        "invocation_evidence": (
            "The reviewed launch trace explicitly loads the fixture Skill."
        ),
        "observed_external_state": None,
        "expectations": [
            {
                "assertion_id": "correct-result",
                "kind": "human-rubric",
                "description": "The requested result is correct.",
                "required": True,
                "trajectory_observation": "not-applicable",
                "status": required_status,
                "evidence": "Reviewer checked the final output.",
                "observation": "final-output",
            },
            {
                "assertion_id": "concise-style",
                "kind": "human-rubric",
                "description": "The result is concise.",
                "required": False,
                "trajectory_observation": "not-applicable",
                "status": optional_status,
                "evidence": "The correct answer includes extra detail.",
                "observation": "final-output",
            },
        ],
    }


def final_review() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "pass",
        "reviewer": "Fixture Reviewer",
        "reviewed_at": "2026-07-27T12:05:00Z",
        "reason": "All subjective assertions were checked against the evidence.",
        "corrective_action": None,
        "sanitization_confirmed": True,
    }


def pending_review_with_sanitization() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "pending",
        "reviewer": None,
        "reviewed_at": None,
        "reason": None,
        "corrective_action": None,
        "sanitization_confirmed": True,
    }


def isolated_claude_environment_evidence() -> dict[str, object]:
    return {
        "schema_version": 2,
        "paths": {
            "USERPROFILE": "profile-root",
            "HOME": "profile-root",
            "CLAUDE_CONFIG_DIR": "profile-root",
            "APPDATA": "profile/AppData/Roaming",
            "LOCALAPPDATA": "profile/AppData/Local",
            "XDG_CONFIG_HOME": "profile/.config",
            "XDG_CACHE_HOME": "profile/.cache",
        },
        "mcp_config": {
            "path": "workspace/.claude/empty-mcp.json",
            "sha256": (
                "sha256:"
                "d8e397af03b5b032f21d0aa967086f0c"
                "78b33c87b76f2e9898ae0a144df7de02"
            ),
        },
        "windows_home_matches_profile": True if sys.platform == "win32" else None,
    }


class ReviewedRecordBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module(
            "skill_evaluator_reviewed_records",
            "reviewed_records.py",
        )
        cls.records = load_module(
            "skill_evaluator_records_for_builder",
            "evaluation_records.py",
        )
        cls.runners = load_module(
            "skill_evaluator_runners_for_builder",
            "runners.py",
        )

    def make_workspace(
        self,
        root: Path,
        *,
        claude_grade: dict[str, object] | None = None,
        codex_grade: dict[str, object] | None = None,
    ) -> tuple[Path, list[dict[str, object]]]:
        skill_path = root / "skills" / "engineering" / "fixture-skill"
        skill_path.mkdir(parents=True)
        (skill_path / "SKILL.md").write_text("# fixture\n", encoding="utf-8")
        plan = fixture_plan(skill_path)
        workspace = root / ".scratch" / "skill-evals" / "batch-fixture"
        execution = Path(tempfile.gettempdir()) / "fixture-eval-workspace"
        for item in plan:
            target = str(item["target"])
            run = (
                workspace
                / "fixture-skill"
                / "normal-use"
                / target
            )
            run.mkdir(parents=True)
            if target == "claude":
                stdout = json.dumps(
                    {
                        "type": "result",
                        "result": (
                            f"Correct result from {execution}; "
                            "Authorization: Bearer secret-token"
                        ),
                    }
                )
                grading = claude_grade or reviewed_grading()
            else:
                stdout = "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "type": "command_execution",
                                    "command": f"tool --root {execution}",
                                    "aggregated_output": "ok",
                                    "exit_code": 0,
                                    "status": "completed",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "type": "agent_message",
                                    "text": "Correct result.",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "turn.completed",
                                "usage": {
                                    "input_tokens": 10,
                                    "output_tokens": 5,
                                },
                            }
                        ),
                    ]
                )
                grading = codex_grade or reviewed_grading()
            (run / "result.json").write_text(
                json.dumps(
                    {
                        "plan": item,
                        "started_at": "2026-07-27T12:00:00Z",
                        "completed_at": "2026-07-27T12:00:01Z",
                        "target_identity": f"{target} fixture 1.0",
                        "target_identity_returncode": 0,
                        "external_tool_evidence": {},
                        "workspace_changes": [],
                        "execution_workspace": str(execution),
                        "environment_isolation": (
                            isolated_claude_environment_evidence()
                            if target == "claude"
                            else None
                        ),
                        "isolation_violations": [],
                        "result": {
                            "command": (
                                self.runners.build_command(
                                    "claude",
                                    "fixture",
                                    Path(item["skill_path"]),
                                    explicit=item["explicit"],
                                    safety=item["safety"],
                                    execution_workspace=execution,
                                )
                                if target == "claude"
                                else ["codex", "exec", "fixture"]
                            ),
                            "returncode": 0,
                            "timed_out": False,
                            "duration_ms": 25,
                            "total_tokens": 15,
                            "stdout": stdout,
                            "stderr": "",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (run / "grading.json").write_text(
                json.dumps(grading, ensure_ascii=False),
                encoding="utf-8",
            )
        return workspace, plan

    def test_builds_valid_reviewed_record_and_sanitizes_git_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-fixture",
                plan,
                human_review=final_review(),
            )

            self.assertEqual(self.records.validate_record_document(record), [])
            self.assertEqual(record["status"], "pass")
            self.assertEqual(record["targets"]["claude"]["status"], "pass")
            self.assertEqual(record["targets"]["codex"]["status"], "pass")
            self.assertTrue(record["warnings"])
            serialized = json.dumps(record, ensure_ascii=False)
            self.assertNotIn(str(Path(tempfile.gettempdir())), serialized)
            self.assertNotIn("secret-token", serialized)
            self.assertIn("[REDACTED_", serialized)
            calls = record["targets"]["codex"]["cases"][0]["observed"][
                "tool_calls"
            ]
            self.assertEqual(calls[0]["sequence"], 1)
            self.assertEqual(calls[0]["status"], "success")

    def test_required_assertion_failure_is_retained_at_assertion_stage(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(
                repo,
                claude_grade=reviewed_grading(required_status="fail"),
                codex_grade=reviewed_grading(required_status="fail"),
            )

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-failed",
                plan,
                human_review=final_review(),
            )

            self.assertEqual(self.records.validate_record_document(record), [])
            self.assertEqual(record["status"], "fail")
            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(case["status"], "fail")
            self.assertEqual(case["failure"]["stage"], "assertion")
            self.assertIn("correct-result", case["failure"]["reason"])

    def test_observed_isolation_violation_is_a_skill_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            result_path = (
                workspace
                / "fixture-skill"
                / "normal-use"
                / "claude"
                / "result.json"
            )
            raw = json.loads(result_path.read_text(encoding="utf-8"))
            outside = str(repo / "private.txt")
            raw["result"]["stdout"] = "\n".join(
                [
                    json.dumps(
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": "tool-1",
                                        "name": "Read",
                                        "input": {"file_path": outside},
                                    }
                                ]
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "user",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": "tool-1",
                                        "content": "private",
                                        "is_error": False,
                                    }
                                ]
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "result",
                            "result": "Fixture result.",
                        }
                    ),
                ]
            )
            evidence = self.builder.aggregate_benchmark.model_evidence(
                "claude",
                raw["result"],
            )
            raw["isolation_violations"] = (
                self.builder.aggregate_benchmark.model_isolation_violations(
                    "claude",
                    evidence,
                    raw["execution_workspace"],
                )
            )
            result_path.write_text(json.dumps(raw), encoding="utf-8")

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-isolation",
                plan,
                human_review=final_review(),
            )

            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(case["status"], "fail")
            self.assertEqual(case["failure"]["stage"], "isolation")

    def test_evaluator_isolation_defect_invalidates_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            result_path = (
                workspace
                / "fixture-skill"
                / "normal-use"
                / "claude"
                / "result.json"
            )
            raw = json.loads(result_path.read_text(encoding="utf-8"))
            raw["result"]["command"] = [
                "claude",
                "-p",
                "fixture",
            ]
            evidence = self.builder.aggregate_benchmark.model_evidence(
                "claude",
                raw["result"],
            )
            raw["isolation_violations"] = (
                self.builder.aggregate_benchmark.model_isolation_violations(
                    "claude",
                    evidence,
                    raw["execution_workspace"],
                    command=raw["result"]["command"],
                )
            )
            result_path.write_text(json.dumps(raw), encoding="utf-8")

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-evaluator-isolation",
                plan,
                human_review=final_review(),
            )

            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(case["status"], "invalid")
            self.assertEqual(case["failure"]["stage"], "isolation")
            self.assertIn(
                "does not exclude user settings",
                case["failure"]["reason"],
            )

    def test_missing_environment_evidence_invalidates_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            result_path = (
                workspace
                / "fixture-skill"
                / "normal-use"
                / "claude"
                / "result.json"
            )
            raw = json.loads(result_path.read_text(encoding="utf-8"))
            raw["environment_isolation"] = None
            evidence = self.builder.aggregate_benchmark.model_evidence(
                "claude",
                raw["result"],
            )
            raw["isolation_violations"] = (
                self.builder.aggregate_benchmark.model_isolation_violations(
                    "claude",
                    evidence,
                    raw["execution_workspace"],
                    command=raw["result"]["command"],
                    environment_isolation=None,
                )
            )
            result_path.write_text(json.dumps(raw), encoding="utf-8")

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-environment-isolation",
                plan,
                human_review=final_review(),
            )

            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(case["status"], "invalid")
            self.assertEqual(case["failure"]["stage"], "isolation")
            self.assertIn(
                "environment isolation evidence is missing",
                case["failure"]["reason"],
            )

    def test_stale_raw_plan_retains_the_plan_and_digest_actually_tested(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, current_plan = self.make_workspace(repo)
            stale_plan = copy.deepcopy(current_plan)
            stale_digest = "sha256:" + ("b" * 64)
            for item in stale_plan:
                item["skill_digest"] = stale_digest
                item["prompt"] = "Historical prompt actually tested."
                result_path = (
                    workspace
                    / "fixture-skill"
                    / item["case_id"]
                    / item["target"]
                    / "result.json"
                )
                raw = json.loads(result_path.read_text(encoding="utf-8"))
                raw["plan"] = item
                result_path.write_text(json.dumps(raw), encoding="utf-8")

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-stale",
                stale_plan,
                current_plan=current_plan,
                human_review=final_review(),
            )

            self.assertEqual(record["skill_digest"], stale_digest)
            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(
                case["prompt"],
                "Historical prompt actually tested.",
            )
            self.assertEqual(case["status"], "invalid")
            self.assertEqual(case["failure"]["stage"], "case-manifest")

    def test_positive_trajectory_cannot_pass_as_verified_absence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            for item in plan:
                assertion = item["assertions"][0]
                assertion["kind"] = "trajectory"
                assertion["trajectory_observation"] = "tool-trace"
                run = (
                    workspace
                    / "fixture-skill"
                    / item["case_id"]
                    / item["target"]
                )
                raw = json.loads(
                    (run / "result.json").read_text(encoding="utf-8")
                )
                raw["plan"] = item
                (run / "result.json").write_text(
                    json.dumps(raw),
                    encoding="utf-8",
                )
                grading = json.loads(
                    (run / "grading.json").read_text(encoding="utf-8")
                )
                grade = grading["expectations"][0]
                grade["kind"] = "trajectory"
                grade["trajectory_observation"] = "tool-trace"
                grade["observation"] = "verified-absence"
                (run / "grading.json").write_text(
                    json.dumps(grading),
                    encoding="utf-8",
                )

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-positive-trajectory",
                plan,
                human_review=final_review(),
            )

            self.assertEqual(record["status"], "invalid")
            self.assertEqual(
                record["targets"]["claude"]["cases"][0]["failure"]["stage"],
                "trajectory-evidence",
            )

    def test_external_state_requires_captured_workspace_change(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            for item in plan:
                assertion = item["assertions"][0]
                assertion["kind"] = "trajectory"
                assertion["trajectory_observation"] = "external-state"
                run = (
                    workspace
                    / "fixture-skill"
                    / item["case_id"]
                    / item["target"]
                )
                raw_path = run / "result.json"
                raw = json.loads(raw_path.read_text(encoding="utf-8"))
                raw["plan"] = item
                raw_path.write_text(json.dumps(raw), encoding="utf-8")
                grading_path = run / "grading.json"
                grading = json.loads(
                    grading_path.read_text(encoding="utf-8")
                )
                grading["observed_external_state"] = (
                    "Reviewer claims output.txt changed."
                )
                grade = grading["expectations"][0]
                grade["kind"] = "trajectory"
                grade["trajectory_observation"] = "external-state"
                grade["observation"] = "external-state"
                grading_path.write_text(
                    json.dumps(grading),
                    encoding="utf-8",
                )

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-no-state-capture",
                plan,
                human_review=final_review(),
            )

            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(case["status"], "invalid")
            self.assertEqual(case["failure"]["stage"], "trajectory-evidence")
            self.assertIsNone(case["observed"]["external_state"])

    def test_external_state_is_derived_from_captured_workspace_change(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            for item in plan:
                assertion = item["assertions"][0]
                assertion["kind"] = "trajectory"
                assertion["trajectory_observation"] = "external-state"
                run = (
                    workspace
                    / "fixture-skill"
                    / item["case_id"]
                    / item["target"]
                )
                raw_path = run / "result.json"
                raw = json.loads(raw_path.read_text(encoding="utf-8"))
                raw["plan"] = item
                raw["workspace_changes"] = [
                    {
                        "path": "output.txt",
                        "change": "created",
                        "before": None,
                        "after": {
                            "kind": "file",
                            "sha256": "sha256:" + ("b" * 64),
                            "size": 9,
                            "text": "completed",
                        },
                    }
                ]
                raw_path.write_text(json.dumps(raw), encoding="utf-8")
                grading_path = run / "grading.json"
                grading = json.loads(
                    grading_path.read_text(encoding="utf-8")
                )
                grading["observed_external_state"] = (
                    "Reviewer confirmed output.txt."
                )
                grade = grading["expectations"][0]
                grade["kind"] = "trajectory"
                grade["trajectory_observation"] = "external-state"
                grade["observation"] = "external-state"
                grading_path.write_text(
                    json.dumps(grading),
                    encoding="utf-8",
                )

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-state-capture",
                plan,
                human_review=final_review(),
            )

            case = record["targets"]["claude"]["cases"][0]
            self.assertEqual(case["status"], "pass")
            self.assertIn("output.txt", case["observed"]["external_state"])
            self.assertIn(
                "sha256:" + ("b" * 64),
                case["observed"]["external_state"],
            )

    def test_nonpending_grade_cannot_keep_pending_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            grading = reviewed_grading()
            grading["expectations"][0]["observation"] = "pending"
            workspace, plan = self.make_workspace(
                repo,
                claude_grade=grading,
                codex_grade=copy.deepcopy(grading),
            )

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-pending-observation",
                plan,
                human_review=final_review(),
            )

            self.assertEqual(record["status"], "invalid")
            self.assertTrue(
                all(
                    target["cases"][0]["failure"]["stage"]
                    == "grading-evidence"
                    for target in record["targets"].values()
                )
            )

    def test_missing_or_malformed_review_evidence_is_invalid_not_a_skill_fail(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            (
                workspace
                / "fixture-skill"
                / "normal-use"
                / "claude"
                / "grading.json"
            ).unlink()

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-invalid",
                plan,
                human_review=final_review(),
            )

            self.assertEqual(self.records.validate_record_document(record), [])
            self.assertEqual(record["status"], "invalid")
            self.assertEqual(
                record["targets"]["claude"]["cases"][0]["status"],
                "invalid",
            )
            self.assertEqual(
                record["targets"]["claude"]["cases"][0]["failure"]["stage"],
                "grading-evidence",
            )

    def test_both_invalid_targets_remain_invalid_before_review_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            for grading_path in workspace.rglob("grading.json"):
                grading_path.unlink()

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-both-invalid",
                plan,
                human_review=pending_review_with_sanitization(),
            )

            self.assertEqual(record["status"], "invalid")
            self.assertEqual(record["human_review"]["status"], "pending")

    def test_both_failed_targets_remain_failed_before_review_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(
                repo,
                claude_grade=reviewed_grading(required_status="fail"),
                codex_grade=reviewed_grading(required_status="fail"),
            )

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-both-failed",
                plan,
                human_review=pending_review_with_sanitization(),
            )

            self.assertEqual(record["status"], "fail")

    def test_one_platform_pass_requires_review_then_remains_failed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(
                repo,
                codex_grade=reviewed_grading(required_status="fail"),
            )

            pending = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-partial",
                plan,
                human_review=pending_review_with_sanitization(),
            )
            reviewed = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-partial-reviewed",
                plan,
                human_review=final_review(),
            )

            self.assertEqual(pending["status"], "human-review-required")
            self.assertEqual(pending["human_review"]["status"], "pending")
            self.assertEqual(reviewed["status"], "fail")
            self.assertNotEqual(reviewed["status"], "pass")

    def test_record_build_fails_closed_without_sanitization_confirmation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)

            with self.assertRaisesRegex(
                ValueError,
                "sanitization confirmation",
            ):
                self.builder.build_record_from_plan(
                    repo,
                    workspace,
                    "fixture-skill",
                    "20260727T120000Z-unconfirmed",
                    plan,
                )

    def test_residual_private_data_blocks_record_construction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            result_path = (
                workspace
                / "fixture-skill"
                / "normal-use"
                / "codex"
                / "result.json"
            )
            raw = json.loads(result_path.read_text(encoding="utf-8"))
            raw["result"]["stdout"] = "\n".join(
                [
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {
                                "type": "agent_message",
                                "text": "Employee SSN 123-45-6789",
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {},
                        }
                    ),
                ]
            )
            result_path.write_text(json.dumps(raw), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "government identifier",
            ):
                self.builder.build_record_from_plan(
                    repo,
                    workspace,
                    "fixture-skill",
                    "20260727T120000Z-sensitive",
                    plan,
                    human_review=final_review(),
                )

    def test_common_credential_labels_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            result_path = (
                workspace
                / "fixture-skill"
                / "normal-use"
                / "codex"
                / "result.json"
            )
            raw = json.loads(result_path.read_text(encoding="utf-8"))
            raw["result"]["stdout"] = "\n".join(
                [
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {
                                "type": "agent_message",
                                "text": (
                                    "client_secret="
                                    "very-secret-production-credential"
                                ),
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {},
                        }
                    ),
                ]
            )
            result_path.write_text(json.dumps(raw), encoding="utf-8")

            record = self.builder.build_record_from_plan(
                repo,
                workspace,
                "fixture-skill",
                "20260727T120000Z-credential-label",
                plan,
                human_review=final_review(),
            )

            serialized = json.dumps(record, ensure_ascii=False)
            self.assertNotIn(
                "very-secret-production-credential",
                serialized,
            )
            self.assertIn("credential-like value", record["sanitization"]["redactions"])

    def test_sensitive_raw_plan_input_is_scanned_before_record_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            workspace, plan = self.make_workspace(repo)
            for item in plan:
                item["prompt"] = "Employee SSN 123-45-6789"
                result_path = (
                    workspace
                    / "fixture-skill"
                    / item["case_id"]
                    / item["target"]
                    / "result.json"
                )
                raw = json.loads(result_path.read_text(encoding="utf-8"))
                raw["plan"] = item
                result_path.write_text(json.dumps(raw), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "government identifier",
            ):
                self.builder.build_record_from_plan(
                    repo,
                    workspace,
                    "fixture-skill",
                    "20260727T120000Z-sensitive-input",
                    plan,
                    human_review=final_review(),
                )

    def test_cli_build_record_uses_current_manifest_without_manual_draft(
        self,
    ) -> None:
        cases = load_module(
            "skill_evaluator_cases_for_record_cli",
            "evaluation_cases.py",
        )
        document = cases.load_cases(ROOT)
        plan = cases.build_plan(ROOT, document, ["skill-evaluator"])
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            retained_plan = cases.summarize_plan(plan)
            retained_plan["run_id"] = "fixture-cli"
            retained_plan["created_at"] = "2026-07-27T12:00:00Z"
            (workspace / "plan.json").write_text(
                json.dumps(retained_plan),
                encoding="utf-8",
            )
            execution = (
                Path(tempfile.gettempdir()) / "fixture-cli-evaluation"
            )
            for item in plan:
                target = item["target"]
                run = (
                    workspace
                    / item["skill_name"]
                    / item["case_id"]
                    / target
                )
                run.mkdir(parents=True)
                needs_tool = any(
                    assertion.get("trajectory_observation")
                    == "tool-trace"
                    for assertion in item["assertions"]
                )
                if target == "claude":
                    events = []
                    if needs_tool:
                        events.extend(
                            [
                                {
                                    "type": "assistant",
                                    "message": {
                                        "content": [
                                            {
                                                "type": "tool_use",
                                                "id": "tool-1",
                                                "name": "Bash",
                                                "input": {
                                                    "command": (
                                                        "skill-evaluator smoke"
                                                    )
                                                },
                                            }
                                        ]
                                    },
                                },
                                {
                                    "type": "user",
                                    "message": {
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": "tool-1",
                                                "content": "pass",
                                                "is_error": False,
                                            }
                                        ]
                                    },
                                },
                            ]
                        )
                    events.append(
                        {
                            "type": "result",
                            "result": "Fixture result satisfies the oracle.",
                        }
                    )
                    stdout = "\n".join(
                        json.dumps(event) for event in events
                    )
                else:
                    events = []
                    if needs_tool:
                        events.append(
                            {
                                "type": "item.completed",
                                "item": {
                                    "type": "command_execution",
                                    "command": "skill-evaluator smoke",
                                    "aggregated_output": "pass",
                                    "exit_code": 0,
                                    "status": "completed",
                                },
                            }
                        )
                    events.extend(
                        [
                            {
                                "type": "item.completed",
                                "item": {
                                    "type": "agent_message",
                                    "text": (
                                        "Fixture result satisfies the oracle."
                                    ),
                                },
                            },
                            {
                                "type": "turn.completed",
                                "usage": {
                                    "input_tokens": 10,
                                    "output_tokens": 5,
                                },
                            },
                        ]
                    )
                    stdout = "\n".join(
                        json.dumps(event) for event in events
                    )
                (run / "result.json").write_text(
                    json.dumps(
                        {
                            "plan": item,
                            "started_at": "2026-07-27T12:00:00Z",
                            "completed_at": "2026-07-27T12:00:01Z",
                            "target_identity": f"{target} fixture 1.0",
                            "target_identity_returncode": 0,
                            "external_tool_evidence": {},
                            "execution_workspace": str(execution),
                            "environment_isolation": (
                                isolated_claude_environment_evidence()
                                if target == "claude"
                                else None
                            ),
                            "isolation_violations": [],
                            "result": {
                                "command": (
                                    self.runners.build_command(
                                        "claude",
                                        "fixture",
                                        Path(item["skill_path"]),
                                        explicit=item["explicit"],
                                        safety=item["safety"],
                                        runtime_tools=item["runtime_tools"],
                                        external_tools=item["external_tools"],
                                        execution_workspace=execution,
                                    )
                                    if target == "claude"
                                    else ["codex", "exec", "fixture"]
                                ),
                                "returncode": 0,
                                "timed_out": False,
                                "duration_ms": 5,
                                "total_tokens": 15,
                                "stdout": stdout,
                                "stderr": "",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                expected_invocation = (
                    "explicit"
                    if item["explicit"]
                    else item["expected_invocation"]
                )
                (run / "grading.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 3,
                            "observed_invocation": expected_invocation,
                            "invocation_evidence": (
                                "Fixture reviewer checked the target trace."
                            ),
                            "observed_external_state": (
                                "Fixture output state matches the oracle."
                                if any(
                                    assertion.get(
                                        "trajectory_observation"
                                    )
                                    == "external-state"
                                    for assertion in item["assertions"]
                                )
                                else None
                            ),
                            "expectations": [
                                {
                                    "assertion_id": assertion["id"],
                                    "kind": assertion["kind"],
                                    "description": assertion["description"],
                                    "required": assertion["required"],
                                    "trajectory_observation": assertion.get(
                                        "trajectory_observation",
                                        "not-applicable",
                                    ),
                                    "status": "pass",
                                    "evidence": "Fixture reviewer checked it.",
                                    "observation": (
                                        assertion["trajectory_observation"]
                                        if assertion["kind"] == "trajectory"
                                        else (
                                            "invocation-trace"
                                            if assertion["id"]
                                            == "invocation-classification"
                                            else "final-output"
                                        )
                                    ),
                                }
                                for assertion in item["assertions"]
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
            review_path = workspace / "skill-evaluator" / "review.json"
            review_path.write_text(
                json.dumps(final_review()),
                encoding="utf-8",
            )
            output = workspace / "record-draft.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ENTRY_POINT),
                    "build-record",
                    str(ROOT),
                    str(workspace),
                    "skill-evaluator",
                    "20260727T120000Z-cli",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "pass")
            self.assertEqual(self.records.validate_record_document(record), [])

            missing_result = next(
                workspace.glob("skill-evaluator/*/codex/result.json")
            )
            missing_result.unlink()
            partial_output = workspace / "partial-record-draft.json"
            partial = subprocess.run(
                [
                    sys.executable,
                    str(ENTRY_POINT),
                    "build-record",
                    str(ROOT),
                    str(workspace),
                    "skill-evaluator",
                    "20260727T120000Z-cli-partial",
                    "--output",
                    str(partial_output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(partial.returncode, 0, partial.stderr)
            partial_record = json.loads(
                partial_output.read_text(encoding="utf-8")
            )
            self.assertEqual(partial_record["status"], "invalid")
            self.assertTrue(
                any(
                    case["failure"]["stage"] == "raw-result"
                    for case in partial_record["targets"]["codex"]["cases"]
                    if case["status"] == "invalid"
                )
            )


if __name__ == "__main__":
    unittest.main()
