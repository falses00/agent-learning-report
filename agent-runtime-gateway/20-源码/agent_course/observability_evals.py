from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .observability import (
    ObservabilityContractError,
    build_observability_report,
    evaluate_observability_report,
)


SUITE_FIELDS = {"suite", "version", "baseline_manifest", "cases"}
CASE_FIELDS = {
    "id",
    "critical",
    "mutation",
    "expected_decision",
    "expected_blockers",
    "forbidden_blockers",
    "min_incidents",
}
MUTATION_FIELDS = {"type", "case_id", "value"}


def _strict(value: dict[str, Any], allowed: set[str], required: set[str], name: str) -> None:
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        raise ObservabilityContractError(f"{name} has unknown fields: {sorted(unknown)}")
    if missing:
        raise ObservabilityContractError(f"{name} is missing fields: {sorted(missing)}")


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObservabilityContractError(f"{name} must be a non-empty string")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ObservabilityContractError(f"{name} must be an array")
    return value


def _load_json(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ObservabilityContractError(f"cannot load {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ObservabilityContractError(f"{name} must be an object")
    return value


def _resolve_within(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ObservabilityContractError("baseline_manifest escapes the eval directory") from exc
    return candidate


def _case_by_id(report: dict[str, Any], case_id: str | None) -> dict[str, Any]:
    cases = report.get("cases", [])
    if case_id:
        for case in cases:
            if case.get("id") == case_id:
                return case
        raise ObservabilityContractError(f"mutation case_id not found: {case_id}")
    if not cases:
        raise ObservabilityContractError("baseline report has no cases")
    return cases[0]


def _apply_mutation(report: dict[str, Any], mutation: dict[str, Any]) -> None:
    kind = mutation["type"]
    target = _case_by_id(report, mutation.get("case_id")) if kind not in {
        "none",
        "trust_external_sampling",
        "unpin_semconv",
        "remove_regression_owner",
    } else None
    if kind == "none":
        return
    if kind == "remove_span":
        spans = target["trace"]["spans"]
        if len(spans) <= 1:
            raise ObservabilityContractError("remove_span requires a child span")
        spans.pop()
        return
    if kind == "invalid_trace_id":
        target["trace"]["trace_id"] = "invalid-trace-id"
        return
    if kind == "remove_audit_event":
        chain = target["audit"]["chain"]
        action = mutation.get("value")
        index = next(
            (index for index, entry in enumerate(chain) if entry["event"]["action"] == action),
            None,
        )
        if index is None:
            raise ObservabilityContractError(f"audit action not found: {action}")
        chain.pop(index)
        return
    if kind == "tamper_audit":
        target["audit"]["chain"][0]["event"]["outcome"] = str(mutation.get("value") or "tampered")
        return
    if kind == "expose_secret":
        target["trace"]["spans"][0]["attributes"]["debug.prompt"] = str(
            mutation.get("value") or "sk-course-canary-123456"
        )
        return
    if kind == "set_latency":
        target["latency_ms"] = float(mutation.get("value") or 5000)
        return
    if kind == "set_cost":
        target["usage"]["cost_usd"] = float(mutation.get("value") or 1)
        return
    if kind == "fail_run":
        target["actual_status"] = str(mutation.get("value") or "failed")
        return
    if kind == "remove_replay_version":
        version = str(mutation.get("value") or "policy_version")
        target["replay_packet"]["versions"].pop(version, None)
        return
    if kind == "trust_external_sampling":
        report["sampling"]["respect_external_sampled"] = True
        return
    if kind == "unpin_semconv":
        report["semantic_convention"]["commit"] = str(mutation.get("value") or "main")
        return
    if kind == "remove_regression_owner":
        report["slo_policy"]["regression_owner"] = ""
        return
    raise ObservabilityContractError(f"unknown mutation type: {kind}")


def _validate_suite(suite: dict[str, Any]) -> None:
    _strict(suite, SUITE_FIELDS, SUITE_FIELDS, "suite")
    _text(suite["suite"], "suite.suite")
    _text(suite["version"], "suite.version")
    _text(suite["baseline_manifest"], "suite.baseline_manifest")
    cases = _list(suite["cases"], "suite.cases")
    if not cases:
        raise ObservabilityContractError("suite.cases must not be empty")
    ids: set[str] = set()
    for index, raw_case in enumerate(cases):
        if not isinstance(raw_case, dict):
            raise ObservabilityContractError(f"suite.cases[{index}] must be an object")
        _strict(raw_case, CASE_FIELDS, CASE_FIELDS, f"suite.cases[{index}]")
        case_id = _text(raw_case["id"], f"suite.cases[{index}].id")
        if case_id in ids:
            raise ObservabilityContractError(f"duplicate case id: {case_id}")
        ids.add(case_id)
        if not isinstance(raw_case["critical"], bool):
            raise ObservabilityContractError(f"suite.cases[{index}].critical must be a boolean")
        if raw_case["expected_decision"] not in {"pass", "block"}:
            raise ObservabilityContractError("expected_decision must be pass or block")
        if not isinstance(raw_case["min_incidents"], int) or raw_case["min_incidents"] < 0:
            raise ObservabilityContractError("min_incidents must be a non-negative integer")
        for field in ("expected_blockers", "forbidden_blockers"):
            for blocker in _list(raw_case[field], f"suite.cases[{index}].{field}"):
                _text(blocker, f"suite.cases[{index}].{field}[]")
        mutation = raw_case["mutation"]
        if not isinstance(mutation, dict):
            raise ObservabilityContractError("mutation must be an object")
        required = {"type"}
        _strict(mutation, MUTATION_FIELDS, required, "mutation")
        _text(mutation["type"], "mutation.type")


def run_observability_eval(path: str | Path) -> dict[str, Any]:
    suite_path = Path(path).resolve()
    suite = _load_json(suite_path, "observability adversarial suite")
    _validate_suite(suite)
    eval_root = suite_path.parent.resolve()
    baseline_path = _resolve_within(eval_root, suite["baseline_manifest"])
    baseline_manifest = _load_json(baseline_path, "observability baseline manifest")
    baseline = build_observability_report(baseline_manifest)
    if not baseline["release_passed"]:
        raise ObservabilityContractError("observability baseline must pass before adversarial evaluation")

    results = []
    failures = []
    assertion_total = 0
    assertion_passed = 0
    for spec in suite["cases"]:
        mutated = copy.deepcopy(baseline)
        mutation_error = None
        try:
            _apply_mutation(mutated, spec["mutation"])
            evaluated = evaluate_observability_report(mutated)
        except ObservabilityContractError as exc:
            mutation_error = str(exc)
            evaluated = {
                "release_decision": "block",
                "blockers": [
                    {
                        "code": "OBSERVABILITY_EVAL_FAILED_CLOSED",
                        "detail": mutation_error,
                    }
                ],
                "incidents": [
                    {
                        "incident_id": "INC-S7-EVAL",
                        "reason_code": "OBSERVABILITY_EVAL_FAILED_CLOSED",
                    }
                ],
            }
        blocker_codes = {item["code"] for item in evaluated.get("blockers", [])}
        checks = [evaluated.get("release_decision") == spec["expected_decision"]]
        checks.extend(code in blocker_codes for code in spec["expected_blockers"])
        checks.extend(code not in blocker_codes for code in spec["forbidden_blockers"])
        checks.append(len(evaluated.get("incidents", [])) >= spec["min_incidents"])
        passed = all(checks)
        assertion_total += len(checks)
        assertion_passed += sum(checks)
        reasons = []
        if not checks[0]:
            reasons.append(
                f"decision {evaluated.get('release_decision')!r} != {spec['expected_decision']!r}"
            )
        missing = sorted(set(spec["expected_blockers"]) - blocker_codes)
        forbidden = sorted(set(spec["forbidden_blockers"]) & blocker_codes)
        if missing:
            reasons.append(f"missing blockers: {missing}")
        if forbidden:
            reasons.append(f"forbidden blockers present: {forbidden}")
        if len(evaluated.get("incidents", [])) < spec["min_incidents"]:
            reasons.append("incident intake count below expectation")
        result = {
            "case_id": spec["id"],
            "critical": spec["critical"],
            "passed": passed,
            "release_decision": evaluated.get("release_decision"),
            "blocker_codes": sorted(blocker_codes),
            "incident_count": len(evaluated.get("incidents", [])),
            "assertions": len(checks),
            "assertions_passed": sum(checks),
            "reasons": reasons,
        }
        if mutation_error:
            result["mutation_error"] = mutation_error
        results.append(result)
        if not passed:
            failures.append({"case_id": spec["id"], "reasons": reasons})

    critical_failed = sum(not item["passed"] and item["critical"] for item in results)
    return {
        "suite": suite["suite"],
        "version": suite["version"],
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": len(failures),
        "critical_failed": critical_failed,
        "release_passed": not failures,
        "assertions": assertion_total,
        "assertions_passed": assertion_passed,
        "case_results": results,
        "failures": failures,
    }
