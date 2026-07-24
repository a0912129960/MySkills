import contextlib
import importlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = REPO_ROOT / "tools" / "obsidian-wiki"
sys.path.insert(0, str(TOOL_ROOT))
cli = importlib.import_module("obsidian_wiki.cli")


class RepositoryOwnedCliBehaviorTests(unittest.TestCase):
    def run_cli(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = cli.main(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cache_commands_track_known_source_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vault = root / "vault"
            vault.mkdir()
            (vault / ".manifest.json").write_text('{"sources": {}}', encoding="utf-8")
            source = root / "source.md"
            source.write_text("version one\n", encoding="utf-8")

            update_code, update_out, _ = self.run_cli(
                "cache-update", str(vault), str(source), "--pages", "concepts/source.md"
            )
            check_code, check_out, _ = self.run_cli(
                "cache-check", str(vault), str(source)
            )
            source.write_text("version two\n", encoding="utf-8")
            _, changed_out, _ = self.run_cli("cache-check", str(vault), str(source))

        self.assertEqual(0, update_code)
        self.assertEqual(64, len(json.loads(update_out)["content_hash"]))
        self.assertEqual(0, check_code)
        self.assertEqual([str(source.resolve())], json.loads(check_out)["unchanged"])
        self.assertEqual([str(source.resolve())], json.loads(changed_out)["modified"])

    def test_ast_extract_and_graph_query_expose_source_behavior(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "example.py"
            source.write_text(
                "import json\n\nclass Example:\n    def run(self):\n        return json.dumps({})\n",
                encoding="utf-8",
            )
            vault = root / "vault"
            concepts = vault / "concepts"
            concepts.mkdir(parents=True)
            (vault / "index.md").write_text(
                "- [[concepts/deep-modules|Deep Modules]]\n", encoding="utf-8"
            )
            (concepts / "deep-modules.md").write_text(
                "---\n"
                "title: Deep Modules\n"
                "summary: Encapsulation and narrow interfaces.\n"
                "tags: [architecture]\n"
                "---\n"
                "# Deep Modules\n",
                encoding="utf-8",
            )

            ast_code, ast_out, _ = self.run_cli("ast-extract", str(source))
            query_code, query_out, _ = self.run_cli(
                "graph-query", str(vault), "What are deep modules?"
            )

        self.assertEqual(0, ast_code)
        ast = json.loads(ast_out)
        serialized = json.dumps(ast)
        self.assertIn("Example", serialized)
        self.assertIn("import::json", serialized)
        self.assertEqual(0, query_code)
        query = json.loads(query_out)
        self.assertEqual("Deep Modules", query["candidates"][0]["title"])

    def test_doctor_checks_private_launcher_runtime_state_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_home = root / "profile" / ".obsidian-wiki"
            vault = root / "vault"
            old = os.environ.get("OBSIDIAN_WIKI_CONFIG_HOME")
            os.environ["OBSIDIAN_WIKI_CONFIG_HOME"] = str(config_home)
            try:
                self.run_cli("setup", "--vault", str(vault))
                code, stdout, stderr = self.run_cli(
                    "doctor", "--json", "--pretty"
                )
            finally:
                if old is None:
                    os.environ.pop("OBSIDIAN_WIKI_CONFIG_HOME", None)
                else:
                    os.environ["OBSIDIAN_WIKI_CONFIG_HOME"] = old

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        report = json.loads(stdout)
        self.assertEqual("pass", report["status"])
        names = {check["name"] for check in report["checks"]}
        self.assertEqual({"config", "vault", "vault-shape", "manifest-json"}, names)


if __name__ == "__main__":
    unittest.main()
