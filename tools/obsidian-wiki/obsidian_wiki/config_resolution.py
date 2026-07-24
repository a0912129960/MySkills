"""Deterministic Obsidian Wiki config discovery shared by the CLI and skills."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping

_PROFILE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*$")
_PLACEHOLDER_VAULTS = {"/path/to/your/vault"}


def user_home(
    environ: Mapping[str, str] | None = None,
    *,
    platform: str | None = None,
) -> Path:
    """Return the interactive user's home without Windows profile API ambiguity."""

    env = os.environ if environ is None else environ
    platform_name = os.name if platform is None else platform
    keys = ("USERPROFILE", "HOME") if platform_name == "nt" else ("HOME", "USERPROFILE")
    for key in keys:
        value = env.get(key, "").strip()
        if value:
            return Path(value).expanduser()
    return Path.home()


def valid_profile_name(name: str) -> bool:
    """Return whether *name* is one portable config-profile filename segment."""

    return (
        bool(_PROFILE_NAME.fullmatch(name))
        and name not in {".", ".."}
        and not name.endswith(".")
    )


def _read_config_values(path: Path) -> tuple[dict[str, str], set[str], set[str]]:
    values: dict[str, str] = {}
    duplicates: set[str] = set()
    malformed: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"^(?:export\s+)?OBSIDIAN_VAULT_PATH\b", line) and not line.startswith(
            "OBSIDIAN_VAULT_PATH="
        ):
            malformed.add("OBSIDIAN_VAULT_PATH")
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key in values:
            duplicates.add(key)
        if value[:1] in {"\"", "'"}:
            if len(value) < 2 or value[-1] != value[0]:
                values[key] = ""
                continue
            value = value[1:-1]
        elif value[-1:] in {"\"", "'"}:
            values[key] = ""
            continue
        values[key] = value
    return values, duplicates, malformed


def read_config(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE config entries without evaluating shell content."""

    return _read_config_values(path)[0]


def _candidate(path: Path, source: str) -> dict[str, object] | None:
    if not path.is_file():
        return None
    values, duplicates, malformed = _read_config_values(path)
    has_vault_setting = (
        "OBSIDIAN_VAULT_PATH" in values
        or "OBSIDIAN_VAULT_PATH" in malformed
    )
    if source == "project" and not has_vault_setting:
        return None
    vault = values.get("OBSIDIAN_VAULT_PATH", "").strip()
    expanded_vault = os.path.expandvars(os.path.expanduser(vault))
    error = ""
    if "OBSIDIAN_VAULT_PATH" in malformed:
        error = "config has a malformed OBSIDIAN_VAULT_PATH assignment"
    elif "OBSIDIAN_VAULT_PATH" in duplicates:
        error = "config defines OBSIDIAN_VAULT_PATH more than once"
    elif not vault:
        error = "config does not set OBSIDIAN_VAULT_PATH"
    elif vault in _PLACEHOLDER_VAULTS:
        error = "config uses the placeholder OBSIDIAN_VAULT_PATH"
    elif not Path(expanded_vault).is_absolute():
        error = "OBSIDIAN_VAULT_PATH must be absolute"
    if error:
        return {
            "status": "invalid",
            "source": source,
            "config_path": str(path),
            "vault_path": "",
            "error": error,
        }
    return {
        "status": "resolved",
        "source": source,
        "config_path": str(path),
        "vault_path": expanded_vault,
    }


def resolve_config(
    cwd: Path,
    *,
    name: str | None = None,
    home: Path | None = None,
) -> dict[str, object]:
    """Resolve inline, project-local, then global config in documented order."""

    resolved_home = (home or user_home()).expanduser()
    config_dir = resolved_home / ".obsidian-wiki"

    if name:
        if not valid_profile_name(name):
            return {
                "status": "invalid",
                "source": "named",
                "config_path": "",
                "vault_path": "",
                "name": name,
                "error": (
                    "profile name must start with a letter, digit, or underscore; "
                    "contain only ASCII letters, digits, dot, underscore, or hyphen; "
                    "and not end with dot"
                ),
            }
        named = config_dir / f"config.{name}"
        result = _candidate(named, "named")
        if result is not None:
            result["name"] = name
            return result
        profiles = sorted(
            path.name.removeprefix("config.")
            for path in config_dir.glob("config.*")
            if path.is_file() and valid_profile_name(path.name.removeprefix("config."))
        )
        return {
            "status": "not-found",
            "source": "named",
            "config_path": str(named),
            "vault_path": "",
            "name": name,
            "available_profiles": profiles,
            "error": f"named vault config does not exist: {name}",
        }

    current = cwd.expanduser().resolve()
    while True:
        result = _candidate(current / ".env", "project")
        if result is not None:
            return result
        if current == resolved_home or current.parent == current:
            break
        current = current.parent

    global_path = config_dir / "config"
    result = _candidate(global_path, "global")
    if result is not None:
        return result
    return {
        "status": "not-found",
        "source": "global",
        "config_path": str(global_path),
        "vault_path": "",
        "error": "no config found",
    }
