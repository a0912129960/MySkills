from __future__ import annotations

import json
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
    def test_dependency_preflight_reports_independent_d_l_r_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_bin = Path(temp_dir) / "bin"
            fake_bin.mkdir()
            (fake_bin / "node.cmd").write_text(
                "@echo off\r\necho v22.0.0\r\n",
                encoding="ascii",
            )
            (fake_bin / "qmd.cmd").write_text(
                "@echo off\r\n"
                'if "%1"=="--version" (echo 2.5.3) else (echo qmd help)\r\n',
                encoding="ascii",
            )
            (fake_bin / "npm.cmd").write_text(
                "@echo off\r\n"
                'if "%1"=="view" (echo \"9.9.9\"& exit /b 0)\r\n'
                'if "%1"=="root" (echo C:\\unowned\\node_modules& exit /b 0)\r\n'
                "exit /b 1\r\n",
                encoding="ascii",
            )
            state_path = Path(temp_dir) / "state.json"
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            env = {
                **os.environ,
                "NO_COLOR": "1",
                "PATH": os.pathsep.join(
                    [
                        str(fake_bin),
                        str(Path(system_root) / "System32"),
                        system_root,
                    ]
                ),
            }
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
                    "Install",
                    "-Skills",
                    "qmd",
                    "-DryRun",
                    "-Yes",
                    "-StatePath",
                    str(state_path),
                ],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertIn(
                result.returncode,
                (0, 1),
                result.stderr + "\n" + result.stdout,
            )
            self.assertFalse(state_path.exists())
            self.assertIn(
                "qmd\tCOMPATIBLE\tD=2.5.3\tL=2.5.3\tR=9.9.9",
                result.stdout,
            )
            self.assertIn(
                "WOULD_OFFER_RELEASE_ADOPTION\tqmd\t2.5.3->9.9.9\tmanual-owner",
                result.stdout,
            )

            install_result = subprocess.run(
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
                    "Install",
                    "-Skills",
                    "qmd",
                    "-Yes",
                    "-StatePath",
                    str(state_path),
                ],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertIn(
                install_result.returncode,
                (0, 1),
                install_result.stderr + "\n" + install_result.stdout,
            )
            self.assertNotIn("DEPENDENCY_ADOPTED", install_result.stdout)
            manifest = json.loads(
                (ROOT / "manifests" / "dependencies.json").read_text(
                    encoding="utf-8"
                )
            )
            qmd_manifest = next(
                item for item in manifest["dependencies"] if item["id"] == "qmd"
            )
            self.assertEqual(qmd_manifest["install_version"], "2.5.3")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            dependencies = {item["id"]: item for item in state["dependencies"]}
            self.assertEqual(dependencies["qmd"]["version"], "2.5.3")
            self.assertEqual(dependencies["qmd"]["ownership"], "preexisting")
            self.assertEqual(
                dependencies["qmd"]["verification_status"],
                "COMPATIBLE",
            )

    def test_install_dry_run_observes_all_targets_before_dependency_offer(
        self,
    ) -> None:
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
                    "Install",
                    "-Skills",
                    "skill-evaluator",
                    "-DryRun",
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
            self.assertEqual(result.stdout.count("TARGET\t"), 3)
            target_index = result.stdout.rindex("TARGET\t")
            dependency_index = result.stdout.find("WOULD_OFFER_DEPENDENCY\t")
            if dependency_index >= 0:
                self.assertLess(target_index, dependency_index)
            self.assertIn("WOULD_INSTALL_TOOL\tskill-evaluator", result.stdout)

    def test_install_dry_run_reports_broken_optional_cli_without_aborting(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_bin = Path(temp_dir) / "bin"
            fake_bin.mkdir()
            (fake_bin / "node.cmd").write_text(
                "@echo off\r\n"
                'if "%1"=="--version" (echo v22.0.0) else (echo x64)\r\n',
                encoding="ascii",
            )
            (fake_bin / "mmdc.cmd").write_text(
                "@echo off\r\n"
                "echo Error: missing mermaid module 1>&2\r\n"
                "exit /b 1\r\n",
                encoding="ascii",
            )
            state_path = Path(temp_dir) / "state.json"
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            env = {
                **os.environ,
                "NO_COLOR": "1",
                "PATH": os.pathsep.join(
                    [
                        str(fake_bin),
                        str(Path(system_root) / "System32"),
                        system_root,
                    ]
                ),
            }

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
                    "Install",
                    "-Skills",
                    "spec-package-generator",
                    "-DryRun",
                    "-BackupAndReplace",
                    "-StatePath",
                    str(state_path),
                ],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(
                result.returncode,
                0,
                result.stderr + "\n" + result.stdout,
            )
            self.assertFalse(state_path.exists())
            self.assertIn("mermaid-cli\tBROKEN", result.stdout)
            self.assertIn("SUMMARY", result.stdout)

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
        self.assertNotIn('$dependencyBlocks["qmd"] = @(', content)
        self.assertIn('"MCP_STATUS`tqmd`tCLI_ONLY"', content)
        self.assertIn("Set-PythonRequirementLock", content)
        self.assertIn("installed_by_myskills", content)
        self.assertIn("PreviousRecord", content)


if __name__ == "__main__":
    unittest.main()
