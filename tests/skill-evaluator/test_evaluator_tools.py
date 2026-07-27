from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


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


class SkillEvaluatorToolContractTests(unittest.TestCase):
    def test_evaluation_case_manifest_runs_each_skill_without_a_baseline(
        self,
    ) -> None:
        cases = load_module(
            "skill_evaluator_cases",
            "evaluation_cases.py",
        )
        document = cases.load_cases(ROOT)
        plan = cases.build_plan(ROOT, document)
        summary = cases.summarize_plan(plan)

        self.assertEqual(summary["skill_count"], 42)
        self.assertEqual(summary["model_run_count"], 504)
        for name in summary["skills"]:
            runs = [item for item in plan if item["skill_name"] == name]
            self.assertEqual(len(runs), 12, name)
            self.assertTrue(
                all(
                    item["evaluation_level"] == "full"
                    and "baseline" not in item
                    and "configuration" not in item
                    for item in runs
                ),
                name,
            )
            self.assertEqual(
                {item["target"] for item in runs},
                {"claude", "codex"},
            )

        qmd_trigger_runs = [
            item
            for item in plan
            if item["skill_name"] == "qmd"
            and item["mode"] == "invocation"
        ]
        self.assertEqual(len(qmd_trigger_runs), 6)
        self.assertEqual(
            sum(item["external_tools"] == ["qmd"] for item in qmd_trigger_runs),
            4,
        )
        self.assertTrue(
            all(
                item["fixture_sets"] == ["qmd-index"]
                and item["fixtures"] == qmd_trigger_runs[0]["fixtures"]
                for item in qmd_trigger_runs
                if item["expected_invocation"] == "implicit"
            )
        )

        with_baseline = copy.deepcopy(document)
        with_baseline["skills"][0]["baseline"] = {
            "kind": "no-skill",
            "identity": "removed-baseline",
        }
        self.assertTrue(
            any(
                "fields are invalid" in error
                for error in cases.validate_cases(ROOT, with_baseline)
            )
        )

        invalid_external = copy.deepcopy(document)
        invalid_qmd = next(
            item
            for item in invalid_external["skills"]
            if item["skill_name"] == "qmd"
        )
        invalid_qmd["invocation_cases"][0]["external_tools"] = ["shell"]
        self.assertTrue(
            any(
                "external_tools are invalid" in error
                for error in cases.validate_cases(ROOT, invalid_external)
            )
        )

        invalid = copy.deepcopy(document)
        invalid["skills"][0]["invocation_cases"][0][
            "expected_invocation"
        ] = "implicit"
        errors = cases.validate_cases(ROOT, invalid)
        self.assertTrue(
            any("invocation cases" in error for error in errors),
            errors,
        )

    def test_case_schema_reserves_discovery_and_git_paths_case_insensitively(
        self,
    ) -> None:
        schema = json.loads(
            (ROOT / "evaluations" / "cases.schema.json").read_text(
                encoding="utf-8"
            )
        )
        pattern = schema["$defs"]["fixture"]["properties"]["path"]["pattern"]

        self.assertIsNone(re.fullmatch(pattern, ".GIT/config"))
        self.assertIsNone(re.fullmatch(pattern, ".Claude/settings.json"))
        self.assertIsNotNone(re.fullmatch(pattern, "fixture/wiki/index.md"))

    def test_batch_plan_cli_is_read_only_and_filterable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "plan.json"
            completed = subprocess.run(
                [
                    "python",
                    str(ENTRY_POINT),
                    "plan-batch",
                    str(ROOT),
                    "--skills",
                    "qmd",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            plan = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(plan["skill_count"], 1)
            self.assertEqual(plan["model_run_count"], 12)
            self.assertEqual(plan["skills"], ["qmd"])

            preview = Path(temp_dir) / "preview.json"
            preview_result = subprocess.run(
                [
                    "python",
                    str(ENTRY_POINT),
                    "run-batch",
                    str(ROOT),
                    "--skills",
                    "qmd",
                    "--max-runs",
                    "2",
                    "--output",
                    str(preview),
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(preview_result.returncode, 0, preview_result.stderr)
            preview_data = json.loads(preview.read_text(encoding="utf-8"))
            self.assertFalse(preview_data["executed"])
            self.assertEqual(preview_data["model_run_count"], 2)

            denied = subprocess.run(
                [
                    "python",
                    str(ENTRY_POINT),
                    "run-batch",
                    str(ROOT),
                    "--skills",
                    "qmd",
                    "--max-runs",
                    "1",
                    "--execute",
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(denied.returncode, 1)
            self.assertIn(
                "--allow-ephemeral-auth-copy",
                denied.stdout,
            )

            denied_single = subprocess.run(
                [
                    "python",
                    str(ENTRY_POINT),
                    "run",
                    str(ROOT / "skills" / "qmd" / "qmd"),
                    "--mode",
                    "explicit",
                    "--prompt",
                    "Do not execute without the isolation authorization.",
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(denied_single.returncode, 1)
            self.assertIn(
                "--allow-ephemeral-auth-copy",
                denied_single.stdout,
            )

    def test_plan_carries_fixture_files_and_companion_skills(self) -> None:
        cases = load_module(
            "skill_evaluator_fixture_cases",
            "evaluation_cases.py",
        )
        attestations = load_module(
            "skill_evaluator_fixture_digests",
            "attestations.py",
        )
        document = cases.load_cases(ROOT)
        extended = copy.deepcopy(document)
        implement = next(
            item for item in extended["skills"]
            if item["skill_name"] == "implement"
        )
        required = implement["core_cases"][0]
        required["fixtures"] = [
            {
                "path": "fixture/spec.md",
                "content": "# Fixture specification\n",
            }
        ]
        required["companion_skills"] = ["tdd", "code-review"]

        self.assertEqual(cases.validate_cases(ROOT, extended), [])
        plan = cases.build_plan(ROOT, extended, ["implement"])
        required_runs = [
            item
            for item in plan
            if item["case_id"] == required["id"]
        ]
        self.assertTrue(
            all(item["fixtures"] == required["fixtures"] for item in required_runs)
        )
        self.assertTrue(
            all(
                item["companion_skills"] == ["tdd", "code-review"]
                and len(item["companion_skill_paths"]) == 2
                for item in required_runs
            )
        )
        self.assertTrue(
            all(
                item["skill_digest"]
                == attestations.directory_digest(item["skill_path"])
                and item["companion_skill_digests"]
                == {
                    name: attestations.directory_digest(path)
                    for name, path in zip(
                        item["companion_skills"],
                        item["companion_skill_paths"],
                    )
                }
                for item in required_runs
            )
        )

    def test_shared_fixture_sets_expand_and_reject_unsafe_duplicates(self) -> None:
        cases = load_module(
            "skill_evaluator_shared_fixtures",
            "evaluation_cases.py",
        )
        document = cases.load_cases(ROOT)
        extended = copy.deepcopy(document)
        extended.setdefault("fixture_sets", {})["wiki-base"] = [
            {
                "path": "fixture/wiki/config.json",
                "content": '{"vault": "{{WORKSPACE}}/fixture/wiki"}\n',
            }
        ]
        qmd = next(
            item for item in extended["skills"]
            if item["skill_name"] == "qmd"
        )
        required = qmd["core_cases"][0]
        required["fixture_sets"] = ["wiki-base"]
        required["fixtures"] = [
            {
                "path": "fixture/query.txt",
                "content": "fixture query\n",
            }
        ]

        self.assertEqual(cases.validate_cases(ROOT, extended), [])
        plan = cases.build_plan(ROOT, extended, ["qmd"])
        required_runs = [
            item
            for item in plan
            if item["case_id"] == required["id"]
        ]
        self.assertTrue(
            all(
                item["fixture_sets"] == ["wiki-base"]
                and item["fixtures"]
                == extended["fixture_sets"]["wiki-base"] + required["fixtures"]
                for item in required_runs
            )
        )

        duplicate = copy.deepcopy(extended)
        duplicate_qmd = next(
            item for item in duplicate["skills"]
            if item["skill_name"] == "qmd"
        )
        duplicate_qmd["core_cases"][0]["fixtures"][0]["path"] = (
            "fixture/wiki/config.json"
        )
        self.assertTrue(
            any(
                "duplicate fixture path" in error
                for error in cases.validate_cases(ROOT, duplicate)
            )
        )

        unsafe = copy.deepcopy(extended)
        unsafe["fixture_sets"]["wiki-base"][0]["path"] = "../settings.json"
        self.assertTrue(
            any(
                "fixture_sets" in error and "invalid" in error
                for error in cases.validate_cases(ROOT, unsafe)
            )
        )
        nested_git = copy.deepcopy(extended)
        nested_git["fixture_sets"]["wiki-base"][0]["path"] = (
            "fixture/.git/config"
        )
        self.assertTrue(
            any(
                "fixture_sets" in error and "invalid" in error
                for error in cases.validate_cases(ROOT, nested_git)
            )
        )
        bad_set_name = copy.deepcopy(extended)
        bad_set_name["fixture_sets"]["Bad Name"] = bad_set_name[
            "fixture_sets"
        ].pop("wiki-base")
        self.assertTrue(
            any(
                "fixture_sets entry is invalid" in error
                for error in cases.validate_cases(ROOT, bad_set_name)
            )
        )
        bad_case_id = copy.deepcopy(extended)
        qmd_case = next(
            item for item in bad_case_id["skills"]
            if item["skill_name"] == "qmd"
        )["core_cases"][0]
        qmd_case["id"] = "Bad ID"
        self.assertTrue(
            any(
                "case id is invalid or duplicated" in error
                for error in cases.validate_cases(ROOT, bad_case_id)
            )
        )
        for invalid_path in ("fixture/bad?.txt", "fixture/.git /config"):
            bad_path = copy.deepcopy(extended)
            bad_path["fixture_sets"]["wiki-base"][0]["path"] = invalid_path
            self.assertTrue(
                any(
                    "fixture_sets" in error and "invalid" in error
                    for error in cases.validate_cases(ROOT, bad_path)
                ),
                invalid_path,
            )

    def test_git_fixture_plan_is_tokenized_and_rejects_unsafe_duplicates(
        self,
    ) -> None:
        cases = load_module(
            "skill_evaluator_git_fixture_cases",
            "evaluation_cases.py",
        )
        document = cases.load_cases(ROOT)
        extended = copy.deepcopy(document)
        qmd = next(
            item for item in extended["skills"]
            if item["skill_name"] == "qmd"
        )
        required = qmd["core_cases"][0]
        required["git_fixture"] = {
            "baseline_files": [
                {
                    "path": "src/value.txt",
                    "content": "baseline\n",
                }
            ],
            "working_tree_files": [
                {
                    "path": "src/value.txt",
                    "content": "working {{WORKSPACE}}\n",
                },
                {
                    "path": "new.txt",
                    "content": "new\n",
                },
            ],
        }

        self.assertEqual(cases.validate_cases(ROOT, extended), [])
        plan = cases.build_plan(ROOT, extended, ["qmd"])
        required_runs = [
            item
            for item in plan
            if item["case_id"] == required["id"]
        ]
        self.assertTrue(
            all(
                item["git_fixture"] == required["git_fixture"]
                for item in required_runs
            )
        )
        self.assertIn(
            "{{WORKSPACE}}",
            required_runs[0]["git_fixture"]["working_tree_files"][0]["content"],
        )

        duplicate = copy.deepcopy(extended)
        duplicate_qmd = next(
            item for item in duplicate["skills"]
            if item["skill_name"] == "qmd"
        )
        duplicate_qmd["core_cases"][0]["git_fixture"][
            "baseline_files"
        ].append(
            {
                "path": "src/value.txt",
                "content": "duplicate\n",
            }
        )
        self.assertTrue(
            any(
                "git_fixture" in error and "duplicate" in error
                for error in cases.validate_cases(ROOT, duplicate)
            )
        )

        cross_collection_duplicate = copy.deepcopy(extended)
        duplicate_qmd = next(
            item for item in cross_collection_duplicate["skills"]
            if item["skill_name"] == "qmd"
        )
        duplicate_qmd["core_cases"][0]["fixtures"] = [
            {
                "path": "new.txt",
                "content": "ambiguous overlay\n",
            }
        ]
        self.assertTrue(
            any(
                "duplicate fixture path" in error
                for error in cases.validate_cases(
                    ROOT,
                    cross_collection_duplicate,
                )
            )
        )

        unsafe = copy.deepcopy(extended)
        unsafe_qmd = next(
            item for item in unsafe["skills"]
            if item["skill_name"] == "qmd"
        )
        unsafe_qmd["core_cases"][0]["git_fixture"][
            "working_tree_files"
        ][0]["path"] = ".git/config"
        self.assertTrue(
            any(
                "git_fixture" in error and "invalid" in error
                for error in cases.validate_cases(ROOT, unsafe)
            )
        )

    def test_runtime_tools_plan_uses_allowlist_and_content_digests(self) -> None:
        cases = load_module(
            "skill_evaluator_runtime_tool_cases",
            "evaluation_cases.py",
        )
        document = cases.load_cases(ROOT)
        extended = copy.deepcopy(document)
        qmd = next(
            item for item in extended["skills"]
            if item["skill_name"] == "qmd"
        )
        qmd["core_cases"][0]["runtime_tools"] = [
            "obsidian-wiki",
            "skill-evaluator",
        ]
        qmd["core_cases"][0]["external_tools"] = ["qmd"]

        self.assertEqual(cases.validate_cases(ROOT, extended), [])
        plan = cases.build_plan(ROOT, extended, ["qmd"])
        required_runs = [
            item
            for item in plan
            if item["case_id"] == qmd["core_cases"][0]["id"]
        ]
        first = required_runs[0]
        self.assertEqual(
            first["runtime_tools"],
            ["obsidian-wiki", "skill-evaluator"],
        )
        self.assertEqual(first["external_tools"], ["qmd"])
        self.assertEqual(
            set(first["runtime_tool_sources"]),
            {"obsidian-wiki", "skill-evaluator"},
        )
        self.assertTrue(
            all(
                Path(path).is_dir()
                for path in first["runtime_tool_sources"].values()
            )
        )
        self.assertTrue(
            all(
                digest.startswith("sha256:") and len(digest) == 71
                for digest in first["runtime_tool_digests"].values()
            )
        )
        self.assertTrue(
            all(
                item["runtime_tool_digests"]
                == first["runtime_tool_digests"]
                for item in required_runs
            )
        )

        unknown = copy.deepcopy(extended)
        unknown_qmd = next(
            item for item in unknown["skills"]
            if item["skill_name"] == "qmd"
        )
        unknown_qmd["core_cases"][0]["runtime_tools"] = ["shell"]
        self.assertTrue(
            any(
                "runtime_tools" in error
                for error in cases.validate_cases(ROOT, unknown)
            )
        )

        duplicate = copy.deepcopy(extended)
        duplicate_qmd = next(
            item for item in duplicate["skills"]
            if item["skill_name"] == "qmd"
        )
        duplicate_qmd["core_cases"][0]["runtime_tools"] = [
            "obsidian-wiki",
            "obsidian-wiki",
        ]
        self.assertTrue(
            any(
                "runtime_tools" in error
                for error in cases.validate_cases(ROOT, duplicate)
            )
        )

    def test_runtime_tool_plan_digest_changes_with_source_content(self) -> None:
        cases = load_module(
            "skill_evaluator_stale_runtime_tool_plan",
            "evaluation_cases.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            skill = repo / "skills" / "engineering" / "fixture-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: Fixture.\n---\n",
                encoding="utf-8",
            )
            inventory = repo / "inventory"
            inventory.mkdir()
            (inventory / "skills.json").write_text(
                json.dumps(
                    {
                        "skills": [
                            {
                                "state": "managed",
                                "managed_name": "fixture-skill",
                                "category": "engineering",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            runtime = repo / "tools" / "skill-evaluator"
            runtime.mkdir(parents=True)
            source = runtime / "tool.py"
            source.write_text("VERSION = 1\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "add", "tools/skill-evaluator/tool.py"],
                cwd=repo,
                check=True,
            )
            document = {
                "skills": [
                    {
                        "skill_name": "fixture-skill",
                        "evaluation_level": "full",
                        "core_cases": [
                            {
                                "id": "required",
                                "version": 1,
                                "prompt": "Exercise the fixture Skill behavior.",
                                "oracle": {
                                    "expected_outcome": "fixture behavior passes",
                                    "assertions": [
                                        {
                                            "id": "fixture-behavior",
                                            "kind": "deterministic",
                                            "description": (
                                                "fixture behavior passes"
                                            ),
                                            "required": True,
                                        }
                                    ],
                                },
                                "safety": "read-only",
                                "runtime_tools": ["skill-evaluator"],
                            }
                        ],
                        "invocation_cases": [
                            {
                                "id": "trigger",
                                "version": 1,
                                "prompt": "Naturally trigger the fixture Skill behavior.",
                                "expected_invocation": "implicit",
                            }
                        ],
                    }
                ]
            }

            before = cases.build_plan(repo, document)[0]
            source.write_text("VERSION = 2\n", encoding="utf-8")
            after = cases.build_plan(repo, document)[0]
            self.assertNotEqual(
                before["runtime_tool_digests"],
                after["runtime_tool_digests"],
            )
            self.assertEqual(
                before["runtime_tool_sources"],
                after["runtime_tool_sources"],
            )

    def test_stale_raw_plan_cannot_attest_changed_skill_content(self) -> None:
        cases = load_module(
            "skill_evaluator_stale_plan",
            "evaluation_cases.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            skill = repo / "skills" / "engineering" / "fixture-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: Fixture.\n---\n",
                encoding="utf-8",
            )
            inventory = repo / "inventory"
            inventory.mkdir()
            (inventory / "skills.json").write_text(
                json.dumps(
                    {
                        "skills": [
                            {
                                "state": "managed",
                                "managed_name": "fixture-skill",
                                "category": "engineering",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            document = {
                "skills": [
                    {
                        "skill_name": "fixture-skill",
                        "evaluation_level": "full",
                        "core_cases": [
                            {
                                "id": "required",
                                "version": 1,
                                "prompt": "Exercise the fixture Skill behavior.",
                                "oracle": {
                                    "expected_outcome": "fixture behavior passes",
                                    "assertions": [
                                        {
                                            "id": "fixture-behavior",
                                            "kind": "deterministic",
                                            "description": (
                                                "fixture behavior passes"
                                            ),
                                            "required": True,
                                        }
                                    ],
                                },
                                "safety": "read-only",
                            }
                        ],
                        "invocation_cases": [
                            {
                                "id": "trigger",
                                "version": 1,
                                "prompt": "Naturally trigger the fixture Skill behavior.",
                                "expected_invocation": "implicit",
                            }
                        ],
                    }
                ]
            }
            plan = cases.build_plan(repo, document)
            workspace = repo / ".scratch" / "skill-evals" / "batch-fixture"
            for item in plan:
                run = (
                    workspace
                    / item["skill_name"]
                    / item["case_id"]
                    / item["target"]
                )
                run.mkdir(parents=True)
                (run / "result.json").write_text(
                    json.dumps(
                        {
                            "plan": item,
                            "target_identity": f"{item['target']} fixture",
                            "target_identity_returncode": 0,
                            "result": {
                                "returncode": 0,
                                "timed_out": False,
                                "duration_ms": 1,
                                "total_tokens": None,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            cases.prepare_review_templates(workspace)
            for grading_path in workspace.rglob("grading.json"):
                grading = json.loads(grading_path.read_text(encoding="utf-8"))
                for expectation in grading["expectations"]:
                    expectation["status"] = "pass"
                    expectation["evidence"] = "Reviewed fixture evidence."
                grading_path.write_text(
                    json.dumps(grading),
                    encoding="utf-8",
                )

            (skill / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: Changed.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "batch plan does not match the manifest",
            ):
                cases.audit_reviewed_skill(
                    repo,
                    workspace,
                    document,
                    "fixture-skill",
                )

    def test_review_templates_fail_closed_and_preserve_human_edits(self) -> None:
        cases = load_module(
            "skill_evaluator_review_templates",
            "evaluation_cases.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run = (
                workspace
                / "qmd"
                / "retrieve-before-answer"
                / "codex"
            )
            run.mkdir(parents=True)
            (run / "result.json").write_text(
                json.dumps(
                    {
                        "plan": {
                            "mode": "core",
                            "assertions": [
                                {
                                    "id": "retrieves-evidence",
                                    "kind": "deterministic",
                                    "description": "retrieves full evidence",
                                    "required": True,
                                },
                                {
                                    "id": "cites-source",
                                    "kind": "human-rubric",
                                    "description": "cites the source",
                                    "required": False,
                                },
                            ],
                        },
                        "result": {"returncode": 0},
                    }
                ),
                encoding="utf-8",
            )
            first = cases.prepare_review_templates(workspace)
            grading_path = run / "grading.json"
            grading = json.loads(grading_path.read_text(encoding="utf-8"))
            self.assertEqual(first["created_grading_count"], 1)
            self.assertEqual(first["created_review_count"], 1)
            self.assertEqual(grading["schema_version"], 3)
            self.assertEqual(grading["observed_invocation"], "unknown")
            self.assertEqual(
                grading["invocation_evidence"],
                "PENDING HUMAN REVIEW",
            )
            review = json.loads(
                (workspace / "qmd" / "review.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIs(review["sanitization_confirmed"], False)
            self.assertTrue(
                all(
                    item["status"] == "pending"
                    and item["evidence"] == "PENDING HUMAN REVIEW"
                    and set(item) == {
                        "assertion_id",
                        "kind",
                        "description",
                        "required",
                        "trajectory_observation",
                        "status",
                        "evidence",
                        "observation",
                    }
                    and item["observation"] == "pending"
                    for item in grading["expectations"]
                )
            )

            grading["expectations"][0]["status"] = "pass"
            grading["expectations"][0]["evidence"] = "Reviewed evidence."
            grading["expectations"][0]["observation"] = "final-output"
            grading_path.write_text(
                json.dumps(grading),
                encoding="utf-8",
            )
            second = cases.prepare_review_templates(workspace)
            preserved = json.loads(grading_path.read_text(encoding="utf-8"))
            self.assertEqual(second["preserved_grading_count"], 1)
            self.assertEqual(preserved["expectations"][0]["status"], "pass")

    def test_interrupted_batch_prepares_every_planned_review(self) -> None:
        cases = load_module(
            "skill_evaluator_interrupted_review_templates",
            "evaluation_cases.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            runs = []
            for skill_name in ("first-skill", "second-skill"):
                runs.append(
                    {
                        "skill_name": skill_name,
                        "case_id": "normal-use",
                        "target": "codex",
                        "mode": "core",
                        "assertions": [
                            {
                                "id": "correct-result",
                                "kind": "deterministic",
                                "description": "Returns the correct result.",
                                "required": True,
                            }
                        ],
                    }
                )
            (workspace / "plan.json").write_text(
                json.dumps(
                    {
                        "schema_version": 4,
                        "skill_count": 2,
                        "model_run_count": 2,
                        "targets": ["claude", "codex"],
                        "skills": ["first-skill", "second-skill"],
                        "runs": runs,
                    }
                ),
                encoding="utf-8",
            )
            malformed = (
                workspace
                / "first-skill"
                / "normal-use"
                / "codex"
                / "result.json"
            )
            malformed.parent.mkdir(parents=True)
            malformed.write_text("{not-json", encoding="utf-8")

            result = cases.prepare_review_templates(workspace)

            self.assertEqual(result["created_grading_count"], 2)
            self.assertEqual(result["created_review_count"], 2)
            for skill_name in ("first-skill", "second-skill"):
                self.assertTrue(
                    (
                        workspace
                        / skill_name
                        / "normal-use"
                        / "codex"
                        / "grading.json"
                    ).is_file()
                )
                self.assertTrue(
                    (workspace / skill_name / "review.json").is_file()
                )
            aggregate = load_module(
                "skill_evaluator_interrupted_aggregate",
                "aggregate_benchmark.py",
            )
            first = aggregate.aggregate_workspace(
                workspace,
                "first-skill",
            )
            second = aggregate.aggregate_workspace(
                workspace,
                "second-skill",
            )
            self.assertEqual(
                first["cases"][0]["raw_result_state"],
                "malformed",
            )
            self.assertEqual(
                second["cases"][0]["raw_result_state"],
                "missing",
            )

    def test_workspace_changes_capture_content_before_cleanup(self) -> None:
        entry = load_module(
            "skill_evaluator_workspace_changes",
            "skill_evaluator.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            deleted = root / "deleted.txt"
            modified = root / "modified.txt"
            deleted.write_text("before delete", encoding="utf-8")
            modified.write_text("before change", encoding="utf-8")
            before = entry._workspace_snapshot(root)
            deleted.unlink()
            modified.write_text("after change", encoding="utf-8")
            (root / "created.txt").write_text("new state", encoding="utf-8")
            after = entry._workspace_snapshot(root)

            changes = entry._workspace_changes(before, after)

            self.assertEqual(
                [item["path"] for item in changes],
                ["created.txt", "deleted.txt", "modified.txt"],
            )
            self.assertEqual(
                [item["change"] for item in changes],
                ["created", "deleted", "modified"],
            )
            self.assertEqual(changes[0]["after"]["text"], "new state")
            self.assertEqual(changes[1]["before"]["text"], "before delete")
            self.assertEqual(changes[2]["after"]["text"], "after change")

    def test_workspace_snapshot_streams_large_files_without_text(self) -> None:
        entry = load_module(
            "skill_evaluator_large_workspace_snapshot",
            "skill_evaluator.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            large = root / "large.bin"
            payload = b"x" * (entry._WORKSPACE_TEXT_LIMIT + 1)
            large.write_bytes(payload)

            with patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("snapshot must stream files"),
            ):
                snapshot = entry._workspace_snapshot(root)

            self.assertEqual(snapshot["large.bin"]["size"], len(payload))
            self.assertEqual(
                snapshot["large.bin"]["sha256"],
                "sha256:" + hashlib.sha256(payload).hexdigest(),
            )
            self.assertIsNone(snapshot["large.bin"]["text"])

    def test_complete_reviewed_batch_passes_fail_closed_audit(self) -> None:
        cases = load_module(
            "skill_evaluator_draft_cases",
            "evaluation_cases.py",
        )
        runners = load_module(
            "skill_evaluator_draft_runners",
            "runners.py",
        )
        document = cases.load_cases(ROOT)
        qmd = next(
            entry
            for entry in document["skills"]
            if entry["skill_name"] == "qmd"
        )
        qmd["core_cases"][0]["oracle"]["assertions"].append(
            {
                "id": "optional-efficiency-warning",
                "kind": "trajectory",
                "description": "uses the shortest available safe query",
                "required": False,
                "trajectory_observation": "tool-trace",
            }
        )
        plan = cases.build_plan(ROOT, document, ["qmd"])
        scratch = ROOT / ".scratch" / "skill-evals"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp_dir:
            workspace = Path(temp_dir)

            def external_tool_evidence(item):
                if item["external_tools"] != ["qmd"]:
                    return {}
                return {
                    "qmd": {
                        "minimum_version": "2.5.3",
                        "identity": {
                            "command": ["qmd", "--version"],
                            "returncode": 0,
                            "timed_out": False,
                            "duration_ms": 1,
                            "stdout": "qmd 2.5.3\n",
                            "stderr": "",
                        },
                        "setup": [
                            {
                                "command": ["qmd", "init"],
                                "returncode": 0,
                                "timed_out": False,
                                "duration_ms": 1,
                                "stdout": "",
                                "stderr": "",
                            },
                            {
                                "command": [
                                    "qmd",
                                    "collection",
                                    "add",
                                    "fixture/qmd-notes",
                                    "--name",
                                    "evaluation",
                                ],
                                "returncode": 0,
                                "timed_out": False,
                                "duration_ms": 1,
                                "stdout": "",
                                "stderr": "",
                            },
                        ],
                        "workspace_index": ".qmd",
                        "fixture_root": "fixture/qmd-notes",
                    }
                }

            def fixture_stdout(item):
                needs_tool = any(
                    assertion.get("trajectory_observation")
                    == "tool-trace"
                    for assertion in item["assertions"]
                )
                if item["target"] == "claude":
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
                                                        "qmd query fixture"
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
                                                "content": "fixture evidence",
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
                            "result": "fixture evidence",
                        }
                    )
                    return "\n".join(json.dumps(event) for event in events)
                events = []
                if needs_tool:
                    events.append(
                        {
                            "type": "item.completed",
                            "item": {
                                "type": "command_execution",
                                "command": "qmd query fixture",
                                "aggregated_output": "fixture evidence",
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
                                "text": "fixture evidence",
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
                return "\n".join(json.dumps(event) for event in events)

            for item in plan:
                execution = (
                    Path(tempfile.gettempdir())
                    / "discarded-myskills-evaluation"
                    / item["case_id"]
                    / item["target"]
                )
                run = (
                    workspace
                    / item["skill_name"]
                    / item["case_id"]
                    / item["target"]
                )
                run.mkdir(parents=True)
                (run / "result.json").write_text(
                    json.dumps(
                        {
                            "plan": item,
                            "target_identity": f"{item['target']} fixture",
                            "target_identity_returncode": 0,
                            "external_tool_evidence": (
                                external_tool_evidence(item)
                            ),
                            "execution_workspace": str(execution),
                            "environment_isolation": (
                                {
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
                                    "windows_home_matches_profile": (
                                        True
                                        if sys.platform == "win32"
                                        else None
                                    ),
                                }
                                if item["target"] == "claude"
                                else None
                            ),
                            "isolation_violations": [],
                            "result": {
                                "command": (
                                    runners.build_command(
                                        "claude",
                                        "fixture",
                                        Path(item["skill_path"]),
                                        explicit=item["explicit"],
                                        safety=item["safety"],
                                        runtime_tools=item["runtime_tools"],
                                        external_tools=item["external_tools"],
                                        execution_workspace=execution,
                                    )
                                    if item["target"] == "claude"
                                    else ["codex", "exec", "fixture"]
                                ),
                                "returncode": 0,
                                "timed_out": False,
                                "duration_ms": 10,
                                "total_tokens": 20,
                                "stdout": fixture_stdout(item),
                                "stderr": "",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            cases.prepare_review_templates(workspace)
            for grading_path in workspace.rglob("grading.json"):
                grading = json.loads(grading_path.read_text(encoding="utf-8"))
                result = json.loads(
                    grading_path.with_name("result.json").read_text(
                        encoding="utf-8"
                    )
                )
                item = result["plan"]
                grading["observed_invocation"] = (
                    "explicit"
                    if item["explicit"]
                    else item["expected_invocation"]
                )
                grading["invocation_evidence"] = (
                    "Human checked the observable target trace."
                )
                for expectation in grading["expectations"]:
                    expectation["status"] = (
                        "pass" if expectation["required"] else "fail"
                    )
                    expectation["evidence"] = "Human checked the raw result."
                    expectation["observation"] = (
                        expectation["trajectory_observation"]
                        if expectation["kind"] == "trajectory"
                        else (
                            "invocation-trace"
                            if expectation["assertion_id"]
                            == "invocation-classification"
                            else "final-output"
                        )
                    )
                grading_path.write_text(
                    json.dumps(grading, indent=2) + "\n",
                    encoding="utf-8",
                )

            review = cases.audit_reviewed_skill(
                ROOT,
                workspace,
                document,
                "qmd",
            )
            self.assertEqual(
                set(review["target_identities"]),
                {"claude", "codex"},
            )
            self.assertEqual(
                review["targets"]["claude"]["core_cases"],
                {"passed": 3, "total": 3},
            )

            external_item = next(
                item
                for item in plan
                if item["external_tools"] == ["qmd"]
                and item["target"] == "claude"
            )
            external_result_path = (
                workspace
                / external_item["skill_name"]
                / external_item["case_id"]
                / external_item["target"]
                / "result.json"
            )
            external_record = json.loads(
                external_result_path.read_text(encoding="utf-8")
            )
            valid_external_evidence = external_record[
                "external_tool_evidence"
            ]
            external_record.pop("external_tool_evidence")
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "external tool evidence keys do not match the plan",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )

            malformed_evidence = copy.deepcopy(valid_external_evidence)
            malformed_evidence["qmd"]["identity"]["timed_out"] = True
            external_record["external_tool_evidence"] = malformed_evidence
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "external tool identity check did not pass",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )

            stale_evidence = copy.deepcopy(valid_external_evidence)
            stale_evidence["qmd"]["minimum_version"] = "2.5.2"
            external_record["external_tool_evidence"] = stale_evidence
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "minimum version does not match the dependency manifest",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )
            external_record["external_tool_evidence"] = valid_external_evidence
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            external_record["isolation_violations"] = [
                "Claude Read accessed the canonical Skill outside its "
                "execution workspace."
            ]
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "model isolation did not pass",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )
            external_record["isolation_violations"] = []
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            execution_workspace = external_record.pop(
                "execution_workspace"
            )
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "execution workspace is missing or not absolute",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )
            external_record["execution_workspace"] = execution_workspace

            original_result = copy.deepcopy(external_record["result"])
            external_record["result"]["stdout"] = "\n".join(
                [
                    json.dumps(
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": "tampered-read",
                                        "name": "Read",
                                        "input": {
                                            "file_path": str(
                                                ROOT
                                                / "skills"
                                                / "qmd"
                                                / "qmd"
                                                / "SKILL.md"
                                            )
                                        },
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
                                        "tool_use_id": "tampered-read",
                                        "content": "escaped",
                                        "is_error": False,
                                    }
                                ]
                            },
                        }
                    ),
                ]
            )
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "stored model isolation audit does not match the raw trace",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )
            external_record["result"] = original_result
            external_result_path.write_text(
                json.dumps(external_record),
                encoding="utf-8",
            )

            grading_path = next(workspace.rglob("grading.json"))
            grading = json.loads(grading_path.read_text(encoding="utf-8"))
            required_expectation = next(
                item for item in grading["expectations"] if item["required"]
            )
            required_expectation["status"] = "fail"
            required_expectation["evidence"] = "Required outcome was absent."
            grading_path.write_text(
                json.dumps(grading, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "every required expectation must pass",
            ):
                cases.audit_reviewed_skill(
                    ROOT,
                    workspace,
                    document,
                    "qmd",
                )

    def test_runner_isolates_skills_and_cleans_ephemeral_auth(self) -> None:
        runners = load_module(
            "skill_evaluator_runners_auth",
            "runners.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex_home = root / "codex"
            claude_home = root / "claude"
            (codex_home / "skills").mkdir(parents=True)
            (claude_home / "skills").mkdir(parents=True)
            codex_user_skill = codex_home / "skills" / "user-one"
            codex_user_skill.mkdir()
            (codex_user_skill / "SKILL.md").write_text(
                "---\nname: user-one\ndescription: User Skill.\n---\n",
                encoding="utf-8",
            )
            agents_user_skill = (
                root / "real-home" / ".agents" / "skills" / "user-two"
            )
            agents_user_skill.mkdir(parents=True)
            (agents_user_skill / "SKILL.md").write_text(
                "---\nname: user-two\ndescription: User Skill.\n---\n",
                encoding="utf-8",
            )
            (codex_home / "auth.json").write_text(
                '{"fixture": true}',
                encoding="utf-8",
            )
            (codex_home / "config.toml").write_text(
                "fixture = true",
                encoding="utf-8",
            )
            (claude_home / ".credentials.json").write_text(
                '{"fixture": true}',
                encoding="utf-8",
            )
            (claude_home / "settings.json").write_text(
                '{"fixture": true}',
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "CODEX_HOME": str(codex_home),
                    "CLAUDE_CONFIG_DIR": str(claude_home),
                    "USERPROFILE": str(root / "real-user"),
                    "HOME": str(root / "real-home"),
                    "APPDATA": str(root / "real-appdata"),
                    "LOCALAPPDATA": str(root / "real-localappdata"),
                    "HOMEDRIVE": "Z:",
                    "HOMEPATH": "\\real-user",
                    "XDG_CONFIG_HOME": str(root / "real-xdg-config"),
                    "XDG_CACHE_HOME": str(root / "real-xdg-cache"),
                    "OPENAI_API_KEY": "",
                    "ANTHROPIC_API_KEY": "",
                    "GIT_CONFIG_GLOBAL": str(root / "untrusted-gitconfig"),
                    "GIT_DIR": str(root / "untrusted-gitdir"),
                },
                clear=False,
            ):
                with runners.isolated_target_environment(
                    "codex",
                    allow_ephemeral_auth_copy=True,
                    allowed_commands=["qmd", "obsidian-wiki"],
                ) as codex_env:
                    isolated_codex = Path(codex_env["CODEX_HOME"])
                    self.assertTrue((isolated_codex / "auth.json").is_file())
                    isolated_config = (
                        isolated_codex / "config.toml"
                    ).read_text(encoding="utf-8")
                    self.assertIn(
                        codex_user_skill.as_posix() + "/SKILL.md",
                        isolated_config,
                    )
                    self.assertIn(
                        agents_user_skill.as_posix() + "/SKILL.md",
                        isolated_config,
                    )
                    self.assertEqual(
                        isolated_config.count("enabled = false"),
                        2,
                    )
                    self.assertNotIn("fixture = true", isolated_config)
                    isolated_rules = (
                        isolated_codex / "rules" / "default.rules"
                    ).read_text(encoding="utf-8")
                    self.assertIn(
                        'pattern = ["obsidian-wiki"]',
                        isolated_rules,
                    )
                    self.assertIn('pattern = ["qmd"]', isolated_rules)
                    self.assertEqual(
                        isolated_rules.count('decision = "allow"'),
                        2,
                    )
                    self.assertNotIn(codex_home.as_posix(), isolated_rules)
                    self.assertFalse((isolated_codex / "skills").exists())
                    self.assertEqual(
                        codex_env["USERPROFILE"],
                        str(isolated_codex),
                    )
                    self.assertEqual(codex_env["HOME"], str(isolated_codex))
                    self.assertEqual(
                        codex_env["APPDATA"],
                        str(root / "real-appdata"),
                    )
                    self.assertEqual(
                        codex_env["LOCALAPPDATA"],
                        str(root / "real-localappdata"),
                    )
                    self.assertEqual(
                        codex_env["XDG_CONFIG_HOME"],
                        str(root / "real-xdg-config"),
                    )
                    self.assertEqual(
                        codex_env["XDG_CACHE_HOME"],
                        str(root / "real-xdg-cache"),
                    )
                    self.assertEqual(codex_env["GIT_CONFIG_GLOBAL"], os.devnull)
                    self.assertEqual(codex_env["GIT_CONFIG_NOSYSTEM"], "1")
                    self.assertNotIn("GIT_DIR", codex_env)
                self.assertFalse(isolated_codex.exists())

                with runners.isolated_target_environment(
                    "claude",
                    allow_ephemeral_auth_copy=True,
                    denied_read_roots=[root / "repository"],
                    restrict_implicit_shell=True,
                    execution_workspace=root / "execution-workspace",
                ) as claude_env:
                    isolated_claude = Path(claude_env["CLAUDE_CONFIG_DIR"])
                    self.assertTrue(
                        (isolated_claude / ".credentials.json").is_file()
                    )
                    isolated_settings = json.loads(
                        (
                            root
                            / "execution-workspace"
                            / ".claude"
                            / "settings.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertFalse(
                        (isolated_claude / "settings.json").exists()
                    )
                    deny_rules = isolated_settings["permissions"]["deny"]
                    ask_rules = isolated_settings["permissions"]["ask"]
                    normalized_repository = (
                        (root / "repository").resolve().as_posix()
                    )
                    expected_repository_rule = (
                        "Read(//"
                        + normalized_repository[0].lower()
                        + normalized_repository[2:]
                        + "/**)"
                    )
                    self.assertIn(expected_repository_rule, deny_rules)
                    self.assertTrue(
                        any(claude_home.name in rule for rule in deny_rules)
                    )
                    self.assertIn("Bash(ls *)", ask_rules)
                    self.assertIn("Bash(find *)", ask_rules)
                    self.assertIn("Bash(cat *)", ask_rules)
                    self.assertIn("Bash(echo *)", ask_rules)
                    self.assertNotIn("fixture", isolated_settings)
                    self.assertFalse((isolated_claude / "skills").exists())
                    self.assertEqual(
                        claude_env["USERPROFILE"],
                        str(isolated_claude),
                    )
                    self.assertEqual(claude_env["HOME"], str(isolated_claude))
                    self.assertEqual(
                        claude_env["APPDATA"],
                        str(isolated_claude / "AppData" / "Roaming"),
                    )
                    self.assertEqual(
                        claude_env["LOCALAPPDATA"],
                        str(isolated_claude / "AppData" / "Local"),
                    )
                    self.assertEqual(
                        claude_env["XDG_CONFIG_HOME"],
                        str(isolated_claude / ".config"),
                    )
                    self.assertEqual(
                        claude_env["XDG_CACHE_HOME"],
                        str(isolated_claude / ".cache"),
                    )
                    if os.name == "nt":
                        drive, home_path = os.path.splitdrive(
                            str(isolated_claude)
                        )
                        self.assertEqual(claude_env["HOMEDRIVE"], drive)
                        self.assertEqual(claude_env["HOMEPATH"], home_path)
                    environment_evidence = (
                        runners.claude_environment_isolation_evidence(
                            claude_env,
                            root / "execution-workspace",
                        )
                    )
                    self.assertEqual(
                        environment_evidence,
                        {
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
                            "windows_home_matches_profile": (
                                True if os.name == "nt" else None
                            ),
                        },
                    )
                self.assertFalse(isolated_claude.exists())

    def test_execution_workspace_is_ephemeral_and_outside_repository(
        self,
    ) -> None:
        runners = load_module(
            "skill_evaluator_runners_execution_workspace",
            "runners.py",
        )
        with runners.isolated_execution_workspace(ROOT) as workspace:
            self.assertTrue(workspace.is_dir())
            with self.assertRaises(ValueError):
                workspace.relative_to(ROOT)
        self.assertFalse(workspace.exists())

    @unittest.skipUnless(os.name == "nt", "Codex execpolicy CLI contract")
    def test_codex_runtime_rule_allows_only_the_guarded_launcher_name(
        self,
    ) -> None:
        runners = load_module(
            "skill_evaluator_runners_execpolicy",
            "runners.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "fixture"},
                clear=False,
            ):
                with runners.isolated_target_environment(
                    "codex",
                    allow_ephemeral_auth_copy=True,
                    allowed_commands=["qmd"],
                ) as env:
                    rules = Path(env["CODEX_HOME"]) / "rules" / "default.rules"
                    allowed = runners.run_command(
                        [
                            "codex",
                            "execpolicy",
                            "check",
                            "--rules",
                            str(rules),
                            "--",
                            "qmd",
                            "search",
                            "fixture",
                        ],
                        cwd=root,
                        env=env,
                        timeout_seconds=30,
                    )
                    bypass = runners.run_command(
                        [
                            "codex",
                            "execpolicy",
                            "check",
                            "--rules",
                            str(rules),
                            "--",
                            (
                                "C:\\WINDOWS\\System32\\WindowsPowerShell"
                                "\\v1.0\\powershell.exe"
                            ),
                            "-NoLogo",
                            "-NoProfile",
                            "-NonInteractive",
                            "-File",
                            "C:\\host\\qmd.ps1",
                            "search",
                            "fixture",
                        ],
                        cwd=root,
                        env=env,
                        timeout_seconds=30,
                    )

            self.assertEqual(allowed["returncode"], 0, allowed["stderr"])
            self.assertEqual(bypass["returncode"], 0, bypass["stderr"])
            self.assertEqual(
                json.loads(allowed["stdout"])["decision"],
                "allow",
            )
            self.assertEqual(
                json.loads(bypass["stdout"])["matchedRules"],
                [],
            )

    def test_evaluation_digest_matches_installer(self) -> None:
        attestations = load_module(
            "skill_evaluator_attestations",
            "attestations.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            skill = Path(temp_dir) / "fixture-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: Fixture.\n---\n",
                encoding="utf-8",
            )
            digest = attestations.directory_digest(skill)
            command = (
                "Import-Module -Force "
                f"'{ROOT / 'scripts' / 'installer_core.psm1'}'; "
                f"Get-DirectoryDigest -Path '{skill}'"
            )
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(digest, f"sha256:{completed.stdout.strip()}")

    def test_attestation_schema_is_a_release_record_pointer(self) -> None:
        schema = json.loads(
            (
                ROOT / "attestations" / "attestation.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            3,
        )
        self.assertEqual(
            set(schema["required"]),
            {
                "$schema",
                "schema_version",
                "skill_name",
                "skill_digest",
                "record_path",
                "record_digest",
                "selected_at",
                "status",
            },
        )
        self.assertNotIn("targets", schema["properties"])
        self.assertNotIn("human_review", schema["properties"])

    def test_single_entry_point_runs_installer_smoke_contract(self) -> None:
        completed = subprocess.run(
            ["python", str(ENTRY_POINT), "smoke", "--json"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["passed"])
        self.assertEqual(
            set(result["checks"]),
            {
                "pyyaml",
                "fixture_validation",
                "claude_command",
                "codex_command",
                "benchmark",
                "static_report",
            },
        )

    def test_windows_launcher_uses_private_venv_and_managed_tool_snapshot(self) -> None:
        launcher = (TOOLS_ROOT / "skill-evaluator.cmd").read_text(encoding="utf-8")
        self.assertIn(
            "%LOCALAPPDATA%\\MySkills\\venvs\\skill-evaluator\\Scripts\\python.exe",
            launcher,
        )
        self.assertIn(
            "%LOCALAPPDATA%\\MySkills\\tools\\skill-evaluator\\skill_evaluator.py",
            launcher,
        )

    def test_validator_reports_public_structure_errors_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: wrong-name\ndescription: Example.\n---\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "python",
                    str(TOOLS_ROOT / "validate_skill.py"),
                    str(skill_dir),
                    "--json",
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("folder" in error for error in result["errors"]), result["errors"]
        )
        self.assertTrue(
            any("openai.yaml" in error for error in result["errors"]),
            result["errors"],
        )

    def test_runner_builds_isolated_commands_for_both_required_targets(self) -> None:
        runners = load_module("skill_evaluator_runners", "runners.py")
        claude = runners.build_command(
            "claude",
            "Use the test skill.",
            Path("C:/tmp/skill"),
            model=None,
            execution_workspace=Path("C:/evaluation/workspace"),
        )
        codex = runners.build_command(
            "codex", "Use the test skill.", Path("C:/tmp/skill"), model=None
        )

        self.assertEqual(claude[0:2], ["claude", "-p"])
        self.assertEqual(
            claude[claude.index("--output-format") + 1],
            "stream-json",
        )
        self.assertIn("--verbose", claude)
        self.assertIn("--setting-sources=project,local", claude)
        self.assertNotIn("--setting-sources", claude)
        self.assertEqual(
            claude[claude.index("--mcp-config") + 1],
            "{}",
        )
        self.assertIn("--strict-mcp-config", claude)
        self.assertIn("--no-chrome", claude)
        self.assertEqual(
            claude[claude.index("--permission-mode") + 1],
            "dontAsk",
        )
        claude_allowed = claude[claude.index("--allowedTools") + 1].split(",")
        self.assertIn(
            "Read(//c/evaluation/workspace/**)",
            claude_allowed,
        )
        self.assertNotIn("Read", claude_allowed)
        self.assertNotIn("Glob", claude_allowed)
        self.assertNotIn("Grep", claude_allowed)
        temporary = runners.build_command(
            "claude",
            "Create the requested fixture.",
            Path("C:/tmp/skill"),
            model=None,
            safety="temporary-workspace",
            execution_workspace=Path("C:/evaluation/workspace"),
        )
        self.assertNotIn("--permission-mode", temporary)
        self.assertNotIn("--allowedTools", temporary)
        self.assertEqual(
            temporary[temporary.index("--tools") + 1],
            "Read,Write,Edit,Glob,Grep,Bash",
        )
        self.assertEqual(
            codex[0:4],
            ["codex", "--ask-for-approval", "untrusted", "exec"],
        )
        self.assertIn("--json", codex)
        self.assertEqual(
            codex[codex.index("--ask-for-approval") + 1],
            "untrusted",
        )
        self.assertNotIn("--ignore-rules", codex)
        self.assertNotIn("--ignore-user-config", codex)
        claude_trigger = runners.build_command(
            "claude",
            "Natural trigger prompt.",
            Path("C:/tmp/skill"),
            explicit=False,
        )
        self.assertNotIn("--disable-slash-commands", claude_trigger)
        with self.assertRaises(TypeError):
            runners.build_command(
                "claude",
                "Natural trigger prompt.",
                Path("C:/tmp/skill"),
                explicit=False,
                baseline=True,
            )
        trigger = runners.build_command(
            "codex",
            "Natural trigger prompt.",
            Path("C:/tmp/skill"),
            explicit=False,
        )
        self.assertIn("Natural trigger prompt.", trigger[-1])
        self.assertNotIn("$skill", trigger[-1])

    def test_claude_isolation_rejects_host_customization_sources(self) -> None:
        aggregate = load_module(
            "skill_evaluator_aggregate_command_isolation",
            "aggregate_benchmark.py",
        )
        runners = load_module(
            "skill_evaluator_runners_command_isolation",
            "runners.py",
        )
        evidence = {
            "events": [],
            "parse_errors": [],
            "metadata": {"terminal_result_count": 1},
        }
        safe_command = runners.build_command(
            "claude",
            "Evaluate the fixture.",
            Path("C:/tmp/skill"),
            execution_workspace=Path("C:/evaluation/workspace"),
        )
        unsafe_command = [
            "claude",
            "-p",
            "Evaluate the fixture.",
            "--output-format",
            "stream-json",
        ]
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=unsafe_command,
            ),
            [
                "Claude command shape permits undeclared capabilities",
                "Claude command does not exclude user settings",
                "Claude command does not enforce an empty MCP configuration",
                "Claude command does not disable Chrome integration",
            ],
        )
        missing_read_boundary = [
            token
            for token in safe_command
            if token not in {
                "--permission-mode",
                "dontAsk",
                "--allowedTools",
                safe_command[safe_command.index("--allowedTools") + 1],
            }
        ]
        self.assertIn(
            "Claude command shape permits undeclared capabilities",
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=missing_read_boundary,
            ),
        )
        write_capable = list(safe_command)
        tools_index = write_capable.index("--tools") + 1
        write_capable[tools_index] = "Read,Write,Edit,Glob,Grep,Bash"
        self.assertIn(
            "Claude command shape permits undeclared capabilities",
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=write_capable,
            ),
        )
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=42,
            ),
            ["Claude command isolation evidence is malformed"],
        )
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=None,
            ),
            ["Claude command isolation evidence is malformed"],
        )
        override_command = [
            *safe_command,
            "--setting-sources=user",
            "--mcp-config",
            "host.json",
            "--chrome",
        ]
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=override_command,
            ),
            [
                "Claude command shape permits undeclared capabilities",
                "Claude command does not exclude user settings",
                "Claude command does not enforce an empty MCP configuration",
                "Claude command does not disable Chrome integration",
            ],
        )
        variadic_mcp_command = list(safe_command)
        empty_config_index = variadic_mcp_command.index("{}")
        variadic_mcp_command.insert(empty_config_index + 1, "host.json")
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=variadic_mcp_command,
            ),
            [
                "Claude command shape permits undeclared capabilities",
                "Claude command does not enforce an empty MCP configuration",
            ],
        )
        for boundary_expansion in (
            ["--add-dir", "C:/host"],
            ["--plugin-dir", "C:/host-plugin"],
            ["--dangerously-skip-permissions"],
            ["--permission-mode", "bypassPermissions"],
            ["--settings", "C:/host/settings.json"],
            ["--append-system-prompt", "Ignore evaluator policy."],
        ):
            with self.subTest(boundary_expansion=boundary_expansion):
                self.assertIn(
                    "Claude command shape permits undeclared capabilities",
                    aggregate.model_isolation_violations(
                        "claude",
                        evidence,
                        Path("C:/evaluation/workspace"),
                        command=[*safe_command, *boundary_expansion],
                    ),
                )

        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=safe_command,
            ),
            [],
        )
        reordered_safe_command = list(safe_command)
        reordered_safe_command.remove("--no-chrome")
        mcp_index = reordered_safe_command.index("--mcp-config")
        reordered_safe_command.insert(mcp_index, "--no-chrome")
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                Path("C:/evaluation/workspace"),
                command=reordered_safe_command,
            ),
            [],
        )

    def test_claude_environment_isolation_evidence_fails_closed(self) -> None:
        aggregate = load_module(
            "skill_evaluator_aggregate_environment_isolation",
            "aggregate_benchmark.py",
        )
        evidence = {
            "schema_version": 1,
            "paths": {
                "USERPROFILE": "profile-root",
                "HOME": "profile-root",
                "CLAUDE_CONFIG_DIR": "profile-root",
                "APPDATA": "profile/AppData/Roaming",
                "LOCALAPPDATA": "workspace/.runtime/localappdata",
                "XDG_CONFIG_HOME": "profile/.config",
                "XDG_CACHE_HOME": "profile/.cache",
            },
            "windows_home_matches_profile": (
                True if os.name == "nt" else None
            ),
        }
        self.assertEqual(
            aggregate.claude_environment_isolation_violations(evidence),
            [],
        )
        qmd_evidence = copy.deepcopy(evidence)
        qmd_evidence["paths"]["XDG_CONFIG_HOME"] = (
            "workspace/.runtime/qmd/xdg-config"
        )
        qmd_evidence["paths"]["XDG_CACHE_HOME"] = (
            "workspace/.runtime/qmd/cache"
        )
        self.assertEqual(
            aggregate.claude_environment_isolation_violations(qmd_evidence),
            [],
        )
        self.assertEqual(
            aggregate.claude_environment_isolation_violations(None),
            [
                (
                    "Claude environment isolation evidence is missing or "
                    "malformed"
                )
            ],
        )
        contaminated = copy.deepcopy(evidence)
        contaminated["paths"]["APPDATA"] = "outside-isolation-roots"
        self.assertEqual(
            aggregate.claude_environment_isolation_violations(contaminated),
            ["Claude environment path is not isolated: APPDATA"],
        )

    def test_claude_writable_command_shape_is_exact(self) -> None:
        aggregate = load_module(
            "skill_evaluator_aggregate_writable_command_isolation",
            "aggregate_benchmark.py",
        )
        runners = load_module(
            "skill_evaluator_runners_writable_command_isolation",
            "runners.py",
        )
        workspace = Path("C:/evaluation/workspace")
        evidence = {
            "events": [],
            "parse_errors": [],
            "metadata": {"terminal_result_count": 1},
        }
        command = runners.build_command(
            "claude",
            "Update the disposable fixture.",
            Path("C:/tmp/skill"),
            safety="temporary-workspace",
            execution_workspace=workspace,
        )
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                evidence,
                workspace,
                audit_undeclared_bash=False,
                command=command,
            ),
            [],
        )

        mutations: list[list[str]] = []
        without_tools = list(command)
        tools_index = without_tools.index("--tools")
        del without_tools[tools_index : tools_index + 2]
        mutations.append(without_tools)

        read_only_tools = list(command)
        read_only_tools[read_only_tools.index("--tools") + 1] = (
            "Read,Glob,Grep"
        )
        mutations.append(read_only_tools)
        mutations.append([*command, "--permission-mode", "dontAsk"])
        mutations.append(
            [
                *command,
                "--allowedTools",
                "Read(//c/evaluation/workspace/**)",
            ]
        )

        for mutation in mutations:
            with self.subTest(command=mutation):
                self.assertIn(
                    "Claude command shape permits undeclared capabilities",
                    aggregate.model_isolation_violations(
                        "claude",
                        evidence,
                        workspace,
                        audit_undeclared_bash=False,
                        command=mutation,
                    ),
                )

    @unittest.skipUnless(os.name == "nt", "Windows launcher contract")
    def test_runner_resolves_windows_cmd_to_adjacent_powershell_shim(
        self,
    ) -> None:
        runners = load_module(
            "skill_evaluator_runners_windows_shim",
            "runners.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "fixture-launcher.cmd").write_text(
                "@echo off\r\nexit /b 99\r\n",
                encoding="utf-8",
            )
            (root / "fixture-launcher.ps1").write_text(
                "Write-Output ($args -join '|')\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PATH"] = str(root) + os.pathsep + env.get("PATH", "")
            prompt = '$qmd & whoami; "quoted" | Write-Output nope'

            result = runners.run_command(
                ["fixture-launcher", "alpha", "two words", prompt],
                cwd=root,
                env=env,
                timeout_seconds=30,
            )

            self.assertEqual(result["returncode"], 0, result["stderr"])
            self.assertEqual(
                result["stdout"].strip(),
                f"alpha|two words|{prompt}",
            )
            self.assertEqual(
                result["command"],
                ["fixture-launcher", "alpha", "two words", prompt],
            )

    def test_claude_read_only_runtime_permissions_are_declaration_scoped(
        self,
    ) -> None:
        runners = load_module(
            "skill_evaluator_runners_runtime_permissions",
            "runners.py",
        )
        command = runners.build_command(
            "claude",
            "Query the fixture Wiki.",
            Path("C:/tmp/wiki-query"),
            runtime_tools=["obsidian-wiki"],
            execution_workspace=Path("C:/evaluation/workspace"),
        )

        tools = command[command.index("--tools") + 1]
        allowed_tools = command[command.index("--allowedTools") + 1]
        self.assertEqual(
            tools,
            "Read,Glob,Grep,Bash",
        )
        self.assertEqual(
            allowed_tools,
            (
                "Read(//c/evaluation/workspace/**),"
                "Bash(obsidian-wiki *)"
            ),
        )
        self.assertNotIn(",Bash,", f",{allowed_tools},")
        qmd_command = runners.build_command(
            "claude",
            "Search the fixture index.",
            Path("C:/tmp/qmd"),
            external_tools=["qmd"],
            execution_workspace=Path("C:/evaluation/workspace"),
        )
        self.assertEqual(
            qmd_command[qmd_command.index("--allowedTools") + 1],
            "Read(//c/evaluation/workspace/**),Bash(qmd *)",
        )
        with self.assertRaisesRegex(ValueError, "runtime tools are invalid"):
            runners.build_command(
                "claude",
                "Query the fixture Wiki.",
                Path("C:/tmp/wiki-query"),
                runtime_tools=["not-allowlisted"],
            )

    def test_runner_stages_only_the_requested_target_discovery_path(self) -> None:
        runners = load_module("skill_evaluator_runners_isolation", "runners.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source" / "example"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(
                "---\nname: example\ndescription: Example.\n---\n",
                encoding="utf-8",
            )

            claude_root = runners.prepare_isolated_workspace(
                source, "claude", root / "claude-run"
            )
            codex_root = runners.prepare_isolated_workspace(
                source, "codex", root / "codex-run"
            )

            self.assertTrue(
                (claude_root / ".claude" / "skills" / "example" / "SKILL.md").is_file()
            )
            self.assertFalse((claude_root / ".agents").exists())
            self.assertTrue(
                (codex_root / ".agents" / "skills" / "example" / "SKILL.md").is_file()
            )
            self.assertFalse((codex_root / ".claude").exists())

    def test_runner_stages_fixture_files_and_only_declared_skills(self) -> None:
        runners = load_module(
            "skill_evaluator_runners_fixtures",
            "runners.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            primary = source / "primary"
            companion = source / "companion"
            for skill in (primary, companion):
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {skill.name}\ndescription: Fixture.\n---\n",
                    encoding="utf-8",
                )

            workspace = runners.prepare_evaluation_workspace(
                [primary, companion],
                "codex",
                root / "run",
                fixtures=[
                    {
                        "path": "fixture/spec.md",
                        "content": "# Fixture specification\n",
                    }
                ],
            )

            self.assertTrue(
                (workspace / ".agents" / "skills" / "primary" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (
                    workspace
                    / ".agents"
                    / "skills"
                    / "companion"
                    / "SKILL.md"
                ).is_file()
            )
            self.assertEqual(
                (workspace / "fixture" / "spec.md").read_text(encoding="utf-8"),
                "# Fixture specification\n",
            )
            self.assertFalse((workspace / ".claude").exists())

    def test_runner_builds_git_fixed_point_and_resolves_workspace_token(
        self,
    ) -> None:
        runners = load_module(
            "skill_evaluator_runners_git_fixture",
            "runners.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "untrusted-template"
            hooks = template / "hooks"
            hooks.mkdir(parents=True)
            (hooks / "pre-commit").write_text(
                "# untrusted user template\n",
                encoding="utf-8",
            )
            global_config = root / "untrusted-gitconfig"
            global_config.write_text(
                f"[init]\n\ttemplateDir = {template.as_posix()}\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": str(global_config)},
            ):
                workspace = runners.prepare_evaluation_workspace(
                    [],
                    "codex",
                    root / "run",
                    fixtures=[
                        {
                            "path": "fixture/workspace.txt",
                            "content": "{{WORKSPACE}}\n",
                        }
                    ],
                    git_fixture={
                        "baseline_files": [
                            {
                                "path": "src/value.txt",
                                "content": "baseline\n",
                            }
                        ],
                        "working_tree_files": [
                            {
                                "path": "src/value.txt",
                                "content": "working {{WORKSPACE}}\n",
                            },
                            {
                                "path": "new.txt",
                                "content": "new\n",
                            },
                        ],
                    },
                )

            self.assertEqual(
                subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    cwd=workspace,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=True,
                ).stdout.strip(),
                "true",
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "show", "HEAD:src/value.txt"],
                    cwd=workspace,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=True,
                ).stdout,
                "baseline\n",
            )
            self.assertEqual(
                (workspace / "src" / "value.txt").read_text(encoding="utf-8"),
                f"working {workspace.as_posix()}\n",
            )
            self.assertEqual(
                (workspace / "fixture" / "workspace.txt").read_text(
                    encoding="utf-8"
                ),
                f"{workspace.as_posix()}\n",
            )
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=workspace,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            ).stdout
            self.assertIn(" M src/value.txt", status)
            self.assertIn("?? fixture/", status)
            self.assertIn("?? new.txt", status)
            self.assertEqual(
                subprocess.run(
                    ["git", "config", "--local", "user.name"],
                    cwd=workspace,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=True,
                ).stdout.strip(),
                "MySkills Evaluation Fixture",
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "config", "--local", "commit.gpgSign"],
                    cwd=workspace,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=True,
                ).stdout.strip(),
                "false",
            )
            self.assertFalse((workspace / ".git" / "hooks" / "pre-commit").exists())
            self.assertEqual(
                subprocess.run(
                    ["git", "config", "--local", "core.hooksPath"],
                    cwd=workspace,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=True,
                ).stdout.strip(),
                str(workspace / ".git" / "myskills-empty-hooks"),
            )

    def test_runner_stages_allowlisted_runtimes_with_isolated_config(
        self,
    ) -> None:
        runners = load_module(
            "skill_evaluator_runners_runtime_tools",
            "runners.py",
        )
        cases = load_module(
            "skill_evaluator_runtime_tool_digests",
            "evaluation_cases.py",
        )
        sources = {
            "obsidian-wiki": str(ROOT / "tools" / "obsidian-wiki"),
            "skill-evaluator": str(ROOT / "tools" / "skill-evaluator"),
        }
        digests = {
            name: cases._runtime_directory_digest(Path(path))
            for name, path in sources.items()
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            user_local = root / "user-local"
            user_local.mkdir()
            (user_local / "settings.json").write_text(
                '{"private": true}\n',
                encoding="utf-8",
            )
            workspace = runners.prepare_evaluation_workspace(
                [],
                "codex",
                root / "run",
                fixtures=[
                    {
                        "path": ".obsidian-wiki/config",
                        "content": (
                            'OBSIDIAN_VAULT_PATH="{{WORKSPACE}}/fixture/wiki"\n'
                        ),
                    },
                    {
                        "path": "fixture/wiki/index.md",
                        "content": "# Fixture Wiki\n",
                    },
                ],
            )
            base_env = os.environ.copy()
            original_path = base_env.get("PATH", "")
            base_env["LOCALAPPDATA"] = str(user_local)
            preparation = runners.prepare_runtime_environment(
                workspace,
                sources,
                digests,
                repo_root=ROOT,
                safety="read-only",
                base_env=base_env,
            )
            env = preparation.environment
            with self.assertRaisesRegex(
                ValueError,
                "outside the repository allowlist",
            ):
                runners.prepare_runtime_environment(
                    workspace,
                    sources,
                    digests,
                    repo_root=root,
                    safety="read-only",
                    base_env=base_env,
                )

            isolated_local = workspace / ".runtime" / "localappdata"
            tool_root = isolated_local / "MySkills"
            bin_root = tool_root / "bin"
            self.assertEqual(env["LOCALAPPDATA"], str(isolated_local.resolve()))
            self.assertEqual(
                env["OBSIDIAN_WIKI_CONFIG_HOME"],
                str(
                    (
                        workspace
                        / ".obsidian-wiki"
                    ).resolve()
                ),
            )
            self.assertEqual(
                env["PATH"],
                str(bin_root.resolve()) + os.pathsep + original_path,
            )
            self.assertFalse(
                (isolated_local / "settings.json").exists(),
            )
            self.assertTrue(
                (
                    tool_root
                    / "tools"
                    / "obsidian-wiki"
                    / "obsidian_wiki"
                    / "__main__.py"
                ).is_file()
            )

            self.assertTrue(
                (
                    tool_root
                    / "tools"
                    / "skill-evaluator"
                    / "skill_evaluator.py"
                ).is_file()
            )

            obsidian = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "--version",
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(obsidian.returncode, 0, obsidian.stderr)
            self.assertIn("obsidian-wiki", obsidian.stdout)
            resolved = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "config",
                    "resolve",
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(
                Path(json.loads(resolved.stdout)["vault_path"]),
                workspace / "fixture" / "wiki",
            )
            blocked = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "setup",
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("blocked by read-only evaluation policy", blocked.stderr)
            escaped = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "lint",
                    str(workspace.parent),
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(escaped.returncode, 2)
            self.assertIn("path escapes evaluation workspace", escaped.stderr)
            escaped_assignment = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "query",
                    "fixture question",
                    f"--vault={workspace.parent}",
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(escaped_assignment.returncode, 2)
            self.assertIn(
                "path escapes evaluation workspace",
                escaped_assignment.stderr,
            )
            repeated_escape = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "query",
                    "fixture question",
                    "--vault",
                    str(workspace / "fixture" / "wiki"),
                    "--vault",
                    str(workspace.parent),
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(repeated_escape.returncode, 2)
            self.assertIn(
                "path escapes evaluation workspace",
                repeated_escape.stderr,
            )
            shifted_path = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "graph-query",
                    "--top",
                    "8",
                    str(workspace.parent),
                    "fixture question",
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(shifted_path.returncode, 2)
            self.assertIn(
                "path escapes evaluation workspace",
                shifted_path.stderr,
            )
            shifted_batch_paths = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "obsidian-wiki.cmd"),
                    "batch-plan",
                    "--max-mb",
                    "2",
                    "--max-files",
                    "5",
                    str(workspace.parent),
                    str(workspace.parent),
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(shifted_batch_paths.returncode, 2)
            self.assertIn(
                "path escapes evaluation workspace",
                shifted_batch_paths.stderr,
            )
            evaluator = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "skill-evaluator.cmd"),
                    "smoke",
                    "--json",
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(evaluator.returncode, 0, evaluator.stderr)
            self.assertTrue(json.loads(evaluator.stdout)["passed"])
            evaluator_escape = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "skill-evaluator.cmd"),
                    "validate",
                    str(workspace.parent),
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(evaluator_escape.returncode, 2)
            self.assertIn(
                "path escapes evaluation workspace",
                evaluator_escape.stderr,
            )
            external_plan = workspace.parent / "escaped-plan.json"
            blocked_output = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "skill-evaluator.cmd"),
                    "plan-batch",
                    str(workspace),
                    "--out",
                    str(external_plan),
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(blocked_output.returncode, 2)
            self.assertFalse(external_plan.exists())
            self.assertIn(
                "command blocked by read-only evaluation policy",
                blocked_output.stderr,
            )
            blocked_commands = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    str(bin_root / "skill-evaluator.cmd"),
                    "commands",
                    "--target",
                    "codex",
                    str(workspace.parent),
                ],
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(blocked_commands.returncode, 2)
            self.assertIn(
                "command blocked by read-only evaluation policy",
                blocked_commands.stderr,
            )

    @unittest.skipUnless(os.name == "nt", "Windows launcher contract")
    def test_runner_prepares_isolated_qmd_and_blocks_mutation(self) -> None:
        runners = load_module(
            "skill_evaluator_runners_external_qmd",
            "runners.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            log_path = root / "qmd.log"
            (fake_bin / "qmd.cmd").write_text(
                '@powershell -NoProfile -File "%~dp0qmd.ps1" %*\n',
                encoding="utf-8",
            )
            (fake_bin / "qmd.ps1").write_text(
                "Add-Content -LiteralPath $env:MYSKILLS_QMD_TEST_LOG "
                "-Value ($args -join '|')\n"
                "if ($args[0] -eq '--version') {\n"
                "  Write-Output 'qmd 2.5.3'\n"
                "  exit 0\n"
                "}\n"
                "Write-Output ('fixture-qmd ' + ($args -join ' '))\n"
                "Write-Output ('INDEX_PATH=' + $env:INDEX_PATH)\n"
                "Write-Output ('QMD_CONFIG_DIR=' + $env:QMD_CONFIG_DIR)\n"
                "exit 0\n",
                encoding="utf-8",
            )
            workspace = runners.prepare_evaluation_workspace(
                [],
                "codex",
                root / "run",
                fixtures=[
                    {
                        "path": "fixture/qmd-notes/retry-policy.md",
                        "content": "# Retry policy\n\nFixture evidence.\n",
                    }
                ],
            )
            base_env = os.environ.copy()
            base_env["PATH"] = (
                str(fake_bin) + os.pathsep + base_env.get("PATH", "")
            )
            base_env["MYSKILLS_QMD_TEST_LOG"] = str(log_path)
            base_env["INDEX_PATH"] = str(root / "user-index.sqlite")
            base_env["QMD_CONFIG_DIR"] = str(root / "user-qmd-config")
            base_env["QMD_SKILLS_DIR"] = str(root / "user-qmd-skills")
            base_env["XDG_CONFIG_HOME"] = str(root / "user-xdg-config")
            base_env["XDG_CACHE_HOME"] = str(root / "user-xdg-cache")

            preparation = runners.prepare_runtime_environment(
                workspace,
                {},
                {},
                repo_root=ROOT,
                safety="read-only",
                base_env=base_env,
                external_tools=["qmd"],
            )
            env = preparation.environment

            setup_log = log_path.read_text(encoding="utf-8")
            identity = preparation.external_tool_evidence["qmd"]["identity"]
            self.assertEqual(identity["returncode"], 0)
            self.assertEqual(identity["stdout"].strip(), "qmd 2.5.3")
            self.assertEqual(
                preparation.external_tool_evidence["qmd"]["minimum_version"],
                "2.5.3",
            )
            self.assertIn("init", setup_log)
            self.assertIn(
                "collection|add|fixture/qmd-notes|--name|evaluation",
                setup_log.replace("\\", "/"),
            )
            safe = runners.run_command(
                ["qmd", "search", "retry policy"],
                cwd=workspace,
                env=env,
                timeout_seconds=30,
            )
            blocked = runners.run_command(
                ["qmd", "update"],
                cwd=workspace,
                env=env,
                timeout_seconds=30,
            )
            redirected = runners.run_command(
                ["qmd", "search", "retry policy", "--index", "other"],
                cwd=workspace,
                env=env,
                timeout_seconds=30,
            )
            self.assertEqual(safe["returncode"], 0, safe["stderr"])
            self.assertIn("fixture-qmd search retry policy", safe["stdout"])
            self.assertIn("INDEX_PATH=", safe["stdout"])
            self.assertNotIn(
                str(root / "user-index.sqlite"),
                safe["stdout"],
            )
            self.assertIn(
                f"QMD_CONFIG_DIR={workspace / '.runtime' / 'qmd' / 'config'}",
                safe["stdout"],
            )
            self.assertEqual(blocked["returncode"], 2)
            self.assertIn(
                "command blocked by read-only evaluation policy",
                blocked["stderr"],
            )
            self.assertEqual(redirected["returncode"], 2)
            self.assertIn(
                "index override blocked by evaluation policy",
                redirected["stderr"],
            )

    def test_runtime_staging_excludes_untracked_source_files(self) -> None:
        runners = load_module(
            "skill_evaluator_runners_tracked_runtime",
            "runners.py",
        )
        cases = load_module(
            "skill_evaluator_cases_tracked_runtime",
            "evaluation_cases.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            source = repo / "tools" / "skill-evaluator"
            source.mkdir(parents=True)
            tracked = source / "skill_evaluator.py"
            tracked.write_text("print('tracked')\n", encoding="utf-8")
            (source / "untracked-secret.txt").write_text(
                "must not be staged\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            subprocess.run(
                ["git", "add", "tools/skill-evaluator/skill_evaluator.py"],
                cwd=repo,
                check=True,
            )
            digest = cases._runtime_directory_digest(
                source,
                repo_root=repo,
            )
            workspace = repo / "workspace"
            runners.prepare_runtime_environment(
                workspace,
                {"skill-evaluator": str(source)},
                {"skill-evaluator": digest},
                repo_root=repo,
                safety="temporary-workspace",
                base_env={},
            )
            staged = (
                workspace
                / ".runtime"
                / "localappdata"
                / "MySkills"
                / "tools"
                / "skill-evaluator"
            )
            self.assertTrue((staged / "skill_evaluator.py").is_file())
            self.assertFalse((staged / "untracked-secret.txt").exists())

    def test_aggregator_and_static_report_cover_fixture_workspace(self) -> None:
        aggregate = load_module(
            "skill_evaluator_aggregate", "aggregate_benchmark.py"
        )
        report = load_module("skill_evaluator_report", "generate_report.py")
        runners = load_module(
            "skill_evaluator_report_runners",
            "runners.py",
        )
        self.assertEqual(aggregate._review_state([]), "pending")
        malformed_claude = aggregate._claude_evidence(
            json.dumps({"permission_denials": 1})
        )
        self.assertEqual(
            malformed_claude["parse_errors"],
            ["Claude permission_denials must be an array"],
        )
        claude_stream = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Searching the fixture.",
                                },
                                {
                                    "type": "tool_use",
                                    "id": "tool-1",
                                    "name": "Bash",
                                    "input": {
                                        "command": (
                                            'qmd search "retry policy"'
                                        )
                                    },
                                },
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
                                    "content": "qmd://evaluation/retry-policy.md",
                                    "is_error": False,
                                }
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "success",
                        "is_error": False,
                        "result": "Claude stream final answer",
                        "num_turns": 2,
                        "usage": {"output_tokens": 12},
                        "permission_denials": [],
                    }
                ),
            ]
        )
        parsed_claude = aggregate._claude_evidence(claude_stream)
        self.assertEqual(
            parsed_claude["final_response"],
            "Claude stream final answer",
        )
        self.assertEqual(
            parsed_claude["events"],
            [
                {
                    "type": "agent_message",
                    "text": "Searching the fixture.",
                },
                {
                    "type": "tool_use",
                    "id": "tool-1",
                    "name": "Bash",
                    "input": {
                        "command": 'qmd search "retry policy"'
                    },
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "tool-1",
                    "content": "qmd://evaluation/retry-policy.md",
                    "is_error": False,
                },
            ],
        )
        self.assertEqual(parsed_claude["parse_errors"], [])
        isolation_stream = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "outside-read",
                                    "name": "Read",
                                    "input": {
                                        "file_path": (
                                            "C:\\project\\MySkills\\skills"
                                            "\\qmd\\qmd\\SKILL.md"
                                        )
                                    },
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
                                    "tool_use_id": "outside-read",
                                    "content": "canonical Skill",
                                    "is_error": False,
                                }
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "generic-bash",
                                    "name": "Bash",
                                    "input": {
                                        "command": "find C:\\project\\MySkills"
                                    },
                                },
                                {
                                    "type": "tool_use",
                                    "id": "guarded-qmd",
                                    "name": "Bash",
                                    "input": {
                                        "command": "qmd search fixture"
                                    },
                                },
                                {
                                    "type": "tool_use",
                                    "id": "relative-read",
                                    "name": "Read",
                                    "input": {
                                        "file_path": "..\\host-secret.txt"
                                    },
                                },
                                {
                                    "type": "tool_use",
                                    "id": "outside-write",
                                    "name": "Write",
                                    "input": {
                                        "file_path": (
                                            "C:\\project\\MySkills\\escaped.txt"
                                        )
                                    },
                                },
                                {
                                    "type": "tool_use",
                                    "id": "compound-qmd",
                                    "name": "Bash",
                                    "input": {
                                        "command": (
                                            "qmd search fixture && "
                                            "type C:\\project\\MySkills\\secret"
                                        )
                                    },
                                },
                                {
                                    "type": "tool_use",
                                    "id": "malformed-grep",
                                    "name": "Grep",
                                    "input": {
                                        "pattern": "secret",
                                        "path": 42,
                                    },
                                },
                                {
                                    "type": "tool_use",
                                    "id": "malformed-bash",
                                    "name": "Bash",
                                    "input": {"command": None},
                                },
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
                                    "tool_use_id": "generic-bash",
                                    "content": "escaped",
                                    "is_error": False,
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "guarded-qmd",
                                    "content": "fixture result",
                                    "is_error": False,
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "relative-read",
                                    "content": "escaped",
                                    "is_error": False,
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "outside-write",
                                    "content": "escaped",
                                    "is_error": False,
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "compound-qmd",
                                    "content": "escaped",
                                    "is_error": False,
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "malformed-grep",
                                    "content": "escaped",
                                    "is_error": False,
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "malformed-bash",
                                    "content": "escaped",
                                    "is_error": False,
                                },
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "success",
                        "is_error": False,
                        "result": "fixture result",
                        "permission_denials": [],
                    }
                ),
            ]
        )
        isolation_evidence = aggregate._claude_evidence(isolation_stream)
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                isolation_evidence,
                Path("C:/evaluation/workspace"),
                allowed_commands=["qmd"],
            ),
            [
                (
                    "Read accessed C:\\project\\MySkills\\skills\\qmd\\qmd"
                    "\\SKILL.md outside C:\\evaluation\\workspace"
                ),
                "Bash executed undeclared command: find C:\\project\\MySkills",
                (
                    "Read accessed ..\\host-secret.txt outside "
                    "C:\\evaluation\\workspace"
                ),
                (
                    "Write accessed C:\\project\\MySkills\\escaped.txt outside "
                    "C:\\evaluation\\workspace"
                ),
                (
                    "Bash executed undeclared command: qmd search fixture && "
                    "type C:\\project\\MySkills\\secret"
                ),
                (
                    "Grep returned success with malformed path field(s): path"
                ),
                "Bash returned success without an auditable command",
            ],
        )
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                {
                    "events": [
                        {
                            "type": "tool_use",
                            "id": "orphan",
                            "name": "Read",
                            "input": {"file_path": "fixture/input.txt"},
                        }
                    ],
                    "parse_errors": [],
                    "metadata": {"terminal_result_count": 1},
                },
                Path("C:/evaluation/workspace"),
            ),
            ["Claude evidence has tool use without result: orphan"],
        )
        truncated = aggregate._claude_evidence(
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "text", "text": "truncated response"}
                        ]
                    },
                }
            )
        )
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                truncated,
                Path("C:/evaluation/workspace"),
            ),
            [
                "Claude evidence must contain exactly one terminal result event"
            ],
        )
        temporary_bash = aggregate._claude_evidence(
            "\n".join(
                [
                    json.dumps(
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": "temporary-python",
                                        "name": "Bash",
                                        "input": {
                                            "command": (
                                                "python -m unittest discover "
                                                "-s tests"
                                            )
                                        },
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
                                        "tool_use_id": "temporary-python",
                                        "content": "OK",
                                        "is_error": False,
                                    }
                                ]
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "result",
                            "result": "Tests passed.",
                            "permission_denials": [],
                        }
                    ),
                ]
            )
        )
        self.assertEqual(
            aggregate.model_isolation_violations(
                "claude",
                temporary_bash,
                Path("C:/evaluation/workspace"),
                audit_undeclared_bash=False,
            ),
            [],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            for target in ("claude", "codex"):
                run_dir = workspace / "example" / "case-one" / target
                run_dir.mkdir(parents=True)
                if target == "claude":
                    stdout = "\n".join(
                        [
                            json.dumps(
                                {
                                    "type": "assistant",
                                    "message": {
                                        "content": [
                                            {
                                                "type": "tool_use",
                                                "id": "tool-qmd",
                                                "name": "Bash",
                                                "input": {
                                                    "command": (
                                                        "qmd search fixture"
                                                    )
                                                },
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
                                                "tool_use_id": "tool-qmd",
                                                "content": (
                                                    "fixture qmd evidence"
                                                ),
                                                "is_error": False,
                                            }
                                        ]
                                    },
                                }
                            ),
                            json.dumps(
                                {
                                    "type": "result",
                                    "subtype": "success",
                                    "is_error": False,
                                    "num_turns": 2,
                                    "result": (
                                        "Claude final answer <unsafe>"
                                    ),
                                    "stop_reason": "end_turn",
                                    "total_cost_usd": 0.01,
                                    "usage": {"output_tokens": 12},
                                    "permission_denials": [],
                                    "terminal_reason": "completed",
                                }
                            ),
                        ]
                    )
                else:
                    stdout = "\n".join(
                        [
                            json.dumps(
                                {
                                    "type": "item.completed",
                                    "item": {
                                        "type": "command_execution",
                                        "command": "Get-Content fixture/input.txt",
                                        "aggregated_output": "fixture evidence",
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
                                        "text": "Codex final answer",
                                    },
                                }
                            ),
                            json.dumps(
                                {
                                    "type": "turn.completed",
                                    "usage": {
                                        "input_tokens": 20,
                                        "output_tokens": 8,
                                    },
                                }
                            ),
                        ]
                    )
                (run_dir / "result.json").write_text(
                    json.dumps(
                        {
                            "plan": {
                                "skill_name": "example",
                                "case_id": "case-one",
                                "target": target,
                                "mode": "required",
                                "prompt": "Use fixture/input.txt to answer.",
                                "assertions": [
                                    "Produces the required file"
                                ],
                                "safety": "read-only",
                                "expected_invocation": None,
                                "explicit": True,
                                "skill_path": "C:/repo/skills/example",
                                "fixtures": [
                                    {
                                        "path": "fixture/input.txt",
                                        "content": "fixture evidence",
                                    }
                                ],
                                "git_fixture": {
                                    "baseline_files": [
                                        {
                                            "path": "tracked.txt",
                                            "content": "committed\n",
                                        }
                                    ],
                                    "working_tree_files": [
                                        {
                                            "path": "tracked.txt",
                                            "content": "changed\n",
                                        }
                                    ],
                                },
                                "fixture_sets": ["example"],
                                "runtime_tools": [],
                                "external_tools": ["qmd"],
                                "companion_skills": [],
                                "skill_digest": "sha256:fixture",
                            },
                            "target_identity": f"{target} fixture",
                            "target_identity_returncode": (
                                1 if target == "codex" else 0
                            ),
                            "external_tool_evidence": {
                                "qmd": {
                                    "minimum_version": "2.5.3",
                                    "identity": {
                                        "command": [
                                            "C:/tools/qmd.ps1",
                                            "--version",
                                        ],
                                        "returncode": 0,
                                        "timed_out": False,
                                        "stdout": "qmd 2.5.3\n",
                                        "stderr": "",
                                    },
                                    "setup": [
                                        {
                                            "command": [
                                                "C:/tools/qmd.ps1",
                                                "init",
                                            ],
                                            "returncode": 0,
                                            "timed_out": False,
                                        }
                                    ],
                                    "workspace_index": ".qmd",
                                    "fixture_root": "fixture/qmd-notes",
                                }
                            },
                            "execution_workspace": str(
                                run_dir / "workspace"
                            ),
                            "environment_isolation": (
                                {
                                    "schema_version": 1,
                                    "paths": {
                                        "USERPROFILE": "profile-root",
                                        "HOME": "profile-root",
                                        "CLAUDE_CONFIG_DIR": "profile-root",
                                        "APPDATA": (
                                            "profile/AppData/Roaming"
                                        ),
                                        "LOCALAPPDATA": (
                                            "profile/AppData/Local"
                                        ),
                                        "XDG_CONFIG_HOME": "profile/.config",
                                        "XDG_CACHE_HOME": "profile/.cache",
                                    },
                                    "windows_home_matches_profile": (
                                        True if os.name == "nt" else None
                                    ),
                                }
                                if target == "claude"
                                else None
                            ),
                            "isolation_violations": (
                                [
                                    "Read accessed canonical Skill outside "
                                    "the execution workspace"
                                ]
                                if target == "claude"
                                else []
                            ),
                            "result": {
                                "command": (
                                    runners.build_command(
                                        "claude",
                                        "fixture prompt",
                                        Path("C:/repo/skills/example"),
                                        safety="read-only",
                                        external_tools=["qmd"],
                                        execution_workspace=(
                                            run_dir / "workspace"
                                        ),
                                    )
                                    if target == "claude"
                                    else [target, "fixture prompt"]
                                ),
                                "returncode": 0,
                                "timed_out": False,
                                "duration_ms": 1000,
                                "stdout": stdout,
                                "stderr": "",
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
                            "invocation_evidence": (
                                "Fixture explicitly invokes the Skill."
                            ),
                            "observed_external_state": None,
                            "expectations": [
                                {
                                    "assertion_id": "produces-required-file",
                                    "kind": "deterministic",
                                    "description": "Produces the required file",
                                    "required": True,
                                    "trajectory_observation": "not-applicable",
                                    "status": "pass",
                                    "evidence": (
                                        "PENDING HUMAN REVIEW"
                                        if target == "claude"
                                        else "fixture"
                                    ),
                                    "observation": "final-output",
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

            benchmark = aggregate.aggregate_workspace(workspace, "example")
            output = workspace / "example" / "review.html"
            report.write_static_report(benchmark, output)

            self.assertEqual(benchmark["summary"]["pass_rate"], 1.0)
            self.assertEqual(
                {case["target"] for case in benchmark["cases"]},
                {"claude", "codex"},
            )
            claude_case = next(
                case
                for case in benchmark["cases"]
                if case["target"] == "claude"
            )
            codex_case = next(
                case
                for case in benchmark["cases"]
                if case["target"] == "codex"
            )
            self.assertEqual(
                claude_case["model_evidence"]["final_response"],
                "Claude final answer <unsafe>",
            )
            self.assertEqual(claude_case["review_state"], "pending")
            self.assertEqual(
                codex_case["model_evidence"]["final_response"],
                "Codex final answer",
            )
            self.assertEqual(
                codex_case["model_evidence"]["events"][0]["command"],
                "Get-Content fixture/input.txt",
            )
            self.assertEqual(
                claude_case["prompt"],
                "Use fixture/input.txt to answer.",
            )
            html = output.read_text(encoding="utf-8")
            self.assertIn("example", html)
            self.assertIn("Use fixture/input.txt to answer.", html)
            self.assertIn("Claude final answer &lt;unsafe&gt;", html)
            self.assertIn("Tool</strong>: Bash", html)
            self.assertIn("qmd search fixture", html)
            self.assertIn("fixture qmd evidence", html)
            self.assertIn("ISOLATION FAIL", html)
            self.assertIn(
                "Read accessed canonical Skill outside",
                html,
            )
            self.assertIn("Codex final answer", html)
            self.assertIn("Get-Content fixture/input.txt", html)
            self.assertIn("Skill run", html)
            self.assertNotIn("Baseline kind", html)
            self.assertIn("Canonical Skill path", html)
            self.assertIn("C:/repo/skills/example", html)
            self.assertIn("External tools</dt><dd>qmd", html)
            self.assertIn("External runtime identity and setup", html)
            self.assertIn(
                "Sanitized child environment isolation evidence",
                html,
            )
            self.assertIn("qmd 2.5.3", html)
            self.assertIn("C:/tools/qmd.ps1", html)
            self.assertIn("Committed baseline files", html)
            missing_audit_html = report._render_run(
                {
                    "process": {
                        "returncode": 0,
                        "timed_out": False,
                    },
                    "target_identity_returncode": 0,
                }
            )
            self.assertIn("ISOLATION FAIL", missing_audit_html)
            self.assertNotIn("ISOLATION PASS", missing_audit_html)
            self.assertIn("Audit state: missing", missing_audit_html)
            self.assertIn("Working-tree changes", html)
            self.assertIn("committed", html)
            self.assertIn("changed", html)
            self.assertIn("Declared/base prompt", html)
            self.assertIn(
                "Exact logical launch command (includes the actual prompt)",
                html,
            )
            self.assertIn("Identity return code</dt><dd>1", html)
            self.assertIn("PROCESS FAIL", html)
            self.assertIn("HUMAN REVIEW: PENDING", html)
            self.assertIn(
                'href="./case-one/claude/result.json"',
                html,
            )
            self.assertIn(
                'href="./case-one/claude/grading.json"',
                html,
            )
            self.assertTrue(
                (
                    output.parent
                    / "case-one"
                    / "claude"
                    / "result.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output.parent
                    / "case-one"
                    / "claude"
                    / "grading.json"
                ).is_file()
            )
            self.assertEqual(report._relative_href("../secret"), "#")
            self.assertEqual(
                report._relative_href("javascript:alert(1)"),
                "./javascript:alert(1)",
            )
            self.assertNotIn("https://", html)
            self.assertNotIn("<unsafe>", html)


if __name__ == "__main__":
    unittest.main()
