#!/usr/bin/env python3
"""Run every MySkills unittest directory, including non-package ownership folders."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def test_directories() -> list[Path]:
    """Return each directory that directly contains test modules."""

    return sorted(
        {
            path.parent
            for path in TESTS.rglob("test_*.py")
            if path.is_file()
        },
        key=lambda path: path.relative_to(TESTS).as_posix(),
    )


def main() -> int:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    failures: list[Path] = []

    for directory in test_directories():
        label = directory.relative_to(ROOT).as_posix()
        print(f"\n=== {label} ===", flush=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(directory),
                "-p",
                "test_*.py",
                "-v",
            ],
            cwd=ROOT,
            env=environment,
            check=False,
        )
        if result.returncode != 0:
            failures.append(directory)

    if failures:
        print(
            "\nFailed test directories: "
            + ", ".join(path.relative_to(ROOT).as_posix() for path in failures),
            file=sys.stderr,
        )
        return 1

    print(f"\nAll {len(test_directories())} test directories passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
