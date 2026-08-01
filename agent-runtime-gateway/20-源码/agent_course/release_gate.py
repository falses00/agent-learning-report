from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .evals import run_eval
from .memory_evals import run_memory_eval


class ReleaseGateError(ValueError):
    """Raised when release evidence is malformed or cannot be trusted."""


RELEASE_VERSION_FIELDS = {
    "agent_version",
    "prompt_version",
    "model_version",
    "tool_registry_version",
    "policy_version",
    "memory_policy_version",
    "knowledge_version",
    "eval_set_version",
    "grader_version",
}
MANIFEST_FIELDS = {
    "schema_version",
    "suite",
    "version",
    "profile",
    "release_versions",
    "policy",
    "source_suites",
    "judge_calibration",
    "metrics",
    "red_team",
    "regressions",
}
POLICY_FIELDS = {
    "required_splits",
    "required_categories",
    "required_red_team_categories",
    "min_case_pass_rate",
    "min_assertion_pass_rate",
    "min_judge_agreement",
    "max_critical_judge_false_passes",
    "max_p95_latency_ms",
    "max_cost_per_success",
    "max_flake_rate",
    "min_trajectory_coverage",
    "min_terminal_state_coverage",
    "require_private_holdout_for_profiles",
}
SOURCE_SUITE_FIELDS = {
    "id",
    "runner",
    "path",
    "split",
    "categories",
    "owner",
    "visibility",
    "trajectory_evidence",
    "terminal_state_evidence",
}
CALIBRATION_FIELDS = {"id", "human_label", "judge_label", "risk", "evidence_ref"}
RED_TEAM_FIELDS = {"id", "category", "case_id", "mutation", "evidence_ref"}
REGRESSION_FIELDS = {"id", "case_id", "owner", "source_ref", "evidence_ref"}
METRIC_FIELDS = {
    "p95_latency_ms",
    "cost_per_success",
    "flake_rate",
    "trajectory_coverage",
    "terminal_state_coverage",
    "evidence_ref",
}
ALLOWED_SPLITS = {"smoke", "golden", "regression", "red_team", "holdout"}
ALLOWED_VISIBILITY = {"public", "private"}
ALLOWED_LABELS = {"pass", "fail", "unknown"}
ALLOWED_RISKS = {"critical", "high", "medium", "low"}


