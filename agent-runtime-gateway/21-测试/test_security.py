from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agent_course.security import (
    SecurityContractError,
    evaluate_security_request,
    run_security_eval,
)


EVAL_PATH = Path(__file__).resolve().parents[1] / "22-评测集" / "s8-security-adversarial.json"


@pytest.fixture(scope="module")
def suite() -> dict[str, object]:
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))


def test_security_suite_passes_all_adversarial_cases() -> None:
    result = run_security_eval(EVAL_PATH)

    assert result["total"] == 25
    assert result["passed"] == 25
    assert result["failed"] == 0
    assert result["critical_failed"] == 0
    assert result["release_passed"] is True
    assert result["assertions"] == 150
    assert result["assertions_passed"] == 150


@pytest.mark.parametrize(
    ("case_id", "decision", "blocker"),
    [
        ("indirect-injection-quarantined", "quarantine", "UNTRUSTED_INSTRUCTION"),
        ("path-traversal-blocked", "block", "PATH_OUTSIDE_WORKSPACE"),
        ("metadata-ssrf-blocked", "block", "SSRF_ADDRESS_DENIED"),
        ("sandbox-unavailable-fails-closed", "block", "SANDBOX_REQUIRED"),
        ("mcp-capability-escalation-blocked", "block", "MCP_CAPABILITY_ESCALATION"),
        ("policy-outage-fails-closed", "block", "SECURITY_POLICY_UNAVAILABLE"),
    ],
)
def test_critical_security_decisions(
    suite: dict[str, object], case_id: str, decision: str, blocker: str
) -> None:
    case = next(item for item in suite["cases"] if item["id"] == case_id)
    result = evaluate_security_request(suite["policy"], case["request"])

    assert result["decision"] == decision
    assert blocker in result["blockers"]
    assert result["side_effect_allowed"] is False


def test_approval_is_not_an_execution_authority(suite: dict[str, object]) -> None:
    case = next(item for item in suite["cases"] if item["id"] == "high-risk-write-awaits-approval")
    waiting = evaluate_security_request(suite["policy"], case["request"])
    approved_request = {**case["request"], "approval": True}
    allowed = evaluate_security_request(suite["policy"], approved_request)

    assert waiting["decision"] == "require_approval"
    assert waiting["side_effect_allowed"] is False
    assert allowed["decision"] == "allow"
    assert allowed["side_effect_allowed"] is True


def test_combined_injection_and_secret_never_degrades_to_approval(
    suite: dict[str, object]
) -> None:
    request = {
        "tool": "ticket.update",
        "principal_scopes": ["ticket:write"],
        "credential_ref": "broker://ticket-oauth",
        "operation_id": "op-combined",
        "source_trust": "untrusted",
        "contains_instructions": True,
        "raw_content": "token=course-secret-value-123456",
    }
    result = evaluate_security_request(suite["policy"], request)

    assert result["decision"] == "quarantine"
    assert {"UNTRUSTED_INSTRUCTION", "RAW_SECRET_DETECTED", "APPROVAL_REQUIRED"} <= set(
        result["blockers"]
    )
    assert result["side_effect_allowed"] is False


@pytest.mark.parametrize(
    ("security_request", "blocker"),
    [
        (
            {
                "tool": "ticket.update",
                "principal_scopes": ["ticket:write"],
                "credential_ref": "broker://ticket-oauth",
                "operation_id": "op-egress",
                "requested_url": "https://docs.example/upload",
            },
            "EGRESS_NOT_ALLOWED",
        ),
        (
            {
                "tool": "shell.run",
                "principal_scopes": ["code:execute"],
                "operation_id": "op-path",
                "requested_path": "/workspace/../etc/shadow",
            },
            "PATH_OUTSIDE_WORKSPACE",
        ),
        (
            {
                "tool": "ticket.update",
                "principal_scopes": ["ticket:write"],
                "credential_ref": "broker://ticket-oauth",
                "operation_id": "op-secret",
                "raw_content": "token=course-secret-value-123456",
            },
            "RAW_SECRET_DETECTED",
        ),
    ],
)
def test_security_blocker_wins_over_approval_wait(
    suite: dict[str, object], security_request: dict[str, object], blocker: str
) -> None:
    result = evaluate_security_request(suite["policy"], security_request)

    assert result["decision"] == "block"
    assert blocker in result["blockers"]
    assert "APPROVAL_REQUIRED" in result["blockers"]
    assert result["side_effect_allowed"] is False


def test_redirect_and_resolved_ip_are_both_revalidated(suite: dict[str, object]) -> None:
    request = {
        "tool": "http.fetch",
        "principal_scopes": ["web:read"],
        "requested_url": "https://docs.example/start",
        "resolved_ips": ["93.184.216.34", "127.0.0.1"],
        "redirect_urls": ["https://api.ticketing.example/final"],
    }
    result = evaluate_security_request(suite["policy"], request)

    assert result["decision"] == "block"
    assert "SSRF_ADDRESS_DENIED" in result["blockers"]


def test_unknown_policy_field_is_rejected(suite: dict[str, object]) -> None:
    policy = copy.deepcopy(suite["policy"])
    policy["prompt_can_override"] = True

    with pytest.raises(SecurityContractError, match="unknown fields"):
        evaluate_security_request(policy, {"tool": "ticket.read", "principal_scopes": ["ticket:read"]})


def test_invalid_policy_reference_is_rejected(suite: dict[str, object]) -> None:
    policy = copy.deepcopy(suite["policy"])
    policy["tools"]["ticket.update"]["credential_refs"] = ["env://PROD_TOKEN"]

    with pytest.raises(SecurityContractError, match="unapproved credentials"):
        evaluate_security_request(policy, {"tool": "ticket.read", "principal_scopes": ["ticket:read"]})


def test_duplicate_case_id_is_rejected(tmp_path: Path, suite: dict[str, object]) -> None:
    invalid = copy.deepcopy(suite)
    invalid["cases"].append(copy.deepcopy(invalid["cases"][0]))
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(SecurityContractError, match="duplicate case id"):
        run_security_eval(path)


def test_suite_contract_failure_does_not_execute_side_effects(
    suite: dict[str, object]
) -> None:
    case = next(item for item in suite["cases"] if item["id"] == "unknown-request-field-fails-closed")

    with pytest.raises(SecurityContractError, match="unknown fields"):
        evaluate_security_request(suite["policy"], case["request"])
