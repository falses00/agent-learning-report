from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .contracts import ContractError, Decision, PolicyDecision, RiskLevel, ToolCall
from .policy import PolicyEngine


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    risk_level: RiskLevel
    executor: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self.refund_execution_count = 0
        self._tools = {
            "knowledge.retrieve": ToolDefinition(
                "knowledge.retrieve", RiskLevel.LOW, self._retrieve_knowledge
            ),
            "billing.refund": ToolDefinition(
                "billing.refund", RiskLevel.HIGH, self._refund
            ),
        }

    def definition(self, tool_name: str) -> ToolDefinition:
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise ContractError(f"unknown tool: {tool_name}") from exc

    def _execute_authorized(self, call: ToolCall, permit: object) -> dict[str, Any]:
        if permit is not self.__execution_permit:
            raise ContractError("tool execution requires a gateway permit")
        definition = self.definition(call.tool_name)
        if call.risk_level is not definition.risk_level:
            raise ContractError("tool risk level does not match registry")
        return definition.executor(call.arguments)

    @property
    def __execution_permit(self) -> object:
        if not hasattr(self, "_ToolRegistry__permit"):
            self.__permit = object()
        return self.__permit

    def _gateway_permit(self) -> object:
        return self.__execution_permit

    @staticmethod
    def _retrieve_knowledge(arguments: dict[str, Any]) -> dict[str, Any]:
        tenant_id = arguments.get("tenant_id")
        query = arguments.get("query")
        if not tenant_id or not query:
            raise ContractError("knowledge.retrieve requires tenant_id and query")
        return {
            "documents": [
                {
                    "document_id": "refund-policy-v1",
                    "tenant_id": tenant_id,
                    "text": "Refunds require approval and must be idempotent.",
                }
            ],
            "citation": "refund-policy-v1",
        }

    def _refund(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticket_id = arguments.get("ticket_id")
        amount = arguments.get("amount")
        if not ticket_id or not isinstance(amount, (int, float)) or amount <= 0:
            raise ContractError("billing.refund requires ticket_id and a positive amount")
        self.refund_execution_count += 1
        return {
            "status": "refunded",
            "ticket_id": ticket_id,
            "amount": amount,
            "provider_reference": f"mock-refund-{ticket_id}",
        }


class ToolGateway:
    """The only application-facing path from a ToolCall to execution."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        policy: PolicyEngine | None = None,
    ) -> None:
        self.__registry = registry or ToolRegistry()
        self.__policy = policy or PolicyEngine()
        self.__permit = self.__registry._gateway_permit()

    def decide(
        self,
        call: ToolCall,
        *,
        trusted_tenant_id: str,
        approved: bool = False,
    ) -> PolicyDecision:
        definition = self.__registry.definition(call.tool_name)
        if call.risk_level is not definition.risk_level:
            return PolicyDecision(
                Decision.DENY,
                "TOOL_RISK_MISMATCH",
                "Tool call risk level does not match the trusted registry.",
            )
        return self.__policy.decide(
            call,
            trusted_tenant_id=trusted_tenant_id,
            approved=approved,
        )

    def invoke(
        self,
        call: ToolCall,
        *,
        trusted_tenant_id: str,
        approved: bool = False,
    ) -> tuple[PolicyDecision, dict[str, Any] | None]:
        decision = self.decide(
            call,
            trusted_tenant_id=trusted_tenant_id,
            approved=approved,
        )
        if decision.decision is not Decision.ALLOW:
            return decision, None
        result = self.__registry._execute_authorized(call, self.__permit)
        return decision, result

    def execution_count(self, tool_name: str) -> int:
        if tool_name == "billing.refund":
            return self.__registry.refund_execution_count
        raise ContractError(f"execution counter is unavailable for tool: {tool_name}")
