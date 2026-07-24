import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
INVENTORY_PATH = REPO_ROOT / "inventory" / "skills.json"
WIKI_ROOT = REPO_ROOT / "skills" / "wiki"


class ManagedWikiSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.managed = {
            skill["managed_name"]: skill
            for skill in cls.inventory["skills"]
            if skill["state"] == "managed" and skill["category"] == "wiki"
        }

    def test_inventory_managed_wiki_entries_are_the_installed_suite(self):
        expected = {
            "cross-linker",
            "graph-colorize",
            "llm-wiki",
            "memory-bridge",
            "project-rules-init",
            "tag-taxonomy",
            "wiki-capture",
            "wiki-context-pack",
            "wiki-dashboard",
            "wiki-dedup",
            "wiki-history-ingest",
            "wiki-ingest",
            "wiki-lint",
            "wiki-query",
            "wiki-rebuild",
            "wiki-research",
            "wiki-setup",
            "wiki-status",
            "wiki-synthesize",
            "wiki-update",
        }
        self.assertEqual(expected, set(self.managed))
        installed = {path.name for path in WIKI_ROOT.iterdir() if path.is_dir()}
        self.assertEqual(expected, installed)

    def test_every_wiki_skill_has_matching_claude_and_codex_invocation_policy(self):
        for name, entry in self.managed.items():
            with self.subTest(skill=name):
                skill_text = (WIKI_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
                metadata = (WIKI_ROOT / name / "agents" / "openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertRegex(skill_text, rf"(?m)^name:\s*{re.escape(name)}\s*$")
                if entry["invocation"] == "explicit":
                    self.assertRegex(
                        skill_text,
                        r"(?m)^disable-model-invocation:\s*true\s*$",
                    )
                    self.assertRegex(
                        metadata,
                        r"(?m)^\s*allow_implicit_invocation:\s*false\s*$",
                    )
                else:
                    self.assertNotRegex(
                        skill_text,
                        r"(?m)^disable-model-invocation:\s*true\s*$",
                    )
                    self.assertRegex(
                        metadata,
                        r"(?m)^\s*allow_implicit_invocation:\s*true\s*$",
                    )

    def test_runtime_content_uses_myskills_contract_not_retired_workflows(self):
        forbidden = (
            "OBSIDIAN_WIKI_REPO",
            "WIKI_STAGED_WRITES",
            "/wiki-stage-commit",
            "wiki-switch",
            "impl-validator",
            "defuddle",
            "scripts/manifest.py",
            "bare `obsidian-wiki`",
        )
        for path in WIKI_ROOT.rglob("*"):
            if (
                not path.is_file()
                or path.suffix.lower()
                not in {".json", ".md", ".ps1", ".py", ".txt", ".yaml", ".yml"}
            ):
                continue
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path.relative_to(REPO_ROOT), token=token):
                    self.assertNotIn(token, text)

    def test_owned_helpers_and_history_adapters_are_packaged(self):
        required = (
            WIKI_ROOT / "llm-wiki" / "scripts" / "manifest.py",
            WIKI_ROOT
            / "wiki-history-ingest"
            / "scripts"
            / "claude"
            / "extract-jsonl.py",
            WIKI_ROOT
            / "wiki-history-ingest"
            / "scripts"
            / "antigravity"
            / "extract-history.py",
            WIKI_ROOT
            / "wiki-history-ingest"
            / "references"
            / "claude-data-format.md",
            WIKI_ROOT
            / "wiki-history-ingest"
            / "references"
            / "codex-data-format.md",
            WIKI_ROOT
            / "wiki-history-ingest"
            / "references"
            / "antigravity-data-format.md",
        )
        for path in required:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertTrue(path.is_file())

    def test_antigravity_adapter_validates_index_and_transcript_shape(self):
        script = (
            WIKI_ROOT
            / "wiki-history-ingest"
            / "scripts"
            / "antigravity"
            / "extract-history.py"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = sqlite3.connect(root / "conversation_summaries.db")
            database.execute(
                "CREATE TABLE conversation_summaries "
                "(conversation_id TEXT PRIMARY KEY, title TEXT, updated_at TEXT)"
            )
            database.execute(
                "INSERT INTO conversation_summaries VALUES (?, ?, ?)",
                ("conv-1", "Design discussion", "2026-07-23T10:00:00Z"),
            )
            database.commit()
            database.close()
            transcript = (
                root
                / "brain"
                / "conv-1"
                / ".system_generated"
                / "logs"
                / "transcript.jsonl"
            )
            transcript.parent.mkdir(parents=True)
            transcript.write_text(
                json.dumps(
                    {
                        "role": "user",
                        "content": "Keep the durable decision.",
                        "timestamp": "2026-07-23T09:59:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("ok", payload["status"])
        self.assertEqual("conv-1", payload["conversations"][0]["conversation_id"])
        self.assertEqual(
            "Keep the durable decision.",
            payload["conversations"][0]["records"][0]["content"],
        )

    def test_antigravity_adapter_fails_safely_on_unknown_database_shape(self):
        script = (
            WIKI_ROOT
            / "wiki-history-ingest"
            / "scripts"
            / "antigravity"
            / "extract-history.py"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = sqlite3.connect(root / "conversation_summaries.db")
            database.execute("CREATE TABLE changed_schema (id TEXT)")
            database.commit()
            database.close()
            result = subprocess.run(
                [sys.executable, str(script), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(4, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual("unsupported-schema", payload["status"])

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_graph_colorize_preserves_unrelated_settings_and_creates_backup(self):
        script = WIKI_ROOT / "graph-colorize" / "scripts" / "set-graph-colors.ps1"
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp)
            obsidian = vault / ".obsidian"
            obsidian.mkdir()
            graph = obsidian / "graph.json"
            graph.write_text(
                json.dumps(
                    {
                        "collapse-filter": True,
                        "showTags": False,
                        "colorGroups": [{"query": "old", "color": {"a": 1}}],
                    }
                ),
                encoding="utf-8",
            )
            (vault / "concepts").mkdir()
            (vault / "concepts" / "sample.md").write_text(
                "---\ntags:\n  - architecture\n---\n# Sample\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-Vault",
                    str(vault),
                    "-Mode",
                    "ByCategory",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            updated = json.loads(graph.read_text(encoding="utf-8-sig"))
            backups = list(obsidian.glob("graph.json.myskills.*.bak"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(updated["collapse-filter"])
        self.assertFalse(updated["showTags"])
        self.assertEqual("path:concepts", updated["colorGroups"][0]["query"])
        self.assertEqual(1, len(backups))

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_rebuild_archive_is_verified_and_excludes_obsidian_settings(self):
        script = WIKI_ROOT / "wiki-rebuild" / "scripts" / "manage-wiki.ps1"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vault = root / "vault"
            archive_root = root / "archives"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / ".obsidian" / "graph.json").write_text("{}", encoding="utf-8")
            (vault / "index.md").write_text("# Index\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-Vault",
                    str(vault),
                    "-Mode",
                    "ArchiveOnly",
                    "-ArchiveRoot",
                    str(archive_root),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            payload = json.loads(result.stdout)
            archive = Path(payload["archive_path"])

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("verified", payload["archive_status"])
            self.assertTrue((archive / "index.md").is_file())
            self.assertFalse((archive / ".obsidian").exists())
            self.assertTrue((archive / "inventory.json").is_file())


if __name__ == "__main__":
    unittest.main()
