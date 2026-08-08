from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RAGDiagnosisError(ValueError):
    """Raised when RAG diagnostic evidence is malformed or unsupported."""


SIGNAL_FIELDS = {
    "answer_in_corpus",
    "parse_fidelity",
    "boundary_split",
    "exact_identifier_miss",
    "domain_shift",
    "query_ambiguity",
    "retrieval_recall",
    "retrieval_precision",
    "multi_hop",
    "path_coverage",
    "visual_evidence",
    "visual_recall",
    "citation_support",
    "cache_stale",
    "cross_tenant_candidates",
    "injection_hits",
    "p95_latency_ms",
    "latency_budget_ms",
}
SUITE_FIELDS = {"suite", "version", "cases"}
CASE_FIELDS = {"id", "critical", "signals", "assertions"}
ASSERTION_FIELDS = {"type", "path", "value"}


def _strict(value: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise RAGDiagnosisError(f"{path} has unknown fields: {unknown}")


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RAGDiagnosisError(f"{path} must be non-empty text")
    return value.strip()


def _ratio(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RAGDiagnosisError(f"{path} must be a number")
    number = float(value)
    if not 0 <= number <= 1:
        raise RAGDiagnosisError(f"{path} must be between 0 and 1")
    return number


def _count(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RAGDiagnosisError(f"{path} must be a non-negative integer")
    return value


def _latency(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise RAGDiagnosisError(f"{path} must be a non-negative number")
    return float(value)


def _validate_signals(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RAGDiagnosisError("signals must be an object")
    _strict(raw, SIGNAL_FIELDS, "signals")
    defaults: dict[str, Any] = {
        "answer_in_corpus": True,
        "parse_fidelity": 1.0,
        "boundary_split": False,
        "exact_identifier_miss": False,
        "domain_shift": False,
        "query_ambiguity": False,
        "retrieval_recall": 1.0,
        "retrieval_precision": 1.0,
        "multi_hop": False,
        "path_coverage": 1.0,
        "visual_evidence": False,
        "visual_recall": 1.0,
        "citation_support": 1.0,
        "cache_stale": False,
        "cross_tenant_candidates": 0,
        "injection_hits": 0,
        "p95_latency_ms": 0.0,
        "latency_budget_ms": 1000.0,
    }
    values = {**defaults, **raw}
    for field in (
        "answer_in_corpus",
        "boundary_split",
        "exact_identifier_miss",
        "domain_shift",
        "query_ambiguity",
        "multi_hop",
        "visual_evidence",
        "cache_stale",
    ):
        if not isinstance(values[field], bool):
            raise RAGDiagnosisError(f"signals.{field} must be a boolean")
    for field in (
        "parse_fidelity",
        "retrieval_recall",
        "retrieval_precision",
        "path_coverage",
        "visual_recall",
        "citation_support",
    ):
        values[field] = _ratio(values[field], f"signals.{field}")
    for field in ("cross_tenant_candidates", "injection_hits"):
        values[field] = _count(values[field], f"signals.{field}")
    for field in ("p95_latency_ms", "latency_budget_ms"):
        values[field] = _latency(values[field], f"signals.{field}")
    if values["latency_budget_ms"] <= 0:
        raise RAGDiagnosisError("signals.latency_budget_ms must be greater than zero")
    return values


def _result(
    action: str,
    layer: str,
    reason: str,
    experiment: str,
    metrics: list[str],
    rollback: str,
    *,
    blocker: str | None = None,
) -> dict[str, Any]:
    blockers = [blocker] if blocker else []
    return {
        "action": action,
        "layer": layer,
        "reason": reason,
        "minimal_experiment": experiment,
        "metrics": metrics,
        "rollback": rollback,
        "release_decision": "block" if blockers else "experiment",
        "blockers": blockers,
    }


def diagnose_rag(raw_signals: dict[str, Any]) -> dict[str, Any]:
    """Select the first bounded intervention from observable RAG failure signals."""

    s = _validate_signals(raw_signals)
    if s["cross_tenant_candidates"]:
        return _result(
            "enforce_acl_before_retrieval",
            "security",
            "Unauthorized candidates crossed the retrieval boundary.",
            "Query tenant A and B canary documents with the same text and inspect candidates, context, cache, and trace.",
            ["cross_tenant_leak", "filtered_recall", "retrieval_p95"],
            "Disable the new index and restore the last ACL-verified namespace.",
            blocker="RAG_ACL_VIOLATION",
        )
    if s["injection_hits"]:
        return _result(
            "quarantine_untrusted_source",
            "security",
            "Retrieved content contains instructions that must remain untrusted data.",
            "Inject a canary document that requests a forbidden tool call and verify quarantine, refusal, and audit evidence.",
            ["injection_success_rate", "poison_hit_at_k", "false_positive_rate"],
            "Remove the suspect source version and rebuild every derived index and cache.",
            blocker="RAG_INJECTION_DETECTED",
        )
    if s["cache_stale"]:
        return _result(
            "invalidate_versioned_cache",
            "freshness",
            "A cache or derived index served evidence older than the authoritative source version.",
            "Change source, model, prompt, and index versions independently and verify cache-key invalidation.",
            ["stale_answer_rate", "index_lag", "wrong_cache_hit_rate"],
            "Bypass cache and read from the last verified index while rebuilding.",
            blocker="RAG_STALE_EVIDENCE",
        )
    if s["citation_support"] < 0.95:
        return _result(
            "validate_claims_or_abstain",
            "generation",
            "The answer contains claims that are not supported by a verifiable source span.",
            "Split the answer into claims and require source id, version, page/chunk, and quote support for each.",
            ["citation_precision", "citation_recall", "unsupported_claim_rate", "abstention_precision"],
            "Remove unsupported claims or return a structured refusal.",
            blocker="RAG_UNSUPPORTED_CLAIM",
        )
    if not s["answer_in_corpus"]:
        return _result(
            "repair_source_coverage",
            "data",
            "Retrieval cannot recover evidence that is absent from the authorized corpus.",
            "Add a versioned source fixture and compare coverage before changing retriever parameters.",
            ["corpus_coverage", "index_lag", "source_version_hit_rate"],
            "Remove the source version if provenance or authorization cannot be established.",
        )
    if s["parse_fidelity"] < 0.95:
        return _result(
            "repair_layout_parsing",
            "ingestion",
            "The source exists, but parsing lost reading order, table cells, or page anchors.",
            "Compare text-only, OCR, and layout-aware parsing on a page-level golden set.",
            ["parse_fidelity", "table_cell_f1", "page_anchor_accuracy"],
            "Route unsupported pages to the previous parser or human review.",
        )
    if s["visual_evidence"] and s["visual_recall"] < 0.8:
        return _result(
            "add_multimodal_retrieval",
            "retrieval",
            "Text extraction cannot preserve all visual, formula, or layout evidence.",
            "Compare OCR-text retrieval, page-image retrieval, and a mixed route on visual questions.",
            ["page_recall", "visual_answer_accuracy", "modality_attribution"],
            "Fall back to text retrieval and refuse claims without page-region evidence.",
        )
    if s["boundary_split"] and s["retrieval_recall"] < 0.8:
        return _result(
            "rechunk_with_parent_context",
            "chunking",
            "The gold evidence is present but split away from its definition, condition, or parent section.",
            "Ablate fixed, structural, parent-child, semantic, and late chunking with one unchanged retriever.",
            ["context_recall", "chunk_hit_rate", "citation_span_coverage"],
            "Restore the fixed/structural baseline and preserve raw document anchors.",
        )
    if s["exact_identifier_miss"]:
        return _result(
            "add_hybrid_retrieval",
            "retrieval",
            "Dense similarity missed an exact identifier or rare keyword.",
            "Compare BM25, dense, and reciprocal-rank fusion on exact and semantic query slices.",
            ["exact_match_recall", "recall_at_50", "rrf_win_rate"],
            "Disable fusion if it fails to beat either single-path baseline.",
        )
    if s["domain_shift"] and s["retrieval_recall"] < 0.8:
        return _result(
            "shadow_domain_embedding",
            "index",
            "The embedding space does not represent domain terminology or language well enough.",
            "Build a shadow index and compare general, multilingual, and domain-adapted embeddings.",
            ["domain_ndcg", "terminology_recall", "cross_language_recall"],
            "Switch the read alias back to the previous versioned index.",
        )
    if s["query_ambiguity"] and s["retrieval_recall"] < 0.8:
        return _result(
            "rewrite_or_clarify_query",
            "query",
            "A short, elliptical, or underspecified query did not express the retrieval intent.",
            "Compare original query, deterministic normalization, multi-query, HyDE, and clarification.",
            ["rewrite_win_rate", "hallucinated_expansion_rate", "recall_at_k"],
            "Use the original query or ask a clarification question when rewrite confidence is low.",
        )
    if s["multi_hop"] and s["path_coverage"] < 0.8:
        return _result(
            "decompose_then_test_graph",
            "reasoning_retrieval",
            "A single retrieval pass did not cover every required relation or document hop.",
            "Compare query decomposition against flat retrieval before adding graph or hierarchical indexing.",
            ["multi_hop_f1", "path_coverage", "entity_edge_precision", "index_cost"],
            "Return to decomposition plus cited passages if graph extraction is noisy.",
        )
    if s["retrieval_recall"] >= 0.8 and s["retrieval_precision"] < 0.6:
        return _result(
            "rerank_candidates",
            "ranking",
            "The gold evidence was retrieved but noisy candidates displaced it in the context pack.",
            "Retrieve a fixed top-50 set and ablate cross-encoder, late-interaction, MMR, and metadata ranking.",
            ["precision_at_5", "mrr", "ndcg", "rerank_p95"],
            "Fall back to the last deterministic ranking if reranking times out or reduces nDCG.",
        )
    if s["p95_latency_ms"] > s["latency_budget_ms"]:
        return _result(
            "route_and_budget_expensive_steps",
            "operations",
            "The quality path exceeds its p95 latency budget.",
            "Route simple and multi-hop queries separately; ablate top-k, rerank depth, graph, and compression.",
            ["p95_latency", "cost_per_query", "quality_delta", "route_accuracy"],
            "Disable the most expensive step whose measured quality lift does not justify its budget.",
        )
    return _result(
        "keep_baseline",
        "baseline",
        "No observed signal justifies additional RAG complexity.",
        "Keep a frozen baseline and add a new failure case before changing the pipeline.",
        ["context_recall", "citation_support", "p95_latency", "cost_per_query"],
        "No rollback is required because no change is proposed.",
    )


def _lookup(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise RAGDiagnosisError(f"assertion path does not exist: {path}")
        current = current[segment]
    return current


def _assert(result: dict[str, Any], assertion: dict[str, Any]) -> bool:
    actual = _lookup(result, assertion["path"])
    if assertion["type"] == "equals":
        return actual == assertion["value"]
    if assertion["type"] == "contains":
        return isinstance(actual, list) and assertion["value"] in actual
    raise RAGDiagnosisError(f"unsupported assertion type: {assertion['type']}")


def run_rag_diagnostic_eval(path: str | Path) -> dict[str, Any]:
    suite_path = Path(path).resolve()
    try:
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RAGDiagnosisError(f"cannot load RAG diagnostic suite: {exc}") from exc
    if not isinstance(suite, dict):
        raise RAGDiagnosisError("suite must be an object")
    _strict(suite, SUITE_FIELDS, "suite")
    _text(suite.get("suite"), "suite.suite")
    _text(suite.get("version"), "suite.version")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise RAGDiagnosisError("suite.cases must be a non-empty array")

    results = []
    failures = []
    seen: set[str] = set()
    assertion_total = 0
    assertion_passed = 0
    for index, raw in enumerate(cases):
        if not isinstance(raw, dict):
            raise RAGDiagnosisError(f"suite.cases[{index}] must be an object")
        _strict(raw, CASE_FIELDS, f"suite.cases[{index}]")
        case_id = _text(raw.get("id"), f"suite.cases[{index}].id")
        if case_id in seen:
            raise RAGDiagnosisError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        if not isinstance(raw.get("critical"), bool):
            raise RAGDiagnosisError(f"suite.cases[{index}].critical must be a boolean")
        assertions = raw.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            raise RAGDiagnosisError(f"suite.cases[{index}].assertions must be non-empty")

        diagnosis: dict[str, Any]
        diagnostic_error = ""
        try:
            diagnosis = diagnose_rag(raw.get("signals"))
        except RAGDiagnosisError as exc:
            diagnostic_error = str(exc)
            diagnosis = {
                "action": "fail_closed",
                "layer": "contract",
                "release_decision": "block",
                "blockers": ["RAG_DIAGNOSTIC_CONTRACT_ERROR"],
            }

        checks = []
        reasons = []
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, dict):
                raise RAGDiagnosisError(
                    f"suite.cases[{index}].assertions[{assertion_index}] must be an object"
                )
            _strict(assertion, ASSERTION_FIELDS, "assertion")
            _text(assertion.get("path"), "assertion.path")
            _text(assertion.get("type"), "assertion.type")
            try:
                passed = _assert(diagnosis, assertion)
            except RAGDiagnosisError as exc:
                passed = False
                reasons.append(str(exc))
            checks.append(passed)
            if not passed and not reasons:
                reasons.append(
                    f"{assertion['path']} did not satisfy {assertion['type']} {assertion['value']!r}"
                )
        if diagnostic_error:
            reasons.insert(0, f"diagnostic contract failed closed: {diagnostic_error}")
        passed = all(checks) and not diagnostic_error
        assertion_total += len(checks)
        assertion_passed += sum(checks)
        item = {
            "case_id": case_id,
            "critical": raw["critical"],
            "passed": passed,
            "action": diagnosis.get("action"),
            "layer": diagnosis.get("layer"),
            "release_decision": diagnosis.get("release_decision"),
            "blockers": diagnosis.get("blockers", []),
            "assertions": len(checks),
            "assertions_passed": sum(checks),
            "reasons": reasons,
        }
        if diagnostic_error:
            item["diagnostic_error"] = diagnostic_error
        results.append(item)
        if not passed:
            failures.append({"case_id": case_id, "reasons": reasons})

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
