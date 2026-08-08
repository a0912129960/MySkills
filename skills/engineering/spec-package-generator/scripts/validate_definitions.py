#!/usr/bin/env python3
"""Meta-validate the spec-package-generator definition plane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

import yaml


SCRIPT = Path(__file__).resolve()
SKILL_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[4]
DEFAULT_DEFINITION_ROOT = SKILL_ROOT / "references"

EXPECTED_FILES = {
    "package-schema.yaml",
    "file-contracts.json",
    "file-guide.yaml",
    "id-schema.yaml",
}
EXPECTED_AREAS = {"current", "candidate", "history", "control"}
EXPECTED_ROLES = {
    "current_id_index",
    "requirement_records",
    "bdd_records",
    "design_records",
    "test_records",
    "task_records",
    "task_manifest",
    "dashboard_view",
    "active_question",
    "candidate_discussion",
    "candidate_application_plan",
    "candidate_review",
    "decision_archive",
    "workflow_state",
    "task_state",
    "id_allocation_state",
    "validation_result",
    "validator_attempt",
    "project_context",
    "project_rule_source",
    "migration_plan",
}
EXPECTED_ID_CLASSES = {
    "REQUIREMENT",
    "BDD",
    "DESIGN",
    "TEST",
    "TASK",
    "QUESTION",
    "DECISION",
}
EXPECTED_CURRENT_CLASSES = {"REQUIREMENT", "BDD", "DESIGN", "TEST", "TASK"}
ROLE_KEYS = {
    "scope",
    "area",
    "path",
    "path_pattern",
    "placeholder_bindings",
    "multiplicity",
    "writer",
    "authority",
    "load_policy",
    "lifecycle",
    "cleanup",
    "contract",
    "guide",
    "producer",
}
REQUIRED_ROLE_KEYS = {
    "scope",
    "multiplicity",
    "writer",
    "authority",
    "load_policy",
    "lifecycle",
    "contract",
    "guide",
    "producer",
}
DISPOSITION_KEYS = {"source", "disposition", "target_role"}
GUIDE_KEYS = {"purpose", "ai_use"}


class DefinitionError(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DefinitionError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError, DefinitionError) as error:
        raise DefinitionError(f"cannot load {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise DefinitionError(f"{path.name} must contain an object")
    return value


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DefinitionError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, DefinitionError) as error:
        raise DefinitionError(f"cannot load {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise DefinitionError(f"{path.name} must contain an object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> list[str]:
    errors: list[str] = []
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        errors.append(f"{label} missing keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")
    return errors


def _safe_relative_path(raw: Any, label: str) -> list[str]:
    if not isinstance(raw, str) or not raw:
        return [f"{label} must be a non-empty relative POSIX path"]
    errors: list[str] = []
    if "\\" in raw or re.match(r"^[A-Za-z]:", raw) or "://" in raw:
        errors.append(f"{label} is not a portable relative path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "**" in raw:
        errors.append(f"{label} escapes its declared scope: {raw!r}")
    return errors


def _template_inventory() -> set[str]:
    sources = {
        path.name
        for path in (SKILL_ROOT / "templates").iterdir()
        if path.is_file()
    }
    implementation = REPO_ROOT / "skills" / "engineering" / "implement-spec-task" / "templates"
    sources.update(
        f"implement-spec-task/{path.name}"
        for path in implementation.iterdir()
        if path.is_file()
    )
    return sources


def _contains_physical_path_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"path", "path_pattern", "area", "filename", "directory"}:
                return True
            if _contains_physical_path_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_physical_path_key(child) for child in value)
    return False


def validate_definition_plane(definition_root: Path) -> list[str]:
    errors: list[str] = []
    for name in sorted(EXPECTED_FILES):
        if not (definition_root / name).is_file():
            errors.append(f"missing definition file: {name}")
    if errors:
        return errors

    try:
        package = _load_yaml(definition_root / "package-schema.yaml")
        contracts_doc = _load_json(definition_root / "file-contracts.json")
        guide_doc = _load_yaml(definition_root / "file-guide.yaml")
        id_schema = _load_yaml(definition_root / "id-schema.yaml")
    except DefinitionError as error:
        return [str(error)]

    errors.extend(
        _require_exact_keys(
            package,
            {"schema_version", "vocabulary", "package", "roles", "repository_migration"},
            "package-schema",
        )
    )
    errors.extend(_require_exact_keys(contracts_doc, {"schema_version", "contracts"}, "file-contracts"))
    errors.extend(_require_exact_keys(guide_doc, {"schema_version", "roles"}, "file-guide"))
    errors.extend(
        _require_exact_keys(
            id_schema,
            {"schema_version", "common_record", "allocation", "classes", "relationships", "rejected_legacy_patterns", "scan_policy"},
            "id-schema",
        )
    )
    if errors:
        return errors

    for label, document in (
        ("package-schema", package),
        ("file-contracts", contracts_doc),
        ("file-guide", guide_doc),
        ("id-schema", id_schema),
    ):
        if document.get("schema_version") != 1:
            errors.append(f"{label} schema_version must be 1")

    vocabulary = package.get("vocabulary")
    package_section = package.get("package")
    roles = package.get("roles")
    migration = package.get("repository_migration")
    contracts = contracts_doc.get("contracts")
    guides = guide_doc.get("roles")
    classes = id_schema.get("classes")
    if not all(isinstance(value, dict) for value in (vocabulary, package_section, roles, migration, contracts, guides, classes)):
        return errors + ["definition catalogs must contain object-valued sections"]

    areas = package_section.get("areas")
    if not isinstance(areas, dict) or set(areas) != EXPECTED_AREAS:
        errors.append("Package Schema must define exactly current, candidate, history, and control areas")
    if set(roles) != EXPECTED_ROLES:
        missing = sorted(EXPECTED_ROLES - set(roles))
        unknown = sorted(set(roles) - EXPECTED_ROLES)
        errors.append(f"Package Schema role set mismatch; missing={missing}, unknown={unknown}")
    if set(guides) != set(roles):
        errors.append("File Guide roles must exactly equal Package Schema roles")

    vocab_sets = {
        "scope": set(vocabulary.get("scopes", [])),
        "multiplicity": set(vocabulary.get("multiplicities", [])),
        "writer": set(vocabulary.get("writers", [])),
        "authority": set(vocabulary.get("authorities", [])),
        "load_policy": set(vocabulary.get("load_policies", [])),
        "lifecycle": set(vocabulary.get("lifecycles", [])),
    }
    resolved_paths: dict[str, str] = {}
    used_contracts: set[str] = set()
    rewrite_producers: dict[str, str] = {}
    for role_name, role in roles.items():
        if not isinstance(role, dict):
            errors.append(f"role {role_name} must be an object")
            continue
        unknown_keys = set(role) - ROLE_KEYS
        missing_keys = REQUIRED_ROLE_KEYS - set(role)
        if unknown_keys:
            errors.append(f"role {role_name} has unknown keys: {sorted(unknown_keys)}")
        if missing_keys:
            errors.append(f"role {role_name} missing keys: {sorted(missing_keys)}")
        for field, allowed in vocab_sets.items():
            if role.get(field) not in allowed:
                errors.append(f"role {role_name} has unknown {field}: {role.get(field)!r}")
        scope = role.get("scope")
        if scope == "feature" and role.get("area") not in EXPECTED_AREAS:
            errors.append(f"feature role {role_name} must resolve to one Feature area")
        if scope == "project" and "area" in role:
            errors.append(f"project role {role_name} must not declare a Feature area")
        path_fields = [field for field in ("path", "path_pattern") if field in role]
        if len(path_fields) != 1:
            errors.append(f"role {role_name} must declare exactly one path or path_pattern")
        else:
            path_value = role[path_fields[0]]
            errors.extend(_safe_relative_path(path_value, f"role {role_name}.{path_fields[0]}"))
            full_path = f"{role.get('area')}/{path_value}" if scope == "feature" else str(path_value)
            if full_path in resolved_paths:
                errors.append(f"roles {resolved_paths[full_path]} and {role_name} overlap at {full_path}")
            resolved_paths[full_path] = role_name
        placeholders = set(re.findall(r"\{([a-z_]+)\}", str(role.get("path_pattern", ""))))
        bindings = role.get("placeholder_bindings", {})
        if placeholders != set(bindings) if isinstance(bindings, dict) else True:
            errors.append(f"role {role_name} placeholder bindings do not match its path pattern")
        contract = role.get("contract")
        guide = role.get("guide")
        if contract not in contracts:
            errors.append(f"role {role_name} references unknown contract {contract!r}")
        else:
            used_contracts.add(contract)
        if guide != role_name or guide not in guides:
            errors.append(f"role {role_name} must resolve to its same-name File Guide entry")
        producer = role.get("producer")
        if not isinstance(producer, dict) or set(producer) != {"kind", "source"}:
            errors.append(f"role {role_name} producer must contain exactly kind and source")
        elif producer.get("kind") not in {"template", "programmatic"}:
            errors.append(f"role {role_name} has unknown producer kind {producer.get('kind')!r}")
        elif producer.get("kind") == "template":
            rewrite_producers[role_name] = producer.get("source")

    for role_name, guide in guides.items():
        if not isinstance(guide, dict) or set(guide) != GUIDE_KEYS:
            errors.append(f"File Guide {role_name} must contain exactly purpose and ai_use")
        elif not all(isinstance(guide[key], str) and guide[key].strip() for key in GUIDE_KEYS):
            errors.append(f"File Guide {role_name} values must be non-empty strings")
    unused_contracts = sorted(set(contracts) - used_contracts)
    if unused_contracts:
        errors.append(f"unused File Contracts: {', '.join(unused_contracts)}")

    disposition_enum = migration.get("disposition_enum")
    dispositions = migration.get("template_dispositions")
    expected_enum = {"rewrite", "merge_replace", "render_none", "retire", "external_current"}
    if set(disposition_enum or []) != expected_enum:
        errors.append("template disposition enum is not the confirmed closed set")
    if not isinstance(dispositions, list):
        errors.append("template_dispositions must be an array")
        dispositions = []
    sources: list[str] = []
    rewritten_roles: dict[str, str] = {}
    for index, row in enumerate(dispositions):
        if not isinstance(row, dict) or set(row) != DISPOSITION_KEYS:
            errors.append(f"template disposition row {index} must contain exactly source, disposition, target_role")
            continue
        source = row.get("source")
        disposition = row.get("disposition")
        target_role = row.get("target_role")
        sources.append(source)
        if disposition not in expected_enum:
            errors.append(f"template {source!r} has unknown disposition {disposition!r}")
        if target_role is not None and target_role not in roles:
            errors.append(f"template {source!r} targets unknown role {target_role!r}")
        if disposition in {"retire", "render_none"} and target_role is not None:
            errors.append(f"template {source!r} disposition {disposition} must not target a persisted role")
        if disposition in {"rewrite", "merge_replace", "external_current"} and target_role is None:
            errors.append(f"template {source!r} disposition {disposition} requires a target role")
        if disposition == "rewrite" and isinstance(target_role, str):
            if target_role in rewritten_roles:
                errors.append(f"role {target_role} has multiple rewrite sources")
            rewritten_roles[target_role] = source
    if len(dispositions) != 43:
        errors.append(f"expected 43 template dispositions, found {len(dispositions)}")
    if len(sources) != len(set(sources)):
        errors.append("template disposition sources must be unique")
    actual_sources = _template_inventory()
    if set(sources) != actual_sources:
        errors.append(
            "template disposition inventory mismatch; "
            f"missing={sorted(actual_sources - set(sources))}, extra={sorted(set(sources) - actual_sources)}"
        )
    for role_name, source in rewritten_roles.items():
        if rewrite_producers.get(role_name) != source:
            errors.append(
                f"rewrite source {source!r} for {role_name} does not match its Package Schema producer"
            )

    if set(classes) != EXPECTED_ID_CLASSES:
        errors.append("ID Schema must define exactly the five Current classes plus QUESTION and DECISION")
    if _contains_physical_path_key(id_schema):
        errors.append("ID Schema must refer to roles and must not contain physical path keys")
    counters = set(id_schema.get("allocation", {}).get("counters", []))
    if counters != {"REQ", "BDD", "DESIGN", "TEST", "TASK", "DECISION"}:
        errors.append("ID Schema allocation counters must be the closed six-counter set")
    indexed_classes: set[str] = set()
    for class_name, definition in classes.items():
        if not isinstance(definition, dict):
            errors.append(f"ID class {class_name} must be an object")
            continue
        role = definition.get("definition_role")
        if role not in roles:
            errors.append(f"ID class {class_name} references unknown definition role {role!r}")
        pattern = definition.get("id_pattern")
        try:
            re.compile(pattern)
        except (TypeError, re.error):
            errors.append(f"ID class {class_name} has invalid id_pattern")
        if definition.get("allocation_counter") not in counters:
            errors.append(f"ID class {class_name} references an unknown allocation counter")
        if definition.get("indexed"):
            indexed_classes.add(class_name)
    if indexed_classes != EXPECTED_CURRENT_CLASSES:
        errors.append("only the five Current ID classes may be indexed")
    for index, relationship in enumerate(id_schema.get("relationships", [])):
        if not isinstance(relationship, dict):
            errors.append(f"relationship {index} must be an object")
            continue
        endpoints = {relationship.get("from_class"), *relationship.get("to_classes", [])}
        unknown = endpoints - set(classes)
        if unknown:
            errors.append(f"relationship {index} references unknown classes: {sorted(unknown)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--definition-root",
        type=Path,
        default=DEFAULT_DEFINITION_ROOT,
        help="Directory containing the four definition-plane files.",
    )
    args = parser.parse_args()
    errors = validate_definition_plane(args.definition_root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    package = _load_yaml(args.definition_root / "package-schema.yaml")
    print(
        f"Validated {len(package['roles'])} file roles and "
        f"{len(package['repository_migration']['template_dispositions'])} template dispositions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
