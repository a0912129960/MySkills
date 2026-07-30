from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_repo.py"


class RepositoryContractTests(unittest.TestCase):
    def test_repository_matches_managed_inventory(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 43 Managed Skill(s)", result.stdout)

    def test_evaluation_gate_is_available_only_when_explicitly_requested(
        self,
    ) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--require-evaluations"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            result.stderr.count(
                "missing passing current-digest release pointer"
            ),
            43,
        )


if __name__ == "__main__":
    unittest.main()
