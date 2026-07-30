from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .contracts import (
    AuditEvent,
    ContractError,
    Decision,
    ErrorModel,
    RiskLevel,
    RunRecord,
    RunRequest,
    RunStatus,
    ToolCall,
)
from .durability import (
    CrashPoint,
    FailureInjector,
    ProviderLookupStatus,
    request_fingerprint,
)
from .policy import PolicyEngine
from .store import SQLiteStore
from .tools import ToolGateway, ToolRegistry


class AgentRuntime:
    def __init__(
        self,
        store: SQLiteStore | None = None,
        tools: ToolRegistry | None = None,
        policy: PolicyEngine | None = None,
        failure_injector: FailureInjector | None = None,
    ) -> None:
        self.store = store or SQLiteStore()
        self.__tool_gateway = ToolGateway(tools, policy)
        self.__failure_injector = failure_injector or FailureInjector()

    def tool_execution_count(self, tool_name: str) -> int:
        return self.__tool_gateway.execution_count(tool_name)

    def start(self, request: RunRequest) -> RunRecord:
        run_id = str(uuid4())
        trace_id = str(uuid4())
        run = RunRecord(run_id=run_id, trace_id=trace_id, request=request)
        self.store.save_run(run)
        self._audit(run, request.principal, "run.create", request.ticket_id, "accepted", "REQUEST_VALID")

        if request.tenant_id != request.ticket_tenant_id:
            run.status = RunStatus.DENIED
            run.error = ErrorModel(
                code="TENANT_MISMATCH",
                category="authorization",
                recoverable=False,
                retryable=False,
                public_message="The ticket is not available to this tenant.",
            )
            self.store.save_run(run)
            self._audit(run, "policy", "run.authorize", request.ticket_id, "denied", "TENANT_MISMATCH")
            return run

        knowledge_call = ToolCall(
            operation_id=f"{run_id}:knowledge",
            tool_name="knowledge.retrieve",
            arguments={
                "tenant_id": request.tenant_id,
                "query": request.message,
                "allowed_sources": ["policy", "kb", "crm_notes"],
                "top_k": 3,
            },
            requested_by=request.principal,
            tenant_id=request.tenant_id,
            trace_id=trace_id,
            risk_level=RiskLevel.LOW,
        )
        knowledge = self._execute_allowed(run, knowledge_call)
        citation = knowledge.get("citation")
        grounded = bool(knowledge.get("grounded"))
        self._audit(
            run,
            "retrieval",
            "rag.retrieve",
            str(citation or "no-citation"),
            "hit" if grounded else "miss",
            "CITATION_VALIDATED" if grounded else "NO_GROUNDED_CONTEXT",
        )

        if self._requests_refund(request.message):
            refund_call = ToolCall(
                operation_id=f"{run_id}:refund",
                tool_name="billing.refund",
                arguments={"ticket_id": request.ticket_id, "amount": 100.0},
                requested_by=request.principal,
                tenant_id=request.tenant_id,
                trace_id=trace_id,
                risk_level=RiskLevel.HIGH,
            )
            decision = self.__tool_gateway.decide(
                refund_call,
                trusted_tenant_id=request.tenant_id,
            )
            self._audit(
                run,
                "policy",
                "tool.decide",
                refund_call.tool_name,
                decision.decision.value,
                decision.reason_code,
            )
            if decision.decision is not Decision.REQUIRE_APPROVAL:
                raise RuntimeError("refund policy must require approval in the baseline")
            run.status = RunStatus.WAITING_APPROVAL
            run.pending_call = refund_call
            run.result = {"knowledge": knowledge, "message": "Refund is waiting for approval."}
            self.store.checkpoint_run(run, "approval.waiting")
            return run

        run.status = RunStatus.COMPLETED
        if grounded:
            run.result = {
                "answer": knowledge["documents"][0]["text"],
                "citation": citation,
                "citations": knowledge["citations"],
                "grounded": True,
            }
        else:
            run.result = {
                "answer": "I do not have accessible, current evidence to answer this request.",
                "citation": None,
                "citations": [],
                "grounded": False,
                "refusal_reason": "NO_GROUNDED_CONTEXT",
            }
        self.store.save_run(run)
        self._audit(run, "runtime", "run.complete", request.ticket_id, "completed", "READ_ONLY_COMPLETE")
        return run

    def approve(self, run_id: str, approver: str) -> RunRecord:
        if not approver.strip():
            raise ContractError("approver must be a non-empty string")
        run = self.store.get_run(run_id)
        if run.status is RunStatus.COMPLETED:
            return run
        if run.status in {RunStatus.EXECUTING, RunStatus.NEEDS_RECONCILIATION}:
            return self.resume(run_id)
        if run.status is not RunStatus.WAITING_APPROVAL or run.pending_call is None:
            raise ContractError(f"run is not waiting for approval: {run.status.value}")

        call = run.pending_call
        decision = self.__tool_gateway.decide(
            call,
            trusted_tenant_id=run.request.tenant_id,
            approved=True,
        )
        if decision.decision is not Decision.ALLOW:
            raise ContractError(f"approved call was not allowed: {decision.reason_code}")

        run.status = RunStatus.EXECUTING
        run.approved_by = approver
        run.error = None
        self.store.begin_operation(
            run,
            call,
            self._event(
                run,
                approver,
                "tool.approve",
                call.tool_name,
                decision.decision.value,
                decision.reason_code,
            ),
        )
        return self._continue_operation(run, call)

    def resume(self, run_id: str) -> RunRecord:
        run = self.store.get_run(run_id)
        self.store.assert_checkpoint_compatible(run_id)
        if run.status is RunStatus.COMPLETED:
            return run
        if run.status is RunStatus.WAITING_APPROVAL:
            raise ContractError("run still requires an approval decision")
        if run.status not in {RunStatus.EXECUTING, RunStatus.NEEDS_RECONCILIATION}:
            raise ContractError(f"run cannot resume from status: {run.status.value}")
        self.store.assert_checkpoint_consistent(run)
        if run.pending_call is None or not run.approved_by:
            raise ContractError("durable run is missing its approved pending operation")

        call = run.pending_call
        decision = self.__tool_gateway.decide(
            call,
            trusted_tenant_id=run.request.tenant_id,
            approved=True,
        )
        if decision.decision is not Decision.ALLOW:
            raise ContractError(f"resumed call was not allowed: {decision.reason_code}")
        self._audit(
            run,
            "runtime",
            "run.resume",
            call.operation_id,
            "resumed",
            "CHECKPOINT_RESTORED",
        )
        return self._continue_operation(run, call)

    def cancel(self, run_id: str, actor: str) -> RunRecord:
        if not actor.strip():
            raise ContractError("actor must be a non-empty string")
        run = self.store.get_run(run_id)
        if run.status is RunStatus.CANCELLED:
            return run
        if run.status is not RunStatus.WAITING_APPROVAL:
            raise ContractError(f"run cannot be safely cancelled from status: {run.status.value}")
        operation_id = run.pending_call.operation_id if run.pending_call else run.run_id
        run.status = RunStatus.CANCELLED
        run.pending_call = None
        run.result = {"message": "Run cancelled before the side effect was approved."}
        self.store.transition_run(
            run,
            self._event(
                run,
                actor,
                "run.cancel",
                operation_id,
                "cancelled",
                "CANCELLED_BEFORE_EXECUTION",
            ),
            "run.cancelled",
        )
        return run

    def _continue_operation(self, run: RunRecord, call: ToolCall) -> RunRecord:
        record = self.store.operation_record(call.operation_id)
        if record is None:
            raise ContractError(f"operation ledger entry not found: {call.operation_id}")
        if record["run_id"] != run.run_id or record["call"] != call.to_dict():
            raise ContractError("pending operation does not match operation ledger")
        if record["args_hash"] != request_fingerprint(call.arguments):
            raise ContractError("operation arguments do not match operation ledger")

        existing_result = self.store.operation_result(call.operation_id)
        if existing_result is not None:
            return self._complete_operation(
                run,
                call,
                existing_result,
                outcome="replayed",
                reason_code="LEDGER_RESULT_REPLAYED",
            )

        if record["attempts"] > 0:
            lookup = self.__tool_gateway.lookup(call)
            if lookup.status is ProviderLookupStatus.SUCCEEDED:
                if lookup.result is None:
                    raise ContractError("provider lookup succeeded without a result")
                return self._complete_operation(
                    run,
                    call,
                    lookup.result,
                    outcome="recovered",
                    reason_code="PROVIDER_RESULT_RECONCILED",
                )
            if lookup.status is ProviderLookupStatus.UNKNOWN:
                return self._require_reconciliation(run, call)

        self.__failure_injector.trip(CrashPoint.BEFORE_PROVIDER_CALL)
        self.store.mark_operation_dispatching(run, call)
        decision, result = self.__tool_gateway.invoke(
            call,
            trusted_tenant_id=run.request.tenant_id,
            approved=True,
        )
        if decision.decision is not Decision.ALLOW:
            raise ContractError(f"approved tool call was not allowed: {decision.reason_code}")
        if result is None:
            raise ContractError("allowed tool call did not return a result")
        self.__failure_injector.trip(CrashPoint.AFTER_PROVIDER_SUCCESS)
        return self._complete_operation(
            run,
            call,
            result,
            outcome="executed",
            reason_code="OPERATION_COMMITTED",
        )

    def _complete_operation(
        self,
        run: RunRecord,
        call: ToolCall,
        result: dict[str, object],
        *,
        outcome: str,
        reason_code: str,
    ) -> RunRecord:
        run.status = RunStatus.COMPLETED
        run.pending_call = None
        run.result = result
        run.error = None
        self.store.complete_operation(
            run,
            call,
            result,
            self._event(
                run,
                "tool-gateway",
                "tool.execute",
                call.tool_name,
                outcome,
                reason_code,
            ),
        )
        return run

    def _require_reconciliation(self, run: RunRecord, call: ToolCall) -> RunRecord:
        run.status = RunStatus.NEEDS_RECONCILIATION
        run.error = ErrorModel(
            code="PROVIDER_OUTCOME_UNKNOWN",
            category="durable_execution",
            recoverable=True,
            retryable=False,
            public_message="The operation outcome must be reconciled before retrying.",
        )
        self.store.mark_reconciliation_required(
            run,
            call,
            self._event(
                run,
                "runtime",
                "operation.reconcile",
                call.operation_id,
                "paused",
                "PROVIDER_OUTCOME_UNKNOWN",
            ),
        )
        return run

    def _execute_allowed(self, run: RunRecord, call: ToolCall) -> dict[str, object]:
        decision, result = self.__tool_gateway.invoke(
            call,
            trusted_tenant_id=run.request.tenant_id,
        )
        self._audit(
            run,
            "policy",
            "tool.decide",
            call.tool_name,
            decision.decision.value,
            decision.reason_code,
        )
        if decision.decision is not Decision.ALLOW:
            raise ContractError(f"tool call not allowed: {decision.reason_code}")
        if result is None:
            raise ContractError("allowed tool call did not return a result")
        self._audit(run, "tool-gateway", "tool.execute", call.tool_name, "executed", "TOOL_SUCCEEDED")
        return result

    @staticmethod
    def _requests_refund(message: str) -> bool:
        lowered = message.lower()
        read_only_markers = ("refund policy", "what is", "how does", "退款政策", "退款规则")
        if any(marker in lowered or marker in message for marker in read_only_markers):
            return False
        action_markers = (
            "please refund",
            "refund this",
            "refund the",
            "issue a refund",
            "退款这个",
            "立即退款",
            "执行退款",
        )
        return any(marker in lowered or marker in message for marker in action_markers)

    def _audit(
        self,
        run: RunRecord,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        reason_code: str,
    ) -> None:
        self.store.append_audit(
            self._event(run, actor, action, resource, outcome, reason_code)
        )

    @staticmethod
    def _event(
        run: RunRecord,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        reason_code: str,
    ) -> AuditEvent:
        return AuditEvent(
            event_id=str(uuid4()),
            run_id=run.run_id,
            trace_id=run.trace_id,
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            reason_code=reason_code,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
