from __future__ import annotations

import ipaddress
import json
import posixpath
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


class SecurityContractError(ValueError):
    """Raised when the security policy or request violates its contract."""


POLICY_FIELDS = {
    "workspace_root",
    "allowed_egress_hosts",
    "approved_credential_refs",
    "tools",
    "mcp_servers",
}
TOOL_FIELDS = {
    "risk",
    "required_scopes",
    "sandbox_required",
    "approval_required",
    "credential_refs",
    "network",
    "filesystem",
    "write",
}
MCP_FIELDS = {"version", "capabilities"}
REQUEST_FIELDS = {
    "tool",
    "principal_scopes",
    "source_trust",
    "contains_instructions",
    "raw_content",
    "requested_path",
    "symlink_escape",
    "requested_url",
    "resolved_ips",
    "redirect_urls",
    "credential_ref",
    "approval",
    "sandbox_available",
    "operation_id",
    "mcp",
    "policy_available",
}
MCP_REQUEST_FIELDS = {"name", "version", "capabilities"}
SUITE_FIELDS = {"suite", "version", "policy", "cases"}
CASE_FIELDS = {
    "id",
    "critical",
    "request",
    "expected_decision",
    "expected_blockers",
    "forbidden_blockers",
    "expected_side_effect",
}

SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:api[_-]?key|token|password)\s*[=:]\s*[^\s]{8,}", re.I),
)


