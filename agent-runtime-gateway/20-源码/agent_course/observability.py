from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from .contracts import RunRequest
from .runtime import AgentRuntime


SCHEMA_VERSION = "opspilot.observability.v1"
W3C_TRACE_ID = re.compile(r"^[0-9a-f]{32}$")
W3C_SPAN_ID = re.compile(r"^[0-9a-f]{16}$")
W3C_TRACEPARENT = re.compile(r"^00-[0-9a-f]{32}-[0-9a-f]{16}-0[01]$")
SENSITIVE_PATTERNS = (
    ("api_key", re.compile(r"\b(?:sk|rk|pk)-[A-Za-z0-9_-]{8,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{12,}")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~-]+", re.I)),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.I)),
    ("mobile_number", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
)
OPAQUE_IDENTIFIER_FIELDS = {
    "trace_id",
    "span_id",
    "parent_span_id",
    "traceparent",
    "run_id",
    "event_id",
    "actor_sha256",
    "resource_sha256",
    "request_sha256",
    "previous_hash",
    "event_hash",
    "chain_head",
    "audit_chain_head",
}
ACTION_OPERATION = {
    "run.create": "invoke_agent",
    "run.authorize": "guardrail",
    "run.complete": "invoke_agent",
    "run.resume": "invoke_agent",
    "run.cancel": "invoke_agent",
    "rag.retrieve": "retrieval",
    "tool.decide": "guardrail",
    "tool.approve": "guardrail",
    "tool.execute": "execute_tool",
    "operation.reconcile": "execute_tool",
}
REQUIRED_VERSIONS = {
    "agent_version",
    "prompt_version",
    "model_version",
    "tool_registry_version",
    "policy_version",
    "knowledge_version",
    "eval_set_version",
    "observability_schema_version",
}
REQUIRED_POLICY = {
    "min_run_success_rate",
    "max_p95_latency_ms",
    "max_cost_per_success_usd",
    "min_trace_coverage",
    "min_audit_coverage",
    "max_sensitive_exposures",
    "page_burn_rate",
    "ticket_burn_rate",
    "regression_owner",
}
MANIFEST_FIELDS = {
    "suite",
    "version",
    "profile",
    "semantic_convention",
    "versions",
    "sampling",
    "slo_policy",
    "cases",
}
CASE_FIELDS = {
    "id",
    "critical",
    "request",
    "approve",
    "expected_status",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "cost_usd",
    "expected_audit_actions",
    "assertions",
}
ASSERTION_FIELDS = {"type", "value"}
EVIDENCE_FIELDS = {
    "schema_version",
    "suite",
    "version",
    "profile",
    "semantic_convention",
    "versions",
    "sampling",
    "slo_policy",
    "cases",
}


class ObservabilityContractError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObservabilityContractError(f"{name} must be an object")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ObservabilityContractError(f"{name} must be an array")
    return value


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObservabilityContractError(f"{name} must be a non-empty string")
    return value


def _number(value: Any, name: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservabilityContractError(f"{name} must be a number")
    if not math.isfinite(float(value)) or float(value) < minimum:
        raise ObservabilityContractError(f"{name} must be >= {minimum}")
    return float(value)


def _strict(value: dict[str, Any], allowed: set[str], required: set[str], name: str) -> None:
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        raise ObservabilityContractError(f"{name} has unknown fields: {sorted(unknown)}")
    if missing:
        raise ObservabilityContractError(f"{name} is missing fields: {sorted(missing)}")


def _sensitive_findings(value: Any, path: str = "$") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(_sensitive_findings(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_sensitive_findings(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        leaf = path.rsplit(".", 1)[-1]
        for label, pattern in SENSITIVE_PATTERNS:
            if leaf in OPAQUE_IDENTIFIER_FIELDS and label in {"mobile_number", "email"}:
                continue
            if pattern.search(value):
                findings.append({"type": label, "path": path})
    return findings


def _trace_id(value: str) -> str:
    normalized = value.replace("-", "").lower()
    if not W3C_TRACE_ID.fullmatch(normalized) or normalized == "0" * 32:
        raise ObservabilityContractError("runtime trace_id cannot form a W3C trace-id")
    return normalized


def _span_id(seed: str) -> str:
    value = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return value if value != "0" * 16 else "1".zfill(16)


def _sanitize_audit(event: dict[str, Any], ordinal: int) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "event_id": event["event_id"],
        "run_id": event["run_id"],
        "trace_id": _trace_id(event["trace_id"]),
        "actor_sha256": _sha256(event["actor"]),
        "action": event["action"],
        "resource_sha256": _sha256(event["resource"]),
        "outcome": event["outcome"],
        "reason_code": event["reason_code"],
    }


def _seal_audit(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    chain: list[dict[str, Any]] = []
    previous = "0" * 64
    for event in events:
        event_hash = _sha256({"previous_hash": previous, "event": event})
        chain.append(
            {
                "previous_hash": previous,
                "event_hash": event_hash,
                "event": event,
            }
        )
        previous = event_hash
    return chain, previous


def verify_audit_chain(chain: Any) -> bool:
    if not isinstance(chain, list) or not chain:
        return False
    previous = "0" * 64
    for entry in chain:
        if not isinstance(entry, dict) or set(entry) != {"previous_hash", "event_hash", "event"}:
            return False
        if entry["previous_hash"] != previous:
            return False
        expected = _sha256({"previous_hash": previous, "event": entry["event"]})
        if entry["event_hash"] != expected:
            return False
        previous = expected
    return True


def _derive_spans(
    *,
    run_id: str,
    runtime_trace_id: str,
    audit_events: list[dict[str, Any]],
    latency_ms: float,
    agent_version: str,
) -> dict[str, Any]:
    trace_id = _trace_id(runtime_trace_id)
    root_span_id = _span_id(f"{run_id}:root")
    spans: list[dict[str, Any]] = [
        {
            "trace_id": trace_id,
            "span_id": root_span_id,
            "parent_span_id": None,
            "name": "invoke_agent OpsPilot",
            "kind": "INTERNAL",
            "status": "OK",
            "duration_ms": latency_ms,
            "attributes": {
                "gen_ai.operation.name": "invoke_agent",
                "gen_ai.provider.name": "opspilot.course",
                "gen_ai.agent.name": "OpsPilot",
                "gen_ai.agent.version": agent_version,
                "opspilot.run.id": run_id,
                "opspilot.content.capture": "metadata_only",
            },
        }
    ]
    child_duration = round(max(0.1, latency_ms / max(2, len(audit_events) + 1)), 3)
    for index, event in enumerate(audit_events):
        operation = ACTION_OPERATION.get(event["action"], "custom")
        attributes = {
            "gen_ai.operation.name": operation,
            "gen_ai.provider.name": "opspilot.course",
            "opspilot.run.id": run_id,
            "opspilot.audit.action": event["action"],
            "opspilot.audit.outcome": event["outcome"],
            "opspilot.audit.reason_code": event["reason_code"],
            "opspilot.content.capture": "metadata_only",
        }
        if operation == "execute_tool":
            attributes["gen_ai.tool.name_sha256"] = event["resource_sha256"]
        spans.append(
            {
                "trace_id": trace_id,
                "span_id": _span_id(f"{run_id}:{event['event_id']}:{index}"),
                "parent_span_id": root_span_id,
                "name": f"{operation} OpsPilot",
                "kind": "INTERNAL",
                "status": "ERROR" if event["outcome"] in {"error", "failed"} else "OK",
                "duration_ms": child_duration,
                "attributes": attributes,
            }
        )
    return {
        "trace_id": trace_id,
        "root_span_id": root_span_id,
        "traceparent": f"00-{trace_id}-{root_span_id}-01",
        "spans": spans,
        "derived_from": "runtime_audit_events",
    }


def _trace_context_valid(trace: Any) -> bool:
    if not isinstance(trace, dict):
        return False
    trace_id = trace.get("trace_id")
    root_span_id = trace.get("root_span_id")
    traceparent = trace.get("traceparent")
    spans = trace.get("spans")
    if not isinstance(trace_id, str) or not W3C_TRACE_ID.fullmatch(trace_id) or trace_id == "0" * 32:
        return False
    if not isinstance(root_span_id, str) or not W3C_SPAN_ID.fullmatch(root_span_id) or root_span_id == "0" * 16:
        return False
    if not isinstance(traceparent, str) or not W3C_TRACEPARENT.fullmatch(traceparent):
        return False
    if not isinstance(spans, list) or not spans:
        return False
    for span in spans:
        if not isinstance(span, dict):
            return False
        if span.get("trace_id") != trace_id:
            return False
        if not isinstance(span.get("span_id"), str) or not W3C_SPAN_ID.fullmatch(span["span_id"]):
            return False
        parent = span.get("parent_span_id")
        if parent is not None and (not isinstance(parent, str) or not W3C_SPAN_ID.fullmatch(parent)):
            return False
    return True


def _replay_complete(packet: Any) -> bool:
    if not isinstance(packet, dict):
        return False
    required = {
        "run_id",
        "trace_id",
        "request_sha256",
        "expected_terminal_status",
        "audit_chain_head",
        "versions",
    }
    if not required.issubset(packet):
        return False
    versions = packet.get("versions")
    return isinstance(versions, dict) and REQUIRED_VERSIONS.issubset(versions) and all(versions.values())


def _assertion_result(assertion: dict[str, Any], case: dict[str, Any]) -> tuple[bool, str]:
    kind = assertion["type"]
    value = assertion["value"]
    if kind == "terminal_status":
        actual = case["actual_status"]
        return actual == value, f"terminal_status={actual!r}, expected={value!r}"
    if kind == "audit_action":
        actions = [entry["event"]["action"] for entry in case["audit"]["chain"]]
        return value in actions, f"audit_action={value!r} must be present"
    if kind == "span_operation":
        operations = [span["attributes"].get("gen_ai.operation.name") for span in case["trace"]["spans"]]
        return value in operations, f"span_operation={value!r} must be present"
    if kind == "trace_context":
        actual = "valid" if _trace_context_valid(case["trace"]) else "invalid"
        return actual == value, f"trace_context={actual!r}, expected={value!r}"
    if kind == "sensitive_exposure":
        actual = len(_sensitive_findings({"trace": case["trace"], "audit": case["audit"], "replay": case["replay_packet"]}))
        return actual == value, f"sensitive_exposure={actual}, expected={value}"
    if kind == "replay_complete":
        actual = _replay_complete(case["replay_packet"])
        return actual == bool(value), f"replay_complete={actual}, expected={bool(value)}"
    return False, f"unknown assertion type: {kind}"


def _refresh_case(case: dict[str, Any]) -> None:
    results = []
    for assertion in case["assertions"]:
        passed, detail = _assertion_result(assertion, case)
        results.append({"type": assertion["type"], "passed": passed, "detail": detail})
    case["assertion_results"] = results
    case["assertions_total"] = len(results)
    case["assertions_passed"] = sum(item["passed"] for item in results)
    case["service_success"] = case["actual_status"] == case["expected_status"]
    case["passed"] = case["service_success"] and case["assertions_passed"] == case["assertions_total"]


def _validate_manifest(manifest: dict[str, Any]) -> None:
    _strict(manifest, MANIFEST_FIELDS, MANIFEST_FIELDS, "manifest")
    _text(manifest["suite"], "manifest.suite")
    _text(manifest["version"], "manifest.version")
    if manifest["profile"] not in {"teaching", "production"}:
        raise ObservabilityContractError("manifest.profile must be teaching or production")

    semconv = _mapping(manifest["semantic_convention"], "manifest.semantic_convention")
    _strict(semconv, {"source", "commit", "status"}, {"source", "commit", "status"}, "manifest.semantic_convention")
    _text(semconv["source"], "manifest.semantic_convention.source")
    commit = _text(semconv["commit"], "manifest.semantic_convention.commit")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ObservabilityContractError("semantic convention commit must be a full Git SHA")
    if semconv["status"] not in {"development", "stable"}:
        raise ObservabilityContractError("semantic convention status must be development or stable")

    versions = _mapping(manifest["versions"], "manifest.versions")
    _strict(versions, REQUIRED_VERSIONS, REQUIRED_VERSIONS, "manifest.versions")
    for key, value in versions.items():
        _text(value, f"manifest.versions.{key}")

    sampling = _mapping(manifest["sampling"], "manifest.sampling")
    _strict(
        sampling,
        {"head_ratio", "tail_keep_errors", "respect_external_sampled"},
        {"head_ratio", "tail_keep_errors", "respect_external_sampled"},
        "manifest.sampling",
    )
    ratio = _number(sampling["head_ratio"], "manifest.sampling.head_ratio")
    if ratio > 1:
        raise ObservabilityContractError("sampling head_ratio must be <= 1")
    if not isinstance(sampling["tail_keep_errors"], bool) or not isinstance(sampling["respect_external_sampled"], bool):
        raise ObservabilityContractError("sampling flags must be booleans")

    policy = _mapping(manifest["slo_policy"], "manifest.slo_policy")
    _strict(policy, REQUIRED_POLICY, REQUIRED_POLICY, "manifest.slo_policy")
    for key in REQUIRED_POLICY - {"regression_owner"}:
        _number(policy[key], f"manifest.slo_policy.{key}")
    _text(policy["regression_owner"], "manifest.slo_policy.regression_owner")
    for key in {"min_run_success_rate", "min_trace_coverage", "min_audit_coverage"}:
        if float(policy[key]) > 1:
            raise ObservabilityContractError(f"manifest.slo_policy.{key} must be <= 1")

    cases = _list(manifest["cases"], "manifest.cases")
    if not cases:
        raise ObservabilityContractError("manifest.cases must not be empty")
    case_ids: set[str] = set()
    allowed_assertions = {
        "terminal_status",
        "audit_action",
        "span_operation",
        "trace_context",
        "sensitive_exposure",
        "replay_complete",
    }
    for index, raw_case in enumerate(cases):
        case = _mapping(raw_case, f"manifest.cases[{index}]")
        _strict(case, CASE_FIELDS, CASE_FIELDS, f"manifest.cases[{index}]")
        case_id = _text(case["id"], f"manifest.cases[{index}].id")
        if case_id in case_ids:
            raise ObservabilityContractError(f"duplicate case id: {case_id}")
        case_ids.add(case_id)
        if not isinstance(case["critical"], bool) or not isinstance(case["approve"], bool):
            raise ObservabilityContractError(f"manifest.cases[{index}] flags must be booleans")
        RunRequest.from_dict(_mapping(case["request"], f"manifest.cases[{index}].request"))
        _text(case["expected_status"], f"manifest.cases[{index}].expected_status")
        for key in ("latency_ms", "input_tokens", "output_tokens", "cost_usd"):
            _number(case[key], f"manifest.cases[{index}].{key}")
        actions = _list(case["expected_audit_actions"], f"manifest.cases[{index}].expected_audit_actions")
        if not actions:
            raise ObservabilityContractError(f"manifest.cases[{index}].expected_audit_actions must not be empty")
        for action in actions:
            _text(action, f"manifest.cases[{index}].expected_audit_actions[]")
        assertions = _list(case["assertions"], f"manifest.cases[{index}].assertions")
        if not assertions:
            raise ObservabilityContractError(f"manifest.cases[{index}].assertions must not be empty")
        for assertion_index, raw_assertion in enumerate(assertions):
            assertion = _mapping(raw_assertion, f"manifest.cases[{index}].assertions[{assertion_index}]")
            _strict(assertion, ASSERTION_FIELDS, ASSERTION_FIELDS, "assertion")
            if assertion["type"] not in allowed_assertions:
                raise ObservabilityContractError(f"unknown assertion type: {assertion['type']}")


def _run_case(spec: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    request = RunRequest.from_dict(spec["request"])
    runtime = AgentRuntime()
    try:
        run = runtime.start(request)
        if spec["approve"]:
            run = runtime.approve(run.run_id, "s7-approver")
        raw_audit = runtime.store.list_audit(run.run_id)
    finally:
        runtime.store.close()
    audit_events = [_sanitize_audit(event, index + 1) for index, event in enumerate(raw_audit)]
    audit_chain, chain_head = _seal_audit(audit_events)
    trace = _derive_spans(
        run_id=run.run_id,
        runtime_trace_id=run.trace_id,
        audit_events=audit_events,
        latency_ms=float(spec["latency_ms"]),
        agent_version=manifest["versions"]["agent_version"],
    )
    request_sha256 = _sha256(spec["request"])
    case = {
        "id": spec["id"],
        "critical": spec["critical"],
        "expected_status": spec["expected_status"],
        "actual_status": run.status.value,
        "latency_ms": float(spec["latency_ms"]),
        "usage": {
            "input_tokens": int(spec["input_tokens"]),
            "output_tokens": int(spec["output_tokens"]),
            "cost_usd": float(spec["cost_usd"]),
            "source": "deterministic_teaching_fixture",
        },
        "request_sha256": request_sha256,
        "expected_audit_actions": copy.deepcopy(spec["expected_audit_actions"]),
        "expected_span_count": len(audit_events) + 1,
        "trace": trace,
        "audit": {
            "chain": audit_chain,
            "chain_head": chain_head,
            "storage_boundary": "hash_chained_export_not_worm_storage",
        },
        "replay_packet": {
            "run_id": run.run_id,
            "trace_id": trace["trace_id"],
            "request_sha256": request_sha256,
            "expected_terminal_status": spec["expected_status"],
            "audit_chain_head": chain_head,
            "versions": copy.deepcopy(manifest["versions"]),
        },
        "assertions": copy.deepcopy(spec["assertions"]),
    }
    _refresh_case(case)
    return case


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _case_metrics(cases: list[dict[str, Any]], target_success_rate: float) -> dict[str, Any]:
    service_successes = sum(bool(case.get("service_success")) for case in cases)
    expected_spans = sum(max(1, int(case.get("expected_span_count", 1))) for case in cases)
    actual_spans = sum(len(case.get("trace", {}).get("spans", [])) for case in cases)
    expected_audits = sum(len(case.get("expected_audit_actions", [])) for case in cases)
    actual_audits = 0
    for case in cases:
        actual_actions = {
            entry.get("event", {}).get("action")
            for entry in case.get("audit", {}).get("chain", [])
            if isinstance(entry, dict)
        }
        actual_audits += sum(action in actual_actions for action in case.get("expected_audit_actions", []))
    evidence = [
        {"trace": case.get("trace"), "audit": case.get("audit"), "replay": case.get("replay_packet")}
        for case in cases
    ]
    sensitive = _sensitive_findings(evidence)
    success_rate = service_successes / len(cases) if cases else 0
    allowed_error_rate = max(0.000001, 1 - target_success_rate)
    error_rate = 1 - success_rate
    return {
        "total_runs": len(cases),
        "successful_runs": service_successes,
        "run_success_rate": round(success_rate, 6),
        "p95_latency_ms": _percentile([float(case.get("latency_ms", 0)) for case in cases], 0.95),
        "total_input_tokens": sum(int(case.get("usage", {}).get("input_tokens", 0)) for case in cases),
        "total_output_tokens": sum(int(case.get("usage", {}).get("output_tokens", 0)) for case in cases),
        "cost_per_success_usd": round(
            sum(float(case.get("usage", {}).get("cost_usd", 0)) for case in cases) / max(1, service_successes),
            8,
        ),
        "trace_coverage": round(min(1.0, actual_spans / max(1, expected_spans)), 6),
        "audit_coverage": round(min(1.0, actual_audits / max(1, expected_audits)), 6),
        "trace_context_valid": all(_trace_context_valid(case.get("trace")) for case in cases),
        "audit_chain_valid": all(verify_audit_chain(case.get("audit", {}).get("chain")) for case in cases),
        "replay_packet_coverage": round(
            sum(_replay_complete(case.get("replay_packet")) for case in cases) / max(1, len(cases)),
            6,
        ),
        "sensitive_exposures": len(sensitive),
        "sensitive_finding_types": sorted({item["type"] for item in sensitive}),
        "error_budget_burn_rate": round(error_rate / allowed_error_rate, 6),
    }


def _evidence_hash(report: dict[str, Any]) -> str:
    return _sha256({key: report.get(key) for key in sorted(EVIDENCE_FIELDS)})


def evaluate_observability_report(report: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(report)
    blockers: list[dict[str, str]] = []

    def block(code: str, detail: str) -> None:
        if not any(item["code"] == code for item in blockers):
            blockers.append({"code": code, "detail": detail})

    provided_hash = result.get("evidence_sha256")
    if not provided_hash:
        block("EVIDENCE_HASH_MISSING", "the observability evidence hash is required")
    elif provided_hash != _evidence_hash(result):
        block("EVIDENCE_HASH_MISMATCH", "observability evidence changed after it was sealed")

    cases = result.get("cases")
    if not isinstance(cases, list) or not cases:
        block("OBSERVABILITY_REPORT_INVALID", "cases must be a non-empty array")
        cases = []
    for case in cases:
        try:
            _refresh_case(case)
        except (KeyError, TypeError, ObservabilityContractError) as exc:
            block("OBSERVABILITY_REPORT_INVALID", f"case evidence is malformed: {exc}")

    policy = result.get("slo_policy")
    if not isinstance(policy, dict):
        policy = {}
        block("OBSERVABILITY_REPORT_INVALID", "slo_policy must be an object")
    metrics = _case_metrics(cases, float(policy.get("min_run_success_rate", 1)))

    if metrics["run_success_rate"] < float(policy.get("min_run_success_rate", 1)):
        block("RUN_SUCCESS_SLO_BREACH", "run success rate is below the declared SLO")
    if metrics["p95_latency_ms"] > float(policy.get("max_p95_latency_ms", 0)):
        block("P95_LATENCY_SLO_BREACH", "p95 end-to-end latency exceeds the declared SLO")
    if metrics["cost_per_success_usd"] > float(policy.get("max_cost_per_success_usd", 0)):
        block("COST_PER_SUCCESS_BUDGET_EXCEEDED", "cost per successful run exceeds the declared budget")
    if metrics["trace_coverage"] < float(policy.get("min_trace_coverage", 1)):
        block("TRACE_COVERAGE_GAP", "one or more required run/audit spans are missing")
    if metrics["audit_coverage"] < float(policy.get("min_audit_coverage", 1)):
        block("AUDIT_COVERAGE_GAP", "one or more required policy/tool/audit actions are missing")
    if not metrics["trace_context_valid"]:
        block("TRACE_CONTEXT_INVALID", "trace-id, span-id, parent linkage, or traceparent is invalid")
    if not metrics["audit_chain_valid"]:
        block("AUDIT_CHAIN_INVALID", "the hash-chained audit export cannot be verified")
    if metrics["replay_packet_coverage"] < 1:
        block("REPLAY_PACKET_INCOMPLETE", "a replay packet is missing lineage or evidence references")
    if metrics["sensitive_exposures"] > int(policy.get("max_sensitive_exposures", 0)):
        block("SENSITIVE_TELEMETRY_DETECTED", "secret or PII patterns were found in exported telemetry")
    if result.get("sampling", {}).get("respect_external_sampled"):
        block("EXTERNAL_SAMPLING_OVERRIDE_TRUSTED", "external sampled flags must not override the service sampling policy")
    semconv = result.get("semantic_convention", {})
    if not re.fullmatch(r"[0-9a-f]{40}", str(semconv.get("commit", ""))):
        block("SEMCONV_VERSION_UNPINNED", "the development semantic convention must be pinned to a full commit")
    if metrics["error_budget_burn_rate"] >= float(policy.get("page_burn_rate", float("inf"))):
        block("ERROR_BUDGET_FAST_BURN", "the snapshot burn rate exceeds the page threshold")

    critical_failed = sum(bool(case.get("critical")) and not bool(case.get("passed")) for case in cases)
    if critical_failed:
        block("CRITICAL_OBSERVABILITY_CASE_FAILED", f"{critical_failed} critical observability cases failed")

    regression_owner = str(policy.get("regression_owner", "")).strip()
    if not regression_owner:
        block("INCIDENT_REGRESSION_OWNER_MISSING", "blocking incidents need a regression owner")

    severity_by_code = {
        "SENSITIVE_TELEMETRY_DETECTED": "P0",
        "AUDIT_CHAIN_INVALID": "P1",
        "AUDIT_COVERAGE_GAP": "P1",
        "TRACE_COVERAGE_GAP": "P1",
        "TRACE_CONTEXT_INVALID": "P1",
        "ERROR_BUDGET_FAST_BURN": "P1",
        "P95_LATENCY_SLO_BREACH": "P2",
        "COST_PER_SUCCESS_BUDGET_EXCEEDED": "P2",
    }
    alerts = []
    incidents = []
    for index, blocker in enumerate(blockers, start=1):
        if blocker["code"] in {"EVIDENCE_HASH_MISMATCH", "EVIDENCE_HASH_MISSING"}:
            continue
        severity = severity_by_code.get(blocker["code"], "P1")
        action = "disable_agent_and_preserve_evidence" if severity == "P0" else "freeze_release_and_investigate"
        alerts.append(
            {
                "rule_id": f"s7-{blocker['code'].lower().replace('_', '-')}",
                "severity": severity,
                "action": action,
                "reason_code": blocker["code"],
            }
        )
        incidents.append(
            {
                "incident_id": f"INC-S7-{index:03d}",
                "severity": severity,
                "reason_code": blocker["code"],
                "evidence_refs": ["trace", "audit_chain", "slo_report"],
                "regression": {
                    "case_id": f"regression-{blocker['code'].lower().replace('_', '-')}",
                    "owner": regression_owner,
                    "required": True,
                },
            }
        )

    ticket_threshold = float(policy.get("ticket_burn_rate", float("inf")))
    page_threshold = float(policy.get("page_burn_rate", float("inf")))
    slow_burn = ticket_threshold <= metrics["error_budget_burn_rate"] < page_threshold
    if slow_burn:
        alerts.append(
            {
                "rule_id": "s7-error-budget-slow-burn",
                "severity": "P2",
                "action": "create_ticket_with_owner_and_deadline",
                "reason_code": "ERROR_BUDGET_SLOW_BURN",
            }
        )
        incidents.append(
            {
                "incident_id": f"INC-S7-{len(incidents) + 1:03d}",
                "severity": "P2",
                "reason_code": "ERROR_BUDGET_SLOW_BURN",
                "evidence_refs": ["trace", "slo_report", "release_version"],
                "regression": {
                    "case_id": "regression-error-budget-slow-burn",
                    "owner": regression_owner,
                    "required": True,
                },
            }
        )

    assertions_total = sum(int(case.get("assertions_total", 0)) for case in cases)
    assertions_passed = sum(int(case.get("assertions_passed", 0)) for case in cases)
    result["summary"] = {
        "total_cases": len(cases),
        "passed_cases": sum(bool(case.get("passed")) for case in cases),
        "failed_cases": sum(not bool(case.get("passed")) for case in cases),
        "critical_failures": critical_failed,
        "assertions": assertions_total,
        "assertions_passed": assertions_passed,
    }
    result["metrics"] = metrics
    result["blockers"] = sorted(blockers, key=lambda item: item["code"])
    result["alerts"] = alerts
    result["incidents"] = incidents
    warnings = [
        {
            "code": "TEACHING_TELEMETRY_FIXTURE",
            "detail": "latency, token, and cost values are deterministic lab fixtures, not production telemetry",
        },
        {
            "code": "OTEL_GENAI_DEVELOPMENT",
            "detail": "the upstream GenAI semantic convention is development status and is pinned for reproducibility",
        },
        {
            "code": "AUDIT_EXPORT_NOT_WORM",
            "detail": "the hash chain detects export tampering but the SQLite source is not immutable/WORM storage",
        },
    ]
    if slow_burn:
        warnings.append(
            {
                "code": "ERROR_BUDGET_SLOW_BURN",
                "detail": "slow burn opens an owned ticket and regression case without paging the on-call engineer",
            }
        )
    result["warnings"] = warnings
    result["release_decision"] = "block" if blockers else "pass"
    result["release_passed"] = not blockers
    result["decision_sha256"] = _sha256(
        {
            "evidence_sha256": provided_hash,
            "release_decision": result["release_decision"],
            "blockers": result["blockers"],
        }
    )
    return result


def build_observability_report(manifest: dict[str, Any]) -> dict[str, Any]:
    _validate_manifest(manifest)
    report = {
        "schema_version": SCHEMA_VERSION,
        "suite": manifest["suite"],
        "version": manifest["version"],
        "profile": manifest["profile"],
        "semantic_convention": copy.deepcopy(manifest["semantic_convention"]),
        "versions": copy.deepcopy(manifest["versions"]),
        "sampling": copy.deepcopy(manifest["sampling"]),
        "slo_policy": copy.deepcopy(manifest["slo_policy"]),
        "cases": [_run_case(case, manifest) for case in manifest["cases"]],
    }
    report["evidence_sha256"] = _evidence_hash(report)
    return evaluate_observability_report(report)


def run_observability(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ObservabilityContractError(f"cannot load observability manifest: {exc}") from exc
    return build_observability_report(_mapping(manifest, "manifest"))
