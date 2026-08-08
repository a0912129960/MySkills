from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = ROOT / "skills" / "engineering" / "spec-package-generator"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_definitions.py"


class SpecPackageDefinitionTests(unittest.TestCase):
    def run_validator(self, definition_root: Path | None = None) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(VALIDATOR)]
        if definition_root is not None:
            command.extend(["--definition-root", str(definition_root)])
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

    def copied_references(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        target = Path(temporary.name) / "references"
        shutil.copytree(SKILL_ROOT / "references", target)
        return temporary, target

    def test_bundled_definition_plane_is_valid(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 21 file roles and 43 template dispositions", result.stdout)

    def test_unknown_contract_reference_fails_closed(self) -> None:
        temporary, references = self.copied_references()
        self.addCleanup(temporary.cleanup)
        schema_path = references / "package-schema.yaml"
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        schema["roles"]["workflow_state"]["contract"] = "missing_contract_v1"
        schema_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")

        result = self.run_validator(references)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_contract_v1", result.stderr)

    def test_duplicate_json_contract_key_is_rejected(self) -> None:
        temporary, references = self.copied_references()
        self.addCleanup(temporary.cleanup)
        contracts_path = references / "file-contracts.json"
        contracts_path.write_text(
            '{"schema_version":1,"contracts":{"same":{},"same":{}}}',
            encoding="utf-8",
        )

        result = self.run_validator(references)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate JSON key", result.stderr)

    def test_unknown_writer_is_rejected(self) -> None:
        temporary, references = self.copied_references()
        self.addCleanup(temporary.cleanup)
        schema_path = references / "package-schema.yaml"
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        schema["roles"]["workflow_state"]["writer"] = "helpful_agent"
        schema_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")

        result = self.run_validator(references)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown writer", result.stderr)

    def test_overlapping_role_paths_are_rejected(self) -> None:
        temporary, references = self.copied_references()
        self.addCleanup(temporary.cleanup)
        schema_path = references / "package-schema.yaml"
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        schema["roles"]["bdd_records"]["path"] = "records/requirements.yaml"
        schema_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")

        result = self.run_validator(references)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("overlap", result.stderr)

    def test_missing_template_disposition_is_rejected(self) -> None:
        temporary, references = self.copied_references()
        self.addCleanup(temporary.cleanup)
        schema_path = references / "package-schema.yaml"
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        schema["repository_migration"]["template_dispositions"].pop()
        schema_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")

        result = self.run_validator(references)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected 43 template dispositions", result.stderr)
        self.assertIn("inventory mismatch", result.stderr)

    def test_unknown_id_definition_role_is_rejected(self) -> None:
        temporary, references = self.copied_references()
        self.addCleanup(temporary.cleanup)
        id_schema_path = references / "id-schema.yaml"
        id_schema = yaml.safe_load(id_schema_path.read_text(encoding="utf-8"))
        id_schema["classes"]["REQUIREMENT"]["definition_role"] = "mystery_records"
        id_schema_path.write_text(yaml.safe_dump(id_schema, sort_keys=False), encoding="utf-8")

        result = self.run_validator(references)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown definition role", result.stderr)

    def test_all_43_source_templates_have_one_disposition(self) -> None:
        schema = yaml.safe_load(
            (SKILL_ROOT / "references" / "package-schema.yaml").read_text(encoding="utf-8")
        )
        dispositions = schema["repository_migration"]["template_dispositions"]
        sources = [row["source"] for row in dispositions]

        actual = {
            path.relative_to(SKILL_ROOT / "templates").as_posix()
            for path in (SKILL_ROOT / "templates").iterdir()
            if path.is_file()
        }
        implementation_root = ROOT / "skills" / "engineering" / "implement-spec-task" / "templates"
        actual.update(
            f"implement-spec-task/{path.name}"
            for path in implementation_root.iterdir()
            if path.is_file()
        )

        self.assertEqual(len(dispositions), 43)
        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual(set(sources), actual)

    def test_id_schema_uses_roles_instead_of_paths(self) -> None:
        schema = yaml.safe_load(
            (SKILL_ROOT / "references" / "id-schema.yaml").read_text(encoding="utf-8")
        )
        encoded = json.dumps(schema)
        self.assertNotIn("current/", encoded)
        self.assertNotIn("candidate/", encoded)
        self.assertNotIn("history/", encoded)
        self.assertNotIn("control/", encoded)


if __name__ == "__main__":
    unittest.main()