def _strict(value: dict[str, Any], allowed: set[str], required: set[str], name: str) -> None:
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        raise SecurityContractError(f"{name} has unknown fields: {sorted(unknown)}")
    if missing:
        raise SecurityContractError(f"{name} is missing fields: {sorted(missing)}")


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SecurityContractError(f"{name} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise SecurityContractError(f"{name} must be an array")
    result = []
    for index, item in enumerate(value):
        result.append(_text(item, f"{name}[{index}]"))
    return result


def _boolean(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise SecurityContractError(f"{name} must be a boolean")
    return value


def _validate_policy(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SecurityContractError("policy must be an object")
    _strict(raw, POLICY_FIELDS, POLICY_FIELDS, "policy")
    workspace_root = posixpath.normpath(_text(raw["workspace_root"], "policy.workspace_root"))
    if not workspace_root.startswith("/"):
        raise SecurityContractError("policy.workspace_root must be an absolute POSIX path")
    allowed_hosts = {
        host.lower().rstrip(".")
        for host in _string_list(raw["allowed_egress_hosts"], "policy.allowed_egress_hosts")
    }
    credential_refs = set(
        _string_list(raw["approved_credential_refs"], "policy.approved_credential_refs")
    )

    if not isinstance(raw["tools"], dict) or not raw["tools"]:
        raise SecurityContractError("policy.tools must be a non-empty object")
    tools: dict[str, dict[str, Any]] = {}
    for name, spec in raw["tools"].items():
        tool_name = _text(name, "policy.tools key")
        if not isinstance(spec, dict):
            raise SecurityContractError(f"policy.tools.{tool_name} must be an object")
        _strict(spec, TOOL_FIELDS, TOOL_FIELDS, f"policy.tools.{tool_name}")
        risk = _text(spec["risk"], f"policy.tools.{tool_name}.risk")
        if risk not in {"low", "medium", "high", "critical"}:
            raise SecurityContractError(f"policy.tools.{tool_name}.risk is invalid")
        network = _text(spec["network"], f"policy.tools.{tool_name}.network")
        filesystem = _text(spec["filesystem"], f"policy.tools.{tool_name}.filesystem")
        if network not in {"deny", "allowlist"}:
            raise SecurityContractError(f"policy.tools.{tool_name}.network is invalid")
        if filesystem not in {"deny", "workspace"}:
            raise SecurityContractError(f"policy.tools.{tool_name}.filesystem is invalid")
        refs = set(_string_list(spec["credential_refs"], f"policy.tools.{tool_name}.credential_refs"))
        if not refs <= credential_refs:
            raise SecurityContractError(f"policy.tools.{tool_name} references unapproved credentials")
        tools[tool_name] = {
            "risk": risk,
            "required_scopes": set(
                _string_list(spec["required_scopes"], f"policy.tools.{tool_name}.required_scopes")
            ),
            "sandbox_required": _boolean(
                spec["sandbox_required"], f"policy.tools.{tool_name}.sandbox_required"
            ),
            "approval_required": _boolean(
                spec["approval_required"], f"policy.tools.{tool_name}.approval_required"
            ),
            "credential_refs": refs,
            "network": network,
            "filesystem": filesystem,
            "write": _boolean(spec["write"], f"policy.tools.{tool_name}.write"),
        }

    if not isinstance(raw["mcp_servers"], dict):
        raise SecurityContractError("policy.mcp_servers must be an object")
    servers: dict[str, dict[str, Any]] = {}
    for name, spec in raw["mcp_servers"].items():
        server_name = _text(name, "policy.mcp_servers key")
        if not isinstance(spec, dict):
            raise SecurityContractError(f"policy.mcp_servers.{server_name} must be an object")
        _strict(spec, MCP_FIELDS, MCP_FIELDS, f"policy.mcp_servers.{server_name}")
        servers[server_name] = {
            "version": _text(spec["version"], f"policy.mcp_servers.{server_name}.version"),
            "capabilities": set(
                _string_list(spec["capabilities"], f"policy.mcp_servers.{server_name}.capabilities")
            ),
        }

    return {
        "workspace_root": workspace_root,
        "allowed_egress_hosts": allowed_hosts,
        "approved_credential_refs": credential_refs,
        "tools": tools,
        "mcp_servers": servers,
    }


def _validate_request(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SecurityContractError("request must be an object")
    _strict(raw, REQUEST_FIELDS, {"tool", "principal_scopes"}, "request")
    request = {
        "tool": _text(raw["tool"], "request.tool"),
        "principal_scopes": set(_string_list(raw["principal_scopes"], "request.principal_scopes")),
        "source_trust": raw.get("source_trust", "trusted"),
        "contains_instructions": raw.get("contains_instructions", False),
        "raw_content": raw.get("raw_content", ""),
        "requested_path": raw.get("requested_path"),
        "symlink_escape": raw.get("symlink_escape", False),
        "requested_url": raw.get("requested_url"),
        "resolved_ips": raw.get("resolved_ips", []),
        "redirect_urls": raw.get("redirect_urls", []),
        "credential_ref": raw.get("credential_ref"),
        "approval": raw.get("approval", False),
        "sandbox_available": raw.get("sandbox_available", True),
        "operation_id": raw.get("operation_id"),
        "mcp": raw.get("mcp"),
        "policy_available": raw.get("policy_available", True),
    }
    if request["source_trust"] not in {"trusted", "untrusted"}:
        raise SecurityContractError("request.source_trust must be trusted or untrusted")
    for field in ("contains_instructions", "symlink_escape", "approval", "sandbox_available", "policy_available"):
        _boolean(request[field], f"request.{field}")
    if not isinstance(request["raw_content"], str):
        raise SecurityContractError("request.raw_content must be a string")
    for field in ("requested_path", "requested_url", "credential_ref", "operation_id"):
        if request[field] is not None:
            request[field] = _text(request[field], f"request.{field}")
    request["resolved_ips"] = _string_list(request["resolved_ips"], "request.resolved_ips")
    request["redirect_urls"] = _string_list(request["redirect_urls"], "request.redirect_urls")
    if request["mcp"] is not None:
        if not isinstance(request["mcp"], dict):
            raise SecurityContractError("request.mcp must be an object")
        _strict(request["mcp"], MCP_REQUEST_FIELDS, MCP_REQUEST_FIELDS, "request.mcp")
        request["mcp"] = {
            "name": _text(request["mcp"]["name"], "request.mcp.name"),
            "version": _text(request["mcp"]["version"], "request.mcp.version"),
            "capabilities": set(
                _string_list(request["mcp"]["capabilities"], "request.mcp.capabilities")
            ),
        }
    return request


def _has_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def _path_blockers(path: str, workspace_root: str) -> list[str]:
    if "\x00" in path:
        return ["PATH_INVALID"]
    decoded = path
    for _ in range(3):
        candidate = unquote(decoded)
        if candidate == decoded:
            break
        decoded = candidate
    normalized = posixpath.normpath(decoded.replace("\\", "/"))
    if not normalized.startswith("/"):
        normalized = posixpath.normpath(posixpath.join(workspace_root, normalized))
    try:
        inside = posixpath.commonpath([workspace_root, normalized]) == workspace_root
    except ValueError:
        inside = False
    return [] if inside else ["PATH_OUTSIDE_WORKSPACE"]


def _host_and_ip_blockers(url: str, allowed_hosts: set[str]) -> list[str]:
    blockers: list[str] = []
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower().rstrip(".")
    except (UnicodeError, ValueError):
        return ["EGRESS_URL_INVALID"]
    if parsed.scheme != "https":
        blockers.append("EGRESS_SCHEME_DENIED")
    if parsed.username or parsed.password or not host:
        blockers.append("EGRESS_URL_INVALID")
    if host not in allowed_hosts:
        blockers.append("EGRESS_HOST_DENIED")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        blockers.append("SSRF_ADDRESS_DENIED")
    return blockers


def evaluate_security_request(raw_policy: dict[str, Any], raw_request: dict[str, Any]) -> dict[str, Any]:
    policy = _validate_policy(raw_policy)
    request = _validate_request(raw_request)
    blockers: list[str] = []

    if not request["policy_available"]:
        blockers.append("SECURITY_POLICY_UNAVAILABLE")
    tool = policy["tools"].get(request["tool"])
    if tool is None:
        blockers.append("TOOL_NOT_REGISTERED")
    else:
        if not tool["required_scopes"] <= request["principal_scopes"]:
            blockers.append("TOOL_SCOPE_DENIED")
        if tool["sandbox_required"] and not request["sandbox_available"]:
            blockers.append("SANDBOX_REQUIRED")
        if tool["write"] and not request["operation_id"]:
            blockers.append("OPERATION_ID_REQUIRED")
        if tool["credential_refs"]:
            if not request["credential_ref"]:
                blockers.append("CREDENTIAL_REF_REQUIRED")
            elif request["credential_ref"] not in tool["credential_refs"]:
                blockers.append("CREDENTIAL_REF_DENIED")
        elif request["credential_ref"]:
            blockers.append("CREDENTIAL_REF_DENIED")

        if request["requested_path"]:
            if tool["filesystem"] != "workspace":
                blockers.append("FILESYSTEM_NOT_ALLOWED")
            else:
                blockers.extend(_path_blockers(request["requested_path"], policy["workspace_root"]))
        if request["symlink_escape"]:
            blockers.append("SYMLINK_ESCAPE_DENIED")

        urls = ([request["requested_url"]] if request["requested_url"] else []) + request["redirect_urls"]
        if urls:
            if tool["network"] != "allowlist":
                blockers.append("EGRESS_NOT_ALLOWED")
            else:
                for url in urls:
                    blockers.extend(_host_and_ip_blockers(url, policy["allowed_egress_hosts"]))
                if not request["resolved_ips"]:
                    blockers.append("DNS_EVIDENCE_REQUIRED")
                for value in request["resolved_ips"]:
                    try:
                        address = ipaddress.ip_address(value)
                    except ValueError:
                        blockers.append("DNS_EVIDENCE_INVALID")
                    else:
                        if not address.is_global:
                            blockers.append("SSRF_ADDRESS_DENIED")

        if tool["approval_required"] and not request["approval"]:
            blockers.append("APPROVAL_REQUIRED")

    if request["source_trust"] == "untrusted" and request["contains_instructions"]:
        blockers.append("UNTRUSTED_INSTRUCTION")
    if _has_secret(request["raw_content"]):
        blockers.append("RAW_SECRET_DETECTED")

    if request["mcp"] is not None:
        server = policy["mcp_servers"].get(request["mcp"]["name"])
        if server is None:
            blockers.append("MCP_SERVER_NOT_APPROVED")
        else:
            if request["mcp"]["version"] != server["version"]:
                blockers.append("MCP_VERSION_MISMATCH")
            if not request["mcp"]["capabilities"] <= server["capabilities"]:
                blockers.append("MCP_CAPABILITY_ESCALATION")

    blockers = sorted(set(blockers))
    if "UNTRUSTED_INSTRUCTION" in blockers:
        decision = "quarantine"
    elif blockers == ["APPROVAL_REQUIRED"]:
        decision = "require_approval"
    elif blockers:
        decision = "block"
    else:
        decision = "allow"
    side_effect_allowed = decision == "allow"
    audit = {
        "action": "security.evaluate",
        "tool": request["tool"],
        "decision": decision,
        "reason_codes": blockers or ["SECURITY_POLICY_ALLOWED"],
        "content_capture": "metadata_only",
    }
    return {
        "decision": decision,
        "blockers": blockers,
        "side_effect_allowed": side_effect_allowed,
        "controls": {
            "scope_checked": True,
            "egress_checked": bool(request["requested_url"] or request["redirect_urls"]),
            "filesystem_checked": bool(request["requested_path"] or request["symlink_escape"]),
            "sandbox_checked": bool(tool and tool["sandbox_required"]),
            "mcp_checked": request["mcp"] is not None,
            "secret_scanned": True,
        },
        "audit": audit,
    }


def _load_suite(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecurityContractError(f"cannot load security suite: {exc}") from exc
    if not isinstance(value, dict):
        raise SecurityContractError("security suite must be an object")
    return value


def run_security_eval(path: str | Path) -> dict[str, Any]:
    suite = _load_suite(Path(path).resolve())
    _strict(suite, SUITE_FIELDS, SUITE_FIELDS, "suite")
    suite_name = _text(suite["suite"], "suite.suite")
    version = _text(suite["version"], "suite.version")
    _validate_policy(suite["policy"])
    if not isinstance(suite["cases"], list) or not suite["cases"]:
        raise SecurityContractError("suite.cases must be a non-empty array")

    results = []
    failures = []
    assertions = 0
    assertions_passed = 0
    ids: set[str] = set()
    for index, spec in enumerate(suite["cases"]):
        if not isinstance(spec, dict):
            raise SecurityContractError(f"suite.cases[{index}] must be an object")
        _strict(spec, CASE_FIELDS, CASE_FIELDS, f"suite.cases[{index}]")
        case_id = _text(spec["id"], f"suite.cases[{index}].id")
        if case_id in ids:
            raise SecurityContractError(f"duplicate case id: {case_id}")
        ids.add(case_id)
        _boolean(spec["critical"], f"suite.cases[{index}].critical")
        expected = _text(spec["expected_decision"], f"suite.cases[{index}].expected_decision")
        if expected not in {"allow", "require_approval", "block", "quarantine"}:
            raise SecurityContractError("expected_decision is invalid")
        expected_blockers = set(_string_list(spec["expected_blockers"], "expected_blockers"))
        forbidden_blockers = set(_string_list(spec["forbidden_blockers"], "forbidden_blockers"))
        expected_side_effect = _boolean(spec["expected_side_effect"], "expected_side_effect")
        contract_error = None
        try:
            evaluated = evaluate_security_request(suite["policy"], spec["request"])
        except SecurityContractError as exc:
            contract_error = str(exc)
            evaluated = {
                "decision": "block",
                "blockers": ["SECURITY_EVAL_FAILED_CLOSED"],
                "side_effect_allowed": False,
                "audit": {
                    "action": "security.evaluate",
                    "decision": "block",
                    "reason_codes": ["SECURITY_EVAL_FAILED_CLOSED"],
                    "content_capture": "metadata_only",
                },
            }
        blocker_codes = set(evaluated["blockers"])
        checks = [
            evaluated["decision"] == expected,
            expected_blockers <= blocker_codes,
            not (forbidden_blockers & blocker_codes),
            evaluated["side_effect_allowed"] == expected_side_effect,
            set(evaluated["audit"]["reason_codes"]) == (blocker_codes or {"SECURITY_POLICY_ALLOWED"}),
            evaluated["audit"]["content_capture"] == "metadata_only",
        ]
        passed = all(checks)
        assertions += len(checks)
        assertions_passed += sum(checks)
        reasons = []
        if not checks[0]:
            reasons.append(f"decision {evaluated['decision']!r} != {expected!r}")
        if not checks[1]:
            reasons.append(f"missing blockers: {sorted(expected_blockers - blocker_codes)}")
        if not checks[2]:
            reasons.append(f"forbidden blockers: {sorted(forbidden_blockers & blocker_codes)}")
        if not checks[3]:
            reasons.append("side effect decision does not match expectation")
        if not checks[4] or not checks[5]:
            reasons.append("audit evidence is incomplete")
        result = {
            "case_id": case_id,
            "critical": spec["critical"],
            "passed": passed,
            "decision": evaluated["decision"],
            "blocker_codes": sorted(blocker_codes),
            "side_effect_allowed": evaluated["side_effect_allowed"],
            "assertions": len(checks),
            "assertions_passed": sum(checks),
            "reasons": reasons,
        }
        if contract_error:
            result["contract_error"] = contract_error
        results.append(result)
        if not passed:
            failures.append({"case_id": case_id, "reasons": reasons})

    critical_failed = sum(not item["passed"] and item["critical"] for item in results)
    return {
        "suite": suite_name,
        "version": version,
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": len(failures),
        "critical_failed": critical_failed,
        "release_passed": not failures,
        "assertions": assertions,
        "assertions_passed": assertions_passed,
        "case_results": results,
        "failures": failures,
    }
