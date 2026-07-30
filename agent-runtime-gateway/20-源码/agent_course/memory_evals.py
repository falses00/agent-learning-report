from __future__ import annotations

import json
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .contracts import ContractError
from .memory import MemoryAccessPolicy, MemoryCandidate, MemoryService, MemoryStore


EVAL_ACCESS_POLICY = MemoryAccessPolicy(
    tenant_memberships={
        "user-a": {"tenant-a"},
        "user-b": {"tenant-a"},
        "agent": {"tenant-a"},
        "agent-a": {"tenant-a"},
        "agent-b": {"tenant-b"},
    },
    resource_grants={
        ("agent", "tenant-a"): {"customer-a:contract", "customer-a:vip"},
        ("agent-a", "tenant-a"): {"customer-a:contract"},
        ("agent-b", "tenant-b"): {"customer-b:contract"},
    },
    tenant_admins={("agent", "tenant-a")},
)


class EvalClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 7, 31, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


def run_memory_eval(path: str | Path) -> dict[str, Any]:
    dataset_path = Path(path)
    cases = _read_jsonl(dataset_path)
    if not cases:
        raise ValueError("memory eval must contain at least one JSONL case")

    failures: list[dict[str, Any]] = []
    assertion_total = 0
    assertion_passed = 0

    for case in cases:
        case_id = str(case.get("id", "missing-case-id"))
        critical = bool(case.get("critical", False))
        case_failures: list[str] = []
        with ExitStack() as resources:
            work_dir = Path(
                resources.enter_context(TemporaryDirectory(prefix="opspilot-s5-eval-"))
            )
            database = work_dir / "memory.db"
            clock = EvalClock()
            store = MemoryStore(str(database))
            resources.callback(store.close)
            service = MemoryService(
                store,
                access_policy=EVAL_ACCESS_POLICY,
                clock=clock,
            )
            setup_results: list[dict[str, Any]] = []

            try:
                for setup in case.get("setup", []):
                    setup_results.append(
                        _execute_operation(
                            service,
                            clock,
                            setup["operation"],
                            setup.get("request", {}),
                            setup_results,
                        )
                    )
                if case.get("reopen_after_setup"):
                    store.close()
                    store = MemoryStore(str(database))
                    resources.callback(store.close)
                    service = MemoryService(
                        store,
                        access_policy=EVAL_ACCESS_POLICY,
                        clock=clock,
                    )
                result = _execute_operation(
                    service,
                    clock,
                    case["operation"],
                    case.get("request", {}),
                    setup_results,
                )
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

            expected_decision = case.get("expected_decision")
            if expected_decision is not None:
                assertion_total += 1
                if result.get("decision") == expected_decision:
                    assertion_passed += 1
                else:
                    case_failures.append(
                        f"decision expected {expected_decision}, got {result.get('decision')}"
                    )

            for assertion in case.get("assertions", []):
                assertion_total += 1
                try:
                    passed, reason = _evaluate_assertion(
                        assertion,
                        result=result,
                        store=store,
                        clock=clock,
                    )
                except (ContractError, KeyError, TypeError, ValueError) as exc:
                    passed = False
                    reason = f"memory assertion failed closed: {exc}"
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

    critical_failed = sum(1 for failure in failures if failure["critical"])
    return {
        "suite": "s5-memory-baseline",
        "version": max(str(case.get("version", "unknown")) for case in cases),
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "critical_failed": critical_failed,
        "release_passed": not failures,
        "assertions": assertion_total,
        "assertions_passed": assertion_passed,
        "failures": failures,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"memory eval line {line_number} must be an object")
        cases.append(value)
    return cases


def _execute_operation(
    service: MemoryService,
    clock: EvalClock,
    operation: str,
    request: dict[str, Any],
    setup_results: list[dict[str, Any]],
) -> dict[str, Any]:
    resolved = _resolve_references(request, setup_results)
    if operation == "memory.add":
        return service.write(MemoryCandidate.from_dict(resolved)).to_dict()
    if operation == "memory.search":
        return service.search(**resolved).to_dict()
    if operation == "memory.update":
        candidate = MemoryCandidate.from_dict(resolved["candidate"])
        return service.update(resolved["memory_id"], candidate).to_dict()
    if operation == "memory.delete":
        return service.delete(**resolved).to_dict()
    if operation == "memory.expire":
        clock.advance(int(resolved.pop("advance_seconds")))
        tenant_id = resolved["tenant_id"]
        expired_count = service.expire_due(tenant_id=tenant_id)
        search = service.search(**resolved).to_dict()
        search["decision"] = "exclude" if expired_count else search["decision"]
        search["reason_code"] = (
            "MEMORY_TTL_EXPIRED" if expired_count else search["reason_code"]
        )
        search["expired_count"] = expired_count
        return search
    if operation == "memory.eval":
        return service.evaluate_retrieval(**resolved)
    raise ContractError(f"unsupported memory eval operation: {operation}")


