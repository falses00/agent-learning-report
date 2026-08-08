from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agent_course.observability import (
    ObservabilityContractError,
    build_observability_report,
    evaluate_observability_report,
    run_observability,
    verify_audit_chain,
)
from agent_course.observability_evals import run_observability_eval


EVAL_DIR = Path(__file__).resolve().parents[1] / "22-评测集"
MANIFEST_PATH = EVAL_DIR / "s7-observability-manifest.json"
ADVERSARIAL_PATH = EVAL_DIR / "s7-observability-adversarial.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _blockers(result: dict) -> set[str]:
    return {item["code"] for item in result["blockers"]}


def test_s7_observability_pipeline_produces_replayable_teaching_evidence() -> None:
    result = run_observability(MANIFEST_PATH)

    assert result["release_passed"] is True
    assert result["release_decision"] == "pass"
    assert result["summary"] == {
        "total_cases": 6,
        "passed_cases": 6,
        "failed_cases": 0,
        "critical_failures": 0,
        "assertions": 36,
        "assertions_passed": 36,
    }
    assert result["metrics"]["trace_coverage"] == 1
    assert result["metrics"]["audit_coverage"] == 1
    assert result["metrics"]["replay_packet_coverage"] == 1
    assert result["metrics"]["p95_latency_ms"] == 640
    assert result["alerts"] == []
    assert result["incidents"] == []
    assert len(result["evidence_sha256"]) == 64
    assert len(result["decision_sha256"]) == 64


def test_s7_observability_gate_survives_adversarial_suite() -> None:
    result = run_observability_eval(ADVERSARIAL_PATH)

    assert result["total"] == 14
    assert result["failed"] == 0
    assert result["assertions"] == 46
    assert result["assertions_passed"] == result["assertions"]


def test_export_uses_w3c_context_and_does_not_copy_prompt_or_identity() -> None:
    result = run_observability(MANIFEST_PATH)
    serialized = json.dumps(result, ensure_ascii=False)

    assert "agent@example.com" not in serialized
    assert "sk-course-canary-123456" not in serialized
    for case in result["cases"]:
        assert len(case["trace"]["trace_id"]) == 32
        assert case["trace"]["traceparent"].startswith("00-")
        assert all(
            span["attributes"]["opspilot.content.capture"] == "metadata_only"
            for span in case["trace"]["spans"]
        )


def test_missing_span_blocks_trace_coverage() -> None:
    report = build_observability_report(_manifest())
    report["cases"][0]["trace"]["spans"].pop()

    result = evaluate_observability_report(report)

    assert result["release_passed"] is False
    assert "TRACE_COVERAGE_GAP" in _blockers(result)
    assert any(item["reason_code"] == "TRACE_COVERAGE_GAP" for item in result["incidents"])


def test_audit_chain_tampering_is_detected() -> None:
    report = build_observability_report(_manifest())
    chain = report["cases"][0]["audit"]["chain"]
    assert verify_audit_chain(chain) is True
    chain[0]["event"]["outcome"] = "tampered"

    result = evaluate_observability_report(report)

    assert verify_audit_chain(chain) is False
    assert "AUDIT_CHAIN_INVALID" in _blockers(result)


def test_secret_canary_in_span_is_zero_budget_incident() -> None:
    report = build_observability_report(_manifest())
    report["cases"][0]["trace"]["spans"][0]["attributes"]["debug.prompt"] = (
        "sk-course-canary-123456"
    )

    result = evaluate_observability_report(report)

    assert "SENSITIVE_TELEMETRY_DETECTED" in _blockers(result)
    incident = next(
        item for item in result["incidents"] if item["reason_code"] == "SENSITIVE_TELEMETRY_DETECTED"
    )
    assert incident["severity"] == "P0"
    assert incident["regression"]["owner"] == "sre-course"


def test_tail_latency_and_cost_are_independent_release_blockers() -> None:
    latency_report = build_observability_report(_manifest())
    latency_report["cases"][-1]["latency_ms"] = 5000
    cost_report = build_observability_report(_manifest())
    cost_report["cases"][0]["usage"]["cost_usd"] = 1

    latency_result = evaluate_observability_report(latency_report)
    cost_result = evaluate_observability_report(cost_report)

    assert "P95_LATENCY_SLO_BREACH" in _blockers(latency_result)
    assert "COST_PER_SUCCESS_BUDGET_EXCEEDED" in _blockers(cost_result)


def test_one_failed_run_exhausts_small_error_budget_and_pages() -> None:
    report = build_observability_report(_manifest())
    report["cases"][0]["actual_status"] = "failed"

    result = evaluate_observability_report(report)

    assert result["metrics"]["error_budget_burn_rate"] > 14.4
    assert {
        "RUN_SUCCESS_SLO_BREACH",
        "ERROR_BUDGET_FAST_BURN",
        "CRITICAL_OBSERVABILITY_CASE_FAILED",
    }.issubset(_blockers(result))


def test_slow_error_budget_burn_creates_owned_ticket_without_paging() -> None:
    report = build_observability_report(_manifest())
    report["slo_policy"]["min_run_success_rate"] = 0.95
    report["cases"][-1]["actual_status"] = "failed"

    result = evaluate_observability_report(report)

    assert 3 <= result["metrics"]["error_budget_burn_rate"] < 14.4
    assert "ERROR_BUDGET_FAST_BURN" not in _blockers(result)
    alert = next(item for item in result["alerts"] if item["reason_code"] == "ERROR_BUDGET_SLOW_BURN")
    assert alert["severity"] == "P2"
    assert alert["action"] == "create_ticket_with_owner_and_deadline"
    incident = next(item for item in result["incidents"] if item["reason_code"] == "ERROR_BUDGET_SLOW_BURN")
    assert incident["regression"]["owner"] == "sre-course"


def test_missing_evidence_hash_fails_closed() -> None:
    report = build_observability_report(_manifest())
    report.pop("evidence_sha256")

    result = evaluate_observability_report(report)

    assert "EVIDENCE_HASH_MISSING" in _blockers(result)
    assert result["release_decision"] == "block"


def test_manifest_rejects_unknown_fields_before_runtime_execution(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["trust_me"] = True
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ObservabilityContractError, match="unknown fields"):
        run_observability(path)


def test_development_semantic_convention_requires_full_commit(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["semantic_convention"]["commit"] = "main"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ObservabilityContractError, match="full Git SHA"):
        run_observability(path)


def test_replay_packet_requires_complete_version_lineage() -> None:
    report = build_observability_report(_manifest())
    changed = copy.deepcopy(report)
    changed["cases"][0]["replay_packet"]["versions"].pop("policy_version")

    result = evaluate_observability_report(changed)

    assert "REPLAY_PACKET_INCOMPLETE" in _blockers(result)


def test_external_sampled_flag_cannot_override_service_policy() -> None:
    report = build_observability_report(_manifest())
    report["sampling"]["respect_external_sampled"] = True

    result = evaluate_observability_report(report)

    assert "EXTERNAL_SAMPLING_OVERRIDE_TRUSTED" in _blockers(result)


def test_adversarial_manifest_cannot_escape_eval_directory(tmp_path: Path) -> None:
    suite = json.loads(ADVERSARIAL_PATH.read_text(encoding="utf-8"))
    suite["baseline_manifest"] = "../outside.json"
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(suite), encoding="utf-8")

    with pytest.raises(ObservabilityContractError, match="escapes the eval directory"):
        run_observability_eval(path)
