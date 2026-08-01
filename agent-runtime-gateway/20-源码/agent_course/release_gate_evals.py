from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .release_gate import (
    ReleaseGateError,
    build_release_report,
    evaluate_release_report,
)


MUTATION_FIELDS = {
    "op",
    "path",
    "value",
    "case_id",
    "field",
    "match_field",
    "match_value",
}


def _resolve_path(root: Any, path: str) -> tuple[Any, str | int]:
    parts = path.split(".")
    if not parts or any(not part for part in parts):
        raise ReleaseGateError(f"invalid mutation path: {path}")
    current = root
    for part in parts[:-1]:
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise ReleaseGateError(f"mutation path is not resolvable: {path}") from exc
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ReleaseGateError(f"mutation path is not resolvable: {path}")
    leaf: str | int = parts[-1]
    if isinstance(current, list):
        try:
            leaf = int(leaf)
        except ValueError as exc:
            raise ReleaseGateError(f"mutation list index is invalid: {path}") from exc
    return current, leaf


def _matching_item(report: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    path = mutation.get("path")
    if not isinstance(path, str):
        raise ReleaseGateError("set_item mutation requires path")
    current: Any = report
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ReleaseGateError(f"mutation collection is missing: {path}")
        current = current[part]
    if not isinstance(current, list):
        raise ReleaseGateError(f"mutation collection is not a list: {path}")
    match_field = mutation.get("match_field")
    match_value = mutation.get("match_value")
    for item in current:
        if isinstance(item, dict) and item.get(match_field) == match_value:
            return item
    raise ReleaseGateError(f"mutation item not found: {path}.{match_field}={match_value}")


def _apply_mutation(report: dict[str, Any], mutation: dict[str, Any]) -> None:
    unknown = sorted(set(mutation) - MUTATION_FIELDS)
    if unknown:
        raise ReleaseGateError(f"mutation has unknown fields: {', '.join(unknown)}")
    operation = mutation.get("op")
    if operation == "set_case":
        case_id = mutation.get("case_id")
        target = next(
            (item for item in report["cases"] if item.get("case_id") == case_id),
            None,
        )
        if target is None:
            raise ReleaseGateError(f"mutation case not found: {case_id}")
        field = mutation.get("field")
        if not isinstance(field, str) or field not in target:
            raise ReleaseGateError(f"mutation case field is invalid: {field}")
        target[field] = copy.deepcopy(mutation.get("value"))
        return
    if operation == "set_path":
        parent, leaf = _resolve_path(report, str(mutation.get("path", "")))
        if isinstance(parent, list):
            if not isinstance(leaf, int) or not 0 <= leaf < len(parent):
                raise ReleaseGateError("mutation list index is out of range")
            parent[leaf] = copy.deepcopy(mutation.get("value"))
        elif isinstance(parent, dict):
            parent[str(leaf)] = copy.deepcopy(mutation.get("value"))
        else:
            raise ReleaseGateError("mutation parent is not writable")
        return
    if operation == "remove_path":
        parent, leaf = _resolve_path(report, str(mutation.get("path", "")))
        try:
            if isinstance(parent, list) and isinstance(leaf, int):
                parent.pop(leaf)
            elif isinstance(parent, dict):
                del parent[str(leaf)]
            else:
                raise KeyError(leaf)
        except (KeyError, IndexError) as exc:
            raise ReleaseGateError("mutation target does not exist") from exc
        return
    if operation == "append_path":
        parent, leaf = _resolve_path(report, str(mutation.get("path", "")))
        target = parent[leaf] if isinstance(parent, (dict, list)) else None
        if not isinstance(target, list):
            raise ReleaseGateError("append mutation target must be a list")
        target.append(copy.deepcopy(mutation.get("value")))
        return
    if operation == "set_item":
        target = _matching_item(report, mutation)
        field = mutation.get("field")
        if not isinstance(field, str) or field not in target:
            raise ReleaseGateError(f"mutation item field is invalid: {field}")
        target[field] = copy.deepcopy(mutation.get("value"))
        return
    if operation == "remove_item":
        path = mutation.get("path")
        target = _matching_item(report, mutation)
        current: Any = report
        for part in str(path).split("."):
            current = current[part]
        current.remove(target)
        return
    raise ReleaseGateError(f"unsupported release-gate mutation: {operation}")


def run_release_gate_eval(path: str | Path) -> dict[str, Any]:
    dataset_path = Path(path).resolve()
    try:
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReleaseGateError(f"invalid release-gate eval JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseGateError("release-gate eval dataset must be an object")
    if set(payload) - {"suite", "version", "base_manifest", "cases"}:
        raise ReleaseGateError("release-gate eval dataset has unknown top-level fields")
    base_manifest = payload.get("base_manifest")
    cases = payload.get("cases")
    if not isinstance(base_manifest, str) or not base_manifest.strip():
        raise ReleaseGateError("release-gate eval base_manifest is required")
    if not isinstance(cases, list) or not cases:
        raise ReleaseGateError("release-gate eval cases must be a non-empty array")

    base_path = (dataset_path.parent / base_manifest).resolve()
    try:
        base_path.relative_to(dataset_path.parent)
    except ValueError as exc:
        raise ReleaseGateError("release-gate eval base_manifest escapes its directory") from exc
    base_report = build_release_report(base_path)
    failures: list[dict[str, Any]] = []
    case_results: list[dict[str, Any]] = []
    assertions = 0
    assertions_passed = 0

    for index, raw in enumerate(cases):
        if not isinstance(raw, dict):
            raise ReleaseGateError(f"release-gate eval cases[{index}] must be an object")
        unknown = sorted(
            set(raw)
            - {
                "id",
                "critical",
                "mutations",
                "expected_decision",
                "expected_blockers",
                "forbidden_blockers",
            }
        )
        if unknown:
            raise ReleaseGateError(
                f"release-gate eval cases[{index}] has unknown fields: {', '.join(unknown)}"
            )
        case_id = str(raw.get("id", "missing-case-id"))
        critical = bool(raw.get("critical", True))
        reasons: list[str] = []
        report = copy.deepcopy(base_report)
        try:
            mutations = raw.get("mutations", [])
            if not isinstance(mutations, list):
                raise ReleaseGateError("mutations must be an array")
            for mutation in mutations:
                if not isinstance(mutation, dict):
                    raise ReleaseGateError("each mutation must be an object")
                _apply_mutation(report, mutation)
            result = evaluate_release_report(report)
        except (ReleaseGateError, KeyError, TypeError, ValueError) as exc:
            result = {
                "release_decision": "block",
                "blockers": [{"code": "GATE_EVAL_FAILED_CLOSED", "detail": str(exc)}],
            }

        blocker_codes = {item["code"] for item in result["blockers"]}
        assertions += 1
        if result["release_decision"] == raw.get("expected_decision"):
            assertions_passed += 1
        else:
            reasons.append(
                f"decision expected {raw.get('expected_decision')}, got {result['release_decision']}"
            )
        for expected in raw.get("expected_blockers", []):
            assertions += 1
            if expected in blocker_codes:
                assertions_passed += 1
            else:
                reasons.append(f"expected blocker not found: {expected}")
        for forbidden in raw.get("forbidden_blockers", []):
            assertions += 1
            if forbidden not in blocker_codes:
                assertions_passed += 1
            else:
                reasons.append(f"forbidden blocker was emitted: {forbidden}")

        case_result = {
            "case_id": case_id,
            "critical": critical,
            "passed": not reasons,
            "release_decision": result["release_decision"],
            "blocker_codes": sorted(blocker_codes),
            "reasons": reasons,
        }
        case_results.append(case_result)
        if reasons:
            failures.append(case_result)

    critical_failed = sum(item["critical"] for item in failures)
    return {
        "suite": payload.get("suite", dataset_path.stem),
        "version": payload.get("version"),
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "critical_failed": critical_failed,
        "release_passed": not failures,
        "assertions": assertions,
        "assertions_passed": assertions_passed,
        "case_results": case_results,
        "failures": failures,
    }
