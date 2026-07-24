from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


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

    def test_aggregator_and_static_report_cover_fixture_workspace(self) -> None:
        aggregate = load_module(
            "skill_evaluator_aggregate", "aggregate_benchmark.py"
        )
        report = load_module("skill_evaluator_report", "generate_report.py")

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            for configuration, passed, tokens in (
                ("with_skill", True, 100),
                ("baseline", False, 80),
            ):
                run_dir = workspace / "case-one" / configuration
                run_dir.mkdir(parents=True)
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
                (run_dir / "timing.json").write_text(
                    json.dumps(
                        {
                            "total_tokens": tokens,
                            "duration_ms": 1000,
                            "total_duration_seconds": 1.0,
                        }
                    ),
                    encoding="utf-8",
                )

            benchmark = aggregate.aggregate_workspace(workspace, "example")
            output = workspace / "review.html"
            report.write_static_report(benchmark, output)

            self.assertEqual(benchmark["configurations"]["with_skill"]["pass_rate"], 1.0)
            self.assertEqual(benchmark["configurations"]["baseline"]["pass_rate"], 0.0)
            html = output.read_text(encoding="utf-8")
            self.assertIn("example", html)
            self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()
