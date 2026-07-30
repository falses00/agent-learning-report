from __future__ import annotations

import json
import sqlite3

import pytest

from agent_course import (
    AgentRuntime,
    CrashPoint,
    FailureInjector,
    MockRefundProvider,
    RunRequest,
    RunStatus,
    SimulatedCrash,
    ToolCall,
)
from agent_course.contracts import ContractError, RiskLevel
from agent_course.durability import ProviderIdempotencyConflict
from agent_course.store import CHECKPOINT_SCHEMA_VERSION, SQLiteStore
from agent_course.tools import ToolRegistry


def refund_request(ticket_id: str = "S4-100") -> RunRequest:
    return RunRequest(
        principal="agent@example.com",
        tenant_id="tenant-a",
        ticket_tenant_id="tenant-a",
        ticket_id=ticket_id,
        message="Please refund this order.",
    )


def durable_runtime(
    runtime_db: str,
    provider_db: str,
    *,
    crash_point: CrashPoint | None = None,
    lookup_available: bool = True,
) -> tuple[AgentRuntime, MockRefundProvider]:
    provider = MockRefundProvider(provider_db, lookup_available=lookup_available)
    injector = FailureInjector([crash_point] if crash_point else [])
    runtime = AgentRuntime(
        store=SQLiteStore(runtime_db),
        tools=ToolRegistry(refund_provider=provider),
        failure_injector=injector,
    )
    return runtime, provider


def test_crash_after_provider_success_reconciles_without_duplicate_side_effect(tmp_path) -> None:
    runtime_path = str(tmp_path / "runtime.db")
    provider_path = str(tmp_path / "provider.db")
    first, provider = durable_runtime(
        runtime_path,
        provider_path,
        crash_point=CrashPoint.AFTER_PROVIDER_SUCCESS,
    )
    waiting = first.start(refund_request())

    with pytest.raises(SimulatedCrash, match="after_provider_success"):
        first.approve(waiting.run_id, "manager@example.com")

    crashed = first.store.get_run(waiting.run_id)
    operation = first.store.operation_record(f"{waiting.run_id}:refund")
    assert crashed.status is RunStatus.EXECUTING
    assert operation["status"] == "dispatching"
    assert operation["attempts"] == 1
    assert provider.execution_count() == 1
    first.store.close()
    provider.close()

    resumed, reopened_provider = durable_runtime(runtime_path, provider_path)
    completed = resumed.resume(waiting.run_id)

    assert completed.status is RunStatus.COMPLETED
    assert completed.result["provider_reference"].endswith(f"{waiting.run_id}:refund")
    assert reopened_provider.execution_count() == 1
    operation = resumed.store.operation_record(f"{waiting.run_id}:refund")
    assert operation["status"] == "committed"
    assert operation["attempts"] == 1
    audit = resumed.store.list_audit(waiting.run_id)
    assert any(event["reason_code"] == "PROVIDER_RESULT_RECONCILED" for event in audit)
    checkpoint = resumed.store.latest_checkpoint(waiting.run_id)
    assert checkpoint["schema_version"] == CHECKPOINT_SCHEMA_VERSION
    assert checkpoint["reason"] == "operation.committed"
    assert "message" not in checkpoint["state"]


def test_crash_before_provider_call_resumes_from_approved_checkpoint(tmp_path) -> None:
    runtime_path = str(tmp_path / "runtime.db")
    provider_path = str(tmp_path / "provider.db")
    first, provider = durable_runtime(
        runtime_path,
        provider_path,
        crash_point=CrashPoint.BEFORE_PROVIDER_CALL,
    )
    waiting = first.start(refund_request("S4-101"))

    with pytest.raises(SimulatedCrash, match="before_provider_call"):
        first.approve(waiting.run_id, "manager@example.com")

    operation = first.store.operation_record(f"{waiting.run_id}:refund")
    assert operation["status"] == "approved"
    assert operation["attempts"] == 0
    assert provider.execution_count() == 0
    first.store.close()
    provider.close()

    resumed, reopened_provider = durable_runtime(runtime_path, provider_path)
    completed = resumed.resume(waiting.run_id)

    assert completed.status is RunStatus.COMPLETED
    assert reopened_provider.execution_count() == 1
    assert resumed.store.operation_record(f"{waiting.run_id}:refund")["attempts"] == 1


def test_unknown_provider_outcome_pauses_until_reconciliation_is_possible(tmp_path) -> None:
    runtime_path = str(tmp_path / "runtime.db")
    provider_path = str(tmp_path / "provider.db")
    first, provider = durable_runtime(
        runtime_path,
        provider_path,
        crash_point=CrashPoint.AFTER_PROVIDER_SUCCESS,
    )
    waiting = first.start(refund_request("S4-102"))
    with pytest.raises(SimulatedCrash):
        first.approve(waiting.run_id, "manager@example.com")
    with pytest.raises(ContractError, match="cannot be safely cancelled"):
        first.cancel(waiting.run_id, "manager@example.com")
    first.store.close()
    provider.close()

    paused_runtime, unavailable_provider = durable_runtime(
        runtime_path,
        provider_path,
        lookup_available=False,
    )
    paused = paused_runtime.resume(waiting.run_id)

    assert paused.status is RunStatus.NEEDS_RECONCILIATION
    assert paused.error.code == "PROVIDER_OUTCOME_UNKNOWN"
    assert paused.error.recoverable is True
    assert paused.error.retryable is False
    assert unavailable_provider.execution_count() == 1
    assert paused_runtime.store.operation_record(f"{waiting.run_id}:refund")["status"] == "ambiguous"

    still_paused = paused_runtime.resume(waiting.run_id)
    assert still_paused.status is RunStatus.NEEDS_RECONCILIATION
    assert unavailable_provider.execution_count() == 1

    unavailable_provider.lookup_available = True
    completed = paused_runtime.resume(waiting.run_id)
    assert completed.status is RunStatus.COMPLETED
    assert unavailable_provider.execution_count() == 1
    reasons = {
        event["reason_code"] for event in paused_runtime.store.list_audit(waiting.run_id)
    }
    assert "PROVIDER_OUTCOME_UNKNOWN" in reasons
    assert "PROVIDER_RESULT_RECONCILED" in reasons


