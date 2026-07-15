from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .contracts import ContractError, RunRequest
from .rag import Citation, KnowledgeBase
from .runtime import AgentRuntime


def run_eval(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("eval payload must contain a non-empty cases array")

    failures: list[dict[str, Any]] = []
    assertion_total = 0
    assertion_passed = 0

    for case in cases:
        case_id = str(case.get("id", "missing-case-id"))
        critical = bool(case.get("critical", False))
        runtime = AgentRuntime()
        before_counts: dict[str, int] = {}
        case_failures: list[str] = []

        try:
            run = runtime.start(RunRequest.from_dict(case["request"]))
            action = case.get("action")
            if action == "approve_twice":
                run = runtime.approve(run.run_id, "manager@example.com")
                run = runtime.approve(run.run_id, "manager@example.com")
            elif action is not None:
                case_failures.append(f"unsupported action: {action}")
        except (ContractError, KeyError, TypeError, ValueError) as exc:
            failures.append(
                {
                    "case_id": case_id,
                    "critical": critical,
                    "reason": f"case setup failed: {exc}",
                    "reasons": [f"case setup failed: {exc}"],
                }
            )
            continue

        expected_status = case.get("expected_status")
        if expected_status is not None:
            assertion_total += 1
            if run.status.value == expected_status:
                assertion_passed += 1
            else:
                case_failures.append(
                    f"status expected {expected_status}, got {run.status.value}"
                )

        if case.get("expected_refund_executions") is not None:
            assertion_total += 1
            expected = case["expected_refund_executions"]
            actual = runtime.tool_execution_count("billing.refund")
            if actual == expected:
                assertion_passed += 1
            else:
                case_failures.append(
                    f"billing.refund executions expected {expected}, got {actual}"
                )

        audit = runtime.store.list_audit(run.run_id)
        for assertion in case.get("assertions", []):
            assertion_total += 1
            passed, reason = _evaluate_assertion(
                assertion,
                run=run,
                runtime=runtime,
                audit=audit,
                before_counts=before_counts,
            )
            if passed:
                assertion_passed += 1
            else:
                case_failures.append(reason)

        if case_failures:
            failures.append(
                {
                    "case_id": case_id,
                    "critical": critical,
                    "reason": "; ".join(case_failures),
                    "reasons": case_failures,
                }
            )

    total = len(cases)
    critical_failed = sum(1 for failure in failures if failure["critical"])
    return {
        "suite": payload.get("suite", Path(path).stem),
        "version": payload.get("version"),
        "total": total,
        "passed": total - len(failures),
        "failed": len(failures),
        "critical_failed": critical_failed,
        "release_passed": not failures,
        "assertions": assertion_total,
        "assertions_passed": assertion_passed,
        "failures": failures,
    }


def _evaluate_assertion(
    assertion: dict[str, Any],
    *,
    run: Any,
    runtime: AgentRuntime,
    audit: list[dict[str, Any]],
    before_counts: dict[str, int],
) -> tuple[bool, str]:
    if not isinstance(assertion, dict):
        return False, "assertion must be an object"
    assertion_type = assertion.get("type")

    if assertion_type == "citation":
        expected = assertion.get("document_id")
        if not isinstance(expected, str) or not expected.strip():
            return False, "citation assertion requires a non-empty document_id"
        validated, citations, validation_reason = _validated_citation_ids(
            run.result,
            tenant_id=run.request.tenant_id,
        )
        if not validated:
            return False, f"citation validation failed: {validation_reason}"
        return (
            expected in citations,
            f"citation expected {expected}, got {sorted(citations)}",
        )

    if assertion_type == "audit":
        expected = {
            key: value
            for key, value in assertion.items()
            if key in {"actor", "action", "resource", "outcome", "reason_code"}
        }
        if not expected:
            return False, "audit assertion must specify at least one audit field"
        matched = any(all(event.get(key) == value for key, value in expected.items()) for event in audit)
        return matched, f"audit event not found: {expected}"

    if assertion_type in {"tool_execution", "forbidden_tool_execution"}:
        tool_name = assertion.get("tool_name")
        if not isinstance(tool_name, str):
            return False, "tool execution assertion requires tool_name"
        try:
            current = runtime.tool_execution_count(tool_name)
        except ContractError as exc:
            return False, str(exc)
        baseline = before_counts.get(tool_name, 0)
        actual = current - baseline
        expected = 0 if assertion_type == "forbidden_tool_execution" else assertion.get("count")
        return actual == expected, f"{tool_name} executions expected {expected}, got {actual}"

    if assertion_type == "trace":
        if not run.trace_id:
            return False, "run trace_id is missing"
        if assertion.get("audit_consistent", True):
            inconsistent = [event for event in audit if event.get("trace_id") != run.trace_id]
            if inconsistent:
                return False, "audit events contain inconsistent trace_id values"
        return bool(audit), "trace assertion requires at least one audit event"

    if assertion_type == "result":
        root = {
            "status": run.status.value,
            "result": run.result,
            "error": asdict(run.error) if run.error else None,
            "trace_id": run.trace_id,
        }
        path = assertion.get("path")
        if not isinstance(path, str) or not path:
            return False, "result assertion requires path"
        exists, actual = _resolve_path(root, path)
        operation = assertion.get("op", "equals")
        expected = assertion.get("value")
        if operation == "exists":
            if "value" in assertion and not isinstance(expected, bool):
                return False, "result exists assertion value must be a boolean"
            expected_exists = assertion.get("value", True)
            passed = exists == expected_exists
            expected = expected_exists
        elif operation == "equals":
            passed = exists and actual == expected
        elif operation == "contains":
            passed = exists and _contains(actual, expected)
        elif operation == "not_contains":
            passed = exists and not _contains(actual, expected)
        else:
            return False, f"unsupported result assertion operation: {operation}"
        return passed, f"result {path} {operation} {expected!r}, got {actual!r}"

    return False, f"unsupported assertion type: {assertion_type}"


def _validated_citation_ids(
    value: Any,
    *,
    tenant_id: str,
) -> tuple[bool, set[str], str]:
    payloads, collection_error = _citation_payloads(value)
    if collection_error:
        return False, set(), collection_error
    if not payloads:
        return False, set(), "a non-empty structured citations array is required"

    citations: list[Citation] = []
    for index, payload in enumerate(payloads):
        string_fields = ("document_id", "chunk_id", "source", "quote")
        if any(
            not isinstance(payload.get(field), str) or not payload[field].strip()
            for field in string_fields
        ):
            return False, set(), f"citations[{index}] has missing or invalid string fields"
        version = payload.get("version")
        if isinstance(version, bool) or not isinstance(version, int):
            return False, set(), f"citations[{index}].version must be an integer"
        citations.append(
            Citation(
                document_id=payload["document_id"],
                chunk_id=payload["chunk_id"],
                source=payload["source"],
                version=version,
                quote=payload["quote"],
            )
        )

    citation_ids = {citation.document_id for citation in citations}
    if not KnowledgeBase().validate_citations(citations, tenant_id=tenant_id):
        return False, citation_ids, "citation provenance, tenant, version, or quote is invalid"
    return True, citation_ids, ""


def _citation_payloads(value: Any) -> tuple[list[dict[str, Any]], str | None]:
    found: list[dict[str, Any]] = []

    def visit(current: Any) -> str | None:
        if isinstance(current, dict):
            if "citations" in current:
                raw = current["citations"]
                if not isinstance(raw, list):
                    return "citations must be an array"
                for index, item in enumerate(raw):
                    if not isinstance(item, dict):
                        return f"citations[{index}] must be an object"
                    found.append(item)
            for key, nested in current.items():
                if key == "citations":
                    continue
                if error := visit(nested):
                    return error
        elif isinstance(current, list):
            for nested in current:
                if error := visit(nested):
                    return error
        return None

    return found, visit(value)


def _resolve_path(root: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = root
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _contains(actual: Any, expected: Any) -> bool:
    if isinstance(actual, str):
        return str(expected) in actual
    if isinstance(actual, (list, tuple, set)):
        return expected in actual
    if isinstance(actual, dict):
        return str(expected) in json.dumps(actual, sort_keys=True)
    return False
