from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, ClassVar


class ContractError(ValueError):
    pass


class RunStatus(StrEnum):
    CREATED = "created"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    DENIED = "denied"
    FAILED = "failed"


class Decision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class RiskLevel(StrEnum):
    LOW = "low"
    HIGH = "high"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")


def _strict_fields(data: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    unknown = set(data) - allowed
    missing = required - set(data)
    if unknown:
        raise ContractError(f"unknown fields: {sorted(unknown)}")
    if missing:
        raise ContractError(f"missing fields: {sorted(missing)}")


@dataclass(frozen=True)
class RunRequest:
    principal: str
    tenant_id: str
    ticket_tenant_id: str
    ticket_id: str
    message: str

    FIELDS: ClassVar[set[str]] = {
        "principal",
        "tenant_id",
        "ticket_tenant_id",
        "ticket_id",
        "message",
    }

    def __post_init__(self) -> None:
        for name in self.FIELDS:
            _require_text(name, getattr(self, name))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunRequest":
        _strict_fields(data, cls.FIELDS, cls.FIELDS)
        return cls(**data)


@dataclass(frozen=True)
class ToolCall:
    operation_id: str
    tool_name: str
    arguments: dict[str, Any]
    requested_by: str
    tenant_id: str
    trace_id: str
    risk_level: RiskLevel

    FIELDS: ClassVar[set[str]] = {
        "operation_id",
        "tool_name",
        "arguments",
        "requested_by",
        "tenant_id",
        "trace_id",
        "risk_level",
    }

    def __post_init__(self) -> None:
        for name in ("operation_id", "tool_name", "requested_by", "tenant_id", "trace_id"):
            _require_text(name, getattr(self, name))
        if not isinstance(self.arguments, dict):
            raise ContractError("arguments must be an object")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCall":
        _strict_fields(data, cls.FIELDS, cls.FIELDS)
        values = dict(data)
        values["risk_level"] = RiskLevel(values["risk_level"])
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason_code: str
    explanation: str


@dataclass(frozen=True)
class ErrorModel:
    code: str
    category: str
    recoverable: bool
    retryable: bool
    public_message: str


@dataclass
class RunRecord:
    run_id: str
    trace_id: str
    request: RunRequest
    status: RunStatus = RunStatus.CREATED
    pending_call: ToolCall | None = None
    result: dict[str, Any] | None = None
    error: ErrorModel | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    run_id: str
    trace_id: str
    actor: str
    action: str
    resource: str
    outcome: str
    reason_code: str
    created_at: str
