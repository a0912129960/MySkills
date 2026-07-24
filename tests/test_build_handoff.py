from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "productivity" / "ai-handoff" / "scripts" / "build_handoff.py"


class BuildHandoffTests(unittest.TestCase):
    def test_ascii_prompt_requests_traditional_chinese_response(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--objective",
                "Audit the repository. Do not edit files.",
                "--target",
                r"C:\project\example",
                "--context-file",
                r"C:\temp\context.md",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        result.stdout.encode("ascii")
        self.assertIn("Answer in Traditional Chinese (zh-TW).", result.stdout)
        self.assertIn(r"Read C:\temp\context.md.", result.stdout)

    def test_ascii_prompt_rejects_non_ascii_payload(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--objective",
                "請檢查專案",
                "--target",
                r"C:\project\example",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("ASCII transport rejected non-ASCII text", result.stderr)

    def test_output_file_is_utf8_with_lf_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "handoff.txt"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--objective",
                    "Prepare a plan.",
                    "--target",
                    "another-session",
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = output.read_bytes()
            payload.decode("utf-8")
            self.assertNotIn(b"\r\n", payload)


if __name__ == "__main__":
    unittest.main()
