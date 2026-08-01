from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agent_course.release_gate import (
    ReleaseGateError,
    build_release_report,
    evaluate_release_report,
    run_release_gate,
)
from agent_course.release_gate_evals import run_release_gate_eval


EVAL_DIR = Path(__file__).resolve().parents[1] / "22-评测集"
MANIFEST_PATH = EVAL_DIR / "s6-release-manifest.json"
ADVERSARIAL_PATH = EVAL_DIR / "s6-release-gate-adversarial.json"


def _blocker_codes(result: dict) -> set[str]:
    return {item["code"] for item in result["blockers"]}


def test_s6_release_gate_produces_hashed_teaching_evidence() -> None:
    result = run_release_gate(MANIFEST_PATH)

    assert result["release_passed"] is True
    assert result["release_decision"] == "pass"
    assert result["summary"]["total_cases"] == 35
    assert result["summary"]["assertions"] == 183
    assert result["summary"]["critical_failures"] == 0
    assert result["summary"]["holdout_overlap"] == 0
    assert {item["code"] for item in result["warnings"]} == {
        "PUBLIC_HOLDOUT_ONLY"
    }
    assert len(result["manifest_sha256"]) == 64
    assert len(result["evidence_sha256"]) == 64
    assert len(result["decision_sha256"]) == 64


def test_release_gate_itself_survives_adversarial_suite() -> None:
    result = run_release_gate_eval(ADVERSARIAL_PATH)

    assert result["failed"] == 0
    assert result["total"] == 16
    assert result["assertions"] == 34
    assert result["assertions_passed"] == result["assertions"]


def test_critical_failure_cannot_hide_inside_high_average() -> None:
    report = build_release_report(MANIFEST_PATH)
    critical = next(item for item in report["cases"] if item["critical"])
    critical["passed"] = False
    critical["deterministic_passed"] = False

    result = evaluate_release_report(report)

    assert result["release_passed"] is False
    assert "CRITICAL_CASE_FAILED" in _blocker_codes(result)
    assert "CASE_PASS_RATE_BELOW_THRESHOLD" not in _blocker_codes(result)
    assert result["summary"]["case_pass_rate"] > 0.95


def test_model_judge_cannot_override_deterministic_control() -> None:
    report = build_release_report(MANIFEST_PATH)
    critical = next(item for item in report["cases"] if item["critical"])
    critical["passed"] = True
    critical["deterministic_passed"] = False
    critical["judge_passed"] = True

    result = evaluate_release_report(report)

    assert "CRITICAL_CASE_FAILED" in _blocker_codes(result)
    assert "MODEL_JUDGE_CANNOT_OVERRIDE_RULE" in _blocker_codes(result)


def test_production_profile_requires_access_controlled_holdout() -> None:
    report = build_release_report(MANIFEST_PATH)
    report["profile"] = "production"

    result = evaluate_release_report(report)

    assert result["release_passed"] is False
    assert "PRIVATE_HOLDOUT_REQUIRED" in _blocker_codes(result)


def test_manifest_rejects_unknown_fields_before_execution(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["trust_me"] = True
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseGateError, match="unknown fields: trust_me"):
        run_release_gate(path)


def test_manifest_source_cannot_escape_eval_directory(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["source_suites"][0]["path"] = "../outside.json"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseGateError, match="escapes the eval-set directory"):
        run_release_gate(path)


def test_decision_hash_changes_when_release_evidence_changes() -> None:
    report = build_release_report(MANIFEST_PATH)
    baseline = evaluate_release_report(report)
    changed = copy.deepcopy(report)
    changed["metrics"]["p95_latency_ms"] = 9999

    blocked = evaluate_release_report(changed)

    assert blocked["release_decision"] == "block"
    assert "EVIDENCE_HASH_MISMATCH" in _blocker_codes(blocked)
    assert baseline["evidence_sha256"] != blocked["evidence_sha256"]
    assert baseline["decision_sha256"] != blocked["decision_sha256"]


def test_manifest_rejects_impossible_flake_threshold(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["policy"]["max_flake_rate"] = 1.01
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseGateError, match="max_flake_rate must be <= 1"):
        run_release_gate(path)


def test_release_report_without_evidence_hash_fails_closed() -> None:
    report = build_release_report(MANIFEST_PATH)
    report.pop("evidence_sha256")

    result = evaluate_release_report(report)

    assert result["release_passed"] is False
    assert "EVIDENCE_HASH_MISSING" in _blocker_codes(result)
