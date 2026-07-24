from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "new-skill.ps1"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


@unittest.skipUnless(POWERSHELL, "PowerShell is required")
class NewSkillCommandTests(unittest.TestCase):
    def run_scaffolder(
        self, root: Path, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                POWERSHELL,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPT),
                "-Root",
                str(root),
                *arguments,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_explicit_scaffold_has_matching_platform_policy_and_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.run_scaffolder(
                root,
                "-Name",
                "example-skill",
                "-Category",
                "engineering",
                "-Description",
                "Handle an example workflow.",
                "-Invocation",
                "explicit",
            )

            skill = root / "skills" / "engineering" / "example-skill"
            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
            metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("disable-model-invocation: true", skill_text)
            self.assertIn("allow_implicit_invocation: false", metadata)
            self.assertIn("$example-skill", metadata)
            self.assertIn("skill-evaluator", result.stdout)
            self.assertIn("inventory/skills.json", result.stdout)

    def test_scaffolder_refuses_to_overwrite_an_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "skills" / "wiki" / "existing-skill"
            target.mkdir(parents=True)
            marker = target / "keep.txt"
            marker.write_text("keep", encoding="utf-8")

            result = self.run_scaffolder(
                root,
                "-Name",
                "existing-skill",
                "-Category",
                "wiki",
                "-Description",
                "Do not overwrite this.",
                "-Invocation",
                "implicit",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
