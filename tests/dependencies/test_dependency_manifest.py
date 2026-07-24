from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "dependencies.json"
SCHEMA_PATH = ROOT / "manifests" / "dependencies.schema.json"
PROBE_SCRIPT = ROOT / "scripts" / "dependencies" / "Probe-Dependencies.ps1"


class DependencyManifestContractTests(unittest.TestCase):
    def test_registry_contains_confirmed_dependency_versions(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        dependencies = {item["id"]: item for item in manifest["dependencies"]}

        self.assertEqual(dependencies["python"]["minimum_version"], "3.10.0")
        self.assertEqual(dependencies["pyyaml"]["install_version"], "6.0.3")
        self.assertEqual(dependencies["node-qmd"]["minimum_version"], "22.0.0")
        self.assertEqual(dependencies["qmd"]["install_version"], "2.5.3")
        self.assertEqual(
            dependencies["mermaid-cli"]["install_version"], "11.16.0"
        )
        self.assertIsNone(dependencies["git"]["minimum_version"])
        self.assertIsNone(dependencies["obsidian-cli"]["minimum_version"])

    def test_registry_is_closed_and_does_not_duplicate_skill_provenance(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(
            {item["id"] for item in manifest["dependencies"]},
            {
                "python",
                "pyyaml",
                "node-qmd",
                "qmd",
                "node-mermaid",
                "mermaid-cli",
                "git",
                "obsidian-cli",
                "claude-cli",
                "codex-cli",
                "antigravity-cli",
            },
        )
        serialized = json.dumps(manifest)
        for forbidden in ("repository_url", "revision", "source_path", "imported_on"):
            self.assertNotIn(forbidden, serialized)

    def test_schema_requires_read_only_probe_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        dependency = schema["$defs"]["dependency"]
        self.assertIn("probe", dependency["required"])
        self.assertFalse(dependency["additionalProperties"])
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_probe_dry_run_returns_one_result_per_dependency(self) -> None:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PROBE_SCRIPT),
                "-ManifestPath",
                str(MANIFEST_PATH),
                "-DryRun",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads(completed.stdout)
        self.assertEqual(len(results), 11)
        self.assertTrue(all(result["status"] == "PLANNED" for result in results))
        self.assertTrue(all("command" in result for result in results))

    def test_selected_probe_still_returns_a_json_array(self) -> None:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PROBE_SCRIPT),
                "-ManifestPath",
                str(MANIFEST_PATH),
                "-DependencyId",
                "git",
                "-DryRun",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads(completed.stdout)
        self.assertIsInstance(results, list)
        self.assertEqual([result["dependency_id"] for result in results], ["git"])


if __name__ == "__main__":
    unittest.main()
