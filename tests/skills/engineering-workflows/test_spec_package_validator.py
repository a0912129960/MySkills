from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = (
    ROOT
    / "skills"
    / "engineering"
    / "spec-package-generator"
    / "scripts"
    / "validate_package.py"
)


class SpecPackageValidatorTests(unittest.TestCase):
    def run_validator(self, feature_root: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(feature_root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        payload = json.loads(result.stdout) if result.stdout else {}
        return result, payload

    def write_yaml(self, root: Path, relative: str, value: object) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    def write_records(self, root: Path, relative: str, records: list[dict]) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump_all(records, sort_keys=False, explicit_start=True), encoding="utf-8")

    def write_valid_current(self, root: Path) -> None:
        self.write_yaml(
            root,
            "current/id-index.yaml",
            {"ids": ["BDD-001", "DESIGN-001", "REQ-001", "TASK-001", "TEST-001"]},
        )
        self.write_records(
            root,
            "current/records/requirements.yaml",
            [{"id": "REQ-001", "content": {"statement": "The system books freight."}}],
        )
        self.write_records(
            root,
            "current/records/bdd.yaml",
            [{
                "id": "BDD-001",
                "content": {
                    "scenario": "Book freight",
                    "given": ["A valid shipment"],
                    "when": ["The user books it"],
                    "then": ["A booking is created"],
                    "requirements": ["REQ-001"],
                },
            }],
        )
        self.write_records(
            root,
            "current/records/design.yaml",
            [{"id": "DESIGN-001", "content": {"decision": "Use a booking service.", "requirements": ["REQ-001"]}}],
        )
        self.write_records(
            root,
            "current/records/tests.yaml",
            [{
                "id": "TEST-001",
                "content": {
                    "method": "automated",
                    "verifies": ["BDD-001"],
                    "entry_point": "tests/test_booking.py",
                    "pass_criteria": ["The test passes"],
                },
            }],
        )
        self.write_records(
            root,
            "current/records/tasks.yaml",
            [{
                "id": "TASK-001",
                "content": {
                    "title": "Implement booking",
                    "outcome": "Booking works.",
                    "covers": ["REQ-001", "BDD-001", "DESIGN-001", "TEST-001"],
                    "depends_on": [],
                },
            }],
        )
        self.write_yaml(
            root,
            "current/manifests/TASK-001.yaml",
            {
                "task_id": "TASK-001",
                "execution_input_ids": ["REQ-001", "BDD-001", "DESIGN-001", "TEST-001"],
                "prompt": "Implement the validated task.",
            },
        )
        self.write_yaml(
            root,
            "control/id-allocation.yaml",
            {"highest_issued": {"REQ": 1, "BDD": 1, "DESIGN": 1, "TEST": 1, "TASK": 1, "DECISION": 0}},
        )

    def test_empty_feature_package_is_legal_because_presence_is_controller_owned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result, payload = self.run_validator(Path(temporary))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload, {"result": "VALID", "findings": []})

    def test_unknown_file_is_rejected_with_a_stable_physical_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            (feature_root / "surprise.md").write_text("unexpected", encoding="utf-8")

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(payload["result"], "INVALID")
        self.assertEqual([finding["code"] for finding in payload["findings"]], ["PKG_UNKNOWN_PATH"])
        self.assertEqual(payload["findings"][0]["location"], {"path": "surprise.md"})

    def test_feature_root_itself_may_not_be_a_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            target = workspace / "target"
            target.mkdir()
            linked_root = workspace / "linked-feature"
            try:
                linked_root.symlink_to(target, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlinks are unavailable: {error}")

            result, payload = self.run_validator(linked_root)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(payload["result"], "ERROR")
        self.assertIn("PKG_FORBIDDEN_LINK", {finding["code"] for finding in payload["findings"]})

    def test_recognized_file_at_the_wrong_location_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            (feature_root / "candidate").mkdir()
            (feature_root / "candidate" / "id-index.yaml").write_text("ids: []\n", encoding="utf-8")

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PKG_WRONG_PATH", {finding["code"] for finding in payload["findings"]})

    def test_manifest_filename_must_bind_a_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            manifests = feature_root / "current" / "manifests"
            manifests.mkdir(parents=True)
            (manifests / "REQ-001.yaml").write_text("{}\n", encoding="utf-8")

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PKG_INVALID_DYNAMIC_NAME", {finding["code"] for finding in payload["findings"]})

    def test_dynamic_role_path_uses_exact_canonical_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            manifests = feature_root / "Current" / "manifests"
            manifests.mkdir(parents=True)
            (manifests / "TASK-001.yaml").write_text("{}\n", encoding="utf-8")

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PKG_CASE_MISMATCH", {finding["code"] for finding in payload["findings"]})

    def test_task_manifest_enforces_its_declared_closed_content_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_yaml(
                feature_root,
                "current/manifests/TASK-001.yaml",
                {"task_id": "TASK-001", "execution_input_ids": ["REQ-001"], "prompt": ""},
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PKG_WRONG_FORMAT", {finding["code"] for finding in payload["findings"]})

    def test_managed_yaml_must_parse_using_its_declared_format(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            index = feature_root / "current" / "id-index.yaml"
            index.parent.mkdir(parents=True)
            index.write_text("ids: [\n", encoding="utf-8")

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PKG_WRONG_FORMAT", {finding["code"] for finding in payload["findings"]})

    def test_index_must_exactly_equal_the_discovered_definition_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_yaml(
                feature_root,
                "current/id-index.yaml",
                {"ids": ["BDD-001", "DESIGN-001", "REQ-001", "TEST-001"]},
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_ACTIVE_SET_MISMATCH", {finding["code"] for finding in payload["findings"]})

    def test_complete_current_package_with_closed_graph_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload, {"result": "VALID", "findings": []})

    def test_structured_reference_to_an_undefined_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_records(
                feature_root,
                "current/records/bdd.yaml",
                [{
                    "id": "BDD-001",
                    "content": {
                        "scenario": "Book freight",
                        "given": ["A valid shipment"],
                        "when": ["The user books it"],
                        "then": ["A booking is created"],
                        "requirements": ["REQ-999"],
                    },
                }],
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_UNDEFINED_REFERENCE", {finding["code"] for finding in payload["findings"]})

    def test_removed_id_hidden_in_normative_prose_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [{"id": "REQ-001", "content": {"statement": "Replace removed REQ-099."}}],
            )

            result, payload = self.run_validator(feature_root)

        codes = {finding["code"] for finding in payload["findings"]}
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_REMOVED_RESIDUE", codes)
        self.assertIn("ID_UNDECLARED_REFERENCE_POSITION", codes)

    def test_active_id_token_in_plain_prose_is_not_mistaken_for_a_structured_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [
                    {"id": "REQ-001", "content": {"statement": "REQ-002"}},
                    {"id": "REQ-002", "content": {"statement": "Another requirement."}},
                ],
            )
            self.write_yaml(
                feature_root,
                "current/id-index.yaml",
                {"ids": ["BDD-001", "DESIGN-001", "REQ-001", "REQ-002", "TASK-001", "TEST-001"]},
            )
            self.write_yaml(
                feature_root,
                "control/id-allocation.yaml",
                {"highest_issued": {"REQ": 2, "BDD": 1, "DESIGN": 1, "TEST": 1, "TASK": 1, "DECISION": 0}},
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_UNDECLARED_REFERENCE_POSITION", {finding["code"] for finding in payload["findings"]})

    def test_removed_id_cannot_hide_in_a_yaml_mapping_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [{"id": "REQ-001", "content": {"statement": "Valid", "REQ-099": "hidden"}}],
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_REMOVED_RESIDUE", {finding["code"] for finding in payload["findings"]})

    def test_legacy_id_token_in_authoritative_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [{"id": "REQ-001", "content": {"statement": "Legacy FR-001 must not survive."}}],
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_LEGACY_PATTERN", {finding["code"] for finding in payload["findings"]})

    def test_active_id_may_not_exceed_its_allocation_high_water(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_yaml(
                feature_root,
                "control/id-allocation.yaml",
                {"highest_issued": {"REQ": 0, "BDD": 1, "DESIGN": 1, "TEST": 1, "TASK": 1, "DECISION": 0}},
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_ALLOCATION_INVALID", {finding["code"] for finding in payload["findings"]})

    def test_workflow_state_rejects_an_unregistered_seventh_phase(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_yaml(
                feature_root,
                "control/workflow-state.yaml",
                {"phase": "paused", "active_question": None, "plan_fingerprint": None},
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("STATE_INVALID_COMBINATION", {finding["code"] for finding in payload["findings"]})

    def test_task_state_keys_must_equal_existing_active_tasks_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)
            self.write_yaml(
                feature_root,
                "control/task-state.yaml",
                {"tasks": {"TASK-999": "not-started"}},
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("STATE_INVALID_COMBINATION", {finding["code"] for finding in payload["findings"]})

    def test_record_definition_must_use_the_declared_owner_and_closed_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_yaml(feature_root, "current/id-index.yaml", {"ids": ["REQ-001"]})
            self.write_records(
                feature_root,
                "current/records/bdd.yaml",
                [{"id": "REQ-001", "content": {"statement": "Wrong owner", "extra": True}}],
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_WRONG_OWNER", {finding["code"] for finding in payload["findings"]})

    def test_decision_archive_records_use_the_common_id_content_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_records(
                feature_root,
                "history/decisions.yaml",
                [{"id": "DEC-001", "content": {"question": "Why?", "decision": "Because."}, "status": "old"}],
            )

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ID_INVALID_CONTENT", {finding["code"] for finding in payload["findings"]})

    def test_candidate_prose_and_view_bytes_are_not_scanned_for_old_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            discussion = feature_root / "candidate" / "discussion.md"
            discussion.parent.mkdir(parents=True)
            discussion.write_text("Discuss replacing REQ-099 and FR-001.", encoding="utf-8")
            dashboard = feature_root / "current" / "views" / "dashboard.html"
            dashboard.parent.mkdir(parents=True)
            dashboard.write_text("<p>Latest view may still display REQ-099.</p>", encoding="utf-8")

            result, payload = self.run_validator(feature_root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload, {"result": "VALID", "findings": []})

    def test_repeated_validation_without_edits_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary)
            self.write_valid_current(feature_root)

            first = subprocess.run(
                [sys.executable, str(VALIDATOR), str(feature_root)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                encoding="utf-8",
                check=False,
            )
            second = subprocess.run(
                [sys.executable, str(VALIDATOR), str(feature_root)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
