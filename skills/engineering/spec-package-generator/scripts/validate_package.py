#!/usr/bin/env python3
"""Validate one Feature Package against the bundled executable catalogs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from validate_definitions import validate_definition_plane


DEFINITION_ROOT = Path(__file__).resolve().parents[1] / "references"


def _finding(
    code: str,
    path: str | None,
    message: str,
    classification: str = "violation",
) -> dict[str, Any]:
    return {
        "code": code,
        "classification": classification,
        "location": {"path": path} if path is not None else None,
        "message": message,
    }


def _result(findings: list[dict[str, Any]]) -> dict[str, Any]:
    findings.sort(
        key=lambda item: (
            (item["location"] or {}).get("path", ""),
            item["code"],
            item["message"],
        )
    )
    result = (
        "ERROR"
        if any(item["classification"] == "system_error" for item in findings)
        else "INVALID"
        if findings
        else "VALID"
    )
    return {"result": result, "findings": findings}


def _load_catalogs(definition_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    package = yaml.safe_load((definition_root / "package-schema.yaml").read_text(encoding="utf-8"))
    contracts = json.loads((definition_root / "file-contracts.json").read_text(encoding="utf-8"))
    id_schema = yaml.safe_load((definition_root / "id-schema.yaml").read_text(encoding="utf-8"))
    return package, contracts, id_schema


def _dynamic_pattern(area: str, pattern: str, bindings: dict[str, str], id_schema: dict[str, Any]) -> re.Pattern[str]:
    class_patterns = {
        definition["prefix"]: definition["id_pattern"].removeprefix("^").removesuffix("$")
        for definition in id_schema["classes"].values()
    }
    expression = re.escape(f"{area}/{pattern}")
    for placeholder, binding in bindings.items():
        bound_pattern = class_patterns.get(binding, r"[^/]+")
        expression = expression.replace(re.escape("{" + placeholder + "}"), f"(?P<{placeholder}>{bound_pattern})")
    return re.compile(f"^{expression}$")


def _is_reparse_point(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        return path.is_symlink()
    return bool(attributes & getattr(os.stat_result, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)) or path.is_symlink()


def _inventory(
    root: Path,
    package: dict[str, Any],
    id_schema: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    classified: list[dict[str, Any]] = []
    roles = {
        name: role for name, role in package["roles"].items() if role["scope"] == "feature"
    }
    fixed: dict[str, tuple[str, dict[str, Any]]] = {}
    dynamic: list[tuple[str, dict[str, Any], re.Pattern[str]]] = []
    leaf_names: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    allowed_directories = {area["path"] for area in package["package"]["areas"].values()}
    for name, role in roles.items():
        area = package["package"]["areas"][role["area"]]["path"]
        if "path" in role:
            relative = f"{area}/{role['path']}"
            fixed[relative] = (name, role)
            leaf_names.setdefault(Path(role["path"]).name, []).append((name, role))
            parts = Path(relative).parts[:-1]
        else:
            relative = f"{area}/{role['path_pattern']}"
            dynamic.append(
                (
                    name,
                    role,
                    _dynamic_pattern(area, role["path_pattern"], role.get("placeholder_bindings", {}), id_schema),
                )
            )
            leaf_names.setdefault(Path(role["path_pattern"]).name, []).append((name, role))
            parts = Path(relative).parts[:-1]
        for end in range(1, len(parts) + 1):
            allowed_directories.add(Path(*parts[:end]).as_posix())

    observed_roles: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if _is_reparse_point(path):
            findings.append(
                _finding(
                    "PKG_FORBIDDEN_LINK",
                    relative,
                    "Links and reparse points are forbidden.",
                    "system_error",
                )
            )
            continue
        if path.is_dir():
            if relative not in allowed_directories or not any(path.iterdir()):
                findings.append(_finding("PKG_ORPHAN_DIRECTORY", relative, "Directory is not required by a present managed file."))
            if len(Path(relative).parts) > package["package"]["root_policy"]["max_directory_depth"]:
                findings.append(_finding("PKG_DEPTH_EXCEEDED", relative, "Directory exceeds the maximum managed depth."))
            continue
        matches: list[tuple[str, dict[str, Any], dict[str, str]]] = []
        if relative in fixed:
            name, role = fixed[relative]
            matches.append((name, role, {}))
        for name, role, pattern in dynamic:
            match = pattern.fullmatch(relative)
            if match:
                matches.append((name, role, match.groupdict()))
        if len(matches) > 1:
            findings.append(_finding("PKG_AMBIGUOUS_ROLE", relative, "Path matches multiple declared roles."))
            continue
        if not matches:
            case_match = next((declared for declared in fixed if declared.casefold() == relative.casefold()), None)
            if case_match:
                findings.append(_finding("PKG_CASE_MISMATCH", relative, f"Canonical path is {case_match}."))
                continue
            dynamic_case_match = next(
                (
                    (name, role)
                    for name, role, pattern in dynamic
                    if re.fullmatch(pattern.pattern, relative, flags=re.IGNORECASE)
                ),
                None,
            )
            if dynamic_case_match:
                findings.append(_finding("PKG_CASE_MISMATCH", relative, f"Dynamic role {dynamic_case_match[0]} requires canonical casing."))
                continue
            recognized = leaf_names.get(path.name, [])
            if recognized:
                findings.append(_finding("PKG_WRONG_PATH", relative, "Recognized managed filename is outside its canonical path."))
            elif path.parent.relative_to(root).as_posix().casefold() == "current/manifests" and path.suffix.casefold() == ".yaml":
                findings.append(_finding("PKG_INVALID_DYNAMIC_NAME", relative, "Manifest filename does not bind a valid TASK ID."))
            else:
                findings.append(_finding("PKG_UNKNOWN_PATH", relative, "Path is not declared by the Package Schema."))
            continue
        name, role, bindings = matches[0]
        observed_roles.setdefault(name, []).append(relative)
        classified.append({"path": path, "relative": relative, "role_name": name, "role": role, "bindings": bindings})

    for role_name, paths in observed_roles.items():
        role = roles[role_name]
        if role["multiplicity"] in {"singleton", "singleton_stream"} and len(paths) > 1:
            for relative in paths:
                findings.append(_finding("PKG_DUPLICATE_ROLE", relative, f"Role {role_name} appears more than once."))
    return classified, findings


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _parse_files(
    classified: list[dict[str, Any]],
    contracts_doc: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    parsed: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    contracts = contracts_doc["contracts"]
    for item in classified:
        relative = item["relative"]
        contract = contracts[item["role"]["contract"]]
        file_format = contract["format"]
        try:
            text = item["path"].read_text(encoding="utf-8")
            if file_format == "yaml":
                documents = list(yaml.load_all(text, Loader=_UniqueKeyLoader))
                parsed[relative] = documents if contract.get("container") == "records" else (documents[0] if len(documents) == 1 else documents)
            elif file_format == "json":
                parsed[relative] = json.loads(text, object_pairs_hook=_json_object)
            else:
                parsed[relative] = text
        except OSError as error:
            findings.append(
                _finding(
                    "PKG_ROOT_UNREADABLE",
                    relative,
                    f"Managed file could not be read safely: {error}",
                    "system_error",
                )
            )
        except (UnicodeError, yaml.YAMLError, json.JSONDecodeError, ValueError) as error:
            findings.append(_finding("PKG_WRONG_FORMAT", relative, f"Declared {file_format} parser rejected the file: {error}"))
    return parsed, findings


def _schema_errors(value: Any, schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    allowed_types = expected_type if isinstance(expected_type, list) else [expected_type] if expected_type else []
    type_matches = False
    for kind in allowed_types:
        if kind == "null" and value is None:
            type_matches = True
        elif kind == "object" and isinstance(value, dict):
            type_matches = True
        elif kind == "array" and isinstance(value, list):
            type_matches = True
        elif kind == "string" and isinstance(value, str):
            type_matches = True
        elif kind == "integer" and isinstance(value, int) and not isinstance(value, bool):
            type_matches = True
    if allowed_types and not type_matches:
        return [f"{label} must have type {allowed_types}"]
    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = sorted(required - set(value))
        if missing:
            errors.append(f"{label} missing fields {missing}")
        if schema.get("additional_properties") is False:
            unknown = sorted(set(value) - set(schema.get("properties", {})))
            if unknown:
                errors.append(f"{label} has unknown fields {unknown}")
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                errors.extend(_schema_errors(value[key], child_schema, f"{label}.{key}"))
    if isinstance(value, list):
        if len(value) < schema.get("min_items", 0):
            errors.append(f"{label} has too few items")
        if schema.get("unique"):
            encoded = [json.dumps(item, sort_keys=True) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{label} items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                errors.extend(_schema_errors(child, item_schema, f"{label}[{index}]"))
    if isinstance(value, str):
        if len(value) < schema.get("min_length", 0):
            errors.append(f"{label} is too short")
        maximum = schema.get("max_length")
        if maximum is not None and len(value) > maximum:
            errors.append(f"{label} is too long")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label} must be one of {schema['enum']}")
    return errors


def _id_class_for(raw: Any, id_schema: dict[str, Any]) -> str | None:
    if not isinstance(raw, str):
        return None
    for class_name, definition in id_schema["classes"].items():
        if re.fullmatch(definition["id_pattern"], raw):
            return class_name
    return None


def _validate_current_records(
    classified: list[dict[str, Any]],
    parsed: dict[str, Any],
    contracts_doc: dict[str, Any],
    id_schema: dict[str, Any],
) -> tuple[set[str], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    definitions: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    index_ids: list[str] = []
    index_present = False
    contracts = contracts_doc["contracts"]
    for item in classified:
        relative = item["relative"]
        if relative not in parsed:
            continue
        role_name = item["role_name"]
        contract = contracts[item["role"]["contract"]]
        if role_name == "current_id_index":
            index_present = True
            value = parsed[relative]
            if not isinstance(value, dict) or set(value) != {"ids"} or not isinstance(value.get("ids"), list):
                findings.append(_finding("ID_ACTIVE_SET_MISMATCH", relative, "ID Index must contain only an ids array."))
                continue
            raw_ids = value["ids"]
            if any(_id_class_for(raw, id_schema) not in {"REQUIREMENT", "BDD", "DESIGN", "TEST", "TASK"} for raw in raw_ids):
                findings.append(_finding("ID_ACTIVE_SET_MISMATCH", relative, "ID Index contains an invalid Current ID."))
            if len(raw_ids) != len(set(raw_ids)) or raw_ids != sorted(raw_ids):
                findings.append(_finding("ID_ACTIVE_SET_MISMATCH", relative, "ID Index IDs must be unique and canonically sorted."))
            index_ids = [raw for raw in raw_ids if isinstance(raw, str)]
            continue
        expected_class = contract.get("record_class")
        if expected_class not in {"REQUIREMENT", "BDD", "DESIGN", "TEST", "TASK"}:
            continue
        records = parsed[relative]
        if not isinstance(records, list):
            records = [records]
        for document_index, record in enumerate(records):
            location = f"{relative}#doc={document_index + 1}"
            if not isinstance(record, dict) or set(record) != {"id", "content"}:
                findings.append(_finding("ID_INVALID_CONTENT", location, "Record must contain exactly id and content."))
                continue
            record_id = record["id"]
            actual_class = _id_class_for(record_id, id_schema)
            if actual_class is None:
                findings.append(_finding("ID_INVALID_FORMAT", location, f"Record ID {record_id!r} has no declared format."))
                continue
            if actual_class != expected_class:
                findings.append(_finding("ID_WRONG_OWNER", location, f"{record_id} belongs to {actual_class}, not {expected_class}."))
                continue
            content_errors = _schema_errors(
                record["content"],
                id_schema["classes"][expected_class]["content_schema"],
                f"{record_id}.content",
            )
            for error in content_errors:
                findings.append(_finding("ID_INVALID_CONTENT", location, error))
            if record_id in definitions:
                duplicate_ids.add(record_id)
            else:
                definitions[record_id] = {
                    "class": expected_class,
                    "content": record["content"],
                    "path": relative,
                }
    for record_id in sorted(duplicate_ids):
        findings.append(_finding("ID_DUPLICATE_DEFINITION", definitions[record_id]["path"], f"{record_id} has multiple definitions."))
    active = set(index_ids) if index_present else set()
    discovered = set(definitions)
    if active != discovered:
        findings.append(
            _finding(
                "ID_ACTIVE_SET_MISMATCH",
                "current/id-index.yaml" if index_present else None,
                f"Active IDs and definitions differ; missing definitions={sorted(active - discovered)}, unindexed definitions={sorted(discovered - active)}.",
            )
        )
    return active, definitions, findings


def _validate_auxiliary_records(
    classified: list[dict[str, Any]],
    parsed: dict[str, Any],
    contracts_doc: dict[str, Any],
    id_schema: dict[str, Any],
) -> tuple[list[tuple[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    observed: list[tuple[str, str]] = []
    contracts = contracts_doc["contracts"]
    for item in classified:
        relative = item["relative"]
        if relative not in parsed:
            continue
        contract = contracts[item["role"]["contract"]]
        expected_class = contract.get("record_class")
        if expected_class not in {"QUESTION", "DECISION"}:
            continue
        value = parsed[relative]
        records = value if contract.get("container") == "records" else [value]
        if not isinstance(records, list):
            records = [records]
        if "single_record" in contract.get("checks", []) and len(records) != 1:
            findings.append(_finding("ID_INVALID_CONTENT", relative, "Role must contain exactly one record."))
        seen: set[str] = set()
        for index, record in enumerate(records):
            location = f"{relative}#doc={index + 1}"
            if not isinstance(record, dict) or set(record) != {"id", "content"}:
                findings.append(_finding("ID_INVALID_CONTENT", location, "Record must contain exactly id and content."))
                continue
            record_id = record["id"]
            actual_class = _id_class_for(record_id, id_schema)
            if actual_class is None:
                findings.append(_finding("ID_INVALID_FORMAT", location, f"Record ID {record_id!r} has no declared format."))
                continue
            if actual_class != expected_class:
                findings.append(_finding("ID_WRONG_OWNER", location, f"{record_id} belongs to {actual_class}, not {expected_class}."))
                continue
            for error in _schema_errors(
                record["content"],
                id_schema["classes"][expected_class]["content_schema"],
                f"{record_id}.content",
            ):
                findings.append(_finding("ID_INVALID_CONTENT", location, error))
            if record_id in seen:
                findings.append(_finding("ID_DUPLICATE_DEFINITION", location, f"{record_id} appears more than once in this role."))
            seen.add(record_id)
            observed.append((record_id, relative))
    return observed, findings


def _walk_string_positions(value: Any, pointer: tuple[Any, ...] = ()) -> list[tuple[str, tuple[Any, ...]]]:
    if isinstance(value, str):
        return [(value, pointer)]
    if isinstance(value, dict):
        result: list[tuple[str, tuple[Any, ...]]] = []
        for key, child in value.items():
            if isinstance(key, str):
                result.append((key, pointer + ("__key__", key)))
            result.extend(_walk_string_positions(child, pointer + (key,)))
        return result
    if isinstance(value, list):
        result: list[tuple[str, tuple[Any, ...]]] = []
        for index, child in enumerate(value):
            result.extend(_walk_string_positions(child, pointer + (index,)))
        return result
    return []


def _id_token_patterns(id_schema: dict[str, Any]) -> tuple[re.Pattern[str], re.Pattern[str]]:
    current_parts = [
        definition["id_pattern"].removeprefix("^").removesuffix("$")
        for definition in id_schema["classes"].values()
        if definition.get("indexed")
    ]
    current = re.compile(r"(?<![A-Z0-9-])(?:" + "|".join(current_parts) + r")(?![A-Z0-9-])")
    id_like = re.compile(r"(?<![A-Z0-9-])[A-Z][A-Z0-9-]*-[0-9]{3}(?![A-Z0-9-])")
    return current, id_like


def _validate_ids_and_graph(
    classified: list[dict[str, Any]],
    parsed: dict[str, Any],
    contracts_doc: dict[str, Any],
    id_schema: dict[str, Any],
    active: set[str],
    definitions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    contracts = contracts_doc["contracts"]
    current_token, id_like_token = _id_token_patterns(id_schema)
    legacy_patterns = [
        (entry["name"], re.compile(entry["pattern"]))
        for entry in id_schema["rejected_legacy_patterns"]
    ]
    relationships = {
        (row["from_class"], row["field"]): row for row in id_schema["relationships"]
    }
    task_edges: dict[str, list[str]] = {}
    for record_id, definition in definitions.items():
        class_name = definition["class"]
        content = definition["content"]
        if isinstance(content, dict):
            for (from_class, field), relationship in relationships.items():
                if from_class != class_name or field not in content or not isinstance(content[field], list):
                    continue
                references = content[field]
                for reference in references:
                    target_class = _id_class_for(reference, id_schema)
                    if target_class not in set(relationship["to_classes"]):
                        findings.append(
                            _finding(
                                "ID_INVALID_REFERENCE_TARGET",
                                definition["path"],
                                f"{record_id}.{field} contains invalid target {reference!r}.",
                            )
                        )
                    elif reference not in active or reference not in definitions:
                        findings.append(
                            _finding(
                                "ID_UNDEFINED_REFERENCE",
                                definition["path"],
                                f"{record_id}.{field} references undefined {reference}.",
                            )
                        )
                if class_name == "TASK" and field == "depends_on":
                    task_edges[record_id] = [reference for reference in references if isinstance(reference, str)]
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> bool:
        if task_id in visiting:
            return True
        if task_id in visited:
            return False
        visiting.add(task_id)
        cyclic = any(visit(child) for child in task_edges.get(task_id, []) if child in task_edges)
        visiting.remove(task_id)
        visited.add(task_id)
        return cyclic

    if any(visit(task_id) for task_id in sorted(task_edges)):
        findings.append(_finding("ID_DEPENDENCY_CYCLE", "current/records/tasks.yaml", "Task dependency graph contains a cycle."))

    for item in classified:
        relative = item["relative"]
        if relative not in parsed:
            continue
        role_name = item["role_name"]
        contract = contracts[item["role"]["contract"]]
        scan_mode = contract.get("id_scan", "none")
        if role_name == "task_manifest":
            value = parsed[relative]
            if isinstance(value, dict):
                task_id = value.get("task_id")
                bound_id = item["bindings"].get("task_id")
                if task_id != bound_id or task_id not in active or _id_class_for(task_id, id_schema) != "TASK":
                    findings.append(_finding("PKG_INVALID_DYNAMIC_NAME", relative, "Manifest filename, task_id, and active TASK binding must agree."))
                execution_inputs = value.get("execution_input_ids", [])
                if not isinstance(execution_inputs, list):
                    execution_inputs = []
                for reference in execution_inputs:
                    if not isinstance(reference, str) or reference not in active:
                        findings.append(_finding("ID_UNDEFINED_REFERENCE", relative, f"Manifest references undefined {reference!r}."))
        if scan_mode not in {"all_string_scalars", "decision_ids_only"}:
            continue
        string_positions = _walk_string_positions(parsed[relative])
        seen: set[tuple[str, str]] = set()
        expected_class = contract.get("record_class")
        relationship_fields = {
            row["field"] for row in id_schema["relationships"] if row["from_class"] == expected_class
        }
        for scalar, pointer in string_positions:
            for legacy_name, pattern in legacy_patterns:
                for match in pattern.finditer(scalar):
                    key = ("ID_LEGACY_PATTERN", match.group(0))
                    if key not in seen:
                        findings.append(_finding("ID_LEGACY_PATTERN", relative, f"Rejected legacy {legacy_name} token {match.group(0)} remains."))
                        seen.add(key)
            current_matches = list(current_token.finditer(scalar))
            if role_name == "decision_archive" and current_matches:
                for match in current_matches:
                    key = ("ID_REMOVED_RESIDUE", match.group(0))
                    if key not in seen:
                        findings.append(_finding("ID_REMOVED_RESIDUE", relative, f"Decision history must not contain Specification token {match.group(0)}."))
                        seen.add(key)
                continue
            for match in current_matches:
                token = match.group(0)
                if token not in active and ("ID_REMOVED_RESIDUE", token) not in seen:
                    findings.append(_finding("ID_REMOVED_RESIDUE", relative, f"Inactive or removed ID {token} remains in managed Current."))
                    seen.add(("ID_REMOVED_RESIDUE", token))
                declared_position = False
                if role_name == "current_id_index":
                    declared_position = len(pointer) == 2 and pointer[0] == "ids" and isinstance(pointer[1], int)
                elif role_name == "task_manifest":
                    declared_position = pointer == ("task_id",) or (
                        len(pointer) == 2
                        and pointer[0] == "execution_input_ids"
                        and isinstance(pointer[1], int)
                    )
                elif expected_class in {"REQUIREMENT", "BDD", "DESIGN", "TEST", "TASK"}:
                    declared_position = (
                        len(pointer) == 2
                        and isinstance(pointer[0], int)
                        and pointer[1] == "id"
                    ) or (
                        len(pointer) == 4
                        and isinstance(pointer[0], int)
                        and pointer[1] == "content"
                        and pointer[2] in relationship_fields
                        and isinstance(pointer[3], int)
                    )
                if scalar != token or not declared_position:
                    key = ("ID_UNDECLARED_REFERENCE_POSITION", token)
                    if key not in seen:
                        findings.append(_finding("ID_UNDECLARED_REFERENCE_POSITION", relative, f"ID token {token} occurs outside a declared ID field."))
                        seen.add(key)
            for match in id_like_token.finditer(scalar):
                token = match.group(0)
                if _id_class_for(token, id_schema) is None and not any(pattern.fullmatch(token) for _, pattern in legacy_patterns):
                    key = ("ID_INVALID_FORMAT", token)
                    if key not in seen:
                        findings.append(_finding("ID_INVALID_FORMAT", relative, f"Unknown ID token {token}."))
                        seen.add(key)
        if "no_yaml_comments" in contract.get("checks", []):
            text = item["path"].read_text(encoding="utf-8")
            if any(re.match(r"^\s*#", line) or re.search(r"\s+#", line) for line in text.splitlines()):
                findings.append(_finding("PKG_WRONG_FORMAT", relative, "YAML comments are forbidden in scanned managed content."))
    return findings


def _validate_closed_shape(value: Any, shape: dict[str, Any], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    required = set(shape.get("required", []))
    properties = shape.get("properties", {})
    allowed = required | set(properties)
    errors: list[str] = []
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        errors.append(f"{label} missing fields {missing}")
    if unknown:
        errors.append(f"{label} has unknown fields {unknown}")
    for key, rule in properties.items():
        if key not in value or not isinstance(rule, dict):
            continue
        child = value[key]
        if "enum" in rule and child not in rule["enum"]:
            errors.append(f"{label}.{key} must be one of {rule['enum']}")
        raw_types = rule.get("type")
        if raw_types is not None:
            types = raw_types if isinstance(raw_types, list) else [raw_types]
            matches = any(
                (kind == "string" and isinstance(child, str))
                or (kind == "null" and child is None)
                or (kind == "array" and isinstance(child, list))
                or (kind == "integer" and isinstance(child, int) and not isinstance(child, bool))
                or (kind == "object" and isinstance(child, dict))
                for kind in types
            )
            if not matches:
                errors.append(f"{label}.{key} must have type {types}")
        if rule.get("unique") and isinstance(child, list) and len(child) != len(set(child)):
            errors.append(f"{label}.{key} must contain unique values")
        if isinstance(child, str) and len(child) < rule.get("min_length", 0):
            errors.append(f"{label}.{key} is too short")
        if "required_keys" in rule:
            if not isinstance(child, dict) or set(child) != set(rule["required_keys"]):
                errors.append(f"{label}.{key} must contain exactly keys {rule['required_keys']}")
            elif "integer_range" in rule:
                low, high = rule["integer_range"]
                if any(not isinstance(item, int) or isinstance(item, bool) or not low <= item <= high for item in child.values()):
                    errors.append(f"{label}.{key} values must be integers in [{low}, {high}]")
    return errors


def _validate_role_contracts(
    classified: list[dict[str, Any]],
    parsed: dict[str, Any],
    contracts_doc: dict[str, Any],
    id_schema: dict[str, Any],
    active: set[str],
    auxiliary_ids: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    contracts = contracts_doc["contracts"]
    current_tasks = {record_id for record_id in active if _id_class_for(record_id, id_schema) == "TASK"}
    counters: dict[str, int] | None = None
    allocation_path: str | None = None
    for item in classified:
        relative = item["relative"]
        if relative not in parsed:
            continue
        role_name = item["role_name"]
        contract = contracts[item["role"]["contract"]]
        value = parsed[relative]
        shape = contract.get("closed_shape")
        if isinstance(shape, dict):
            shape_errors = _validate_closed_shape(value, shape, role_name)
            code = (
                "STATE_INVALID_COMBINATION"
                if role_name in {"workflow_state", "task_state"}
                else "ID_ALLOCATION_INVALID"
                if role_name == "id_allocation_state"
                else "PLAN_INVALID_SHAPE"
                if role_name == "candidate_application_plan"
                else "PKG_WRONG_FORMAT"
            )
            for error in shape_errors:
                findings.append(_finding(code, relative, error))
        if role_name == "task_state" and isinstance(value, dict) and isinstance(value.get("tasks"), dict):
            tasks = value["tasks"]
            if set(tasks) != current_tasks:
                findings.append(_finding("STATE_INVALID_COMBINATION", relative, "Task State keys must exactly equal active TASK IDs."))
            lifecycle = set(contract.get("lifecycle_enum", []))
            for task_id, state in tasks.items():
                if state not in lifecycle:
                    findings.append(_finding("STATE_INVALID_COMBINATION", relative, f"{task_id} has illegal lifecycle {state!r}."))
        if role_name == "task_manifest" and isinstance(value, dict):
            task_id = value.get("task_id")
            if _id_class_for(task_id, id_schema) != "TASK":
                findings.append(_finding("PKG_WRONG_FORMAT", relative, "task_id must be a declared TASK-format ID."))
            execution_inputs = value.get("execution_input_ids")
            if not isinstance(execution_inputs, list) or any(
                _id_class_for(reference, id_schema) not in {"REQUIREMENT", "BDD", "DESIGN", "TEST", "TASK"}
                for reference in execution_inputs
            ):
                findings.append(_finding("PKG_WRONG_FORMAT", relative, "execution_input_ids must be an array of Current IDs."))
        if role_name == "id_allocation_state" and isinstance(value, dict):
            raw = value.get("highest_issued")
            if isinstance(raw, dict) and set(raw) == set(id_schema["allocation"]["counters"]):
                if all(isinstance(number, int) and not isinstance(number, bool) for number in raw.values()):
                    counters = raw
                    allocation_path = relative
    if counters is not None:
        allocated_ids = [(active_id, allocation_path) for active_id in sorted(active)] + auxiliary_ids
        for active_id, source_path in allocated_ids:
            class_name = _id_class_for(active_id, id_schema)
            if class_name is None:
                continue
            counter = id_schema["classes"][class_name]["allocation_counter"]
            suffix = int(active_id.rsplit("-", 1)[1])
            if suffix > counters[counter]:
                findings.append(_finding("ID_ALLOCATION_INVALID", source_path or allocation_path, f"{active_id} exceeds {counter} high-water {counters[counter]}."))
    return findings


def validate(feature_root: Path, definition_root: Path = DEFINITION_ROOT) -> dict[str, Any]:
    """Return the deterministic legality result for one Feature Package."""

    if feature_root.exists() and _is_reparse_point(feature_root):
        return {
            "result": "ERROR",
            "findings": [
                {
                    "code": "PKG_FORBIDDEN_LINK",
                    "classification": "system_error",
                    "location": None,
                    "message": "Feature root may not be a link or reparse point.",
                }
            ],
        }
    root = feature_root.resolve()
    if not root.is_dir():
        return {
            "result": "ERROR",
            "findings": [
                {
                    "code": "PKG_ROOT_UNREADABLE",
                    "classification": "system_error",
                    "location": None,
                    "message": "Feature root is not a readable directory.",
                }
            ],
        }
    definition_errors = validate_definition_plane(definition_root)
    if definition_errors:
        return {
            "result": "ERROR",
            "findings": [
                {
                    "code": "VALIDATOR_DEFINITION_ERROR",
                    "classification": "system_error",
                    "location": None,
                    "message": "; ".join(definition_errors),
                }
            ],
        }
    package, contracts, id_schema = _load_catalogs(definition_root)
    classified, findings = _inventory(root, package, id_schema)
    parsed, parse_findings = _parse_files(classified, contracts)
    findings.extend(parse_findings)
    active, definitions, record_findings = _validate_current_records(
        classified, parsed, contracts, id_schema
    )
    findings.extend(record_findings)
    auxiliary_ids, auxiliary_findings = _validate_auxiliary_records(
        classified, parsed, contracts, id_schema
    )
    findings.extend(auxiliary_findings)
    findings.extend(
        _validate_ids_and_graph(
            classified, parsed, contracts, id_schema, active, definitions
        )
    )
    findings.extend(
        _validate_role_contracts(
            classified, parsed, contracts, id_schema, active, auxiliary_ids
        )
    )
    return _result(findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feature_root", type=Path)
    parser.add_argument("--definition-root", type=Path, default=DEFINITION_ROOT)
    args = parser.parse_args()
    payload = validate(args.feature_root, args.definition_root.resolve())
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return {"VALID": 0, "INVALID": 1, "ERROR": 2}[payload["result"]]


if __name__ == "__main__":
    raise SystemExit(main())
