#!/usr/bin/env python3
"""Read validated Antigravity conversation summaries and transcript JSONL."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path


CONVERSATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUIRED_COLUMNS = {"conversation_id", "title", "updated_at"}
ALLOWED_ROLES = {"user", "assistant", "system", "tool"}


class UnsupportedShape(ValueError):
    pass


def _safe_transcript(root: Path, conversation_id: str) -> Path:
    if not CONVERSATION_ID.fullmatch(conversation_id):
        raise UnsupportedShape(f"unsafe conversation id: {conversation_id!r}")
    path = (
        root
        / "brain"
        / conversation_id
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    ).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise UnsupportedShape("transcript path escapes history root") from exc
    return path


def _read_index(database_path: Path) -> list[dict[str, str]]:
    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if "conversation_summaries" not in tables:
            raise UnsupportedShape("missing conversation_summaries table")
        columns = {
            str(row["name"])
            for row in connection.execute("PRAGMA table_info(conversation_summaries)")
        }
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise UnsupportedShape(
                "conversation_summaries missing columns: " + ", ".join(sorted(missing))
            )
        rows = connection.execute(
            "SELECT conversation_id, title, updated_at "
            "FROM conversation_summaries ORDER BY updated_at, conversation_id"
        )
        result = []
        for row in rows:
            values = {
                "conversation_id": str(row["conversation_id"] or ""),
                "title": str(row["title"] or ""),
                "updated_at": str(row["updated_at"] or ""),
            }
            if not all(values.values()):
                raise UnsupportedShape("conversation summary contains an empty required field")
            result.append(values)
        return result
    finally:
        connection.close()


def _read_transcript(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    records: list[dict[str, str]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise UnsupportedShape(
                f"{path}: line {line_number} is not valid JSON"
            ) from exc
        if not isinstance(value, dict):
            raise UnsupportedShape(f"{path}: line {line_number} is not an object")
        role = value.get("role")
        content = value.get("content")
        timestamp = value.get("timestamp")
        if role not in ALLOWED_ROLES:
            raise UnsupportedShape(f"{path}: line {line_number} has unknown role")
        if not isinstance(content, str) or not content.strip():
            raise UnsupportedShape(f"{path}: line {line_number} has invalid content")
        if not isinstance(timestamp, str) or not timestamp.strip():
            raise UnsupportedShape(f"{path}: line {line_number} has invalid timestamp")
        records.append(
            {
                "role": role,
                "content": content,
                "timestamp": timestamp,
            }
        )
    return records


def extract(root: Path) -> dict[str, object]:
    history_root = root.expanduser().resolve()
    summaries = _read_index(history_root / "conversation_summaries.db")
    conversations = []
    for summary in summaries:
        transcript = _safe_transcript(history_root, summary["conversation_id"])
        conversations.append(
            {
                **summary,
                "transcript_path": str(transcript),
                "records": _read_transcript(transcript),
            }
        )
    return {
        "status": "ok",
        "source": "antigravity",
        "history_root": str(history_root),
        "conversation_count": len(conversations),
        "conversations": conversations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("history_root")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = extract(Path(args.history_root))
        code = 0
    except FileNotFoundError as exc:
        result = {
            "status": "not-found",
            "source": "antigravity",
            "error": str(exc),
        }
        code = 4
    except (OSError, sqlite3.Error, UnsupportedShape) as exc:
        result = {
            "status": "unsupported-schema",
            "source": "antigravity",
            "error": str(exc),
        }
        code = 4
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
