from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .contracts import ContractError, Decision, PolicyDecision, RiskLevel, ToolCall
from .policy import PolicyEngine
from .rag import KnowledgeBase


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    risk_level: RiskLevel
    executor: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        self._knowledge_base = knowledge_base or KnowledgeBase()
        self._execution_counts: dict[str, int] = {}
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
        result = definition.executor(call.arguments)
        self._execution_counts[call.tool_name] = self._execution_counts.get(call.tool_name, 0) + 1
        return result

    @property
    def __execution_permit(self) -> object:
        if not hasattr(self, "_ToolRegistry__permit"):
            self.__permit = object()
        return self.__permit

    def _gateway_permit(self) -> object:
        return self.__execution_permit

    def _retrieve_knowledge(self, arguments: dict[str, Any]) -> dict[str, Any]:
        tenant_id = arguments.get("tenant_id")
        query = arguments.get("query")
        if not tenant_id or not query:
            raise ContractError("knowledge.retrieve requires tenant_id and query")
        result = self._knowledge_base.retrieve(
            tenant_id=tenant_id,
            query=query,
            allowed_sources=arguments.get("allowed_sources"),
            top_k=arguments.get("top_k", 3),
        )
        return {
            "documents": [document.to_context_dict() for document in result.documents],
            "citations": [citation.to_dict() for citation in result.citations],
            "citation": result.citations[0].document_id if result.citations else None,
            "grounded": result.grounded and self._knowledge_base.validate_citations(
                result.citations, tenant_id=tenant_id
            ),
        }

    def _refund(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticket_id = arguments.get("ticket_id")
        amount = arguments.get("amount")
        if not ticket_id or not isinstance(amount, (int, float)) or amount <= 0:
            raise ContractError("billing.refund requires ticket_id and a positive amount")
        return {
            "status": "refunded",
            "ticket_id": ticket_id,
            "amount": amount,
            "provider_reference": f"mock-refund-{ticket_id}",
        }

    def execution_count(self, tool_name: str) -> int:
        self.definition(tool_name)
        return self._execution_counts.get(tool_name, 0)


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
        return self.__registry.execution_count(tool_name)
