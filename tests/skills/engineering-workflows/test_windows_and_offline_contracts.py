from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[3]
ENGINEERING = ROOT / "skills" / "engineering"
PRODUCTIVITY = ROOT / "skills" / "productivity"


class WindowsAndOfflineContractTests(unittest.TestCase):
    def test_managed_engineering_and_productivity_have_no_bundled_shell_scripts(
        self,
    ) -> None:
        shell_scripts = [
            path
            for bucket in (ENGINEERING, PRODUCTIVITY)
            for path in bucket.rglob("*.sh")
            if path.is_file()
        ]
        self.assertEqual(shell_scripts, [])

    def test_diagnosis_human_loop_is_a_valid_powershell_script(self) -> None:
        script = (
            ENGINEERING
            / "diagnosing-bugs"
            / "scripts"
            / "hitl-loop.template.ps1"
        )
        self.assertTrue(script.is_file())

        command = (
            "$errors = $null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            f"'{script}', [ref]$null, [ref]$errors) | Out-Null; "
            "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_architecture_report_guidance_has_no_network_dependency(self) -> None:
        guidance = (
            ENGINEERING / "improve-codebase-architecture" / "HTML-REPORT.md"
        ).read_text(encoding="utf-8")
        lowered = guidance.lower()

        self.assertNotIn("cdn", lowered)
        self.assertNotIn("https://", lowered)
        self.assertNotIn("http://", lowered)
        self.assertIn("embedded css", lowered)
        self.assertIn("inline svg", lowered)

    def test_spec_generator_uses_official_mermaid_cli_with_mmd_fallback(
        self,
    ) -> None:
        reference = (
            ENGINEERING
            / "spec-package-generator"
            / "references"
            / "mermaid-rendering.md"
        ).read_text(encoding="utf-8")

        self.assertIn("@mermaid-js/mermaid-cli", reference)
        self.assertIn("`mmdc`", reference)
        self.assertIn(".mmd", reference)
        self.assertNotIn("npm install", reference)
        self.assertNotIn("mermaid-diagram-renderer", reference)
        self.assertNotIn("beautiful-mermaid", reference)

    def test_ai_handoff_core_has_no_python_runtime(self) -> None:
        scripts = PRODUCTIVITY / "ai-handoff" / "scripts"
        self.assertTrue((scripts / "build-handoff.ps1").is_file())
        self.assertEqual(list(scripts.glob("*.py")), [])


if __name__ == "__main__":
    unittest.main()
