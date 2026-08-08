from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_course.rag_diagnostics import (
    RAGDiagnosisError,
    diagnose_rag,
    run_rag_diagnostic_eval,
)


EVAL_PATH = Path(__file__).resolve().parents[1] / "22-评测集" / "rag-diagnostic-baseline.json"


def test_rag_diagnostic_suite_executes_all_cases() -> None:
    result = run_rag_diagnostic_eval(EVAL_PATH)

    assert result["suite"] == "rag-diagnostic-baseline"
    assert result["total"] == 16
    assert result["passed"] == 16
    assert result["failed"] == 0
    assert result["critical_failed"] == 0
    assert result["assertions"] == 64
    assert result["assertions_passed"] == 64
    assert result["release_passed"] is True


@pytest.mark.parametrize(
    ("signals", "action"),
    [
        ({"cross_tenant_candidates": 1}, "enforce_acl_before_retrieval"),
        ({"injection_hits": 1}, "quarantine_untrusted_source"),
        ({"answer_in_corpus": False}, "repair_source_coverage"),
        ({"parse_fidelity": 0.7}, "repair_layout_parsing"),
        ({"visual_evidence": True, "visual_recall": 0.2}, "add_multimodal_retrieval"),
        ({"boundary_split": True, "retrieval_recall": 0.4}, "rechunk_with_parent_context"),
        ({"exact_identifier_miss": True}, "add_hybrid_retrieval"),
        ({"domain_shift": True, "retrieval_recall": 0.4}, "shadow_domain_embedding"),
        ({"query_ambiguity": True, "retrieval_recall": 0.4}, "rewrite_or_clarify_query"),
        ({"multi_hop": True, "path_coverage": 0.4}, "decompose_then_test_graph"),
        ({"retrieval_recall": 0.9, "retrieval_precision": 0.3}, "rerank_candidates"),
        ({"cache_stale": True}, "invalidate_versioned_cache"),
        ({"citation_support": 0.4}, "validate_claims_or_abstain"),
        ({"p95_latency_ms": 1001, "latency_budget_ms": 1000}, "route_and_budget_expensive_steps"),
        ({}, "keep_baseline"),
    ],
)
def test_rag_diagnostic_priority_rules(signals: dict[str, object], action: str) -> None:
    assert diagnose_rag(signals)["action"] == action


def test_security_signal_wins_over_quality_tuning() -> None:
    result = diagnose_rag(
        {
            "cross_tenant_candidates": 1,
            "parse_fidelity": 0.1,
            "retrieval_recall": 0.1,
            "citation_support": 0.1,
        }
    )

    assert result["action"] == "enforce_acl_before_retrieval"
    assert result["release_decision"] == "block"
    assert result["blockers"] == ["RAG_ACL_VIOLATION"]


@pytest.mark.parametrize(
    ("signals", "action", "blocker"),
    [
        (
            {"cache_stale": True, "retrieval_recall": 0.9, "retrieval_precision": 0.3},
            "invalidate_versioned_cache",
            "RAG_STALE_EVIDENCE",
        ),
        (
            {"citation_support": 0.4, "exact_identifier_miss": True},
            "validate_claims_or_abstain",
            "RAG_UNSUPPORTED_CLAIM",
        ),
        (
            {"citation_support": 0.4, "boundary_split": True, "retrieval_recall": 0.4},
            "validate_claims_or_abstain",
            "RAG_UNSUPPORTED_CLAIM",
        ),
    ],
)
def test_release_blocker_wins_over_quality_tuning(
    signals: dict[str, object], action: str, blocker: str
) -> None:
    result = diagnose_rag(signals)

    assert result["action"] == action
    assert result["release_decision"] == "block"
    assert result["blockers"] == [blocker]


def test_unknown_signal_and_invalid_ratio_fail_closed() -> None:
    with pytest.raises(RAGDiagnosisError, match="unknown fields"):
        diagnose_rag({"magic_graph": True})
    with pytest.raises(RAGDiagnosisError, match="between 0 and 1"):
        diagnose_rag({"retrieval_recall": 1.2})


def test_unknown_assertion_fails_the_case(tmp_path: Path) -> None:
    suite = {
        "suite": "bad-assertion",
        "version": "test",
        "cases": [
            {
                "id": "bad",
                "critical": True,
                "signals": {},
                "assertions": [
                    {"type": "always_pass", "path": "action", "value": "keep_baseline"}
                ],
            }
        ],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(suite), encoding="utf-8")

    result = run_rag_diagnostic_eval(path)

    assert result["failed"] == 1
    assert result["critical_failed"] == 1
    assert result["release_passed"] is False
    assert "unsupported assertion type" in result["failures"][0]["reasons"][0]


def test_unknown_signal_fails_suite_even_when_assertions_expect_fail_closed(
    tmp_path: Path,
) -> None:
    suite = {
        "suite": "bad-signal",
        "version": "test",
        "cases": [
            {
                "id": "bad",
                "critical": True,
                "signals": {"magic_graph": True},
                "assertions": [
                    {"type": "equals", "path": "action", "value": "fail_closed"},
                    {"type": "equals", "path": "release_decision", "value": "block"},
                ],
            }
        ],
    }
    path = tmp_path / "bad-signal.json"
    path.write_text(json.dumps(suite), encoding="utf-8")

    result = run_rag_diagnostic_eval(path)

    assert result["failed"] == 1
    assert result["critical_failed"] == 1
    assert result["release_passed"] is False
    assert result["case_results"][0]["assertions_passed"] == 2
    assert "diagnostic contract failed closed" in result["failures"][0]["reasons"][0]
