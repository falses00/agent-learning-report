from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_course import AgentRuntime
from agent_course.evals import _evaluate_assertion, run_eval


EVAL_DIR = Path(__file__).resolve().parents[1] / "22-评测集"


def test_composable_assertions_pass_engineering_and_rag_baselines() -> None:
    engineering = run_eval(EVAL_DIR / "engineering-baseline.json")
    rag = run_eval(EVAL_DIR / "s3-rag-baseline.json")

    assert engineering["failed"] == 0
    assert engineering["suite"] == "engineering-baseline"
    assert engineering["assertions"] >= 20
    assert engineering["assertions_passed"] == engineering["assertions"]
    assert engineering["release_passed"] is True
    assert rag["failed"] == 0
    assert rag["suite"] == "s3-rag-baseline"
    assert rag["assertions"] >= 20
    assert rag["assertions_passed"] == rag["assertions"]


def test_eval_reports_critical_citation_failure(tmp_path) -> None:
    dataset = {
        "version": "test",
        "cases": [
            {
                "id": "wrong-citation",
                "critical": True,
                "request": {
                    "principal": "agent@example.com",
                    "tenant_id": "tenant-a",
                    "ticket_tenant_id": "tenant-a",
                    "ticket_id": "EVAL-001",
                    "message": "What is the refund policy?",
                },
                "expected_status": "completed",
                "assertions": [
                    {"type": "citation", "document_id": "made-up-document"}
                ],
            }
        ],
    }
    path = tmp_path / "failure.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")

    result = run_eval(path)

    assert result["failed"] == 1
    assert result["critical_failed"] == 1
    assert result["release_passed"] is False
    assert "made-up-document" in result["failures"][0]["reason"]


def test_citation_assertion_rejects_bare_id_and_tampered_quote() -> None:
    runtime = AgentRuntime()
    request = SimpleNamespace(tenant_id="tenant-a")
    assertion = {"type": "citation", "document_id": "refund-policy-v1"}

    bare_id_run = SimpleNamespace(
        request=request,
        result={"citation": "refund-policy-v1", "grounded": True},
    )
    passed, reason = _evaluate_assertion(
        assertion,
        run=bare_id_run,
        runtime=runtime,
        audit=[],
        before_counts={},
    )

    assert passed is False
    assert "structured citations array" in reason

    tampered_run = SimpleNamespace(
        request=request,
        result={
            "citation": "refund-policy-v1",
            "citations": [
                {
                    "document_id": "refund-policy-v1",
                    "chunk_id": "refund-policy-v1#0",
                    "source": "policy",
                    "version": 1,
                    "quote": "Refunds never need approval.",
                }
            ],
            "grounded": True,
        },
    )
    passed, reason = _evaluate_assertion(
        assertion,
        run=tampered_run,
        runtime=runtime,
        audit=[],
        before_counts={},
    )

    assert passed is False
    assert "provenance" in reason


def test_eval_unknown_assertion_fails_closed(tmp_path) -> None:
    dataset = {
        "cases": [
            {
                "id": "unknown-assertion",
                "request": {
                    "principal": "agent@example.com",
                    "tenant_id": "tenant-a",
                    "ticket_tenant_id": "tenant-a",
                    "ticket_id": "EVAL-002",
                    "message": "What is the refund policy?",
                },
                "assertions": [{"type": "always_pass"}],
            }
        ]
    }
    path = tmp_path / "unknown.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")

    result = run_eval(path)

    assert result["failed"] == 1
    assert "unsupported assertion type" in result["failures"][0]["reason"]


def test_result_exists_defaults_to_true_and_can_assert_absence(tmp_path) -> None:
    dataset = {
        "cases": [
            {
                "id": "exists-semantics",
                "request": {
                    "principal": "agent@example.com",
                    "tenant_id": "tenant-a",
                    "ticket_tenant_id": "tenant-a",
                    "ticket_id": "EVAL-003",
                    "message": "What is the refund policy?",
                },
                "assertions": [
                    {"type": "result", "path": "status", "op": "exists"},
                    {
                        "type": "result",
                        "path": "result.nonexistent_field",
                        "op": "exists",
                        "value": False,
                    },
                ],
            }
        ]
    }
    path = tmp_path / "exists.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")

    result = run_eval(path)

    assert result["failed"] == 0
    assert result["assertions"] == 2

    dataset["cases"][0]["assertions"] = [
        {"type": "result", "path": "status", "op": "exists", "value": "false"}
    ]
    path.write_text(json.dumps(dataset), encoding="utf-8")
    invalid = run_eval(path)

    assert invalid["failed"] == 1
    assert "must be a boolean" in invalid["failures"][0]["reason"]


def test_eval_rejects_empty_dataset(tmp_path) -> None:
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="non-empty cases"):
        run_eval(path)
