import contextlib
import importlib
import io
import json
import os
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = REPO_ROOT / "tools" / "obsidian-wiki"
sys.path.insert(0, str(TOOL_ROOT))


class RepositoryOwnedCliContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = importlib.import_module("obsidian_wiki.cli")

    def run_cli(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = self.cli.main(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_version_identifies_myskills_content_snapshot(self):
        code, stdout, _ = self.run_cli("--version")
        self.assertEqual(0, code)
        self.assertRegex(
            stdout.strip(),
            r"^obsidian-wiki myskills-[0-9A-Za-z][0-9A-Za-z._-]*\+[0-9a-f]{12}$",
        )

    def test_retired_install_and_policy_commands_are_not_exposed(self):
        code, stdout, _ = self.run_cli("--help")
        self.assertEqual(0, code)
        self.assertNotIn("install-skills", stdout)
        self.assertNotIn("update-skills", stdout)
        self.assertNotIn("rules", stdout)
        self.assertIn("setup", stdout)
        self.assertIn("doctor", stdout)
        self.assertIn("query", stdout)

    def test_setup_initializes_vault_without_installing_agent_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vault = root / "vault"
            config_home = root / "profile" / ".obsidian-wiki"
            old = os.environ.get("OBSIDIAN_WIKI_CONFIG_HOME")
            os.environ["OBSIDIAN_WIKI_CONFIG_HOME"] = str(config_home)
            try:
                code, stdout, stderr = self.run_cli(
                    "setup", "--vault", str(vault), "--pretty"
                )
            finally:
                if old is None:
                    os.environ.pop("OBSIDIAN_WIKI_CONFIG_HOME", None)
                else:
                    os.environ["OBSIDIAN_WIKI_CONFIG_HOME"] = old
            self.assertEqual("", stderr)
            self.assertEqual(0, code)
            result = json.loads(stdout)
            self.assertEqual("created", result["status"])
            self.assertTrue((config_home / "config").is_file())
            self.assertTrue((vault / "index.md").is_file())
            self.assertFalse((root / "profile" / ".agents" / "skills").exists())
            self.assertFalse((root / "profile" / ".claude" / "skills").exists())

    def test_policy_modules_are_not_part_of_repository_owned_tool(self):
        package = TOOL_ROOT / "obsidian_wiki"
        self.assertFalse((package / "policy.py").exists())
        self.assertFalse((package / "project_rules.py").exists())

    def test_tool_has_zero_dependency_offline_install_contract(self):
        metadata = tomllib.loads(
            (TOOL_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        project = metadata["project"]
        self.assertEqual("obsidian-wiki-myskills", project["name"])
        self.assertEqual([], project["dependencies"])
        self.assertEqual(">=3.10", project["requires-python"])
        self.assertEqual(
            "obsidian_wiki.cli:main",
            project["scripts"]["obsidian-wiki"],
        )


if __name__ == "__main__":
    unittest.main()
