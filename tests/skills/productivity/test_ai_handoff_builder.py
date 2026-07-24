from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT
    / "skills"
    / "productivity"
    / "ai-handoff"
    / "scripts"
    / "build-handoff.ps1"
)


def run_builder(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            *arguments,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class AiHandoffBuilderTests(unittest.TestCase):
    def test_agent_payload_is_ascii_and_has_no_forced_response_language(self) -> None:
        result = run_builder(
            "-Objective",
            "Review the current implementation.",
            "-Target",
            r"C:\project\example",
            "-Deliverable",
            "Return findings with file evidence.",
            "-Audience",
            "agent",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        result.stdout.encode("ascii")
        self.assertIn("AUDIENCE: agent", result.stdout)
        self.assertNotIn("Traditional Chinese", result.stdout)

    def test_human_final_audience_adds_the_zh_tw_instruction(self) -> None:
        result = run_builder(
            "-Objective",
            "Audit the repository.",
            "-Target",
            r"C:\project\example",
            "-Deliverable",
            "Return a concise report.",
            "-Audience",
            "agent",
            "-FinalAudience",
            "human",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FINAL_AUDIENCE: human", result.stdout)
        self.assertIn("Answer in Traditional Chinese (zh-TW).", result.stdout)

    def test_authoritative_context_and_constraints_are_preserved(self) -> None:
        result = run_builder(
            "-Objective",
            "Review the implementation.",
            "-Target",
            r"C:\project\example",
            "-ContextFile",
            r"C:\project\example\AGENTS.md",
            "-Constraint",
            "Do not modify files.",
            "-Deliverable",
            "Return findings with evidence.",
            "-Audience",
            "agent",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AUTHORITATIVE_CONTEXT:", result.stdout)
        self.assertIn(r"- C:\project\example\AGENTS.md", result.stdout)
        self.assertIn("CONSTRAINTS:", result.stdout)
        self.assertIn("- Do not modify files.", result.stdout)

    def test_non_ascii_transport_input_is_rejected(self) -> None:
        result = run_builder(
            "-Objective",
            "審查此專案",
            "-Target",
            r"C:\project\example",
            "-Deliverable",
            "Return findings.",
            "-Audience",
            "agent",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ASCII", result.stderr)

    def test_payload_over_hard_ceiling_is_rejected_without_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "handoff.txt"
            result = run_builder(
                "-Objective",
                "x" * 10_000,
                "-Target",
                r"C:\project\example",
                "-Deliverable",
                "Return findings.",
                "-Audience",
                "agent",
                "-Output",
                str(output_path),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("10,000", result.stderr)
            self.assertFalse(output_path.exists())

    def test_extended_budget_requires_an_explicit_override(self) -> None:
        arguments = (
            "-Objective",
            "x" * 6_000,
            "-Target",
            r"C:\project\example",
            "-Deliverable",
            "Return findings.",
            "-Audience",
            "agent",
        )
        rejected = run_builder(*arguments)
        accepted = run_builder(*arguments, "-AllowExtendedBudget")

        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("6,000", rejected.stderr)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertLessEqual(len(accepted.stdout.rstrip("\r\n")), 10_000)


if __name__ == "__main__":
    unittest.main()
