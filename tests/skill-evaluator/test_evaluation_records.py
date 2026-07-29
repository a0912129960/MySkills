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


def load_records_module():
    path = TOOLS_ROOT / "evaluation_records.py"
    spec = importlib.util.spec_from_file_location("skill_evaluator_records", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_attestations_module():
    path = TOOLS_ROOT / "attestations.py"
    spec = importlib.util.spec_from_file_location(
        "skill_evaluator_release_pointers",
        path,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_record() -> dict[str, object]:
    digest = "sha256:" + ("a" * 64)
    case = {
        "case_id": "normal-use",
        "case_version": 1,
        "kind": "core",
        "prompt": "Use the explicitly invoked fixture Skill to produce the requested result.",
        "expected": {
            "invocation": "explicit",
            "outcome": "The requested result is present.",
            "assertions": [
                {
                    "id": "requested-result",
                    "kind": "human-rubric",
                    "description": "The requested result is correct and complete.",
                    "required": True,
                }
            ],
        },
        "observed": {
            "invocation": "explicit",
            "invocation_evidence": (
                "The reviewed trace shows explicit Skill loading."
            ),
            "tool_calls": [],
            "final_output": "The requested result.",
            "external_state": None,
            "environment_isolation": None,
            "unavailable": [],
        },
        "assertion_results": [
            {
                "assertion_id": "requested-result",
                "status": "pass",
                "evidence": "The final output contains the requested result.",
                "observation": "final-output",
            }
        ],
        "status": "pass",
        "failure": {
            "stage": None,
            "reason": None,
            "corrective_action": None,
        },
    }
    target = {
        "status": "pass",
        "runner": {
            "value": "fixture-runner 1.0",
            "unavailable_reason": None,
        },
        "duration_ms": 25,
        "total_tokens": {
            "value": 120,
            "unavailable_reason": None,
        },
        "cases": [case],
    }
    record = {
        "$schema": "../../../record.schema.json",
        "schema_version": 2,
        "run_id": "20260727T120000Z-fixture",
        "skill_name": "fixture-skill",
        "skill_digest": digest,
        "case_manifest_digest": digest,
        "evaluator_version": "myskills-skill-evaluator/4",
        "started_at": "2026-07-27T12:00:00Z",
        "completed_at": "2026-07-27T12:00:01Z",
        "status": "pass",
        "targets": {
            "claude": copy.deepcopy(target),
            "codex": copy.deepcopy(target),
        },
        "human_review": {
            "status": "pass",
            "reviewer": "Fixture Reviewer",
            "reviewed_at": "2026-07-27T12:01:00Z",
            "reason": "The written rubric is satisfied.",
            "corrective_action": None,
        },
        "warnings": [],
        "sanitization": {
            "status": "pass",
            "redactions": [],
            "human_confirmed": True,
        },
    }
    record["targets"]["claude"]["cases"][0]["observed"][
        "environment_isolation"
    ] = {
        "schema_version": 3,
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
        "project_settings": {
            "path": "workspace/.claude/settings.json",
            "disable_bundled_skills": True,
        },
        "windows_home_matches_profile": (
            True if sys.platform == "win32" else None
        ),
    }
    return record


class EvaluationRecordContractTests(unittest.TestCase):
    def test_record_schema_declares_reviewable_evidence_contract(self) -> None:
        schema = json.loads(
            (ROOT / "evaluations" / "record.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertEqual(
            set(schema["required"]),
            {
                "$schema",
                "schema_version",
                "run_id",
                "skill_name",
                "skill_digest",
                "case_manifest_digest",
                "evaluator_version",
                "started_at",
                "completed_at",
                "status",
                "targets",
                "human_review",
                "warnings",
                "sanitization",
            },
        )
        self.assertEqual(
            set(schema["$defs"]["case"]["required"]),
            {
                "case_id",
                "case_version",
                "kind",
                "prompt",
                "expected",
                "observed",
                "assertion_results",
                "status",
                "failure",
            },
        )
        self.assertIn(
            "environment_isolation",
            schema["$defs"]["observed"]["required"],
        )
        self.assertEqual(
            schema["$defs"]["environmentIsolation"]["properties"][
                "schema_version"
            ],
            {"enum": [1, 2, 3]},
        )
        self.assertNotIn(
            "mcp_config",
            schema["$defs"]["environmentIsolation"]["required"],
        )

    def test_record_validator_accepts_reviewable_git_record(self) -> None:
        records = load_records_module()

        self.assertEqual(records.validate_record_document(valid_record()), [])

    def test_record_validator_accepts_workspace_isolated_qmd_xdg_paths(
        self,
    ) -> None:
        records = load_records_module()
        record = valid_record()
        record["targets"]["claude"]["cases"][0]["observed"][
            "environment_isolation"
        ] = {
            "schema_version": 3,
            "paths": {
                "USERPROFILE": "profile-root",
                "HOME": "profile-root",
                "CLAUDE_CONFIG_DIR": "profile-root",
                "APPDATA": "profile/AppData/Roaming",
                "LOCALAPPDATA": "workspace/.runtime/localappdata",
                "XDG_CONFIG_HOME": "workspace/.runtime/qmd/xdg-config",
                "XDG_CACHE_HOME": "workspace/.runtime/qmd/cache",
            },
            "mcp_config": {
                "path": "workspace/.claude/empty-mcp.json",
                "sha256": (
                    "sha256:"
                    "d8e397af03b5b032f21d0aa967086f0c"
                    "78b33c87b76f2e9898ae0a144df7de02"
                ),
            },
            "project_settings": {
                "path": "workspace/.claude/settings.json",
                "disable_bundled_skills": True,
            },
            "windows_home_matches_profile": True,
        }

        self.assertEqual(records.validate_record_document(record), [])

    def test_record_validator_preserves_v1_environment_evidence(
        self,
    ) -> None:
        records = load_records_module()
        record = valid_record()
        record["targets"]["claude"]["cases"][0]["observed"][
            "environment_isolation"
        ] = {
            "schema_version": 1,
            "paths": {
                "USERPROFILE": "profile-root",
                "HOME": "profile-root",
                "CLAUDE_CONFIG_DIR": "profile-root",
                "APPDATA": "profile/AppData/Roaming",
                "LOCALAPPDATA": "profile/AppData/Local",
                "XDG_CONFIG_HOME": "profile/.config",
                "XDG_CACHE_HOME": "profile/.cache",
            },
            "windows_home_matches_profile": True,
        }

        self.assertEqual(records.validate_record_document(record), [])
        with tempfile.TemporaryDirectory() as temp_dir:
            historical_path = Path(temp_dir) / "record.json"
            historical_path.write_text(
                json.dumps(record),
                encoding="utf-8",
            )
            self.assertEqual(
                records.read_record_document(historical_path),
                record,
            )
            with self.assertRaisesRegex(
                ValueError,
                "new evaluation records require environment evidence "
                "version 3",
            ):
                records.write_record(Path(temp_dir), record)

    def test_record_validator_preserves_v2_environment_evidence(
        self,
    ) -> None:
        records = load_records_module()
        record = valid_record()
        evidence = record["targets"]["claude"]["cases"][0]["observed"][
            "environment_isolation"
        ]
        evidence["schema_version"] = 2
        evidence.pop("project_settings")

        self.assertEqual(records.validate_record_document(record), [])
        with tempfile.TemporaryDirectory() as temp_dir:
            historical_path = Path(temp_dir) / "record.json"
            historical_path.write_text(
                json.dumps(record),
                encoding="utf-8",
            )
            self.assertEqual(
                records.read_record_document(historical_path),
                record,
            )
            with self.assertRaisesRegex(
                ValueError,
                "new evaluation records require environment evidence "
                "version 3",
            ):
                records.write_record(Path(temp_dir), record)

    def test_new_passing_claude_record_requires_v3_environment_evidence(
        self,
    ) -> None:
        records = load_records_module()
        record = valid_record()
        record["targets"]["claude"]["cases"][0]["observed"][
            "environment_isolation"
        ] = None

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                ValueError,
                "new non-invalid Claude cases require environment "
                "evidence version 3",
            ):
                records.write_record(Path(temp_dir), record)

    def test_passing_case_requires_only_required_assertions_to_pass(
        self,
    ) -> None:
        records = load_records_module()
        record = valid_record()
        for target in record["targets"].values():
            case = target["cases"][0]
            case["expected"]["assertions"].append(
                {
                    "id": "optional-style",
                    "kind": "human-rubric",
                    "description": "The output uses the preferred concise style.",
                    "required": False,
                }
            )
            case["assertion_results"].append(
                {
                    "assertion_id": "optional-style",
                    "status": "fail",
                    "evidence": "The output is correct but verbose.",
                    "observation": "final-output",
                }
            )
        self.assertEqual(records.validate_record_document(record), [])
        summary = records.render_summary(record)
        self.assertIn("optional-style", summary)
        self.assertIn("optional assertion", summary.lower())

        for target in record["targets"].values():
            target["cases"][0]["assertion_results"][1][
                "status"
            ] = "human-review-required"
        errors = records.validate_record_document(record)
        self.assertTrue(
            any("assertion status is invalid" in error for error in errors),
            errors,
        )

        for target in record["targets"].values():
            target["cases"][0]["assertion_results"][1]["status"] = "fail"
            target["cases"][0]["assertion_results"][0]["status"] = "fail"
        errors = records.validate_record_document(record)
        self.assertTrue(
            any("required assertions to pass" in error for error in errors),
            errors,
        )

    def test_record_loader_accepts_canonical_source_controlled_path(self) -> None:
        records = load_records_module()
        record = valid_record()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = (
                root
                / "evaluations"
                / "records"
                / record["skill_name"]
                / record["run_id"]
                / "record.json"
            )
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(record, indent=2) + "\n",
                encoding="utf-8",
            )

            self.assertEqual(records.load_record(root, path), record)

    def test_record_writer_creates_append_only_human_and_machine_evidence(
        self,
    ) -> None:
        records = load_records_module()
        record = valid_record()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            output = records.write_record(root, record)

            self.assertEqual(
                output,
                root
                / "evaluations"
                / "records"
                / record["skill_name"]
                / record["run_id"],
            )
            self.assertEqual(
                json.loads(
                    (output / "record.json").read_text(encoding="utf-8")
                ),
                record,
            )
            summary = (output / "summary.md").read_text(encoding="utf-8")
            self.assertIn("# Skill evaluation: fixture-skill", summary)
            self.assertIn("Run: `20260727T120000Z-fixture`", summary)
            self.assertIn("| Claude | pass | 1/1 |", summary)
            self.assertIn("Expected: The requested result is present.", summary)
            self.assertIn("Actual: The requested result.", summary)
            with self.assertRaisesRegex(
                FileExistsError,
                "evaluation record already exists",
            ):
                records.write_record(root, record)

    def test_publish_record_cli_writes_canonical_evidence(self) -> None:
        record = valid_record()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            draft = Path(temp_dir) / "record-draft.json"
            draft.write_text(
                json.dumps(record, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ENTRY_POINT),
                    "publish-record",
                    str(root),
                    str(draft),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = (
                root
                / "evaluations"
                / "records"
                / record["skill_name"]
                / record["run_id"]
            )
            self.assertEqual(Path(completed.stdout.strip()), output)
            self.assertEqual(
                json.loads((output / "record.json").read_text(encoding="utf-8")),
                record,
            )

    def test_release_pointer_binds_current_skill_to_passing_record(self) -> None:
        attestations = load_attestations_module()
        records = load_records_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "skills" / "engineering" / "fixture-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: fixture-skill\n"
                "description: Exercise release pointer validation.\n"
                "---\n",
                encoding="utf-8",
            )
            record = valid_record()
            record["skill_digest"] = attestations.directory_digest(skill)
            record_root = records.write_record(root, record)
            pointer = attestations.build_release_pointer(
                root,
                skill,
                record_root / "record.json",
                selected_at="2026-07-27T12:02:00Z",
            )
            pointer_path = (
                root / "attestations" / "skills" / "fixture-skill.json"
            )
            pointer_path.parent.mkdir(parents=True)
            pointer_path.write_text(
                json.dumps(pointer, indent=2) + "\n",
                encoding="utf-8",
            )

            self.assertEqual(pointer["schema_version"], 3)
            self.assertEqual(
                pointer["record_path"],
                "evaluations/records/fixture-skill/"
                "20260727T120000Z-fixture/record.json",
            )
            self.assertEqual(
                attestations.validate_release_pointer(
                    root,
                    skill,
                    pointer_path,
                ),
                [],
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ENTRY_POINT),
                    "verify-attestation",
                    str(skill),
                    str(pointer_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: fixture-skill\n"
                "description: Changed after evaluation.\n"
                "---\n",
                encoding="utf-8",
            )
            errors = attestations.validate_release_pointer(
                root,
                skill,
                pointer_path,
            )
            self.assertTrue(
                any("skill_digest does not match" in error for error in errors),
                errors,
            )

    def test_select_record_cli_writes_current_release_pointer(self) -> None:
        attestations = load_attestations_module()
        records = load_records_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "skills" / "engineering" / "fixture-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: fixture-skill\n"
                "description: Exercise release pointer selection.\n"
                "---\n",
                encoding="utf-8",
            )
            record = valid_record()
            record["skill_digest"] = attestations.directory_digest(skill)
            record_path = records.write_record(root, record) / "record.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ENTRY_POINT),
                    "select-record",
                    str(root),
                    str(skill),
                    str(record_path),
                    "--selected-at",
                    "2026-07-27T12:02:00Z",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            pointer_path = (
                root / "attestations" / "skills" / "fixture-skill.json"
            )
            self.assertEqual(Path(completed.stdout.strip()), pointer_path)
            self.assertEqual(
                attestations.validate_release_pointer(
                    root,
                    skill,
                    pointer_path,
                ),
                [],
            )

    def test_failed_case_requires_observable_failure_location(self) -> None:
        records = load_records_module()
        record = copy.deepcopy(valid_record())
        record["status"] = "fail"
        for target in record["targets"].values():
            target["status"] = "fail"
            target["cases"][0]["status"] = "fail"

        errors = records.validate_record_document(record)

        self.assertTrue(
            any(
                "failed or invalid case requires an observable stage and reason"
                in error
                for error in errors
            ),
            errors,
        )

    def test_passing_human_rubric_requires_completed_human_review(self) -> None:
        records = load_records_module()
        record = copy.deepcopy(valid_record())
        record["human_review"] = {
            "status": "pending",
            "reviewer": None,
            "reviewed_at": None,
            "reason": None,
            "corrective_action": None,
        }

        errors = records.validate_record_document(record)

        self.assertTrue(
            any(
                "passing human-rubric record requires completed human review"
                in error
                for error in errors
            ),
            errors,
        )

    def test_source_controlled_record_requires_completed_sanitization(self) -> None:
        records = load_records_module()
        record = copy.deepcopy(valid_record())
        record["sanitization"]["status"] = "pending"

        errors = records.validate_record_document(record)

        self.assertTrue(
            any("sanitization.status must be 'pass'" in error for error in errors),
            errors,
        )

    def test_tool_trajectory_requires_contiguous_call_order(self) -> None:
        records = load_records_module()
        record = copy.deepcopy(valid_record())
        tool_calls = [
            {
                "sequence": 2,
                "name": "fixture.read",
                "arguments": {"path": "fixture/input.txt"},
                "status": "success",
                "result_summary": "Read the fixture.",
            },
            {
                "sequence": 1,
                "name": "fixture.write",
                "arguments": {"path": "fixture/output.txt"},
                "status": "success",
                "result_summary": "Wrote the result.",
            },
        ]
        for target in record["targets"].values():
            target["cases"][0]["observed"]["tool_calls"] = tool_calls

        errors = records.validate_record_document(record)

        self.assertTrue(
            any(
                "tool_calls sequence must be contiguous and ordered"
                in error
                for error in errors
            ),
            errors,
        )

    def test_trajectory_pass_must_match_predeclared_observation(
        self,
    ) -> None:
        records = load_records_module()
        record = copy.deepcopy(valid_record())
        for target in record["targets"].values():
            case = target["cases"][0]
            assertion = case["expected"]["assertions"][0]
            assertion["kind"] = "trajectory"
            assertion["trajectory_observation"] = "tool-trace"
            case["assertion_results"][0][
                "observation"
            ] = "verified-absence"

        errors = records.validate_record_document(record)
        self.assertTrue(
            any(
                "observation must be tool-trace" in error
                for error in errors
            ),
            errors,
        )

        for target in record["targets"].values():
            target["cases"][0]["assertion_results"][0][
                "observation"
            ] = "tool-trace"
        errors = records.validate_record_document(record)
        self.assertTrue(
            any(
                "requires an observed Tool call" in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
