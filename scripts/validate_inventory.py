#!/usr/bin/env python3
"""Validate the authoritative MySkills candidate inventory."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from .inventory_loader import (
        DEFAULT_INVENTORY_PATH,
        InventoryValidationError,
        load_inventory,
    )
except ImportError:
    from inventory_loader import (
        DEFAULT_INVENTORY_PATH,
        InventoryValidationError,
        load_inventory,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="inventory JSON path (default: inventory/skills.json)",
    )
    args = parser.parse_args(argv)

    try:
        inventory = load_inventory(args.path)
    except InventoryValidationError as error:
        for message in error.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    states = inventory["summary"]["states"]
    print(
        f"Validated {len(inventory['skills'])} candidates: "
        f"{states['managed']} managed, {states['excluded']} excluded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