def test_waiting_approval_can_be_cancelled_without_side_effect() -> None:
    runtime = AgentRuntime()
    waiting = runtime.start(refund_request("S4-103"))

    cancelled = runtime.cancel(waiting.run_id, "manager@example.com")

    assert cancelled.status is RunStatus.CANCELLED
    assert runtime.tool_execution_count("billing.refund") == 0
    with pytest.raises(ContractError, match="not waiting for approval"):
        runtime.approve(waiting.run_id, "manager@example.com")


def test_resume_rejects_unknown_checkpoint_schema(tmp_path) -> None:
    runtime = AgentRuntime(store=SQLiteStore(str(tmp_path / "runtime.db")))
    waiting = runtime.start(refund_request("S4-104"))
    runtime.store.connection.execute(
        "UPDATE checkpoints SET schema_version = ? WHERE run_id = ?",
        (CHECKPOINT_SCHEMA_VERSION + 1, waiting.run_id),
    )
    runtime.store.connection.commit()

    with pytest.raises(ContractError, match="schema version is not supported"):
        runtime.resume(waiting.run_id)


def test_resume_rejects_tampered_checkpoint_state(tmp_path) -> None:
    runtime = AgentRuntime(store=SQLiteStore(str(tmp_path / "runtime.db")))
    waiting = runtime.start(refund_request("S4-105"))
    runtime.store.connection.execute(
        "UPDATE checkpoints SET state_json = state_json || 'tampered' WHERE run_id = ?",
        (waiting.run_id,),
    )
    runtime.store.connection.commit()

    with pytest.raises(ContractError, match="state hash mismatch"):
        runtime.resume(waiting.run_id)


def test_provider_rejects_same_operation_id_with_different_payload() -> None:
    provider = MockRefundProvider()
    provider.execute("operation-1", {"ticket_id": "T-1", "amount": 100})

    with pytest.raises(ProviderIdempotencyConflict, match="different refund arguments"):
        provider.execute("operation-1", {"ticket_id": "T-1", "amount": 200})

    assert provider.execution_count() == 1


def test_resume_rejects_run_state_that_differs_from_checkpoint(tmp_path) -> None:
    runtime_path = str(tmp_path / "runtime.db")
    provider_path = str(tmp_path / "provider.db")
    runtime, provider = durable_runtime(
        runtime_path,
        provider_path,
        crash_point=CrashPoint.BEFORE_PROVIDER_CALL,
    )
    waiting = runtime.start(refund_request("S4-106"))
    with pytest.raises(SimulatedCrash, match="before_provider_call"):
        runtime.approve(waiting.run_id, "manager@example.com")

    row = runtime.store.connection.execute(
        "SELECT pending_call_json FROM runs WHERE run_id = ?",
        (waiting.run_id,),
    ).fetchone()
    tampered_call = json.loads(row["pending_call_json"])
    tampered_call["arguments"]["amount"] = 999.0
    runtime.store.connection.execute(
        "UPDATE runs SET pending_call_json = ? WHERE run_id = ?",
        (json.dumps(tampered_call), waiting.run_id),
    )
    runtime.store.connection.commit()

    with pytest.raises(ContractError, match="does not match latest checkpoint"):
        runtime.resume(waiting.run_id)
    assert provider.execution_count() == 0


def test_provider_lookup_rejects_operation_with_different_arguments() -> None:
    provider = MockRefundProvider()
    provider.execute("operation-lookup", {"ticket_id": "T-1", "amount": 100.0})
    registry = ToolRegistry(refund_provider=provider)
    mismatched = ToolCall(
        operation_id="operation-lookup",
        tool_name="billing.refund",
        arguments={"ticket_id": "T-1", "amount": 200.0},
        requested_by="agent@example.com",
        tenant_id="tenant-a",
        trace_id="trace-1",
        risk_level=RiskLevel.HIGH,
    )

    with pytest.raises(ProviderIdempotencyConflict, match="different refund arguments"):
        registry.lookup(mismatched)


def test_store_migrates_legacy_schema_without_losing_operation(tmp_path) -> None:
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE runs (
            run_id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            request_json TEXT NOT NULL,
            status TEXT NOT NULL,
            pending_call_json TEXT,
            result_json TEXT,
            error_json TEXT
        );
        CREATE TABLE audit_events (
            event_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            event_json TEXT NOT NULL
        );
        CREATE TABLE operations (
            operation_id TEXT PRIMARY KEY,
            result_json TEXT NOT NULL
        );
        INSERT INTO operations(operation_id, result_json)
        VALUES ('legacy-operation', '{"status": "already-committed"}');
        """
    )
    connection.close()

    store = SQLiteStore(str(database))

    run_columns = {
        row["name"] for row in store.connection.execute("PRAGMA table_info(runs)")
    }
    operation = store.operation_record("legacy-operation")
    assert "approved_by" in run_columns
    assert operation["status"] == "committed"
    assert operation["attempts"] == 0
    assert operation["result"] == {"status": "already-committed"}
