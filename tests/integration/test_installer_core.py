from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "scripts" / "installer_core.psm1"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


@unittest.skipUnless(POWERSHELL, "PowerShell is required")
class InstallerCoreTests(unittest.TestCase):
    def run_powershell(
        self, command: str, *, environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["MYSKILLS_TEST_CORE"] = str(CORE)
        if environment:
            env.update(environment)
        return subprocess.run(
            [
                POWERSHELL,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "Import-Module -Force $env:MYSKILLS_TEST_CORE; "
                    "$ErrorActionPreference = 'Stop'; "
                    + command
                ),
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_directory_digest_ignores_timestamps_and_creation_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            (first / "b.txt").write_text("bravo\n", encoding="utf-8")
            (first / "a.txt").write_text("alpha\n", encoding="utf-8")
            (second / "a.txt").write_text("alpha\n", encoding="utf-8")
            (second / "b.txt").write_text("bravo\n", encoding="utf-8")
            os.utime(first / "a.txt", (1_000_000_000, 1_000_000_000))

            result = self.run_powershell(
                "Write-Output ((Get-DirectoryDigest -Path "
                "$env:MYSKILLS_TEST_FIRST), (Get-DirectoryDigest -Path "
                "$env:MYSKILLS_TEST_SECOND) -join \"`n\")",
                environment={
                    "MYSKILLS_TEST_FIRST": str(first),
                    "MYSKILLS_TEST_SECOND": str(second),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            hashes = result.stdout.strip().splitlines()
            self.assertEqual(len(hashes), 2)
            self.assertEqual(hashes[0], hashes[1])
            self.assertRegex(hashes[0], r"^[0-9a-f]{64}$")

    def test_deployment_state_matches_the_confirmed_hash_matrix(self) -> None:
        cases = (
            ("false", "source", "$null", "$null", "MISSING"),
            ("true", "source", "$null", "actual", "UNOWNED"),
            ("true", "same", "same", "same", "CURRENT"),
            ("true", "new", "old", "old", "UPDATE_AVAILABLE"),
            ("true", "source", "recorded", "changed", "DRIFTED"),
        )
        for exists, source, recorded, actual, expected in cases:
            with self.subTest(expected=expected):
                result = self.run_powershell(
                    "Get-SkillDeploymentState "
                    f"-TargetExists:${exists} "
                    f"-SourceHash '{source}' "
                    f"-RecordedHash {recorded} "
                    f"-ActualHash {actual}"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)

    def test_snapshot_copy_is_exact_and_refuses_an_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "destination" / "example"
            (source / "nested").mkdir(parents=True)
            (source / "SKILL.md").write_text("skill\n", encoding="utf-8")
            (source / "nested" / "data.txt").write_text("data\n", encoding="utf-8")

            environment = {
                "MYSKILLS_TEST_SOURCE": str(source),
                "MYSKILLS_TEST_TARGET": str(target),
            }
            first = self.run_powershell(
                "Install-DirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET",
                environment=environment,
            )
            second = self.run_powershell(
                "Install-DirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET",
                environment=environment,
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertEqual(
                (target / "nested" / "data.txt").read_text(encoding="utf-8"),
                "data\n",
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already exists", second.stderr)

    def test_snapshot_update_replaces_a_managed_target_without_leaving_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "destination" / "example"
            source.mkdir()
            target.mkdir(parents=True)
            (source / "SKILL.md").write_text("new\n", encoding="utf-8")
            (target / "SKILL.md").write_text("old\n", encoding="utf-8")

            result = self.run_powershell(
                "Update-DirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET",
                environment={
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "new\n",
            )
            self.assertEqual(
                list((root / "destination").glob(".myskills-*")),
                [],
            )

    def test_backup_snapshot_verifies_an_exact_recoverable_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "installed"
            backup = root / "backups" / "example"
            source.mkdir()
            (source / "SKILL.md").write_text("local edits\n", encoding="utf-8")

            result = self.run_powershell(
                "Backup-DirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Backup $env:MYSKILLS_TEST_BACKUP",
                environment={
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_BACKUP": str(backup),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (backup / "SKILL.md").read_text(encoding="utf-8"),
                "local edits\n",
            )

    def test_failed_post_copy_verification_removes_a_new_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "destination" / "example"
            source.mkdir()
            (source / "SKILL.md").write_text("new\n", encoding="utf-8")

            result = self.run_powershell(
                "Install-DirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET "
                "-Verify { param($Path) return $false }",
                environment={
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Post-copy verification failed", result.stderr)
            self.assertFalse(target.exists())

    def test_failed_update_verification_restores_the_previous_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "destination" / "example"
            source.mkdir()
            target.mkdir(parents=True)
            (source / "SKILL.md").write_text("new\n", encoding="utf-8")
            (target / "SKILL.md").write_text("old\n", encoding="utf-8")

            result = self.run_powershell(
                "Update-DirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET "
                "-Verify { param($Path) return $false }",
                environment={
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Post-copy verification failed", result.stderr)
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "old\n",
            )


if __name__ == "__main__":
    unittest.main()
