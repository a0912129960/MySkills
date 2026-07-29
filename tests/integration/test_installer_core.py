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

    def test_target_plan_line_discloses_reparse_type_and_destination(self) -> None:
        result = self.run_powershell(
            "Format-SkillTargetPlanLine "
            "-PlatformId 'claude-code' "
            "-SkillName 'example' "
            "-Status 'UNOWNED' "
            "-TargetPath 'C:\\skills\\example' "
            "-IsReparsePoint $true "
            "-LinkType 'Junction' "
            "-LinkTarget 'C:\\source\\example'"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            (
                "TARGET\tclaude-code\texample\tUNOWNED\t"
                "C:\\skills\\example\tLINK\tJunction\tC:\\source\\example"
            ),
        )

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

    def test_reparse_replacement_preserves_link_target_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            linked = root / "linked-source"
            target = root / "destination" / "example"
            source.mkdir()
            linked.mkdir()
            target.parent.mkdir()
            (source / "SKILL.md").write_text("managed\n", encoding="utf-8")
            (linked / "SKILL.md").write_text("preexisting\n", encoding="utf-8")
            (linked / "keep.txt").write_text("keep\n", encoding="utf-8")

            result = self.run_powershell(
                "New-Item -ItemType Junction "
                "-Path $env:MYSKILLS_TEST_TARGET "
                "-Target $env:MYSKILLS_TEST_LINKED | Out-Null; "
                "$hash = Set-ReparsePointDirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET; "
                "$item = Get-Item -LiteralPath $env:MYSKILLS_TEST_TARGET -Force; "
                "$isReparse = (($item.Attributes -band "
                "[IO.FileAttributes]::ReparsePoint) -ne 0); "
                'Write-Output "HASH=$hash"; '
                'Write-Output "REPARSE=$isReparse"',
                environment={
                    "MYSKILLS_TEST_LINKED": str(linked),
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("REPARSE=False", result.stdout)
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "managed\n",
            )
            self.assertEqual(
                (linked / "SKILL.md").read_text(encoding="utf-8"),
                "preexisting\n",
            )
            self.assertEqual(
                (linked / "keep.txt").read_text(encoding="utf-8"),
                "keep\n",
            )
            self.assertEqual(list(target.parent.glob(".myskills-*")), [])

    def test_reparse_replacement_restores_link_after_verification_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            linked = root / "linked-source"
            target = root / "destination" / "example"
            source.mkdir()
            linked.mkdir()
            target.parent.mkdir()
            (source / "SKILL.md").write_text("managed\n", encoding="utf-8")
            (linked / "SKILL.md").write_text("preexisting\n", encoding="utf-8")

            result = self.run_powershell(
                "New-Item -ItemType Junction "
                "-Path $env:MYSKILLS_TEST_TARGET "
                "-Target $env:MYSKILLS_TEST_LINKED | Out-Null; "
                "Set-ReparsePointDirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET "
                "-Verify { param($Path) return $false }",
                environment={
                    "MYSKILLS_TEST_LINKED": str(linked),
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )
            observation = self.run_powershell(
                "$item = Get-Item "
                "-LiteralPath $env:MYSKILLS_TEST_TARGET -Force; "
                "$isReparse = (($item.Attributes -band "
                "[IO.FileAttributes]::ReparsePoint) -ne 0); "
                "$linkTarget = @($item.Target) -join ';'; "
                'Write-Output "REPARSE=$isReparse"; '
                'Write-Output "LINK_TYPE=$($item.LinkType)"; '
                'Write-Output "LINK_TARGET=$linkTarget"',
                environment={"MYSKILLS_TEST_TARGET": str(target)},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Post-copy verification failed", result.stderr)
            self.assertEqual(observation.returncode, 0, observation.stderr)
            self.assertIn("REPARSE=True", observation.stdout)
            self.assertIn("LINK_TYPE=Junction", observation.stdout)
            self.assertIn(f"LINK_TARGET={linked}", observation.stdout)
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "preexisting\n",
            )
            self.assertEqual(
                (linked / "SKILL.md").read_text(encoding="utf-8"),
                "preexisting\n",
            )
            self.assertEqual(list(target.parent.glob(".myskills-*")), [])

    def test_reparse_replacement_restores_exact_link_when_verifier_throws(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            linked = root / "linked-source"
            target = root / "destination" / "example"
            source.mkdir()
            linked.mkdir()
            target.parent.mkdir()
            (source / "SKILL.md").write_text("managed\n", encoding="utf-8")
            (linked / "SKILL.md").write_text("preexisting\n", encoding="utf-8")

            result = self.run_powershell(
                "New-Item -ItemType Junction "
                "-Path $env:MYSKILLS_TEST_TARGET "
                "-Target $env:MYSKILLS_TEST_LINKED | Out-Null; "
                "Set-ReparsePointDirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET "
                "-Verify { param($Path) throw 'discovery exploded' }",
                environment={
                    "MYSKILLS_TEST_LINKED": str(linked),
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )
            observation = self.run_powershell(
                "$item = Get-Item "
                "-LiteralPath $env:MYSKILLS_TEST_TARGET -Force; "
                "$linkTarget = @($item.Target) -join ';'; "
                'Write-Output "LINK_TYPE=$($item.LinkType)"; '
                'Write-Output "LINK_TARGET=$linkTarget"',
                environment={"MYSKILLS_TEST_TARGET": str(target)},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("discovery exploded", result.stderr)
            self.assertEqual(observation.returncode, 0, observation.stderr)
            self.assertIn("LINK_TYPE=Junction", observation.stdout)
            self.assertIn(f"LINK_TARGET={linked}", observation.stdout)
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "preexisting\n",
            )
            self.assertEqual(list(target.parent.glob(".myskills-*")), [])

    def test_symbolic_link_replacement_preserves_link_target_contents(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            linked = root / "linked-source"
            target = root / "destination" / "example"
            source.mkdir()
            linked.mkdir()
            target.parent.mkdir()
            (source / "SKILL.md").write_text("managed\n", encoding="utf-8")
            (linked / "SKILL.md").write_text("preexisting\n", encoding="utf-8")

            result = self.run_powershell(
                "New-Item -ItemType SymbolicLink "
                "-Path $env:MYSKILLS_TEST_TARGET "
                "-Target $env:MYSKILLS_TEST_LINKED | Out-Null; "
                "Set-ReparsePointDirectorySnapshot "
                "-Source $env:MYSKILLS_TEST_SOURCE "
                "-Target $env:MYSKILLS_TEST_TARGET",
                environment={
                    "MYSKILLS_TEST_LINKED": str(linked),
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            if (
                result.returncode != 0
                and "privilege required" in result.stderr.lower()
            ):
                self.skipTest(
                    "creating a symbolic link requires elevated Windows privileges"
                )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "managed\n",
            )
            self.assertEqual(
                (linked / "SKILL.md").read_text(encoding="utf-8"),
                "preexisting\n",
            )
            self.assertEqual(list(target.parent.glob(".myskills-*")), [])

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

    def test_thrown_post_copy_verification_removes_a_new_target(self) -> None:
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
                "-Verify { param($Path) throw 'discovery probe crashed' }",
                environment={
                    "MYSKILLS_TEST_SOURCE": str(source),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("discovery probe crashed", result.stderr)
            self.assertFalse(target.exists())

    def test_codex_discovery_lists_an_explicit_skill_by_installed_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "skills" / "ai-handoff"
            fake_bin = root / "bin"
            target.mkdir(parents=True)
            fake_bin.mkdir()
            skill_file = target / "SKILL.md"
            skill_file.write_text("---\nname: ai-handoff\n---\n", encoding="utf-8")
            fake_script = fake_bin / "fake-codex-server.ps1"
            fake_script.write_text(
                "$init = [Console]::In.ReadLine() | ConvertFrom-Json\n"
                "$notification = @{\n"
                "  method = 'remoteControl/status/changed'\n"
                "  params = @{ status = 'disabled' }\n"
                "} | ConvertTo-Json -Compress -Depth 8\n"
                "[Console]::Out.WriteLine($notification)\n"
                "$initResponse = @{\n"
                "  id = $init.id\n"
                "  result = @{ codexHome = $env:MYSKILLS_TEST_CODEX_HOME }\n"
                "} | ConvertTo-Json -Compress -Depth 8\n"
                "[Console]::Out.WriteLine($initResponse)\n"
                "[Console]::Out.Flush()\n"
                "$null = [Console]::In.ReadLine()\n"
                "$request = [Console]::In.ReadLine() | ConvertFrom-Json\n"
                "$response = @{\n"
                "  id = $request.id\n"
                "  result = @{ data = @(@{\n"
                "    cwd = $env:MYSKILLS_TEST_CWD\n"
                "    errors = @()\n"
                "    skills = @(@{\n"
                "      name = 'ai-handoff'\n"
                "      path = $env:MYSKILLS_TEST_SKILL_FILE\n"
                "      description = 'Explicit handoff'\n"
                "      enabled = $true\n"
                "      scope = 'user'\n"
                "    })\n"
                "  }) }\n"
                "} | ConvertTo-Json -Compress -Depth 12\n"
                "[Console]::Out.WriteLine($response)\n"
                "[Console]::Out.Flush()\n",
                encoding="utf-8",
            )
            fake_ps1 = fake_bin / "codex.ps1"
            fake_ps1.write_text("exit 99\n", encoding="utf-8")
            fake_cmd = fake_bin / "codex.cmd"
            fake_cmd.write_text(
                "@echo off\r\n"
                "powershell -NoLogo -NoProfile -NonInteractive "
                '-File "%~dp0fake-codex-server.ps1"\r\n',
                encoding="ascii",
            )

            result = self.run_powershell(
                "if (-not (Test-CodexSkillDiscovery "
                "-Executable $env:MYSKILLS_TEST_CODEX "
                "-SkillName 'ai-handoff' "
                "-TargetPath $env:MYSKILLS_TEST_TARGET "
                "-WorkingDirectory $env:MYSKILLS_TEST_CWD)) { "
                "throw 'Codex did not discover the explicit Skill' }",
                environment={
                    "MYSKILLS_TEST_CODEX": str(fake_ps1),
                    "MYSKILLS_TEST_CODEX_HOME": str(root / "codex-home"),
                    "MYSKILLS_TEST_CWD": str(ROOT),
                    "MYSKILLS_TEST_SKILL_FILE": str(skill_file),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_claude_discovery_reads_init_from_a_local_only_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "skills" / "ai-handoff"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text(
                "---\nname: ai-handoff\n---\n",
                encoding="utf-8",
            )
            fake_script = root / "fake-claude.ps1"
            fake_script.write_text(
                "$arguments = $args -join ' '\n"
                "[IO.File]::WriteAllText(\n"
                "  $env:MYSKILLS_TEST_CLAUDE_ARGS,\n"
                "  $arguments\n"
                ")\n"
                "$safeEndpoint =\n"
                "  $env:ANTHROPIC_BASE_URL.StartsWith('http://127.0.0.1:')\n"
                "$safeKey =\n"
                "  $env:ANTHROPIC_API_KEY -eq 'myskills-local-discovery-probe'\n"
                "$skills = if ($safeEndpoint -and $safeKey) {\n"
                "  @('ai-handoff')\n"
                "} else {\n"
                "  @()\n"
                "}\n"
                "@{\n"
                "  type = 'system'\n"
                "  subtype = 'init'\n"
                "  skills = $skills\n"
                "  slash_commands = @('same-name-command')\n"
                "} | ConvertTo-Json -Compress -Depth 6\n",
                encoding="utf-8",
            )
            fake_claude = root / "claude.cmd"
            argument_log = root / "claude-arguments.txt"
            fake_claude.write_text(
                "@echo off\r\n"
                "powershell -NoLogo -NoProfile -NonInteractive "
                '-File "%~dp0fake-claude.ps1" %*\r\n',
                encoding="ascii",
            )

            result = self.run_powershell(
                "if (-not (Test-ClaudeSkillDiscovery "
                "-Executable $env:MYSKILLS_TEST_CLAUDE "
                "-SkillName 'ai-handoff' "
                "-TargetPath $env:MYSKILLS_TEST_TARGET)) { "
                "throw 'Claude did not receive the discovery prompt' }",
                environment={
                    "MYSKILLS_TEST_CLAUDE_ARGS": str(argument_log),
                    "MYSKILLS_TEST_CLAUDE": str(fake_claude),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            arguments = argument_log.read_text(encoding="utf-8")
            self.assertIn("/ai-handoff", arguments, arguments)
            self.assertLess(arguments.index("--print"), arguments.index("/ai-handoff"))
            self.assertIn("--output-format stream-json", arguments)

    def test_claude_discovery_rejects_a_same_name_slash_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "skills" / "ai-handoff"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text(
                "---\nname: ai-handoff\n---\n",
                encoding="utf-8",
            )
            fake_script = root / "fake-claude.ps1"
            fake_script.write_text(
                "@{\n"
                "  type = 'system'\n"
                "  subtype = 'init'\n"
                "  skills = @()\n"
                "  slash_commands = @('ai-handoff')\n"
                "} | ConvertTo-Json -Compress -Depth 6\n",
                encoding="utf-8",
            )
            fake_claude = root / "claude.cmd"
            fake_claude.write_text(
                "@echo off\r\n"
                "powershell -NoLogo -NoProfile -NonInteractive "
                '-File "%~dp0fake-claude.ps1"\r\n',
                encoding="ascii",
            )

            result = self.run_powershell(
                "if (Test-ClaudeSkillDiscovery "
                "-Executable $env:MYSKILLS_TEST_CLAUDE "
                "-SkillName 'ai-handoff' "
                "-TargetPath $env:MYSKILLS_TEST_TARGET) { "
                "throw 'Claude slash command was accepted as Skill evidence' }",
                environment={
                    "MYSKILLS_TEST_CLAUDE": str(fake_claude),
                    "MYSKILLS_TEST_TARGET": str(target),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)

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
