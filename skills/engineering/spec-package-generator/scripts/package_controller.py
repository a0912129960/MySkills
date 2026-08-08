#!/usr/bin/env python3
"""Control and resume one specification Feature Package transaction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

import yaml

from validate_package import (
    DEFINITION_ROOT,
    _inventory,
    _load_catalogs,
    _parse_files,
    validate as validate_package,
)


COUNTERS = ("REQ", "BDD", "DESIGN", "TEST", "TASK", "DECISION")
CURRENT_ID_TOKEN = re.compile(
    r"(?<![A-Z0-9-])(?:REQ|BDD|DESIGN|TEST|TASK)-[0-9]{3}(?![A-Z0-9-])"
)
PHASES = {
    "discussing",
    "planning",
    "applying_current",
    "validating",
    "finalizing",
    "pass",
}
NEW_ID_HANDLE = re.compile(
    r"^@new/(?P<counter>REQ|BDD|DESIGN|TEST|TASK)/(?P<label>[a-z][a-z0-9-]{0,63})$"
)


class ControllerError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_yaml(path: Path, value: Any) -> None:
    _atomic_write_text(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def _canonical_fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _current_fingerprint(root: Path) -> str:
    package, contracts, id_schema = _load_catalogs(DEFINITION_ROOT)
    classified, inventory_findings = _inventory(root, package, id_schema)
    parsed, parse_findings = _parse_files(classified, contracts)
    if inventory_findings or parse_findings:
        raise ControllerError("PLAN_UNEXPECTED_CURRENT", "Current cannot be fingerprinted from an illegal package inventory.")
    content: list[dict[str, Any]] = []
    for item in classified:
        if (
            item["role"].get("area") == "current"
            and item["role"].get("authority") in {"normative", "routing"}
            and item["relative"] in parsed
        ):
            content.append({"path": item["relative"], "value": parsed[item["relative"]]})
    content.sort(key=lambda row: row["path"])
    return _canonical_fingerprint(content)


def _load_plan(path: Path) -> dict[str, Any]:
    value = _read_yaml(path)
    if not isinstance(value, dict) or set(value) != {
        "basis",
        "allocation_baseline",
        "expected_final_current_fingerprint",
        "operations",
    }:
        raise ControllerError("PLAN_INVALID_SHAPE", "Application Plan has an invalid top-level shape.")
    basis = value["basis"]
    if not isinstance(basis, dict) or set(basis) != {"kind", "id", "fingerprint"}:
        raise ControllerError("PLAN_INVALID_SHAPE", "Question Plan basis is invalid.")
    if basis["kind"] != "question" or not re.fullmatch(r"Q-[0-9]{3}", str(basis["id"])):
        raise ControllerError("PLAN_INVALID_SHAPE", "Question Plan basis identity is invalid.")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(basis["fingerprint"])):
        raise ControllerError("PLAN_INVALID_SHAPE", "Question Plan basis fingerprint is invalid.")
    if not isinstance(value["operations"], list):
        raise ControllerError("PLAN_INVALID_SHAPE", "Plan operations must be an array.")
    baseline = value["allocation_baseline"]
    baseline_counters = set(COUNTERS) - {"DECISION"}
    if (
        not isinstance(baseline, dict)
        or set(baseline) != baseline_counters
        or any(
            not isinstance(number, int)
            or isinstance(number, bool)
            or not 0 <= number <= 999
            for number in baseline.values()
        )
    ):
        raise ControllerError("PLAN_INVALID_SHAPE", "Allocation baseline is invalid.")
    target_keys: list[str] = []
    for operation in value["operations"]:
        if not isinstance(operation, dict) or set(operation) != {"target", "before", "after"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Each operation must have target, before, and after.")
        target = operation["target"]
        if not isinstance(target, dict) or (
            set(target) != {"record_id"} and set(target) != {"file_role"}
        ):
            raise ControllerError("PLAN_INVALID_SHAPE", "Operation target is invalid.")
        if "record_id" in target:
            _record_role(target["record_id"])
        elif target["file_role"] != "current_id_index":
            raise ControllerError("PLAN_INVALID_SHAPE", "Only the Current ID Index fixed target is supported.")
        target_keys.append(_target_key(target))
        before = operation["before"]
        if not isinstance(before, dict) or before.get("state") not in {"present", "absent"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Operation before state is invalid.")
        if before["state"] == "absent" and set(before) != {"state"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Absent before state cannot have a fingerprint.")
        if before["state"] == "present" and (
            set(before) != {"state", "fingerprint"}
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(before["fingerprint"]))
        ):
            raise ControllerError("PLAN_INVALID_SHAPE", "Present before state requires a fingerprint.")
        after = operation["after"]
        if not isinstance(after, dict) or after.get("state") not in {"present", "absent"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Operation after state is invalid.")
        if after["state"] == "absent" and set(after) != {"state"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Absent after state cannot have a payload.")
        if after["state"] == "present" and set(after) != {"state", "payload"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Present after state requires a payload.")
        if "record_id" in target and after["state"] == "present":
            payload = after["payload"]
            if (
                not isinstance(payload, dict)
                or set(payload) != {"id", "content"}
                or payload["id"] != target["record_id"]
            ):
                raise ControllerError("PLAN_INVALID_SHAPE", "Record payload does not match its target.")
    if len(set(target_keys)) != len(target_keys) or target_keys != sorted(target_keys):
        raise ControllerError("PLAN_INVALID_SHAPE", "Plan targets must be unique and canonically ordered.")
    if not re.fullmatch(
        r"sha256:[0-9a-f]{64}",
        str(value["expected_final_current_fingerprint"]),
    ):
        raise ControllerError("PLAN_INVALID_SHAPE", "Expected-final fingerprint is invalid.")
    return value


def _replace_symbols(value: Any, allocations: dict[str, str]) -> Any:
    if isinstance(value, str):
        return allocations.get(value, value)
    if isinstance(value, list):
        return [_replace_symbols(item, allocations) for item in value]
    if isinstance(value, dict):
        return {key: _replace_symbols(child, allocations) for key, child in value.items()}
    return value


def _collect_symbols(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value} if NEW_ID_HANDLE.fullmatch(value) else set()
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_collect_symbols(item))
        return result
    if isinstance(value, dict):
        result = set()
        for child in value.values():
            result.update(_collect_symbols(child))
        return result
    return set()


def _record_role(record_id: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if not isinstance(record_id, str):
        raise ControllerError("PLAN_INVALID_SHAPE", "Record target ID must be a string.")
    package, _contracts, id_schema = _load_catalogs(DEFINITION_ROOT)
    for definition in id_schema["classes"].values():
        if definition.get("indexed") and re.fullmatch(definition["id_pattern"], record_id):
            role_name = definition["definition_role"]
            return role_name, package["roles"][role_name], definition
    raise ControllerError("PLAN_INVALID_SHAPE", f"{record_id!r} is not a Current Record ID.")


def _record_path(root: Path, record_id: str) -> Path:
    _role_name, role, _definition = _record_role(record_id)
    return root / role["area"] / role["path"]


def _read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    if any(not isinstance(record, dict) for record in records):
        raise ControllerError("PLAN_TARGET_CONFLICT", f"Record owner {path.name} is malformed.")
    return records


def _fixed_role_path(root: Path, role_name: str) -> Path:
    package, _contracts, _id_schema = _load_catalogs(DEFINITION_ROOT)
    role = package["roles"].get(role_name)
    if not isinstance(role, dict) or role.get("scope") != "feature" or "path" not in role:
        raise ControllerError("PLAN_INVALID_SHAPE", f"{role_name!r} is not a fixed Feature role.")
    return root / role["area"] / role["path"]


def _target_value(root: Path, target: dict[str, Any]) -> Any | None:
    if set(target) == {"record_id"}:
        record_id = target["record_id"]
        records = _read_records(_record_path(root, record_id))
        matching = [record for record in records if record.get("id") == record_id]
        if len(matching) > 1:
            raise ControllerError("PLAN_TARGET_CONFLICT", f"{record_id} has duplicate definitions.")
        return matching[0] if matching else None
    if set(target) == {"file_role"}:
        path = _fixed_role_path(root, target["file_role"])
        return _read_yaml(path) if path.exists() else None
    raise ControllerError("PLAN_INVALID_SHAPE", "Target must identify one Record or fixed file role.")


def _before_state(value: Any | None) -> dict[str, Any]:
    if value is None:
        return {"state": "absent"}
    return {"state": "present", "fingerprint": _canonical_fingerprint(value)}


def _after_value(after: dict[str, Any]) -> Any | None:
    return after.get("payload") if after.get("state") == "present" else None


def _operation_status(root: Path, operation: dict[str, Any]) -> str:
    current = _target_value(root, operation["target"])
    current_state = _before_state(current)
    after = operation["after"]
    after_state = _before_state(_after_value(after))
    if current_state == after_state:
        return "complete"
    if current_state == operation["before"]:
        return "pending"
    return "conflict"


def _target_key(target: dict[str, Any]) -> str:
    return json.dumps(target, sort_keys=True, separators=(",", ":"))


def _write_records(path: Path, records: list[dict[str, Any]]) -> None:
    if records:
        _atomic_write_text(
            path,
            yaml.safe_dump_all(
                records,
                sort_keys=False,
                explicit_start=True,
                allow_unicode=True,
            ),
        )
    elif path.exists():
        path.unlink()


def _apply_operations(root: Path, operations: list[dict[str, Any]]) -> None:
    record_groups: dict[Path, list[dict[str, Any]]] = {}
    fixed: list[dict[str, Any]] = []
    for operation in operations:
        if "record_id" in operation["target"]:
            path = _record_path(root, operation["target"]["record_id"])
            record_groups.setdefault(path, []).append(operation)
        else:
            fixed.append(operation)
    for path, group in record_groups.items():
        records = _read_records(path)
        by_id = {record["id"]: record for record in records}
        for operation in group:
            record_id = operation["target"]["record_id"]
            after = operation["after"]
            if after["state"] == "absent":
                by_id.pop(record_id, None)
            else:
                by_id[record_id] = after["payload"]
        ordered = sorted(by_id.values(), key=lambda record: record["id"])
        _write_records(path, ordered)
    for operation in fixed:
        path = _fixed_role_path(root, operation["target"]["file_role"])
        after = operation["after"]
        if after["state"] == "absent":
            if path.exists():
                path.unlink()
        else:
            _atomic_write_yaml(path, after["payload"])


def _target_summaries(root: Path, operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"target": operation["target"], "status": _operation_status(root, operation)}
        for operation in sorted(operations, key=lambda row: _target_key(row["target"]))
    ]


def _validate_expected_final(root: Path, plan: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        virtual_root = Path(temporary) / root.name
        shutil.copytree(root, virtual_root)
        _apply_operations(virtual_root, plan["operations"])
        validation = validate_package(virtual_root)
        if validation["result"] != "VALID":
            codes = sorted({finding["code"] for finding in validation["findings"]})
            raise ControllerError("PLAN_INVALID_SHAPE", f"Virtual final Current is invalid: {codes}.")
        if _current_fingerprint(virtual_root) != plan["expected_final_current_fingerprint"]:
            raise ControllerError("PLAN_UNEXPECTED_CURRENT", "Plan expected-final fingerprint is not reproducible.")


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _ensure_allocator(root: Path) -> tuple[Path, dict[str, Any]]:
    path = root / "control" / "id-allocation.yaml"
    if not path.exists():
        value = {"highest_issued": {counter: 0 for counter in COUNTERS}}
        _atomic_write_yaml(path, value)
        return path, value
    value = _read_yaml(path)
    counters = value.get("highest_issued") if isinstance(value, dict) else None
    if (
        not isinstance(counters, dict)
        or set(counters) != set(COUNTERS)
        or any(not isinstance(number, int) or isinstance(number, bool) or not 0 <= number <= 999 for number in counters.values())
    ):
        raise ControllerError("ID_ALLOCATION_INVALID", "ID allocation state is malformed.")
    return path, value


def _load_question(path: Path) -> dict[str, Any]:
    value = _read_yaml(path)
    if not isinstance(value, dict) or set(value) != {"id", "content"}:
        raise ControllerError("QUESTION_INVALID", "Question must contain exactly id and content.")
    question_id = value["id"]
    content = value["content"]
    if not isinstance(question_id, str) or not re.fullmatch(r"Q-[0-9]{3}", question_id):
        raise ControllerError("QUESTION_INVALID", "Question ID is invalid.")
    if not isinstance(content, dict) or set(content) != {"question", "answer"}:
        raise ControllerError("QUESTION_INVALID", "Question content must contain exactly question and answer.")
    question = content["question"]
    answer = content["answer"]
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000:
        raise ControllerError("QUESTION_INVALID", "Question text is outside its bounded contract.")
    if answer is not None and (not isinstance(answer, str) or not 1 <= len(answer.strip()) <= 2000):
        raise ControllerError("QUESTION_INVALID", "Answer is outside its bounded contract.")
    return value


def _load_state(path: Path) -> dict[str, Any]:
    value = _read_yaml(path)
    if not isinstance(value, dict) or set(value) != {
        "phase",
        "active_question",
        "plan_fingerprint",
    }:
        raise ControllerError("STATE_INVALID_COMBINATION", "Workflow State has an invalid shape.")
    if value["phase"] not in PHASES:
        raise ControllerError("STATE_INVALID_COMBINATION", "Workflow State has an unknown phase.")
    if value["active_question"] is not None and (
        not isinstance(value["active_question"], str)
        or not re.fullmatch(r"Q-[0-9]{3}", value["active_question"])
    ):
        raise ControllerError("STATE_INVALID_COMBINATION", "active_question is invalid.")
    fingerprint = value["plan_fingerprint"]
    if fingerprint is not None and (
        not isinstance(fingerprint, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint)
    ):
        raise ControllerError("STATE_INVALID_COMBINATION", "plan_fingerprint is invalid.")
    return value


def _question_subjects(question: dict[str, Any]) -> set[str]:
    return set(CURRENT_ID_TOKEN.findall(question["content"]["question"]))


def _assert_answer_subjects(question: dict[str, Any]) -> None:
    answer = question["content"]["answer"]
    if answer is None:
        return
    introduced = set(CURRENT_ID_TOKEN.findall(answer)) - _question_subjects(question)
    if introduced:
        raise ControllerError(
            "QUESTION_SUBJECT_MISMATCH",
            f"Answer introduces undeclared subjects: {sorted(introduced)}.",
        )


def _summary(root: Path, **overrides: Any) -> dict[str, Any]:
    result = {
        "feature": root.name,
        "phase": "uninitialized",
        "transaction": None,
        "targets": [],
        "next_action": "start_question",
        "read_selectors": [],
        "blocked_reason": None,
    }
    result.update(overrides)
    return result


def resume(feature_root: Path) -> dict[str, Any]:
    root = feature_root.resolve()
    if not root.is_dir():
        return _summary(
            root,
            phase="invalid",
            next_action="human_recovery",
            blocked_reason="FEATURE_ROOT_UNREADABLE",
        )
    state_path = root / "control" / "workflow-state.yaml"
    candidate = root / "candidate"
    if not state_path.exists() and not candidate.exists():
        _ensure_allocator(root)
        return _summary(root)
    if not state_path.exists() and candidate.is_dir():
        files = sorted(path.name for path in candidate.iterdir())
        if files == ["question.yaml"]:
            try:
                question = _load_question(candidate / "question.yaml")
                if question["content"]["answer"] is not None:
                    raise ControllerError("QUESTION_INVALID", "An orphan question must be unanswered.")
                _, allocation = _ensure_allocator(root)
                suffix = int(question["id"].split("-")[1])
                if suffix > allocation["highest_issued"]["DECISION"]:
                    raise ControllerError("ID_ALLOCATION_INVALID", "Orphan question was not reserved.")
                _atomic_write_yaml(
                    state_path,
                    {
                        "phase": "discussing",
                        "active_question": question["id"],
                        "plan_fingerprint": None,
                    },
                )
                return _summary(
                    root,
                    phase="discussing",
                    transaction=question["id"],
                    next_action="answer_question",
                    read_selectors=[{"role": "active_question", "whole_role": True}],
                )
            except ControllerError as error:
                return _summary(
                    root,
                    phase="invalid",
                    next_action="human_recovery",
                    blocked_reason=error.code,
                )
    if state_path.is_file():
        try:
            state = _load_state(state_path)
            if state["phase"] == "discussing":
                if state["active_question"] is None or state["plan_fingerprint"] is not None:
                    raise ControllerError("STATE_INVALID_COMBINATION", "Discussing state has illegal bindings.")
                question_path = candidate / "question.yaml"
                if not question_path.is_file():
                    raise ControllerError("STATE_INVALID_COMBINATION", "Bound question is missing.")
                question = _load_question(question_path)
                if question["id"] != state["active_question"]:
                    raise ControllerError("STATE_INVALID_COMBINATION", "State and question IDs differ.")
                if question["content"]["answer"] is None:
                    return _summary(
                        root,
                        phase="discussing",
                        transaction=question["id"],
                        next_action="answer_question",
                        read_selectors=[{"role": "active_question", "whole_role": True}],
                    )
                _assert_answer_subjects(question)
                next_state = {
                    "phase": "planning",
                    "active_question": question["id"],
                    "plan_fingerprint": None,
                }
                _atomic_write_yaml(state_path, next_state)
                return _summary(
                    root,
                    phase="planning",
                    transaction=question["id"],
                    next_action="submit_plan",
                    read_selectors=[
                        {"role": "active_question", "whole_role": True},
                        {"role": "candidate_discussion", "whole_role": True},
                    ],
                )
            if state["phase"] == "planning":
                if state["active_question"] is None or state["plan_fingerprint"] is not None:
                    raise ControllerError("STATE_INVALID_COMBINATION", "Planning state has illegal bindings.")
                question_path = candidate / "question.yaml"
                if not question_path.is_file():
                    raise ControllerError("STATE_INVALID_COMBINATION", "Planning question is missing.")
                question = _load_question(question_path)
                if question["id"] != state["active_question"] or question["content"]["answer"] is None:
                    raise ControllerError("STATE_INVALID_COMBINATION", "Planning requires its answered question.")
                _assert_answer_subjects(question)
                plan_path = candidate / "application-plan.yaml"
                if plan_path.exists():
                    plan = _load_plan(plan_path)
                    if (
                        plan["basis"]["id"] != question["id"]
                        or plan["basis"]["fingerprint"] != _canonical_fingerprint(question)
                    ):
                        raise ControllerError("PLAN_BINDING_MISMATCH", "Unsealed Plan and question differ.")
                    targets = _target_summaries(root, plan["operations"])
                    if any(target["status"] != "pending" for target in targets):
                        raise ControllerError(
                            "PLAN_TARGET_CONFLICT",
                            "An unsealed Plan may only be resumed from its exact before state.",
                        )
                    _validate_expected_final(root, plan)
                    plan_fingerprint = _canonical_fingerprint(plan)
                    _atomic_write_yaml(
                        state_path,
                        {
                            "phase": "applying_current",
                            "active_question": question["id"],
                            "plan_fingerprint": plan_fingerprint,
                        },
                    )
                    return _summary(
                        root,
                        phase="applying_current",
                        transaction=question["id"],
                        targets=targets,
                        next_action="apply_plan" if targets else "finalize_question",
                    )
                return _summary(
                    root,
                    phase="planning",
                    transaction=question["id"],
                    next_action="submit_plan",
                    read_selectors=[
                        {"role": "active_question", "whole_role": True},
                        {"role": "candidate_discussion", "whole_role": True},
                    ],
                )
            if state["phase"] == "applying_current":
                if state["active_question"] is None or state["plan_fingerprint"] is None:
                    raise ControllerError("STATE_INVALID_COMBINATION", "Applying state has illegal bindings.")
                question_path = candidate / "question.yaml"
                plan_path = candidate / "application-plan.yaml"
                if not question_path.is_file() or not plan_path.is_file():
                    raise ControllerError("STATE_INVALID_COMBINATION", "Applying transaction files are missing.")
                question = _load_question(question_path)
                plan = _load_plan(plan_path)
                plan_fingerprint = _canonical_fingerprint(plan)
                if (
                    question["id"] != state["active_question"]
                    or plan_fingerprint != state["plan_fingerprint"]
                    or plan["basis"]["id"] != question["id"]
                    or plan["basis"]["fingerprint"] != _canonical_fingerprint(question)
                ):
                    raise ControllerError("PLAN_BINDING_MISMATCH", "Applying transaction bindings differ.")
                targets = _target_summaries(root, plan["operations"])
                if any(target["status"] == "conflict" for target in targets):
                    raise ControllerError("PLAN_TARGET_CONFLICT", "At least one target is in a third state.")
                if all(target["status"] == "complete" for target in targets):
                    if _current_fingerprint(root) != plan["expected_final_current_fingerprint"]:
                        raise ControllerError(
                            "PLAN_UNEXPECTED_CURRENT",
                            "Complete targets do not equal expected final Current.",
                        )
                    _atomic_write_yaml(
                        state_path,
                        {
                            "phase": "finalizing",
                            "active_question": question["id"],
                            "plan_fingerprint": plan_fingerprint,
                        },
                    )
                    return _summary(
                        root,
                        phase="finalizing",
                        transaction=question["id"],
                        targets=targets,
                        next_action="finalize_question",
                    )
                return _summary(
                    root,
                    phase="applying_current",
                    transaction=question["id"],
                    targets=targets,
                    next_action="apply_plan",
                )
            if state["phase"] == "finalizing":
                if state["active_question"] is None and state["plan_fingerprint"] is None:
                    if candidate.exists():
                        allowed = {
                            "question.yaml",
                            "discussion.md",
                            "application-plan.yaml",
                            "review.html",
                        }
                        if any(path.name not in allowed for path in candidate.iterdir()):
                            raise ControllerError(
                                "STATE_INVALID_COMBINATION",
                                "Clean marker does not own unknown Candidate residue.",
                            )
                        _cleanup_question_candidate(root)
                    return _summary(
                        root,
                        phase="finalizing",
                        next_action="start_question_or_finish",
                    )
                if state["active_question"] is None or state["plan_fingerprint"] is None:
                    raise ControllerError("STATE_INVALID_COMBINATION", "Finalizing bindings are incomplete.")
                question_path = candidate / "question.yaml"
                plan_path = candidate / "application-plan.yaml"
                if not question_path.is_file() or not plan_path.is_file():
                    raise ControllerError("STATE_INVALID_COMBINATION", "Finalizing transaction files are missing.")
                question = _load_question(question_path)
                plan = _load_plan(plan_path)
                plan_fingerprint = _canonical_fingerprint(plan)
                if (
                    question["id"] != state["active_question"]
                    or plan_fingerprint != state["plan_fingerprint"]
                    or plan["basis"]["id"] != question["id"]
                    or plan["basis"]["fingerprint"] != _canonical_fingerprint(question)
                ):
                    raise ControllerError("PLAN_BINDING_MISMATCH", "Finalizing transaction bindings differ.")
                targets = _target_summaries(root, plan["operations"])
                if any(target["status"] != "complete" for target in targets):
                    raise ControllerError("PLAN_TARGET_CONFLICT", "Finalizing Plan is not fully applied.")
                if _current_fingerprint(root) != plan["expected_final_current_fingerprint"]:
                    raise ControllerError("PLAN_UNEXPECTED_CURRENT", "Finalizing Current is unexpected.")
                return _summary(
                    root,
                    phase="finalizing",
                    transaction=question["id"],
                    targets=targets,
                    next_action="finalize_question",
                )
        except ControllerError as error:
            return _summary(
                root,
                phase="invalid",
                next_action="human_recovery",
                blocked_reason=error.code,
            )
    return _summary(
        root,
        phase="invalid",
        next_action="human_recovery",
        blocked_reason="STATE_INVALID_COMBINATION",
    )


def start_question(feature_root: Path, question_text: str) -> dict[str, Any]:
    root = feature_root.resolve()
    if not root.is_dir():
        raise ControllerError("FEATURE_ROOT_UNREADABLE", "Feature root is not a directory.")
    question_text = question_text.strip()
    if not 1 <= len(question_text) <= 1000:
        raise ControllerError("QUESTION_INVALID", "Question must contain 1 to 1000 characters.")
    state_path = root / "control" / "workflow-state.yaml"
    candidate_root = root / "candidate"
    if candidate_root.exists() and any(candidate_root.iterdir()):
        raise ControllerError("STATE_INVALID_COMBINATION", "Candidate already contains active transaction data.")
    if state_path.exists():
        state = _read_yaml(state_path)
        allowed = isinstance(state, dict) and (
            state == {"phase": "pass", "active_question": None, "plan_fingerprint": None}
            or state == {"phase": "finalizing", "active_question": None, "plan_fingerprint": None}
        )
        if not allowed:
            raise ControllerError("STATE_INVALID_COMBINATION", "Workflow State does not permit a new question.")
    allocation_path, allocation = _ensure_allocator(root)
    suffix = allocation["highest_issued"]["DECISION"] + 1
    if suffix > 999:
        raise ControllerError("ID_ALLOCATION_INVALID", "DECISION ID allocation is exhausted.")
    allocation["highest_issued"]["DECISION"] = suffix
    _atomic_write_yaml(allocation_path, allocation)
    question_id = f"Q-{suffix:03d}"
    _atomic_write_yaml(
        candidate_root / "question.yaml",
        {
            "id": question_id,
            "content": {"question": question_text, "answer": None},
        },
    )
    _atomic_write_yaml(
        state_path,
        {
            "phase": "discussing",
            "active_question": question_id,
            "plan_fingerprint": None,
        },
    )
    return _summary(
        root,
        phase="discussing",
        transaction=question_id,
        next_action="answer_question",
        read_selectors=[{"role": "active_question", "whole_role": True}],
    )


def answer_question(feature_root: Path, answer_text: str) -> dict[str, Any]:
    root = feature_root.resolve()
    state_path = root / "control" / "workflow-state.yaml"
    question_path = root / "candidate" / "question.yaml"
    if not state_path.is_file() or not question_path.is_file():
        raise ControllerError("STATE_INVALID_COMBINATION", "Bound discussion state and question are required.")
    state = _read_yaml(state_path)
    question = _load_question(question_path)
    if state != {
        "phase": "discussing",
        "active_question": question["id"],
        "plan_fingerprint": None,
    }:
        raise ControllerError("STATE_INVALID_COMBINATION", "Question is not in a resumable discussion state.")
    if question["content"]["answer"] is not None:
        raise ControllerError("STATE_INVALID_COMBINATION", "Question already has an answer.")
    answer_text = answer_text.strip()
    if not 1 <= len(answer_text) <= 2000:
        raise ControllerError("QUESTION_INVALID", "Answer must contain 1 to 2000 characters.")
    question["content"]["answer"] = answer_text
    _assert_answer_subjects(question)
    _atomic_write_yaml(question_path, question)
    _atomic_write_yaml(
        state_path,
        {
            "phase": "planning",
            "active_question": question["id"],
            "plan_fingerprint": None,
        },
    )
    return _summary(
        root,
        phase="planning",
        transaction=question["id"],
        next_action="submit_plan",
        read_selectors=[
            {"role": "active_question", "whole_role": True},
            {"role": "candidate_discussion", "whole_role": True},
        ],
    )


def submit_plan(feature_root: Path, proposal_path: Path) -> dict[str, Any]:
    root = feature_root.resolve()
    state_path = root / "control" / "workflow-state.yaml"
    question_path = root / "candidate" / "question.yaml"
    if not state_path.is_file() or not question_path.is_file():
        raise ControllerError("STATE_INVALID_COMBINATION", "Planning requires State and an answered question.")
    state = _load_state(state_path)
    question = _load_question(question_path)
    if state != {
        "phase": "planning",
        "active_question": question["id"],
        "plan_fingerprint": None,
    }:
        raise ControllerError("STATE_INVALID_COMBINATION", "Question is not in an unsealed planning state.")
    if question["content"]["answer"] is None:
        raise ControllerError("QUESTION_INVALID", "Question must be answered before Plan submission.")
    _assert_answer_subjects(question)
    proposal = _read_yaml(proposal_path.resolve())
    if not isinstance(proposal, dict) or set(proposal) != {"changes"} or not isinstance(proposal["changes"], list):
        raise ControllerError("PLAN_INVALID_SHAPE", "Plan proposal must contain only a changes array.")
    allocation_path, allocation = _ensure_allocator(root)
    baseline = {
        counter: allocation["highest_issued"][counter]
        for counter in COUNTERS
        if counter != "DECISION"
    }
    symbols = sorted(_collect_symbols(proposal))
    allocations: dict[str, str] = {}
    for symbol in symbols:
        match = NEW_ID_HANDLE.fullmatch(symbol)
        assert match is not None
        counter = match.group("counter")
        suffix = allocation["highest_issued"][counter] + 1
        if suffix > 999:
            raise ControllerError("ID_ALLOCATION_INVALID", f"{counter} allocation is exhausted.")
        allocation["highest_issued"][counter] = suffix
        allocations[symbol] = f"{counter}-{suffix:03d}"
    if allocations:
        _atomic_write_yaml(allocation_path, allocation)
    changes = _replace_symbols(proposal["changes"], allocations)
    operations: list[dict[str, Any]] = []
    target_keys: set[str] = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"target", "after"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Each change must contain exactly target and after.")
        target = change["target"]
        after = change["after"]
        if not isinstance(target, dict) or set(target) != {"record_id"}:
            raise ControllerError("PLAN_INVALID_SHAPE", "Question proposals currently target Records only.")
        record_id = target["record_id"]
        _record_role(record_id)
        key = _target_key(target)
        if key in target_keys:
            raise ControllerError("PLAN_INVALID_SHAPE", f"Duplicate target {record_id}.")
        target_keys.add(key)
        if not isinstance(after, dict) or after.get("state") not in {"present", "absent"}:
            raise ControllerError("PLAN_INVALID_SHAPE", f"{record_id} after state is invalid.")
        if after["state"] == "absent":
            if set(after) != {"state"}:
                raise ControllerError("PLAN_INVALID_SHAPE", "Absent after state cannot contain payload.")
        else:
            if set(after) != {"state", "payload"}:
                raise ControllerError("PLAN_INVALID_SHAPE", "Present after state requires exactly one payload.")
            payload = after["payload"]
            if not isinstance(payload, dict) or set(payload) != {"id", "content"} or payload["id"] != record_id:
                raise ControllerError("PLAN_INVALID_SHAPE", "Record after payload must match its target ID.")
        before_value = _target_value(root, target)
        before = _before_state(before_value)
        if before == _before_state(_after_value(after)):
            raise ControllerError("PLAN_INVALID_SHAPE", f"{record_id} change is a no-op.")
        operations.append({"target": target, "before": before, "after": after})
    removed_ids = {
        operation["target"]["record_id"]
        for operation in operations
        if operation["before"]["state"] == "present" and operation["after"]["state"] == "absent"
    }
    if not _question_subjects(question).issubset(removed_ids):
        missing = sorted(_question_subjects(question) - removed_ids)
        raise ControllerError("PLAN_INVALID_SHAPE", f"Question subjects are not removed: {missing}.")
    added_ids = {
        operation["target"]["record_id"]
        for operation in operations
        if operation["before"]["state"] == "absent" and operation["after"]["state"] == "present"
    }
    index_path = _fixed_role_path(root, "current_id_index")
    index_value = _read_yaml(index_path) if index_path.exists() else {"ids": []}
    if not isinstance(index_value, dict) or set(index_value) != {"ids"} or not isinstance(index_value["ids"], list):
        raise ControllerError("PLAN_TARGET_CONFLICT", "Current ID Index is malformed.")
    final_ids = sorted((set(index_value["ids"]) - removed_ids) | added_ids)
    if final_ids != index_value["ids"]:
        index_target = {"file_role": "current_id_index"}
        operations.append(
            {
                "target": index_target,
                "before": _before_state(index_value if index_path.exists() else None),
                "after": {"state": "present", "payload": {"ids": final_ids}},
            }
        )
    operations.sort(key=lambda row: _target_key(row["target"]))
    with tempfile.TemporaryDirectory() as temporary:
        virtual_root = Path(temporary) / root.name
        shutil.copytree(root, virtual_root)
        _apply_operations(virtual_root, operations)
        validation = validate_package(virtual_root)
        if validation["result"] != "VALID":
            codes = sorted({finding["code"] for finding in validation["findings"]})
            raise ControllerError("PLAN_INVALID_SHAPE", f"Virtual final Current is invalid: {codes}.")
        expected_final = _current_fingerprint(virtual_root)
    plan = {
        "basis": {
            "kind": "question",
            "id": question["id"],
            "fingerprint": _canonical_fingerprint(question),
        },
        "allocation_baseline": baseline,
        "expected_final_current_fingerprint": expected_final,
        "operations": operations,
    }
    plan_path = root / "candidate" / "application-plan.yaml"
    _atomic_write_yaml(plan_path, plan)
    plan_fingerprint = _canonical_fingerprint(plan)
    _atomic_write_yaml(
        state_path,
        {
            "phase": "applying_current",
            "active_question": question["id"],
            "plan_fingerprint": plan_fingerprint,
        },
    )
    return _summary(
        root,
        phase="applying_current",
        transaction=question["id"],
        targets=_target_summaries(root, operations),
        next_action="apply_plan" if operations else "finalize_question",
    )


def apply_plan(feature_root: Path) -> dict[str, Any]:
    root = feature_root.resolve()
    state_path = root / "control" / "workflow-state.yaml"
    plan_path = root / "candidate" / "application-plan.yaml"
    question_path = root / "candidate" / "question.yaml"
    if not state_path.is_file() or not plan_path.is_file() or not question_path.is_file():
        raise ControllerError("STATE_INVALID_COMBINATION", "Applying requires State, Q, and the sealed Plan.")
    state = _load_state(state_path)
    plan = _load_plan(plan_path)
    question = _load_question(question_path)
    plan_fingerprint = _canonical_fingerprint(plan)
    if state != {
        "phase": "applying_current",
        "active_question": question["id"],
        "plan_fingerprint": plan_fingerprint,
    }:
        raise ControllerError("PLAN_BINDING_MISMATCH", "State does not bind the exact sealed Plan.")
    if plan["basis"]["id"] != question["id"] or plan["basis"]["fingerprint"] != _canonical_fingerprint(question):
        raise ControllerError("PLAN_BINDING_MISMATCH", "Question and sealed Plan differ.")
    statuses = _target_summaries(root, plan["operations"])
    if any(target["status"] == "conflict" for target in statuses):
        raise ControllerError("PLAN_TARGET_CONFLICT", "At least one target matches neither before nor after.")
    pending_keys = {
        _target_key(target["target"])
        for target in statuses
        if target["status"] == "pending"
    }
    pending = [
        operation
        for operation in plan["operations"]
        if _target_key(operation["target"]) in pending_keys
    ]
    if pending:
        _apply_operations(root, pending)
    statuses = _target_summaries(root, plan["operations"])
    if any(target["status"] != "complete" for target in statuses):
        raise ControllerError("PLAN_TARGET_CONFLICT", "Plan did not converge to complete targets.")
    if _current_fingerprint(root) != plan["expected_final_current_fingerprint"]:
        raise ControllerError("PLAN_UNEXPECTED_CURRENT", "Complete targets do not equal expected final Current.")
    _atomic_write_yaml(
        state_path,
        {
            "phase": "finalizing",
            "active_question": question["id"],
            "plan_fingerprint": plan_fingerprint,
        },
    )
    return _summary(
        root,
        phase="finalizing",
        transaction=question["id"],
        targets=statuses,
        next_action="finalize_question",
    )


def _project_decision_text(text: str) -> str:
    _package, _contracts, id_schema = _load_catalogs(DEFINITION_ROOT)
    patterns = [CURRENT_ID_TOKEN]
    patterns.extend(re.compile(row["pattern"]) for row in id_schema["rejected_legacy_patterns"])
    projected = text
    for pattern in patterns:
        projected = pattern.sub("the affected specification item(s)", projected)
    return " ".join(projected.split())


def _append_decision(root: Path, question: dict[str, Any]) -> None:
    archive_path = root / "history" / "decisions.yaml"
    decision_id = "DEC-" + question["id"].split("-", 1)[1]
    expected = {
        "id": decision_id,
        "content": {
            "question": _project_decision_text(question["content"]["question"]),
            "decision": _project_decision_text(question["content"]["answer"]),
        },
    }
    records: list[Any] = []
    if archive_path.exists():
        records = list(yaml.safe_load_all(archive_path.read_text(encoding="utf-8")))
    matching = [record for record in records if isinstance(record, dict) and record.get("id") == decision_id]
    if matching:
        if len(matching) != 1 or matching[0] != expected:
            raise ControllerError("DEC_COMMIT_COLLISION", f"{decision_id} already has different content.")
        return
    records.append(expected)
    _atomic_write_text(
        archive_path,
        yaml.safe_dump_all(
            records,
            sort_keys=False,
            explicit_start=True,
            allow_unicode=True,
        ),
    )


def _cleanup_question_candidate(root: Path) -> None:
    candidate = root / "candidate"
    for name in ("question.yaml", "discussion.md", "application-plan.yaml", "review.html"):
        path = candidate / name
        if path.exists():
            path.unlink()
    if candidate.exists() and not any(candidate.iterdir()):
        candidate.rmdir()


def finalize_question(feature_root: Path) -> dict[str, Any]:
    root = feature_root.resolve()
    state_path = root / "control" / "workflow-state.yaml"
    question_path = root / "candidate" / "question.yaml"
    plan_path = root / "candidate" / "application-plan.yaml"
    if not state_path.is_file() or not question_path.is_file() or not plan_path.is_file():
        raise ControllerError("STATE_INVALID_COMBINATION", "Question finalization requires State, Q, and Plan.")
    state = _load_state(state_path)
    question = _load_question(question_path)
    plan = _load_plan(plan_path)
    plan_fingerprint = _canonical_fingerprint(plan)
    allowed_states = {
        (
            "applying_current",
            question["id"],
            plan_fingerprint,
        ),
        (
            "finalizing",
            question["id"],
            plan_fingerprint,
        ),
    }
    if (state["phase"], state["active_question"], state["plan_fingerprint"]) not in allowed_states:
        raise ControllerError("PLAN_BINDING_MISMATCH", "State does not bind the exact question Plan.")
    if plan["basis"]["id"] != question["id"] or plan["basis"]["fingerprint"] != _canonical_fingerprint(question):
        raise ControllerError("PLAN_BINDING_MISMATCH", "Question and Plan basis differ.")
    if any(
        target["status"] != "complete"
        for target in _target_summaries(root, plan["operations"])
    ):
        raise ControllerError("PLAN_TARGET_CONFLICT", "Plan still contains unapplied or conflicting operations.")
    if _current_fingerprint(root) != plan["expected_final_current_fingerprint"]:
        raise ControllerError("PLAN_UNEXPECTED_CURRENT", "Current differs from the sealed expected final state.")
    if state["phase"] == "applying_current":
        _atomic_write_yaml(
            state_path,
            {
                "phase": "finalizing",
                "active_question": question["id"],
                "plan_fingerprint": plan_fingerprint,
            },
        )
    _append_decision(root, question)
    _atomic_write_yaml(
        state_path,
        {"phase": "finalizing", "active_question": None, "plan_fingerprint": None},
    )
    _cleanup_question_candidate(root)
    return _summary(
        root,
        phase="finalizing",
        next_action="start_question_or_finish",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("feature_root", type=Path)
    start_parser = subparsers.add_parser("start-question")
    start_parser.add_argument("feature_root", type=Path)
    start_parser.add_argument("--question", required=True)
    answer_parser = subparsers.add_parser("answer-question")
    answer_parser.add_argument("feature_root", type=Path)
    answer_parser.add_argument("--answer", required=True)
    plan_parser = subparsers.add_parser("submit-plan")
    plan_parser.add_argument("feature_root", type=Path)
    plan_parser.add_argument("proposal", type=Path)
    apply_parser = subparsers.add_parser("apply-plan")
    apply_parser.add_argument("feature_root", type=Path)
    finalize_parser = subparsers.add_parser("finalize-question")
    finalize_parser.add_argument("feature_root", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "resume":
            payload = resume(args.feature_root)
        elif args.command == "start-question":
            payload = start_question(args.feature_root, args.question)
        elif args.command == "answer-question":
            payload = answer_question(args.feature_root, args.answer)
        elif args.command == "submit-plan":
            payload = submit_plan(args.feature_root, args.proposal)
        elif args.command == "apply-plan":
            payload = apply_plan(args.feature_root)
        else:
            payload = finalize_question(args.feature_root)
    except ControllerError as error:
        payload = _summary(
            args.feature_root.resolve(),
            phase="invalid",
            next_action="human_recovery",
            blocked_reason=error.code,
        )
    except (OSError, UnicodeError, yaml.YAMLError):
        payload = _summary(
            args.feature_root.resolve(),
            phase="invalid",
            next_action="human_recovery",
            blocked_reason="CONTROLLER_INPUT_ERROR",
        )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if payload["blocked_reason"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
