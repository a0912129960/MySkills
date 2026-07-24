"""Load and validate the machine-readable MySkills candidate inventory."""

from __future__ import annotations

from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = ROOT / "inventory" / "skills.json"

STATES = ("pending", "managed", "deferred", "excluded")
CATEGORIES = (
    "engineering",
    "productivity",
    "personal",
    "wiki",
    "obsidian",
    "qmd",
)
INSTALL_TARGETS = ("codex", "claude-code", "antigravity-cli")
INVOCATION_POLICIES = ("explicit", "implicit")

_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_TOP_LEVEL_KEYS = {"$schema", "schema_version", "origins", "summary", "skills"}
_ORIGIN_KEYS = {"id", "kind", "repository_url", "revision"}
_SKILL_KEYS = {
    "id",
    "source_name",
    "managed_name",
    "origin",
    "source_path",
    "category",
    "state",
    "owner",
    "invocation",
    "install_targets",
}
_SKILL_OPTIONAL_KEYS = {"imported_on"}


class InventoryValidationError(ValueError):
    """Raised when an inventory document cannot be loaded as valid authority."""

    def __init__(self, errors: list[str] | tuple[str, ...]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryValidationError([f"duplicate JSON key: {key}"])
        result[key] = value
    return result


def _unknown_and_missing_keys(
    value: dict[str, Any],
    expected: set[str],
    location: str,
    errors: list[str],
    *,
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    unknown = sorted(set(value) - expected - optional)
    missing = sorted(expected - set(value))
    if unknown:
        errors.append(f"{location} has unknown fields: {', '.join(unknown)}")
    if missing:
        errors.append(f"{location} is missing fields: {', '.join(missing)}")


def _is_non_negative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_origins(value: Any, errors: list[str]) -> set[str]:
    if not isinstance(value, list):
        errors.append("origins must be an array")
        return set()

    origin_ids: set[str] = set()
    for index, origin in enumerate(value):
        location = f"origins[{index}]"
        if not isinstance(origin, dict):
            errors.append(f"{location} must be an object")
            continue
        _unknown_and_missing_keys(origin, _ORIGIN_KEYS, location, errors)

        origin_id = origin.get("id")
        if not isinstance(origin_id, str) or not _NAME_PATTERN.fullmatch(origin_id):
            errors.append(f"{location}.id must be a kebab-case identifier")
        elif origin_id in origin_ids:
            errors.append(f"duplicate origin id: {origin_id}")
        else:
            origin_ids.add(origin_id)

        if origin.get("kind") not in ("repository", "local-installation"):
            errors.append(f"{location}.kind is invalid")

        repository_url = origin.get("repository_url")
        if repository_url is not None and (
            not isinstance(repository_url, str)
            or not repository_url.startswith(("https://", "ssh://", "git@"))
        ):
            errors.append(f"{location}.repository_url must be a repository URL or null")

        revision = origin.get("revision")
        if revision is not None and (
            not isinstance(revision, str) or not _REVISION_PATTERN.fullmatch(revision)
        ):
            errors.append(f"{location}.revision must be a 40-character Git SHA or null")

        if origin.get("kind") == "repository" and repository_url is None:
            errors.append(f"{location}.repository_url is required for repository origins")
        if origin.get("kind") == "local-installation" and (
            repository_url is not None or revision is not None
        ):
            errors.append(
                f"{location} local installations cannot claim a repository or revision"
            )

    return origin_ids


def _validate_summary_shape(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("summary must be an object")
        return
    _unknown_and_missing_keys(value, {"states", "categories"}, "summary", errors)
    for field, expected_keys in (("states", STATES), ("categories", CATEGORIES)):
        counts = value.get(field)
        if not isinstance(counts, dict):
            errors.append(f"summary.{field} must be an object")
            continue
        _unknown_and_missing_keys(
            counts, set(expected_keys), f"summary.{field}", errors
        )
        for name, count in counts.items():
            if not _is_non_negative_integer(count):
                errors.append(f"summary.{field}.{name} must be a non-negative integer")


def _validate_skill(
    skill: Any,
    index: int,
    origin_ids: set[str],
    seen_ids: set[str],
    managed_names: set[str],
    errors: list[str],
) -> None:
    location = f"skills[{index}]"
    if not isinstance(skill, dict):
        errors.append(f"{location} must be an object")
        return
    _unknown_and_missing_keys(
        skill,
        _SKILL_KEYS,
        location,
        errors,
        optional=_SKILL_OPTIONAL_KEYS,
    )

    skill_id = skill.get("id")
    if not isinstance(skill_id, str) or not skill_id:
        errors.append(f"{location}.id must be a non-empty string")
    elif skill_id in seen_ids:
        errors.append(f"duplicate skill id: {skill_id}")
    else:
        seen_ids.add(skill_id)

    source_name = skill.get("source_name")
    if not isinstance(source_name, str) or not _NAME_PATTERN.fullmatch(source_name):
        errors.append(f"{location}.source_name must be a kebab-case skill name")

    origin_id = skill.get("origin")
    if not isinstance(origin_id, str) or origin_id not in origin_ids:
        errors.append(f"{location}.origin does not reference a declared origin")
    if not isinstance(skill.get("source_path"), str) or not skill.get("source_path"):
        errors.append(f"{location}.source_path must be a non-empty relative path")
    elif (
        Path(skill["source_path"]).is_absolute()
        or "\\" in skill["source_path"]
        or ".." in Path(skill["source_path"]).parts
    ):
        errors.append(
            f"{location}.source_path must use portable forward-slash relative syntax"
        )

    if skill.get("category") not in CATEGORIES:
        errors.append(f"{location}.category is invalid")
    state = skill.get("state")
    if state not in STATES:
        errors.append(f"{location}.state is invalid")
        return

    imported_on = skill.get("imported_on")
    if imported_on is not None:
        try:
            valid_import_date = bool(
                isinstance(imported_on, str)
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", imported_on)
                and date.fromisoformat(imported_on)
            )
        except ValueError:
            valid_import_date = False
        if not valid_import_date:
            errors.append(f"{location}.imported_on must be an ISO 8601 date or null")
        if state != "managed":
            errors.append(f"{location}.imported_on is allowed only for managed skills")

    install_targets = skill.get("install_targets")
    if not isinstance(install_targets, list) or any(
        not isinstance(target, str) for target in install_targets
    ):
        errors.append(f"{location}.install_targets must be an array of strings")
        install_targets = []
    elif len(install_targets) != len(set(install_targets)):
        errors.append(f"{location}.install_targets contains duplicates")
    elif any(target not in INSTALL_TARGETS for target in install_targets):
        errors.append(f"{location}.install_targets contains an invalid target")

    if state == "managed":
        managed_name = skill.get("managed_name")
        if not isinstance(managed_name, str) or not _NAME_PATTERN.fullmatch(managed_name):
            errors.append(f"{location}.managed_name must be a kebab-case skill name")
        elif managed_name in managed_names:
            errors.append(f"duplicate managed skill name: {managed_name}")
        else:
            managed_names.add(managed_name)
        if skill.get("owner") != "MySkills":
            errors.append(f"{location}.owner must be MySkills for managed skills")
        if skill.get("invocation") not in INVOCATION_POLICIES:
            errors.append(f"{location}.invocation is invalid for a managed skill")
        if set(install_targets) != set(INSTALL_TARGETS):
            errors.append(
                f"{location}: managed skills must target codex, claude-code, "
                "and antigravity-cli"
            )
    else:
        if skill.get("managed_name") is not None:
            errors.append(f"{location}.managed_name must be null unless managed")
        if skill.get("owner") is not None:
            errors.append(f"{location}.owner must be null unless managed")
        if skill.get("invocation") is not None:
            errors.append(f"{location}.invocation must be null unless managed")
        if install_targets:
            errors.append(f"{location}.install_targets must be empty unless managed")


def _actual_summary(skills: list[Any]) -> dict[str, dict[str, int]]:
    states = Counter(
        skill.get("state")
        for skill in skills
        if isinstance(skill, dict) and skill.get("state") in STATES
    )
    categories = Counter(
        skill.get("category")
        for skill in skills
        if isinstance(skill, dict) and skill.get("category") in CATEGORIES
    )
    return {
        "states": {state: states[state] for state in STATES},
        "categories": {category: categories[category] for category in CATEGORIES},
    }


def validate_inventory(document: Any) -> list[str]:
    """Return all structural and cross-record validation errors."""

    errors: list[str] = []
    if not isinstance(document, dict):
        return ["inventory root must be an object"]

    _unknown_and_missing_keys(document, _TOP_LEVEL_KEYS, "inventory", errors)
    if document.get("$schema") != "./skills.schema.json":
        errors.append("$schema must reference ./skills.schema.json")
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    origin_ids = _validate_origins(document.get("origins"), errors)
    _validate_summary_shape(document.get("summary"), errors)

    skills = document.get("skills")
    if not isinstance(skills, list):
        errors.append("skills must be an array")
        return errors

    seen_ids: set[str] = set()
    managed_names: set[str] = set()
    for index, skill in enumerate(skills):
        _validate_skill(
            skill,
            index,
            origin_ids,
            seen_ids,
            managed_names,
            errors,
        )

    actual_summary = _actual_summary(skills)
    summary = document.get("summary")
    if isinstance(summary, dict):
        if summary.get("states") != actual_summary["states"]:
            errors.append("summary.states does not match skill records")
        if summary.get("categories") != actual_summary["categories"]:
            errors.append("summary.categories does not match skill records")

    return errors


def load_inventory(path: Path | str = DEFAULT_INVENTORY_PATH) -> dict[str, Any]:
    """Load an inventory document, rejecting malformed or invalid authority."""

    inventory_path = Path(path)
    try:
        document = json.loads(
            inventory_path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except InventoryValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InventoryValidationError(
            [f"cannot load inventory {inventory_path}: {error}"]
        ) from error

    errors = validate_inventory(document)
    if errors:
        raise InventoryValidationError(errors)
    return document
