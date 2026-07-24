from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts" / "install.ps1"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


@unittest.skipUnless(POWERSHELL, "PowerShell is required")
class InstallerCommandTests(unittest.TestCase):
    def test_status_is_read_only_and_accepts_a_managed_skill_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(INSTALLER),
                    "-Action",
                    "Status",
                    "-Skills",
                    "ai-handoff",
                    "-StatePath",
                    str(state_path),
                ],
                cwd=ROOT,
                env={**os.environ, "NO_COLOR": "1"},
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(state_path.exists())
            self.assertIn("PREFLIGHT", result.stdout)
            self.assertIn("ai-handoff", result.stdout)

    def test_unknown_skill_is_rejected_without_writing_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(INSTALLER),
                    "-Action",
                    "Status",
                    "-Skills",
                    "not-a-managed-skill",
                    "-StatePath",
                    str(state_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(state_path.exists())
            self.assertIn("Unknown Managed Skill", result.stderr)

    def test_installer_exposes_copy_only_operations(self) -> None:
        content = INSTALLER.read_text(encoding="utf-8")

        self.assertNotIn('"Junction"', content)
        self.assertNotIn("ItemType Junction", content)
        self.assertIn('"Install", "Status", "Verify", "Uninstall"', content)


if __name__ == "__main__":
    unittest.main()
