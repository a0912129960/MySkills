from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.inventory_loader import (
    InventoryValidationError,
    load_inventory,
    validate_inventory,
)


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "inventory" / "skills.json"
SCHEMA = ROOT / "inventory" / "skills.schema.json"
VALIDATOR = ROOT / "scripts" / "validate_inventory.py"


class AuthoritativeInventoryTests(unittest.TestCase):
    def test_inventory_matches_confirmed_candidate_decisions(self) -> None:
        inventory = load_inventory(INVENTORY)
        skills = inventory["skills"]

        self.assertEqual(len(skills), 92)
        self.assertEqual(
            inventory["summary"],
            {
                "states": {
                    "pending": 0,
                    "managed": 42,
                    "deferred": 0,
                    "excluded": 50,
                },
                "categories": {
                    "engineering": 32,
                    "productivity": 15,
                    "personal": 0,
                    "wiki": 38,
                    "obsidian": 6,
                    "qmd": 1,
                },
            },
        )

        managed_by_source = {
            skill["source_name"]: skill["managed_name"]
            for skill in skills
            if skill["state"] == "managed"
        }
        self.assertEqual(managed_by_source["ask-matt"], "ask-myskills")
        self.assertEqual(managed_by_source["skill-creator"], "skill-evaluator")
        self.assertEqual(managed_by_source["handoff"], "session-checkpoint")
        self.assertEqual(
            sum(
                skill["state"] == "managed" and skill["category"] == "wiki"
                for skill in skills
            ),
            20,
        )

    def test_inventory_references_a_valid_json_schema_document(self) -> None:
        inventory = load_inventory(INVENTORY)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(inventory["$schema"], "./skills.schema.json")
        self.assertEqual(
            schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertEqual(schema["title"], "MySkills candidate inventory")


class InventoryLoaderTests(unittest.TestCase):
    def test_loader_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate.json"
            path.write_text(
                '{"schema_version": 1, "schema_version": 1, "origins": [], '
                '"summary": {}, "skills": []}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                InventoryValidationError, "duplicate JSON key: schema_version"
            ):
                load_inventory(path)

    def test_validator_rejects_incomplete_managed_install_targets(self) -> None:
        inventory = load_inventory(INVENTORY)
        changed = copy.deepcopy(inventory)
        managed = next(
            skill for skill in changed["skills"] if skill["state"] == "managed"
        )
        managed["install_targets"] = ["codex"]

        errors = validate_inventory(changed)

        self.assertTrue(
            any(
                "managed skills must target codex, claude-code, and antigravity-cli"
                in error
                for error in errors
            ),
            errors,
        )

    def test_validator_rejects_stale_summary(self) -> None:
        inventory = load_inventory(INVENTORY)
        changed = copy.deepcopy(inventory)
        changed["summary"]["states"]["managed"] = 41

        errors = validate_inventory(changed)

        self.assertTrue(
            any("summary.states does not match skill records" in error for error in errors),
            errors,
        )

    def test_validator_reports_wrong_field_types_without_crashing(self) -> None:
        inventory = load_inventory(INVENTORY)
        changed = copy.deepcopy(inventory)
        changed["skills"][0]["origin"] = ["myskills"]
        changed["skills"][0]["state"] = ["managed"]

        errors = validate_inventory(changed)

        self.assertTrue(
            any("origin does not reference a declared origin" in error for error in errors),
            errors,
        )
        self.assertTrue(any(".state is invalid" in error for error in errors), errors)

    def test_validator_rejects_invalid_import_provenance_date(self) -> None:
        inventory = load_inventory(INVENTORY)
        changed = copy.deepcopy(inventory)
        changed["skills"][0]["imported_on"] = "24-07-2026"

        errors = validate_inventory(changed)

        self.assertTrue(
            any("imported_on must be an ISO 8601 date" in error for error in errors),
            errors,
        )

    def test_validator_cli_accepts_authoritative_inventory(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "Validated 92 candidates: 42 managed, 50 excluded.",
        )


if __name__ == "__main__":
    unittest.main()
