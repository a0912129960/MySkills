from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONTROLLER = (
    ROOT
    / "skills"
    / "engineering"
    / "spec-package-generator"
    / "scripts"
    / "package_controller.py"
)


class PackageControllerTests(unittest.TestCase):
    def plan_fingerprint(self, value: object) -> str:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    def run_controller(self, *arguments: object) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, str(CONTROLLER), *(str(argument) for argument in arguments)],
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
        path.write_text(
            yaml.safe_dump_all(records, sort_keys=False, explicit_start=True),
            encoding="utf-8",
        )

    def write_minimal_requirement_current(self, root: Path) -> None:
        self.write_yaml(root, "current/id-index.yaml", {"ids": ["REQ-001"]})
        self.write_records(
            root,
            "current/records/requirements.yaml",
            [{"id": "REQ-001", "content": {"statement": "Old requirement."}}],
        )
        self.write_yaml(
            root,
            "control/id-allocation.yaml",
            {"highest_issued": {"REQ": 1, "BDD": 0, "DESIGN": 0, "TEST": 0, "TASK": 0, "DECISION": 0}},
        )

    def prepare_replacement_plan(self, feature_root: Path, proposal_path: Path) -> None:
        self.write_minimal_requirement_current(feature_root)
        self.run_controller(
            "start-question",
            feature_root,
            "--question",
            "Should REQ-001 be replaced?",
        )
        self.run_controller(
            "answer-question",
            feature_root,
            "--answer",
            "Yes, replace REQ-001 with the corrected rule.",
        )
        proposal_path.write_text(
            """changes:
  - target: {record_id: REQ-001}
    after: {state: absent}
  - target: {record_id: '@new/REQ/replacement'}
    after:
      state: present
      payload:
        id: '@new/REQ/replacement'
        content: {statement: 'Corrected requirement.'}
""",
            encoding="utf-8",
        )
        result, _payload = self.run_controller("submit-plan", feature_root, proposal_path)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_resume_initializes_only_the_allocator_for_a_fresh_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "new-feature"
            feature_root.mkdir()

            result, payload = self.run_controller("resume", feature_root)

            allocation = yaml.safe_load(
                (feature_root / "control" / "id-allocation.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            payload,
            {
                "feature": "new-feature",
                "phase": "uninitialized",
                "transaction": None,
                "targets": [],
                "next_action": "start_question",
                "read_selectors": [],
                "blocked_reason": None,
            },
        )
        self.assertEqual(
            allocation,
            {
                "highest_issued": {
                    "REQ": 0,
                    "BDD": 0,
                    "DESIGN": 0,
                    "TEST": 0,
                    "TASK": 0,
                    "DECISION": 0,
                }
            },
        )

    def test_start_question_reserves_decision_id_and_enters_discussion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()

            result, payload = self.run_controller(
                "start-question",
                feature_root,
                "--question",
                "Should booking support a draft state?",
            )

            question = yaml.safe_load(
                (feature_root / "candidate" / "question.yaml").read_text(encoding="utf-8")
            )
            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )
            allocation = yaml.safe_load(
                (feature_root / "control" / "id-allocation.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "discussing")
        self.assertEqual(payload["transaction"], "Q-001")
        self.assertEqual(payload["next_action"], "answer_question")
        self.assertEqual(
            question,
            {
                "id": "Q-001",
                "content": {
                    "question": "Should booking support a draft state?",
                    "answer": None,
                },
            },
        )
        self.assertEqual(
            state,
            {"phase": "discussing", "active_question": "Q-001", "plan_fingerprint": None},
        )
        self.assertEqual(allocation["highest_issued"]["DECISION"], 1)

    def test_resume_binds_one_unanswered_orphan_question_after_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.write_yaml(
                feature_root,
                "control/id-allocation.yaml",
                {"highest_issued": {"REQ": 0, "BDD": 0, "DESIGN": 0, "TEST": 0, "TASK": 0, "DECISION": 1}},
            )
            self.write_yaml(
                feature_root,
                "candidate/question.yaml",
                {"id": "Q-001", "content": {"question": "Enable drafts?", "answer": None}},
            )

            result, payload = self.run_controller("resume", feature_root)

            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "discussing")
        self.assertEqual(payload["transaction"], "Q-001")
        self.assertEqual(payload["next_action"], "answer_question")
        self.assertEqual(
            state,
            {"phase": "discussing", "active_question": "Q-001", "plan_fingerprint": None},
        )

    def test_answer_question_persists_answer_then_enters_planning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.run_controller(
                "start-question",
                feature_root,
                "--question",
                "Should booking support a draft state?",
            )

            result, payload = self.run_controller(
                "answer-question",
                feature_root,
                "--answer",
                "Yes, keep drafts until submission.",
            )

            question = yaml.safe_load(
                (feature_root / "candidate" / "question.yaml").read_text(encoding="utf-8")
            )
            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "planning")
        self.assertEqual(payload["transaction"], "Q-001")
        self.assertEqual(payload["next_action"], "submit_plan")
        self.assertEqual(question["content"]["answer"], "Yes, keep drafts until submission.")
        self.assertEqual(
            state,
            {"phase": "planning", "active_question": "Q-001", "plan_fingerprint": None},
        )

    def test_resume_advances_answered_question_after_state_write_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.run_controller("start-question", feature_root, "--question", "Enable drafts?")
            self.write_yaml(
                feature_root,
                "candidate/question.yaml",
                {"id": "Q-001", "content": {"question": "Enable drafts?", "answer": "Yes."}},
            )

            result, payload = self.run_controller("resume", feature_root)

            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "planning")
        self.assertEqual(payload["next_action"], "submit_plan")
        self.assertEqual(
            state,
            {"phase": "planning", "active_question": "Q-001", "plan_fingerprint": None},
        )

    def test_submit_empty_exact_plan_seals_an_explicit_no_current_change_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.run_controller("start-question", feature_root, "--question", "Document this decision?")
            self.run_controller("answer-question", feature_root, "--answer", "Yes, with no Current change.")
            proposal = Path(temporary) / "proposal.yaml"
            proposal.write_text("changes: []\n", encoding="utf-8")

            result, payload = self.run_controller("submit-plan", feature_root, proposal)

            plan = yaml.safe_load(
                (feature_root / "candidate" / "application-plan.yaml").read_text(encoding="utf-8")
            )
            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "applying_current")
        self.assertEqual(payload["targets"], [])
        self.assertEqual(payload["next_action"], "finalize_question")
        self.assertEqual(set(plan), {"basis", "allocation_baseline", "expected_final_current_fingerprint", "operations"})
        self.assertEqual(plan["basis"]["kind"], "question")
        self.assertEqual(plan["basis"]["id"], "Q-001")
        self.assertEqual(plan["operations"], [])
        self.assertRegex(plan["basis"]["fingerprint"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(plan["expected_final_current_fingerprint"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(state["plan_fingerprint"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(state["phase"], "applying_current")

    def test_malformed_proposal_fails_closed_with_a_stable_controller_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.run_controller("start-question", feature_root, "--question", "Document this decision?")
            self.run_controller("answer-question", feature_root, "--answer", "Yes.")
            proposal = Path(temporary) / "proposal.yaml"
            proposal.write_text("changes: [\n", encoding="utf-8")

            result, payload = self.run_controller("submit-plan", feature_root, proposal)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["phase"], "invalid")
        self.assertEqual(payload["next_action"], "human_recovery")
        self.assertEqual(payload["blocked_reason"], "CONTROLLER_INPUT_ERROR")

    def test_finalize_question_appends_deterministic_decision_and_cleans_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.run_controller("start-question", feature_root, "--question", "Document this decision?")
            self.run_controller("answer-question", feature_root, "--answer", "Yes, with no Current change.")
            proposal = Path(temporary) / "proposal.yaml"
            proposal.write_text("changes: []\n", encoding="utf-8")
            self.run_controller("submit-plan", feature_root, proposal)

            result, payload = self.run_controller("finalize-question", feature_root)

            decisions = list(
                yaml.safe_load_all(
                    (feature_root / "history" / "decisions.yaml").read_text(encoding="utf-8")
                )
            )
            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "finalizing")
        self.assertIsNone(payload["transaction"])
        self.assertEqual(payload["next_action"], "start_question_or_finish")
        self.assertEqual(
            decisions,
            [
                {
                    "id": "DEC-001",
                    "content": {
                        "question": "Document this decision?",
                        "decision": "Yes, with no Current change.",
                    },
                }
            ],
        )
        self.assertEqual(
            state,
            {"phase": "finalizing", "active_question": None, "plan_fingerprint": None},
        )
        self.assertFalse((feature_root / "candidate").exists())

    def test_submit_replacement_plan_allocates_fresh_id_and_generates_index_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.write_minimal_requirement_current(feature_root)
            self.run_controller(
                "start-question",
                feature_root,
                "--question",
                "Should REQ-001 be replaced?",
            )
            self.run_controller(
                "answer-question",
                feature_root,
                "--answer",
                "Yes, replace REQ-001 with the corrected rule.",
            )
            proposal = Path(temporary) / "proposal.yaml"
            proposal.write_text(
                """changes:
  - target: {record_id: REQ-001}
    after: {state: absent}
  - target: {record_id: '@new/REQ/replacement'}
    after:
      state: present
      payload:
        id: '@new/REQ/replacement'
        content: {statement: 'Corrected requirement.'}
""",
                encoding="utf-8",
            )

            result, payload = self.run_controller("submit-plan", feature_root, proposal)

            plan = yaml.safe_load(
                (feature_root / "candidate" / "application-plan.yaml").read_text(encoding="utf-8")
            )
            allocation = yaml.safe_load(
                (feature_root / "control" / "id-allocation.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "applying_current")
        self.assertEqual(payload["next_action"], "apply_plan")
        self.assertEqual([target["status"] for target in payload["targets"]], ["pending", "pending", "pending"])
        self.assertEqual(plan["allocation_baseline"]["REQ"], 1)
        self.assertEqual(allocation["highest_issued"]["REQ"], 2)
        targets = [operation["target"] for operation in plan["operations"]]
        self.assertEqual(
            targets,
            [
                {"file_role": "current_id_index"},
                {"record_id": "REQ-001"},
                {"record_id": "REQ-002"},
            ],
        )
        self.assertEqual(plan["operations"][0]["after"]["payload"], {"ids": ["REQ-002"]})
        self.assertEqual(plan["operations"][2]["after"]["payload"]["id"], "REQ-002")

    def test_apply_plan_reconciles_all_targets_and_enters_decision_precommit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            proposal = Path(temporary) / "proposal.yaml"
            self.prepare_replacement_plan(feature_root, proposal)

            result, payload = self.run_controller("apply-plan", feature_root)

            records = list(
                yaml.safe_load_all(
                    (feature_root / "current" / "records" / "requirements.yaml").read_text(
                        encoding="utf-8"
                    )
                )
            )
            index = yaml.safe_load(
                (feature_root / "current" / "id-index.yaml").read_text(encoding="utf-8")
            )
            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "finalizing")
        self.assertEqual(payload["transaction"], "Q-001")
        self.assertEqual(payload["next_action"], "finalize_question")
        self.assertEqual([target["status"] for target in payload["targets"]], ["complete", "complete", "complete"])
        self.assertEqual(records, [{"id": "REQ-002", "content": {"statement": "Corrected requirement."}}])
        self.assertEqual(index, {"ids": ["REQ-002"]})
        self.assertEqual(state["phase"], "finalizing")
        self.assertEqual(state["active_question"], "Q-001")
        self.assertRegex(state["plan_fingerprint"], r"^sha256:[0-9a-f]{64}$")

    def test_resume_reports_each_target_independently_after_interrupted_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            proposal = Path(temporary) / "proposal.yaml"
            self.prepare_replacement_plan(feature_root, proposal)
            plan = yaml.safe_load(
                (feature_root / "candidate" / "application-plan.yaml").read_text(encoding="utf-8")
            )
            operations = {
                json.dumps(operation["target"], sort_keys=True): operation
                for operation in plan["operations"]
            }
            self.write_yaml(
                feature_root,
                "current/id-index.yaml",
                operations['{"file_role": "current_id_index"}']["after"]["payload"],
            )
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [
                    {"id": "REQ-001", "content": {"statement": "Old requirement."}},
                    operations['{"record_id": "REQ-002"}']["after"]["payload"],
                ],
            )

            result, payload = self.run_controller("resume", feature_root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "applying_current")
        self.assertEqual(payload["next_action"], "apply_plan")
        self.assertEqual(
            payload["targets"],
            [
                {"target": {"file_role": "current_id_index"}, "status": "complete"},
                {"target": {"record_id": "REQ-001"}, "status": "pending"},
                {"target": {"record_id": "REQ-002"}, "status": "complete"},
            ],
        )

    def test_resume_revalidates_and_seals_a_plan_written_before_state_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            proposal = Path(temporary) / "proposal.yaml"
            self.prepare_replacement_plan(feature_root, proposal)
            self.write_yaml(
                feature_root,
                "control/workflow-state.yaml",
                {"phase": "planning", "active_question": "Q-001", "plan_fingerprint": None},
            )

            result, payload = self.run_controller("resume", feature_root)

            plan = yaml.safe_load(
                (feature_root / "candidate" / "application-plan.yaml").read_text(encoding="utf-8")
            )
            state = yaml.safe_load(
                (feature_root / "control" / "workflow-state.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["phase"], "applying_current")
        self.assertEqual(payload["next_action"], "apply_plan")
        self.assertEqual([target["status"] for target in payload["targets"]], ["pending"] * 3)
        self.assertEqual(state["active_question"], "Q-001")
        self.assertEqual(state["plan_fingerprint"], self.plan_fingerprint(plan))

    def test_resume_blocks_when_a_plan_target_matches_neither_before_nor_after(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            proposal = Path(temporary) / "proposal.yaml"
            self.prepare_replacement_plan(feature_root, proposal)
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [{"id": "REQ-001", "content": {"statement": "Unexpected direct edit."}}],
            )

            result, payload = self.run_controller("resume", feature_root)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["phase"], "invalid")
        self.assertEqual(payload["next_action"], "human_recovery")
        self.assertEqual(payload["blocked_reason"], "PLAN_TARGET_CONFLICT")

    def test_apply_blocks_an_unlisted_but_structurally_valid_current_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            proposal = Path(temporary) / "proposal.yaml"
            self.write_yaml(feature_root, "current/id-index.yaml", {"ids": ["REQ-001", "REQ-010"]})
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [
                    {"id": "REQ-001", "content": {"statement": "Old requirement."}},
                    {"id": "REQ-010", "content": {"statement": "Stable requirement."}},
                ],
            )
            self.write_yaml(
                feature_root,
                "control/id-allocation.yaml",
                {
                    "highest_issued": {
                        "REQ": 10,
                        "BDD": 0,
                        "DESIGN": 0,
                        "TEST": 0,
                        "TASK": 0,
                        "DECISION": 0,
                    }
                },
            )
            self.run_controller(
                "start-question", feature_root, "--question", "Should REQ-001 be replaced?"
            )
            self.run_controller(
                "answer-question",
                feature_root,
                "--answer",
                "Yes, replace REQ-001 with the corrected rule.",
            )
            proposal.write_text(
                """changes:
  - target: {record_id: REQ-001}
    after: {state: absent}
  - target: {record_id: '@new/REQ/replacement'}
    after:
      state: present
      payload:
        id: '@new/REQ/replacement'
        content: {statement: 'Corrected requirement.'}
""",
                encoding="utf-8",
            )
            submit_result, _submit = self.run_controller("submit-plan", feature_root, proposal)
            self.assertEqual(submit_result.returncode, 0, submit_result.stderr)
            self.write_records(
                feature_root,
                "current/records/requirements.yaml",
                [
                    {"id": "REQ-001", "content": {"statement": "Old requirement."}},
                    {"id": "REQ-010", "content": {"statement": "Unlisted direct edit."}},
                ],
            )

            result, payload = self.run_controller("apply-plan", feature_root)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["blocked_reason"], "PLAN_UNEXPECTED_CURRENT")
        self.assertEqual(payload["next_action"], "human_recovery")

    def test_resume_returns_to_planning_or_clean_question_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            self.run_controller("start-question", feature_root, "--question", "Document this decision?")
            self.run_controller("answer-question", feature_root, "--answer", "Yes.")

            planning_result, planning = self.run_controller("resume", feature_root)

            self.write_yaml(
                feature_root,
                "control/workflow-state.yaml",
                {"phase": "finalizing", "active_question": None, "plan_fingerprint": None},
            )
            for child in (feature_root / "candidate").iterdir():
                child.unlink()
            (feature_root / "candidate").rmdir()

            clean_result, clean = self.run_controller("resume", feature_root)

        self.assertEqual(planning_result.returncode, 0, planning_result.stderr)
        self.assertEqual(planning["phase"], "planning")
        self.assertEqual(planning["next_action"], "submit_plan")
        self.assertEqual(clean_result.returncode, 0, clean_result.stderr)
        self.assertEqual(clean["phase"], "finalizing")
        self.assertIsNone(clean["transaction"])
        self.assertEqual(clean["next_action"], "start_question_or_finish")

    def test_finalize_replays_same_decision_but_blocks_a_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature_root = Path(temporary) / "booking"
            feature_root.mkdir()
            proposal = Path(temporary) / "proposal.yaml"
            self.prepare_replacement_plan(feature_root, proposal)
            self.run_controller("apply-plan", feature_root)
            expected = {
                "id": "DEC-001",
                "content": {
                    "question": "Should the affected specification item(s) be replaced?",
                    "decision": (
                        "Yes, replace the affected specification item(s) with the corrected rule."
                    ),
                },
            }
            self.write_records(feature_root, "history/decisions.yaml", [expected])

            replay_result, replay = self.run_controller("finalize-question", feature_root)

            collision_root = Path(temporary) / "collision"
            collision_root.mkdir()
            collision_proposal = Path(temporary) / "collision-proposal.yaml"
            self.prepare_replacement_plan(collision_root, collision_proposal)
            self.run_controller("apply-plan", collision_root)
            self.write_records(
                collision_root,
                "history/decisions.yaml",
                [{"id": "DEC-001", "content": {"question": "Different", "decision": "Different"}}],
            )

            collision_result, collision = self.run_controller("finalize-question", collision_root)

        self.assertEqual(replay_result.returncode, 0, replay_result.stderr)
        self.assertEqual(replay["next_action"], "start_question_or_finish")
        self.assertEqual(collision_result.returncode, 1)
        self.assertEqual(collision["blocked_reason"], "DEC_COMMIT_COLLISION")


if __name__ == "__main__":
    unittest.main()