def _resolve_references(value: Any, setup_results: list[dict[str, Any]]) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_references(item, setup_results) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_references(item, setup_results) for item in value]
    if isinstance(value, str) and value.startswith("$setup."):
        parts = value.split(".")
        if len(parts) < 3:
            raise ContractError(f"invalid setup reference: {value}")
        current: Any = setup_results[int(parts[1])]
        for part in parts[2:]:
            current = current[part]
        return current
    return value


def _evaluate_assertion(
    assertion: dict[str, Any],
    *,
    result: dict[str, Any],
    store: MemoryStore,
    clock: EvalClock,
) -> tuple[bool, str]:
    if not isinstance(assertion, dict):
        return False, "memory assertion must be an object"
    assertion_type = assertion.get("type")
    if assertion_type == "result":
        path = assertion.get("path")
        if not isinstance(path, str) or not path:
            return False, "result assertion requires path"
        exists, actual = _value_at_path(result, path)
        op = assertion.get("op", "equals")
        expected = assertion.get("value")
        if op == "exists":
            expected_exists = assertion.get("value", True)
            if not isinstance(expected_exists, bool):
                return False, "result exists assertion value must be boolean"
            return exists is expected_exists, f"result path {path} exists={exists}"
        if not exists:
            return False, f"result path is missing: {path}"
        if op == "equals":
            return actual == expected, f"result {path} expected {expected!r}, got {actual!r}"
        if op == "gte":
            return actual >= expected, f"result {path} expected >= {expected}, got {actual}"
        if op == "lte":
            return actual <= expected, f"result {path} expected <= {expected}, got {actual}"
        if op == "contains":
            return expected in actual, f"result {path} does not contain {expected!r}"
        return False, f"unsupported result assertion op: {op}"

    if assertion_type == "store":
        metric = assertion.get("metric")
        actual = _store_metric(store, clock, metric, assertion)
        expected = assertion.get("value")
        return actual == expected, f"store {metric} expected {expected!r}, got {actual!r}"

    if assertion_type == "state_absent":
        value = assertion.get("value")
        if not isinstance(value, str) or not value:
            return False, "state_absent assertion requires non-empty value"
        present = value in store.serialized_state()
        return not present, f"sensitive value was persisted: {value}"

    if assertion_type == "audit":
        expected = {
            key: value
            for key, value in assertion.items()
            if key in {"operation", "decision", "reason_code", "tenant_id"}
        }
        if not expected:
            return False, "audit assertion requires at least one audit field"
        matched = any(
            all(event.get(key) == value for key, value in expected.items())
            for event in store.list_audit()
        )
        return matched, f"memory audit event not found: {expected}"

    if assertion_type == "history":
        tenant_id = assertion.get("tenant_id")
        subject_id = assertion.get("subject_id")
        history = store.history(tenant_id=tenant_id, subject_id=subject_id)
        if "count" in assertion and len(history) != assertion["count"]:
            return False, f"history count expected {assertion['count']}, got {len(history)}"
        if assertion.get("old_valid_to_exists") and (
            len(history) < 2 or history[0].valid_to is None
        ):
            return False, "superseded memory does not have valid_to"
        if "latest_content" in assertion and (
            not history or history[-1].content != assertion["latest_content"]
        ):
            actual = history[-1].content if history else None
            return False, f"latest history content expected {assertion['latest_content']!r}, got {actual!r}"
        return True, ""

    return False, f"unsupported memory assertion type: {assertion_type}"


def _store_metric(
    store: MemoryStore,
    clock: EvalClock,
    metric: Any,
    assertion: dict[str, Any],
) -> Any:
    if metric == "active_count":
        return store.active_count(
            tenant_id=assertion.get("tenant_id"),
            now=clock().isoformat(),
        )
    if metric == "index_count":
        return store.index_count()
    if metric == "tombstone_count":
        return store.tombstone_count()
    if metric == "audit_count":
        return len(store.list_audit())
    raise ContractError(f"unsupported store metric: {metric}")


def _value_at_path(value: Any, path: str) -> tuple[bool, Any]:
    current = value
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None
    return True, current
