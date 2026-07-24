from __future__ import annotations

import importlib.util
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = ROOT / "tools" / "skill-evaluator"
ENTRY_POINT = TOOLS_ROOT / "skill_evaluator.py"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS_ROOT / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillEvaluatorToolContractTests(unittest.TestCase):
    def test_evaluation_case_manifest_covers_every_skill_and_full_baseline(
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
        self.assertEqual(summary["model_run_count"], 336)
        cases_by_name = {
            entry["skill_name"]: entry
            for entry in document["skills"]
        }
        for name in summary["skills"]:
            runs = [item for item in plan if item["skill_name"] == name]
            self.assertEqual(len(runs), 8, name)
            self.assertTrue(
                all(
                    item["evaluation_level"] == "full"
                    and item["baseline"] == cases_by_name[name]["baseline"]
                    for item in runs
                ),
                name,
            )
            self.assertEqual(
                {(item["target"], item["configuration"]) for item in runs},
                {
                    ("claude", "with_skill"),
                    ("claude", "baseline"),
                    ("codex", "with_skill"),
                    ("codex", "baseline"),
                },
            )

        invalid = copy.deepcopy(document)
        invalid["skills"][0]["trigger_cases"][0]["expected_invocation"] = "implicit"
        errors = cases.validate_cases(ROOT, invalid)
        self.assertTrue(
            any("expected_invocation" in error for error in errors),
            errors,
        )

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
            self.assertEqual(plan["model_run_count"], 8)
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
        required = implement["required_cases"][0]
        required["fixtures"] = [
            {
                "path": "fixture/spec.md",
                "content": "# Fixture specification\n",
            }
        ]
        required["companion_skills"] = ["tdd", "code-review"]

        self.assertEqual(cases.validate_cases(ROOT, extended), [])
        plan = cases.build_plan(ROOT, extended, ["implement"])
        required_runs = [item for item in plan if item["mode"] == "required"]
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
                        "baseline": {
                            "kind": "no-skill",
                            "identity": "fixture-baseline",
                        },
                        "required_cases": [
                            {
                                "id": "required",
                                "prompt": "Exercise the fixture Skill behavior.",
                                "assertions": ["fixture behavior passes"],
                                "safety": "read-only",
                            }
                        ],
                        "trigger_cases": [
                            {
                                "id": "trigger",
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
                    / item["configuration"]
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
                    expectation["passed"] = True
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
                / "with_skill"
                / "codex"
            )
            run.mkdir(parents=True)
            (run / "result.json").write_text(
                json.dumps(
                    {
                        "plan": {
                            "mode": "required",
                            "assertions": [
                                "retrieves full evidence",
                                "cites the source",
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
            self.assertTrue(
                all(
                    item["passed"] is False
                    and item["evidence"] == "PENDING HUMAN REVIEW"
                    for item in grading["expectations"]
                )
            )

            grading["expectations"][0]["passed"] = True
            grading["expectations"][0]["evidence"] = "Reviewed evidence."
            grading_path.write_text(
                json.dumps(grading),
                encoding="utf-8",
            )
            second = cases.prepare_review_templates(workspace)
            preserved = json.loads(grading_path.read_text(encoding="utf-8"))
            self.assertEqual(second["preserved_grading_count"], 1)
            self.assertTrue(preserved["expectations"][0]["passed"])

    def test_complete_reviewed_batch_produces_pending_attestation_draft(self) -> None:
        cases = load_module(
            "skill_evaluator_draft_cases",
            "evaluation_cases.py",
        )
        document = cases.load_cases(ROOT)
        plan = cases.build_plan(ROOT, document, ["qmd"])
        scratch = ROOT / ".scratch" / "skill-evals"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp_dir:
            workspace = Path(temp_dir)
            for item in plan:
                run = (
                    workspace
                    / item["skill_name"]
                    / item["case_id"]
                    / item["configuration"]
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
                                "duration_ms": 10,
                                "total_tokens": 20,
                                "stdout": "fixture evidence",
                                "stderr": "",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            cases.prepare_review_templates(workspace)
            for grading_path in workspace.rglob("grading.json"):
                grading = json.loads(grading_path.read_text(encoding="utf-8"))
                for expectation in grading["expectations"]:
                    expectation["passed"] = True
                    expectation["evidence"] = "Human checked the raw result."
                grading_path.write_text(
                    json.dumps(grading, indent=2) + "\n",
                    encoding="utf-8",
                )

            output = workspace / "qmd-attestation-draft.json"
            completed = subprocess.run(
                [
                    "python",
                    str(ENTRY_POINT),
                    "draft-attestation",
                    str(ROOT),
                    str(workspace),
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

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            draft = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(draft["status"], "pending-human-review")
            self.assertEqual(draft["human_review"]["status"], "pending")
            self.assertEqual(
                draft["evidence"]["baseline"]["identity"],
                plan[0]["baseline"]["identity"],
            )
            self.assertEqual(
                set(draft["evidence"]["target_identities"]),
                {"claude", "codex"},
            )
            self.assertEqual(
                draft["targets"]["claude"]["required_cases"],
                {"passed": 1, "total": 1},
            )
            self.assertTrue((workspace / "qmd" / "review.html").is_file())

            grading_path = next(workspace.rglob("grading.json"))
            grading = json.loads(grading_path.read_text(encoding="utf-8"))
            grading["expectations"][0]["passed"] = False
            grading["expectations"][0]["evidence"] = "PENDING HUMAN REVIEW"
            grading_path.write_text(
                json.dumps(grading, indent=2) + "\n",
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [
                    "python",
                    str(ENTRY_POINT),
                    "draft-attestation",
                    str(ROOT),
                    str(workspace),
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
            self.assertEqual(rejected.returncode, 1)
            failure = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn(
                "every expectation must pass",
                failure["errors"][0],
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
                    "OPENAI_API_KEY": "",
                    "ANTHROPIC_API_KEY": "",
                },
                clear=False,
            ):
                with runners.isolated_target_environment(
                    "codex",
                    allow_ephemeral_auth_copy=True,
                ) as codex_env:
                    isolated_codex = Path(codex_env["CODEX_HOME"])
                    self.assertTrue((isolated_codex / "auth.json").is_file())
                    self.assertFalse((isolated_codex / "config.toml").exists())
                    self.assertFalse((isolated_codex / "skills").exists())
                self.assertFalse(isolated_codex.exists())

                with runners.isolated_target_environment(
                    "claude",
                    allow_ephemeral_auth_copy=True,
                ) as claude_env:
                    isolated_claude = Path(claude_env["CLAUDE_CONFIG_DIR"])
                    self.assertTrue(
                        (isolated_claude / ".credentials.json").is_file()
                    )
                    self.assertFalse(
                        (isolated_claude / "settings.json").exists()
                    )
                    self.assertFalse((isolated_claude / "skills").exists())
                self.assertFalse(isolated_claude.exists())

    def test_attestation_digest_matches_installer_and_rejects_stale_content(
        self,
    ) -> None:
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

            target = {
                "status": "pass",
                "discovery": True,
                "explicit_invocation": True,
                "isolation": True,
                "required_cases": {"passed": 1, "total": 1},
                "trigger_results": {"passed": 1, "total": 1},
                "summary": "Fixture target checks passed.",
            }
            data = {
                "$schema": "../attestation.schema.json",
                "schema_version": 1,
                "skill_name": "fixture-skill",
                "skill_digest": digest,
                "source_digest": None,
                "evaluation_level": "full",
                "evaluator_version": attestations.EVALUATOR_VERSION,
                "evaluated_at": "2026-07-24T00:00:00+00:00",
                "targets": {"claude": target, "codex": target},
                "evidence": {
                    "raw_run_root": ".scratch/skill-evals/fixture-skill/run",
                    "structural": {
                        "status": "pass",
                        "summary": "Structure passed.",
                    },
                    "baseline": {
                        "kind": "no-skill",
                        "identity": "fixture-no-skill",
                        "summary": "Fixture baseline compared.",
                    },
                    "assertions": {
                        "passed": 2,
                        "total": 2,
                        "summary": "Fixture assertions passed.",
                    },
                    "target_identities": {
                        "claude": "claude fixture",
                        "codex": "codex fixture",
                    },
                    "efficiency": {
                        "claude": {"duration_ms": 1, "total_tokens": 1},
                        "codex": {"duration_ms": 1, "total_tokens": None},
                    },
                    "static_review": {
                        "status": "pass",
                        "path": (
                            ".scratch/skill-evals/fixture-skill/run/review.html"
                        ),
                        "summary": "Fixture static review passed.",
                    },
                },
                "human_review": {
                    "status": "pass",
                    "reviewer": "fixture reviewer",
                    "reviewed_at": "2026-07-24T00:00:00+00:00",
                    "notes": "Fixture review passed.",
                },
                "unavailable_capabilities": [],
                "status": "pass",
            }
            attestation = Path(temp_dir) / "fixture-skill.json"
            attestation.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                attestations.validate_attestation(skill, attestation),
                [],
            )
            data["evaluation_level"] = "snapshot-smoke"
            data["source_digest"] = digest
            attestation.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
            snapshot_errors = attestations.validate_attestation(
                skill,
                attestation,
            )
            self.assertTrue(
                any("recorded source" in error for error in snapshot_errors),
                snapshot_errors,
            )
            self.assertEqual(
                attestations.validate_attestation(
                    skill,
                    attestation,
                    recorded_source_digest=digest,
                ),
                [],
            )
            data["evaluation_level"] = "full"
            data["source_digest"] = None
            attestation.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
            (skill / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: Changed.\n---\n",
                encoding="utf-8",
            )
            errors = attestations.validate_attestation(skill, attestation)
            self.assertTrue(
                any("skill_digest" in error for error in errors),
                errors,
            )

    def test_attestation_schema_requires_both_primary_targets_and_human_review(
        self,
    ) -> None:
        schema = json.loads(
            (
                ROOT / "attestations" / "attestation.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["targets"]["required"],
            ["claude", "codex"],
        )
        self.assertIn("human_review", schema["required"])

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
            "claude", "Use the test skill.", Path("C:/tmp/skill"), model=None
        )
        codex = runners.build_command(
            "codex", "Use the test skill.", Path("C:/tmp/skill"), model=None
        )

        self.assertEqual(claude[0:2], ["claude", "-p"])
        self.assertIn("--output-format", claude)
        self.assertEqual(codex[0:3], ["codex", "exec", "--ephemeral"])
        self.assertIn("--json", codex)
        trigger = runners.build_command(
            "codex",
            "Natural trigger prompt.",
            Path("C:/tmp/skill"),
            explicit=False,
        )
        self.assertIn("Natural trigger prompt.", trigger[-1])
        self.assertNotIn("$skill", trigger[-1])

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

    def test_aggregator_and_static_report_cover_fixture_workspace(self) -> None:
        aggregate = load_module(
            "skill_evaluator_aggregate", "aggregate_benchmark.py"
        )
        report = load_module("skill_evaluator_report", "generate_report.py")

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            for configuration, passed in (
                ("with_skill", True),
                ("baseline", False),
            ):
                for target in ("claude", "codex"):
                    run_dir = (
                        workspace
                        / "example"
                        / "case-one"
                        / configuration
                        / target
                    )
                    run_dir.mkdir(parents=True)
                    (run_dir / "result.json").write_text(
                        json.dumps(
                            {
                                "plan": {
                                    "skill_name": "example",
                                    "case_id": "case-one",
                                    "configuration": configuration,
                                    "target": target,
                                },
                                "target_identity": f"{target} fixture",
                                "target_identity_returncode": 0,
                                "result": {
                                    "returncode": 0,
                                    "timed_out": False,
                                    "duration_ms": 1000,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    (run_dir / "grading.json").write_text(
                        json.dumps(
                            {
                                "expectations": [
                                    {
                                        "text": "Produces the required file",
                                        "passed": passed,
                                        "evidence": "fixture",
                                    }
                                ]
                            }
                        ),
                        encoding="utf-8",
                    )

            benchmark = aggregate.aggregate_workspace(workspace, "example")
            output = workspace / "review.html"
            report.write_static_report(benchmark, output)

            self.assertEqual(benchmark["configurations"]["with_skill"]["pass_rate"], 1.0)
            self.assertEqual(benchmark["configurations"]["baseline"]["pass_rate"], 0.0)
            self.assertEqual(
                {(case["configuration"], case["target"]) for case in benchmark["cases"]},
                {
                    ("with_skill", "claude"),
                    ("with_skill", "codex"),
                    ("baseline", "claude"),
                    ("baseline", "codex"),
                },
            )
            html = output.read_text(encoding="utf-8")
            self.assertIn("example", html)
            self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()
