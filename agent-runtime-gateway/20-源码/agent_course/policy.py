from __future__ import annotations

from .contracts import Decision, PolicyDecision, RiskLevel, ToolCall


class PolicyEngine:
    """Makes decisions from trusted runtime facts, never prompt claims."""

    def decide(self, call: ToolCall, *, trusted_tenant_id: str, approved: bool = False) -> PolicyDecision:
        if call.tenant_id != trusted_tenant_id:
            return PolicyDecision(
                Decision.DENY,
                "TENANT_MISMATCH",
                "Tool call tenant does not match the authenticated tenant.",
            )
        if call.risk_level is RiskLevel.HIGH and not approved:
            return PolicyDecision(
                Decision.REQUIRE_APPROVAL,
                "HIGH_RISK_APPROVAL_REQUIRED",
                "High-risk side effects require explicit approval.",
            )
        return PolicyDecision(Decision.ALLOW, "POLICY_ALLOWED", "Policy checks passed.")
