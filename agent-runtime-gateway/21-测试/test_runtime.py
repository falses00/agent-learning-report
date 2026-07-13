import pytest

from agent_course import AgentRuntime, RunRequest, RunStatus
from agent_course.contracts import ContractError
from agent_course.store import SQLiteStore


def make_request(message: str, *, tenant_id: str = "tenant-a", ticket_tenant_id: str = "tenant-a") -> RunRequest:
    return RunRequest(
        principal="agent@example.com",
        tenant_id=tenant_id,
        ticket_tenant_id=ticket_tenant_id,
        ticket_id="T-100",
        message=message,
    )


def test_read_only_question_completes_with_citation() -> None:
    runtime = AgentRuntime()

    run = runtime.start(make_request("What is the refund policy?"))

    assert run.status is RunStatus.COMPLETED
    assert run.result["citation"] == "refund-policy-v1"
    assert runtime.tool_execution_count("billing.refund") == 0


def test_policy_question_is_not_misclassified_as_refund_action() -> None:
    runtime = AgentRuntime()

    run = runtime.start(make_request("How does the refund policy work?"))

    assert run.status is RunStatus.COMPLETED
    assert runtime.tool_execution_count("billing.refund") == 0


def test_refund_waits_for_approval_and_duplicate_approval_is_idempotent() -> None:
    runtime = AgentRuntime()
    run = runtime.start(make_request("Please refund this order."))

    assert run.status is RunStatus.WAITING_APPROVAL
    assert runtime.tool_execution_count("billing.refund") == 0

    completed = runtime.approve(run.run_id, "manager@example.com")
    repeated = runtime.approve(run.run_id, "manager@example.com")

    assert completed.status is RunStatus.COMPLETED
    assert repeated.result == completed.result
    assert runtime.tool_execution_count("billing.refund") == 1
    audit = runtime.store.list_audit(run.run_id)
    assert any(event["action"] == "tool.approve" for event in audit)
    assert any(event["reason_code"] == "OPERATION_COMMITTED" for event in audit)


def test_cross_tenant_request_is_denied_before_tools_run() -> None:
    runtime = AgentRuntime()

    run = runtime.start(
        make_request("Please refund this order.", tenant_id="tenant-a", ticket_tenant_id="tenant-b")
    )

    assert run.status is RunStatus.DENIED
    assert run.error.code == "TENANT_MISMATCH"
    assert runtime.tool_execution_count("billing.refund") == 0


def test_waiting_run_can_resume_after_store_reopen(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    first_runtime = AgentRuntime(store=SQLiteStore(str(database)))
    waiting = first_runtime.start(make_request("Please refund this order."))

    resumed_runtime = AgentRuntime(store=SQLiteStore(str(database)))
    completed = resumed_runtime.approve(waiting.run_id, "manager@example.com")

    assert completed.status is RunStatus.COMPLETED
    assert resumed_runtime.tool_execution_count("billing.refund") == 1


def test_denied_run_cannot_be_approved() -> None:
    runtime = AgentRuntime()
    denied = runtime.start(
        make_request("Refund this order.", tenant_id="tenant-a", ticket_tenant_id="tenant-b")
    )

    with pytest.raises(ContractError, match="not waiting for approval"):
        runtime.approve(denied.run_id, "manager@example.com")