def _reject_unknown(value: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ReleaseGateError(f"{path} has unknown fields: {', '.join(unknown)}")


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReleaseGateError(f"{path} must be an object")
    return value


def _items(value: Any, path: str, *, non_empty: bool = True) -> list[Any]:
    if not isinstance(value, list) or (non_empty and not value):
        suffix = "a non-empty array" if non_empty else "an array"
        raise ReleaseGateError(f"{path} must be {suffix}")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseGateError(f"{path} must be non-empty text")
    return value.strip()


def _number(value: Any, path: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReleaseGateError(f"{path} must be a number")
    number = float(value)
    if number < minimum:
        raise ReleaseGateError(f"{path} must be >= {minimum}")
    return number


def _ratio(value: Any, path: str) -> float:
    number = _number(value, path)
    if number > 1:
        raise ReleaseGateError(f"{path} must be <= 1")
    return number


def _string_list(value: Any, path: str) -> list[str]:
    output = [_text(item, f"{path}[{index}]") for index, item in enumerate(_items(value, path))]
    if len(set(output)) != len(output):
        raise ReleaseGateError(f"{path} must not contain duplicates")
    return output


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _safe_source_path(manifest_path: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ReleaseGateError("source suite path must be relative to the manifest directory")
    root = manifest_path.parent.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ReleaseGateError("source suite path escapes the eval-set directory") from exc
    if not candidate.is_file():
        raise ReleaseGateError(f"source suite does not exist: {relative}")
    return candidate


def _read_source_cases(path: Path, runner: str) -> list[dict[str, Any]]:
    if runner == "runtime":
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases = payload.get("cases") if isinstance(payload, dict) else None
        if not isinstance(cases, list) or not cases:
            raise ReleaseGateError(f"runtime source must contain non-empty cases[]: {path.name}")
        return [_mapping(item, f"{path.name}.cases[{index}]") for index, item in enumerate(cases)]
    if runner == "memory":
        cases: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                cases.append(_mapping(json.loads(line), f"{path.name}:{line_number}"))
            except json.JSONDecodeError as exc:
                raise ReleaseGateError(f"invalid JSONL at {path.name}:{line_number}") from exc
        if not cases:
            raise ReleaseGateError(f"memory source must contain JSONL cases: {path.name}")
        return cases
    raise ReleaseGateError(f"unsupported source suite runner: {runner}")


def _case_fingerprint(case: dict[str, Any]) -> str:
    request = case.get("request")
    if isinstance(request, dict):
        input_value: Any = {
            key: request.get(key)
            for key in ("tenant_id", "ticket_tenant_id", "message")
            if key in request
        }
    else:
        input_value = case.get("input", {"case_id": case.get("id")})
    return _digest(input_value)


def _validate_manifest(manifest: dict[str, Any]) -> None:
    _reject_unknown(manifest, MANIFEST_FIELDS, "manifest")
    if _text(manifest.get("schema_version"), "manifest.schema_version") != "1.0":
        raise ReleaseGateError("manifest.schema_version must be 1.0")
    _text(manifest.get("suite"), "manifest.suite")
    _text(manifest.get("version"), "manifest.version")
    _text(manifest.get("profile"), "manifest.profile")

    versions = _mapping(manifest.get("release_versions"), "manifest.release_versions")
    _reject_unknown(versions, RELEASE_VERSION_FIELDS, "manifest.release_versions")
    missing_versions = sorted(RELEASE_VERSION_FIELDS - set(versions))
    if missing_versions:
        raise ReleaseGateError(f"manifest.release_versions is missing: {', '.join(missing_versions)}")
    for field in RELEASE_VERSION_FIELDS:
        _text(versions[field], f"manifest.release_versions.{field}")

    policy = _mapping(manifest.get("policy"), "manifest.policy")
    _reject_unknown(policy, POLICY_FIELDS, "manifest.policy")
    required_policy = POLICY_FIELDS - {"require_private_holdout_for_profiles"}
    missing_policy = sorted(required_policy - set(policy))
    if missing_policy:
        raise ReleaseGateError(f"manifest.policy is missing: {', '.join(missing_policy)}")
    splits = _string_list(policy["required_splits"], "manifest.policy.required_splits")
    if set(splits) - ALLOWED_SPLITS:
        raise ReleaseGateError("manifest.policy.required_splits contains an unsupported split")
    _string_list(policy["required_categories"], "manifest.policy.required_categories")
    _string_list(
        policy["required_red_team_categories"],
        "manifest.policy.required_red_team_categories",
    )
    for field in (
        "min_case_pass_rate",
        "min_assertion_pass_rate",
        "min_judge_agreement",
        "min_trajectory_coverage",
        "min_terminal_state_coverage",
    ):
        _ratio(policy[field], f"manifest.policy.{field}")
    for field in (
        "max_critical_judge_false_passes",
        "max_p95_latency_ms",
        "max_cost_per_success",
    ):
        _number(policy[field], f"manifest.policy.{field}")
    _ratio(policy["max_flake_rate"], "manifest.policy.max_flake_rate")
    _string_list(
        policy.get("require_private_holdout_for_profiles", ["production"]),
        "manifest.policy.require_private_holdout_for_profiles",
    )

    source_ids: set[str] = set()
    for index, raw in enumerate(_items(manifest.get("source_suites"), "manifest.source_suites")):
        item = _mapping(raw, f"manifest.source_suites[{index}]")
        _reject_unknown(item, SOURCE_SUITE_FIELDS, f"manifest.source_suites[{index}]")
        for field in SOURCE_SUITE_FIELDS - {"trajectory_evidence", "terminal_state_evidence"}:
            if field == "categories":
                continue
            _text(item.get(field), f"manifest.source_suites[{index}].{field}")
        suite_id = item["id"]
        if suite_id in source_ids:
            raise ReleaseGateError("manifest.source_suites ids must be unique")
        source_ids.add(suite_id)
        if item["runner"] not in {"runtime", "memory"}:
            raise ReleaseGateError(f"unsupported source suite runner: {item['runner']}")
        if item["split"] not in ALLOWED_SPLITS:
            raise ReleaseGateError(f"unsupported source suite split: {item['split']}")
        if item["visibility"] not in ALLOWED_VISIBILITY:
            raise ReleaseGateError(f"unsupported source suite visibility: {item['visibility']}")
        _string_list(item.get("categories"), f"manifest.source_suites[{index}].categories")
        for field in ("trajectory_evidence", "terminal_state_evidence"):
            if not isinstance(item.get(field), bool):
                raise ReleaseGateError(f"manifest.source_suites[{index}].{field} must be boolean")

    for index, raw in enumerate(
        _items(manifest.get("judge_calibration"), "manifest.judge_calibration")
    ):
        item = _mapping(raw, f"manifest.judge_calibration[{index}]")
        _reject_unknown(item, CALIBRATION_FIELDS, f"manifest.judge_calibration[{index}]")
        for field in CALIBRATION_FIELDS:
            _text(item.get(field), f"manifest.judge_calibration[{index}].{field}")
        if item["human_label"] not in {"pass", "fail"}:
            raise ReleaseGateError("human calibration labels must be pass or fail")
        if item["judge_label"] not in ALLOWED_LABELS:
            raise ReleaseGateError("judge calibration label is unsupported")
        if item["risk"] not in ALLOWED_RISKS:
            raise ReleaseGateError("judge calibration risk is unsupported")

    for collection, fields in (
        ("red_team", RED_TEAM_FIELDS),
        ("regressions", REGRESSION_FIELDS),
    ):
        for index, raw in enumerate(_items(manifest.get(collection), f"manifest.{collection}")):
            item = _mapping(raw, f"manifest.{collection}[{index}]")
            _reject_unknown(item, fields, f"manifest.{collection}[{index}]")
            for field in fields:
                _text(item.get(field), f"manifest.{collection}[{index}].{field}")

    metrics = _mapping(manifest.get("metrics"), "manifest.metrics")
    _reject_unknown(metrics, METRIC_FIELDS, "manifest.metrics")
    if set(metrics) != METRIC_FIELDS:
        missing = sorted(METRIC_FIELDS - set(metrics))
        raise ReleaseGateError(f"manifest.metrics is missing: {', '.join(missing)}")
    for field in METRIC_FIELDS - {"evidence_ref"}:
        value = metrics[field]
        if field.endswith("coverage") or field == "flake_rate":
            _ratio(value, f"manifest.metrics.{field}")
        else:
            _number(value, f"manifest.metrics.{field}")
    _text(metrics["evidence_ref"], "manifest.metrics.evidence_ref")


def build_release_report(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path).resolve()
    try:
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "manifest",
        )
    except json.JSONDecodeError as exc:
        raise ReleaseGateError(f"invalid release manifest JSON: {exc}") from exc
    _validate_manifest(manifest)

    cases: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for source in manifest["source_suites"]:
        source_path = _safe_source_path(manifest_path, source["path"])
        source_cases = _read_source_cases(source_path, source["runner"])
        result = run_eval(source_path) if source["runner"] == "runtime" else run_memory_eval(source_path)
        result_by_id = {
            item["case_id"]: item for item in result.get("case_results", [])
        }
        if len(result_by_id) != len(source_cases):
            raise ReleaseGateError(
                f"source runner did not return one result per case: {source['id']}"
            )
        for case in source_cases:
            case_id = _text(case.get("id"), f"{source['id']}.case.id")
            if case_id in seen_case_ids:
                raise ReleaseGateError(f"duplicate case id across source suites: {case_id}")
            seen_case_ids.add(case_id)
            case_result = result_by_id.get(case_id)
            if not isinstance(case_result, dict):
                raise ReleaseGateError(f"source result is missing case: {case_id}")
            passed = bool(case_result.get("passed"))
            cases.append(
                {
                    "case_id": case_id,
                    "suite_id": source["id"],
                    "split": source["split"],
                    "categories": list(source["categories"]),
                    "owner": source["owner"],
                    "critical": bool(case_result.get("critical")),
                    "passed": passed,
                    "deterministic_passed": passed,
                    "judge_passed": None,
                    "assertions": int(case_result.get("assertions", 0)),
                    "assertions_passed": int(case_result.get("assertions_passed", 0)),
                    "trajectory_complete": bool(source["trajectory_evidence"]),
                    "terminal_state_verified": bool(source["terminal_state_evidence"]),
                    "input_fingerprint": _case_fingerprint(case),
                    "evidence_ref": f"{source['path']}#{case_id}",
                    "reasons": list(case_result.get("reasons", [])),
                }
            )
        source_reports.append(
            {
                "suite_id": source["id"],
                "runner": source["runner"],
                "path": source["path"],
                "split": source["split"],
                "categories": list(source["categories"]),
                "owner": source["owner"],
                "visibility": source["visibility"],
                "total": result["total"],
                "passed": result["passed"],
                "failed": result["failed"],
                "critical_failed": result["critical_failed"],
                "assertions": result["assertions"],
                "assertions_passed": result["assertions_passed"],
                "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            }
        )

    report = {
        "schema_version": manifest["schema_version"],
        "suite": manifest["suite"],
        "version": manifest["version"],
        "profile": manifest["profile"],
        "release_versions": copy.deepcopy(manifest["release_versions"]),
        "policy": copy.deepcopy(manifest["policy"]),
        "source_suites": source_reports,
        "cases": cases,
        "judge_calibration": copy.deepcopy(manifest["judge_calibration"]),
        "metrics": copy.deepcopy(manifest["metrics"]),
        "red_team": copy.deepcopy(manifest["red_team"]),
        "regressions": copy.deepcopy(manifest["regressions"]),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    report["evidence_sha256"] = _digest(report)
    return report


def evaluate_release_report(report: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    def block(code: str, detail: str, *, case_id: str | None = None) -> None:
        item: dict[str, Any] = {"code": code, "detail": detail}
        if case_id:
            item["case_id"] = case_id
        if item not in blockers:
            blockers.append(item)

    def warn(code: str, detail: str) -> None:
        item = {"code": code, "detail": detail}
        if item not in warnings:
            warnings.append(item)

    evidence_payload = copy.deepcopy(report)
    supplied_evidence_sha = evidence_payload.pop("evidence_sha256", None)
    computed_evidence_sha = _digest(evidence_payload)
    if not isinstance(supplied_evidence_sha, str) or not supplied_evidence_sha:
        block(
            "EVIDENCE_HASH_MISSING",
            "release evidence must include the hash created by the evidence builder",
        )
    elif supplied_evidence_sha != computed_evidence_sha:
        block(
            "EVIDENCE_HASH_MISMATCH",
            "release evidence changed after its evidence hash was created",
        )

    policy = _mapping(report.get("policy"), "report.policy")
    cases = [_mapping(item, "report.cases[]") for item in _items(report.get("cases"), "report.cases")]
    case_by_id = {str(item.get("case_id")): item for item in cases}
    if len(case_by_id) != len(cases):
        block("DUPLICATE_CASE_ID", "case ids must be unique across the release report")

    for field in RELEASE_VERSION_FIELDS:
        value = report.get("release_versions", {}).get(field)
        if not isinstance(value, str) or not value.strip():
            block("VERSION_MANIFEST_INCOMPLETE", f"missing release version: {field}")

    splits = {str(item.get("split")) for item in cases}
    for split in policy["required_splits"]:
        if split not in splits:
            block("EVAL_SPLIT_MISSING", f"required split is missing: {split}")
    categories = {
        str(category)
        for item in cases
        for category in item.get("categories", [])
    }
    for category in policy["required_categories"]:
        if category not in categories:
            block("EVAL_CATEGORY_MISSING", f"required category is missing: {category}")

    for item in cases:
        case_id = str(item.get("case_id", "missing-case-id"))
        deterministic_passed = item.get("deterministic_passed") is True
        passed = item.get("passed") is True and deterministic_passed
        if bool(item.get("critical")) and not passed:
            block(
                "CRITICAL_CASE_FAILED",
                "critical failures are zero-tolerance and cannot be averaged",
                case_id=case_id,
            )
        if bool(item.get("critical")) and item.get("judge_passed") is True and not deterministic_passed:
            block(
                "MODEL_JUDGE_CANNOT_OVERRIDE_RULE",
                "a model judge cannot override a failed deterministic control",
                case_id=case_id,
            )
        critical_categories = {"tool", "trajectory", "security", "durability", "memory"}
        if bool(item.get("critical")) and critical_categories.intersection(item.get("categories", [])):
            if item.get("trajectory_complete") is not True:
                block(
                    "TRAJECTORY_EVIDENCE_MISSING",
                    "critical action or security cases require a complete trajectory",
                    case_id=case_id,
                )
            if item.get("terminal_state_verified") is not True:
                block(
                    "TERMINAL_STATE_EVIDENCE_MISSING",
                    "critical cases require verification of the environment outcome",
                    case_id=case_id,
                )

    total = len(cases)
    passed_count = sum(
        item.get("passed") is True and item.get("deterministic_passed") is True
        for item in cases
    )
    case_pass_rate = passed_count / total
    assertion_total = sum(int(item.get("assertions", 0)) for item in cases)
    assertion_passed = sum(int(item.get("assertions_passed", 0)) for item in cases)
    assertion_pass_rate = assertion_passed / assertion_total if assertion_total else 0.0
    if case_pass_rate < float(policy["min_case_pass_rate"]):
        block(
            "CASE_PASS_RATE_BELOW_THRESHOLD",
            f"case pass rate {case_pass_rate:.4f} is below {policy['min_case_pass_rate']}",
        )
    if assertion_pass_rate < float(policy["min_assertion_pass_rate"]):
        block(
            "ASSERTION_PASS_RATE_BELOW_THRESHOLD",
            f"assertion pass rate {assertion_pass_rate:.4f} is below {policy['min_assertion_pass_rate']}",
        )

    calibration = _items(report.get("judge_calibration"), "report.judge_calibration")
    calibration_matches = sum(
        item.get("human_label") == item.get("judge_label") for item in calibration
    )
    judge_agreement = calibration_matches / len(calibration)
    critical_false_passes = sum(
        item.get("risk") == "critical"
        and item.get("human_label") == "fail"
        and item.get("judge_label") == "pass"
        for item in calibration
    )
    if judge_agreement < float(policy["min_judge_agreement"]):
        block(
            "JUDGE_CALIBRATION_BELOW_THRESHOLD",
            f"judge agreement {judge_agreement:.4f} is below {policy['min_judge_agreement']}",
        )
    if critical_false_passes > int(policy["max_critical_judge_false_passes"]):
        block(
            "JUDGE_CRITICAL_FALSE_PASS",
            f"judge produced {critical_false_passes} critical false pass(es)",
        )

    tuning_fingerprints = {
        str(item.get("input_fingerprint"))
        for item in cases
        if item.get("split") != "holdout"
    }
    holdout_fingerprints = {
        str(item.get("input_fingerprint"))
        for item in cases
        if item.get("split") == "holdout"
    }
    overlap = sorted(tuning_fingerprints & holdout_fingerprints)
    if overlap:
        block(
            "HOLDOUT_CONTAMINATION_DETECTED",
            f"{len(overlap)} holdout fingerprint(s) also appear in visible tuning splits",
        )
    holdout_suites = [
        item for item in report.get("source_suites", []) if item.get("split") == "holdout"
    ]
    private_holdout = any(item.get("visibility") == "private" for item in holdout_suites)
    private_profiles = policy.get("require_private_holdout_for_profiles", ["production"])
    if report.get("profile") in private_profiles and not private_holdout:
        block(
            "PRIVATE_HOLDOUT_REQUIRED",
            f"profile {report.get('profile')} requires an access-controlled holdout suite",
        )
    elif not private_holdout:
        warn(
            "PUBLIC_HOLDOUT_ONLY",
            "the committed holdout is a teaching example and cannot prove contamination resistance",
        )

    red_team = _items(report.get("red_team"), "report.red_team")
    red_team_categories = {str(item.get("category")) for item in red_team}
    for category in policy["required_red_team_categories"]:
        if category not in red_team_categories:
            block(
                "RED_TEAM_COVERAGE_MISSING",
                f"required red-team category is missing: {category}",
            )
    for item in red_team:
        case_id = str(item.get("case_id"))
        case = case_by_id.get(case_id)
        if case is None:
            block("RED_TEAM_CASE_ORPHANED", f"red-team case is missing: {case_id}")
        elif not bool(case.get("critical")) or not bool(case.get("deterministic_passed")):
            block(
                "RED_TEAM_CASE_NOT_BLOCKING",
                "red-team evidence must reference a passing critical deterministic case",
                case_id=case_id,
            )

    for item in _items(report.get("regressions"), "report.regressions"):
        case_id = str(item.get("case_id"))
        if case_id not in case_by_id:
            block("REGRESSION_CASE_ORPHANED", f"regression case is missing: {case_id}")
        for field in ("owner", "source_ref", "evidence_ref"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                block(
                    "REGRESSION_OWNERSHIP_INCOMPLETE",
                    f"regression {item.get('id')} is missing {field}",
                )

    metrics = _mapping(report.get("metrics"), "report.metrics")
    metric_rules = (
        ("p95_latency_ms", "max_p95_latency_ms", "P95_LATENCY_BUDGET_EXCEEDED"),
        ("cost_per_success", "max_cost_per_success", "COST_BUDGET_EXCEEDED"),
        ("flake_rate", "max_flake_rate", "FLAKE_RATE_EXCEEDED"),
    )
    for metric, threshold, code in metric_rules:
        if float(metrics.get(metric, float("inf"))) > float(policy[threshold]):
            block(code, f"{metric} {metrics.get(metric)} exceeds {policy[threshold]}")
    coverage_rules = (
        ("trajectory_coverage", "min_trajectory_coverage", "TRAJECTORY_COVERAGE_BELOW_THRESHOLD"),
        (
            "terminal_state_coverage",
            "min_terminal_state_coverage",
            "TERMINAL_STATE_COVERAGE_BELOW_THRESHOLD",
        ),
    )
    for metric, threshold, code in coverage_rules:
        if float(metrics.get(metric, -1)) < float(policy[threshold]):
            block(code, f"{metric} {metrics.get(metric)} is below {policy[threshold]}")

    summary = {
        "total_cases": total,
        "passed_cases": passed_count,
        "failed_cases": total - passed_count,
        "critical_failures": sum(
            bool(item.get("critical"))
            and not (item.get("passed") is True and item.get("deterministic_passed") is True)
            for item in cases
        ),
        "case_pass_rate": case_pass_rate,
        "assertions": assertion_total,
        "assertions_passed": assertion_passed,
        "assertion_pass_rate": assertion_pass_rate,
        "judge_agreement": judge_agreement,
        "judge_critical_false_passes": critical_false_passes,
        "holdout_overlap": len(overlap),
        "red_team_categories": sorted(red_team_categories),
    }
    decision = "pass" if not blockers else "block"
    result = {
        "suite": report.get("suite"),
        "version": report.get("version"),
        "profile": report.get("profile"),
        "release_decision": decision,
        "release_passed": decision == "pass",
        "summary": summary,
        "metrics": copy.deepcopy(metrics),
        "blockers": blockers,
        "warnings": warnings,
        "release_versions": copy.deepcopy(report.get("release_versions")),
        "source_suites": copy.deepcopy(report.get("source_suites")),
        "manifest_sha256": report.get("manifest_sha256"),
        "evidence_sha256": computed_evidence_sha,
    }
    result["decision_sha256"] = _digest(result)
    return result


def run_release_gate(path: str | Path) -> dict[str, Any]:
    return evaluate_release_report(build_release_report(path))
