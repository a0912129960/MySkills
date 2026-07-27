from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = ROOT / "tools" / "skill-evaluator"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS_ROOT / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvaluationCaseContractV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_module(
            "skill_evaluator_case_contract_v4",
            "evaluation_cases.py",
        )

    def test_catalog_has_one_owned_file_per_managed_skill(self) -> None:
        index = json.loads(
            (ROOT / "evaluations" / "cases.json").read_text(encoding="utf-8")
        )

        self.assertEqual(index["schema_version"], 4)
        self.assertEqual(len(index["skill_case_files"]), 42)
        self.assertEqual(
            index["skill_case_files"],
            sorted(index["skill_case_files"]),
        )
        self.assertEqual(len(set(index["skill_case_files"])), 42)
        for relative in index["skill_case_files"]:
            self.assertRegex(relative, r"^cases/[a-z0-9]+(?:-[a-z0-9]+)*\.json$")
            self.assertTrue((ROOT / "evaluations" / relative).is_file())

    def test_parallel_case_ownership_is_complete_and_non_overlapping(
        self,
    ) -> None:
        index = json.loads(
            (ROOT / "evaluations" / "cases.json").read_text(encoding="utf-8")
        )
        ownership = json.loads(
            (ROOT / "evaluations" / "case-ownership.json").read_text(
                encoding="utf-8"
            )
        )
        groups = ownership["agents"]
        flattened = [
            path
            for group in ("agent-a", "agent-b", "agent-c")
            for path in groups[group]
        ]
        expected = [
            f"evaluations/{path}"
            for path in index["skill_case_files"]
        ]

        self.assertEqual(len(groups), 3)
        self.assertTrue(all(len(groups[group]) == 14 for group in groups))
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(sorted(flattened), sorted(expected))

    def test_every_skill_has_fixed_core_and_invocation_suites(self) -> None:
        document = self.cases.load_cases(ROOT)
        self.assertEqual(document["schema_version"], 4)
        self.assertEqual(len(document["skills"]), 42)

        for entry in document["skills"]:
            name = entry["skill_name"]
            self.assertEqual(len(entry["core_cases"]), 3, name)
            self.assertEqual(
                {case["role"] for case in entry["core_cases"]},
                {"normal", "boundary", "safety-or-core"},
                name,
            )
            self.assertEqual(len(entry["invocation_cases"]), 3, name)
            for case in entry["core_cases"]:
                self.assertEqual(case["version"], 1)
                self.assertTrue(case["oracle"]["expected_outcome"].strip())
                self.assertTrue(case["oracle"]["assertions"])
                self.assertTrue(
                    any(
                        assertion["required"]
                        for assertion in case["oracle"]["assertions"]
                    ),
                    f"{name}/{case['id']}",
                )
                for assertion in case["oracle"]["assertions"]:
                    if assertion["kind"] == "trajectory":
                        self.assertIn(
                            assertion["trajectory_observation"],
                            {
                                "tool-trace",
                                "external-state",
                                "verified-absence",
                            },
                        )
                    else:
                        self.assertNotIn(
                            "trajectory_observation",
                            assertion,
                        )

            if entry["invocation"] == "explicit":
                self.assertEqual(
                    {
                        case["expected_invocation"]
                        for case in entry["invocation_cases"]
                    },
                    {"not-invoked"},
                    name,
                )
            else:
                by_variant = {
                    case["variant"]: case["expected_invocation"]
                    for case in entry["invocation_cases"]
                }
                self.assertEqual(
                    by_variant,
                    {
                        "direct": "implicit",
                        "paraphrase": "implicit",
                        "boundary": "not-invoked",
                    },
                    name,
                )

    def test_plan_runs_each_case_once_per_platform_without_baseline(self) -> None:
        document = self.cases.load_cases(ROOT)
        plan = self.cases.build_plan(ROOT, document)
        summary = self.cases.summarize_plan(plan)

        self.assertEqual(summary["schema_version"], 4)
        self.assertEqual(summary["skill_count"], 42)
        self.assertEqual(summary["model_run_count"], 504)
        for name in summary["skills"]:
            runs = [item for item in plan if item["skill_name"] == name]
            self.assertEqual(len(runs), 12, name)
            self.assertEqual(
                {
                    (item["case_id"], item["target"])
                    for item in runs
                },
                {
                    (case["id"], target)
                    for entry in document["skills"]
                    if entry["skill_name"] == name
                    for case in (
                        entry["core_cases"] + entry["invocation_cases"]
                    )
                    for target in ("claude", "codex")
                },
                name,
            )
            self.assertTrue(
                all(
                    item["max_attempts"] == 1
                    and item["assertions"]
                    and "baseline" not in item
                    and "configuration" not in item
                    for item in runs
                ),
                name,
            )

    def test_validator_rejects_policy_weakening(self) -> None:
        document = self.cases.load_cases(ROOT)

        too_few = copy.deepcopy(document)
        too_few["skills"][0]["core_cases"].pop()
        errors = self.cases.validate_cases(ROOT, too_few)
        self.assertTrue(any("exactly 3 core_cases" in error for error in errors))

        retry = copy.deepcopy(document)
        retry["skills"][0]["automatic_retries"] = 1
        errors = self.cases.validate_cases(ROOT, retry)
        self.assertTrue(any("fields are invalid" in error for error in errors))

        baseline = copy.deepcopy(document)
        baseline["skills"][0]["baseline"] = {"kind": "no-skill"}
        errors = self.cases.validate_cases(ROOT, baseline)
        self.assertTrue(any("fields are invalid" in error for error in errors))

        wrong_boundary = copy.deepcopy(document)
        implicit = next(
            entry
            for entry in wrong_boundary["skills"]
            if entry["invocation"] == "implicit"
        )
        boundary = next(
            case
            for case in implicit["invocation_cases"]
            if case["variant"] == "boundary"
        )
        boundary["expected_invocation"] = "implicit"
        errors = self.cases.validate_cases(ROOT, wrong_boundary)
        self.assertTrue(any("boundary" in error for error in errors), errors)

        invalid_version = copy.deepcopy(document)
        invalid_version["skills"][0]["core_cases"][0]["version"] = 0
        errors = self.cases.validate_cases(ROOT, invalid_version)
        self.assertTrue(any("version" in error for error in errors), errors)

        missing_trajectory_observation = copy.deepcopy(document)
        trajectory = next(
            assertion
            for entry in missing_trajectory_observation["skills"]
            for case in entry["core_cases"]
            for assertion in case["oracle"]["assertions"]
            if assertion["kind"] == "trajectory"
        )
        trajectory.pop("trajectory_observation")
        errors = self.cases.validate_cases(
            ROOT,
            missing_trajectory_observation,
        )
        self.assertTrue(
            any("assertion fields are invalid" in error for error in errors),
            errors,
        )

    def test_golden_cases_require_versioned_human_approval(self) -> None:
        document = self.cases.load_cases(ROOT)
        skill = document["skills"][0]
        golden = copy.deepcopy(skill["core_cases"][0])
        golden.pop("role")
        golden.update(
            {
                "id": "reviewed-real-case",
                "provenance": "support-case-2026-07",
                "approved_by": "reviewer@example.invalid",
                "approved_at": "2026-07-27T12:00:00+08:00",
                "deidentified": True,
            }
        )
        skill["golden_cases"] = [golden]
        self.assertEqual(self.cases.validate_cases(ROOT, document), [])

        invalid = copy.deepcopy(document)
        invalid["skills"][0]["golden_cases"][0][
            "approved_at"
        ] = "not-a-date"
        errors = self.cases.validate_cases(ROOT, invalid)
        self.assertTrue(
            any("approved_at is invalid" in error for error in errors),
            errors,
        )

    def test_loader_rejects_invalid_catalog_sources_and_duplicate_keys(
        self,
    ) -> None:
        def copy_contract(temp_dir: str) -> Path:
            repo = Path(temp_dir)
            shutil.copytree(ROOT / "evaluations", repo / "evaluations")
            shutil.copytree(ROOT / "inventory", repo / "inventory")
            return repo

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = copy_contract(temp_dir)
            index_path = repo / "evaluations" / "cases.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["skill_case_files"][0], index["skill_case_files"][1] = (
                index["skill_case_files"][1],
                index["skill_case_files"][0],
            )
            index_path.write_text(
                json.dumps(index, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unsorted"):
                self.cases.load_cases(repo)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = copy_contract(temp_dir)
            first = (
                repo
                / "evaluations"
                / json.loads(
                    (repo / "evaluations" / "cases.json").read_text(
                        encoding="utf-8"
                    )
                )["skill_case_files"][0]
            )
            content = first.read_text(encoding="utf-8")
            first.write_text(
                content.replace(
                    '"schema_version": 4,',
                    '"schema_version": 4, "schema_version": 4,',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                self.cases.load_cases(repo)

    def test_validator_reports_wrong_nested_types_without_crashing(self) -> None:
        document = self.cases.load_cases(ROOT)
        invalid = copy.deepcopy(document)
        invalid["skills"][0]["core_cases"][0]["fixtures"] = [
            {"not": "a fixture"}
        ]
        invalid["skills"][0]["core_cases"][0]["runtime_tools"] = [
            {"not": "a tool"}
        ]
        invalid["skills"][0]["invocation_cases"][0]["variant"] = [
            "not-hashable"
        ]

        errors = self.cases.validate_cases(ROOT, invalid)

        self.assertTrue(any("fixtures are invalid" in error for error in errors))
        self.assertTrue(
            any("runtime_tools are invalid" in error for error in errors)
        )
        self.assertTrue(
            any("invocation variant is invalid" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
