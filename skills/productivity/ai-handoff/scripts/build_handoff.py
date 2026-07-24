#!/usr/bin/env python3
"""Build a deterministic prompt for another AI session."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate a cross-session AI handoff prompt."
    )
    parser.add_argument("--objective", required=True, help="One concrete objective.")
    parser.add_argument("--target", required=True, help="Destination repo or session.")
    parser.add_argument(
        "--context-file",
        action="append",
        default=[],
        help="Authoritative context path. Repeat as needed.",
    )
    parser.add_argument(
        "--constraint",
        action="append",
        default=[],
        help="Authority boundary or non-goal. Repeat as needed.",
    )
    parser.add_argument(
        "--deliverable",
        action="append",
        default=[],
        help="Expected output. Repeat as needed.",
    )
    parser.add_argument(
        "--transport",
        choices=("ascii", "unicode"),
        default="ascii",
        help="ASCII is the safe default for Windows PTY transport.",
    )
    parser.add_argument(
        "--response-language",
        default="Traditional Chinese (zh-TW)",
        help="Language requested from the receiving AI.",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="UTF-8 output file, or - for stdout.",
    )
    return parser.parse_args()


def bullets(values: list[str], fallback: str) -> list[str]:
    selected = values or [fallback]
    return [f"- {value}" for value in selected]


def build_prompt(args: argparse.Namespace) -> str:
    lines = [
        "ROLE",
        f"You are the receiving agent working in {args.target}.",
        "",
        "OBJECTIVE",
        args.objective,
        "",
        "AUTHORITATIVE CONTEXT",
        *bullets(
            [f"Read {path}." for path in args.context_file],
            "Inspect the destination's current state before relying on this handoff.",
        ),
        "",
        "CONSTRAINTS",
        *bullets(
            args.constraint,
            "Do not expand authority beyond the objective.",
        ),
        "",
        "DELIVERABLES",
        *bullets(
            args.deliverable,
            "Complete the objective and report verifiable evidence.",
        ),
        "",
        "VERIFICATION",
        "- Treat destination files and runtime state as authoritative.",
        "- Distinguish observed facts from assumptions.",
        "- Report blockers instead of inventing missing information.",
        "",
        "RESPONSE",
        f"Answer in {args.response_language}.",
        "",
    ]
    return "\n".join(lines)


def validate_ascii(prompt: str) -> None:
    try:
        prompt.encode("ascii")
    except UnicodeEncodeError as error:
        bad = prompt[error.start : error.end]
        raise ValueError(
            "ASCII transport rejected non-ASCII text "
            f"at character {error.start}: {bad!r}. "
            "Move non-ASCII content to a UTF-8 context file and describe it in English."
        ) from error


def main() -> int:
    args = parse_args()
    prompt = build_prompt(args)

    if args.transport == "ascii":
        try:
            validate_ascii(prompt)
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2

    if args.output == "-":
        sys.stdout.write(prompt)
        return 0

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prompt, encoding="utf-8", newline="\n")
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
