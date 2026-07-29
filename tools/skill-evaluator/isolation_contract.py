"""Shared deterministic constants for evaluator isolation evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CLAUDE_EMPTY_MCP_CONFIG_RELATIVE = (
    Path(".claude") / "empty-mcp.json"
)
CLAUDE_EMPTY_MCP_CONFIG_PATH_LABEL = (
    "workspace/" + CLAUDE_EMPTY_MCP_CONFIG_RELATIVE.as_posix()
)
CLAUDE_EMPTY_MCP_CONFIG_TEXT = (
    json.dumps(
        {"mcpServers": {}},
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
CLAUDE_EMPTY_MCP_CONFIG_DIGEST = (
    "sha256:"
    + hashlib.sha256(
        CLAUDE_EMPTY_MCP_CONFIG_TEXT.encode("utf-8")
    ).hexdigest()
)
CLAUDE_PROJECT_SETTINGS_RELATIVE = (
    Path(".claude") / "settings.json"
)
CLAUDE_PROJECT_SETTINGS_PATH_LABEL = (
    "workspace/" + CLAUDE_PROJECT_SETTINGS_RELATIVE.as_posix()
)
