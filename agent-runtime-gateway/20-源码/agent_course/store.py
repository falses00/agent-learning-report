from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .contracts import (
    AuditEvent,
    ContractError,
    ErrorModel,
    OperationStatus,
    RunRecord,
    RunRequest,
    RunStatus,
    ToolCall,
)
from .durability import request_fingerprint


CHECKPOINT_SCHEMA_VERSION = 1


class SQLiteStore:
    def __init__(self, path: str = ":memory:") -> None:
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                request_json TEXT NOT NULL,
                status TEXT NOT NULL,
                pending_call_json TEXT,
                approved_by TEXT,
                result_json TEXT,
                error_json TEXT
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                event_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS operations (
                operation_id TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                run_id TEXT,
                tool_name TEXT,
                call_json TEXT,
                args_hash TEXT,
                status TEXT NOT NULL DEFAULT 'committed',
                attempts INTEGER NOT NULL DEFAULT 0,
                error_json TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                parent_checkpoint_id TEXT,
                run_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                schema_version INTEGER NOT NULL,
                state_json TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._add_column("runs", "approved_by", "TEXT")
        operation_columns = {
            "run_id": "TEXT",
            "tool_name": "TEXT",
            "call_json": "TEXT",
            "args_hash": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'committed'",
            "attempts": "INTEGER NOT NULL DEFAULT 0",
            "error_json": "TEXT",
            "updated_at": "TEXT",
        }
        for name, definition in operation_columns.items():
            self._add_column("operations", name, definition)
        self.connection.commit()

    def _add_column(self, table: str, name: str, definition: str) -> None:
        existing = {
            row["name"]
            for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if name not in existing:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _upsert_run(self, run: RunRecord) -> None:
        self.connection.execute(
            """
            INSERT INTO runs(
                run_id, trace_id, request_json, status, pending_call_json,
                approved_by, result_json, error_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status = excluded.status,
                pending_call_json = excluded.pending_call_json,
                approved_by = excluded.approved_by,
                result_json = excluded.result_json,
                error_json = excluded.error_json
            """,
            (
                run.run_id,
                run.trace_id,
                json.dumps(asdict(run.request)),
                run.status.value,
                json.dumps(run.pending_call.to_dict()) if run.pending_call else None,
                run.approved_by,
                json.dumps(run.result) if run.result is not None else None,
                json.dumps(asdict(run.error)) if run.error else None,
            ),
        )

    def save_run(self, run: RunRecord) -> None:
        with self.connection:
            self._upsert_run(run)

    def checkpoint_run(self, run: RunRecord, reason: str) -> None:
        with self.connection:
            self._upsert_run(run)
            self._insert_checkpoint(run, reason)

    def transition_run(self, run: RunRecord, event: AuditEvent, reason: str) -> None:
        with self.connection:
            self._upsert_run(run)
            self._insert_audit(event)
            self._insert_checkpoint(run, reason)

    def get_run(self, run_id: str) -> RunRecord:
        row = self.connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"run not found: {run_id}")
        pending = ToolCall.from_dict(json.loads(row["pending_call_json"])) if row["pending_call_json"] else None
        error = ErrorModel(**json.loads(row["error_json"])) if row["error_json"] else None
        return RunRecord(
            run_id=row["run_id"],
            trace_id=row["trace_id"],
            request=RunRequest.from_dict(json.loads(row["request_json"])),
            status=RunStatus(row["status"]),
            pending_call=pending,
            approved_by=row["approved_by"],
            result=json.loads(row["result_json"]) if row["result_json"] else None,
            error=error,
        )

    def _checkpoint_state(self, run: RunRecord) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "trace_id": run.trace_id,
            "status": run.status.value,
            "tenant_id": run.request.tenant_id,
            "ticket_id": run.request.ticket_id,
            "pending_call": run.pending_call.to_dict() if run.pending_call else None,
            "approved_by": run.approved_by,
            "result": run.result if run.status is RunStatus.COMPLETED else None,
            "error": asdict(run.error) if run.error else None,
        }

    def _insert_checkpoint(self, run: RunRecord, reason: str) -> None:
        parent = self.connection.execute(
            "SELECT checkpoint_id FROM checkpoints WHERE run_id = ? ORDER BY rowid DESC LIMIT 1",
            (run.run_id,),
        ).fetchone()
        state_json = json.dumps(
            self._checkpoint_state(run),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.connection.execute(
            """
            INSERT INTO checkpoints(
                checkpoint_id, parent_checkpoint_id, run_id, reason,
                schema_version, state_json, state_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                parent["checkpoint_id"] if parent else None,
                run.run_id,
                reason,
                CHECKPOINT_SCHEMA_VERSION,
                state_json,
                hashlib.sha256(state_json.encode("utf-8")).hexdigest(),
                self._now(),
            ),
        )

    def latest_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM checkpoints WHERE run_id = ? ORDER BY rowid DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        actual_hash = hashlib.sha256(row["state_json"].encode("utf-8")).hexdigest()
        if actual_hash != row["state_hash"]:
            raise ContractError("checkpoint state hash mismatch")
        return {
            "checkpoint_id": row["checkpoint_id"],
            "parent_checkpoint_id": row["parent_checkpoint_id"],
            "run_id": row["run_id"],
            "reason": row["reason"],
            "schema_version": row["schema_version"],
            "state": json.loads(row["state_json"]),
            "state_hash": row["state_hash"],
            "created_at": row["created_at"],
        }

    def assert_checkpoint_compatible(self, run_id: str) -> None:
        checkpoint = self.latest_checkpoint(run_id)
        if checkpoint is not None and checkpoint["schema_version"] != CHECKPOINT_SCHEMA_VERSION:
            raise ContractError(
                "checkpoint schema version is not supported: "
                f"{checkpoint['schema_version']}"
            )

    def assert_checkpoint_consistent(self, run: RunRecord) -> None:
        checkpoint = self.latest_checkpoint(run.run_id)
        if checkpoint is None:
            raise ContractError("durable run is missing its checkpoint")
        if checkpoint["state"] != self._checkpoint_state(run):
            raise ContractError("run state does not match latest checkpoint")

    def begin_operation(self, run: RunRecord, call: ToolCall, approval_event: AuditEvent) -> None:
        call_json = json.dumps(call.to_dict(), ensure_ascii=True, sort_keys=True)
        fingerprint = request_fingerprint(call.arguments)
        with self.connection:
            existing = self.connection.execute(
                "SELECT args_hash FROM operations WHERE operation_id = ?",
                (call.operation_id,),
            ).fetchone()
            if existing is not None and existing["args_hash"] not in {None, fingerprint}:
                raise ContractError("operation_id was reused with different arguments")
            self.connection.execute(
                """
                INSERT INTO operations(
                    operation_id, result_json, run_id, tool_name, call_json,
                    args_hash, status, attempts, error_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
                ON CONFLICT(operation_id) DO NOTHING
                """,
                (
                    call.operation_id,
                    "null",
                    run.run_id,
                    call.tool_name,
                    call_json,
                    fingerprint,
                    OperationStatus.APPROVED.value,
                    self._now(),
                ),
            )
            self._upsert_run(run)
            self._insert_audit(approval_event)
            self._insert_checkpoint(run, "operation.approved")

    def mark_operation_dispatching(self, run: RunRecord, call: ToolCall) -> None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE operations
                SET status = ?, attempts = attempts + 1, error_json = NULL, updated_at = ?
                WHERE operation_id = ? AND status != ?
                """,
                (
                    OperationStatus.DISPATCHING.value,
                    self._now(),
                    call.operation_id,
                    OperationStatus.COMMITTED.value,
                ),
            )
            if cursor.rowcount != 1:
                raise ContractError(f"operation is missing or already committed: {call.operation_id}")
            self._upsert_run(run)
            self._insert_checkpoint(run, "operation.dispatching")

    def complete_operation(
        self,
        run: RunRecord,
        call: ToolCall,
        result: dict[str, Any],
        event: AuditEvent,
    ) -> None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE operations
                SET status = ?, result_json = ?, error_json = NULL, updated_at = ?
                WHERE operation_id = ?
                """,
                (
                    OperationStatus.COMMITTED.value,
                    json.dumps(result),
                    self._now(),
                    call.operation_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ContractError(f"operation not found: {call.operation_id}")
            self._upsert_run(run)
            self._insert_audit(event)
            self._insert_checkpoint(run, "operation.committed")

    def mark_reconciliation_required(
        self,
        run: RunRecord,
        call: ToolCall,
        event: AuditEvent,
    ) -> None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE operations
                SET status = ?, error_json = ?, updated_at = ?
                WHERE operation_id = ? AND status != ?
                """,
                (
                    OperationStatus.AMBIGUOUS.value,
                    json.dumps(asdict(run.error)) if run.error else None,
                    self._now(),
                    call.operation_id,
                    OperationStatus.COMMITTED.value,
                ),
            )
            if cursor.rowcount != 1:
                raise ContractError(f"operation is missing or already committed: {call.operation_id}")
            self._upsert_run(run)
            self._insert_audit(event)
            self._insert_checkpoint(run, "operation.ambiguous")

    def operation_record(self, operation_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM operations WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        return self._operation_row(row) if row else None

    def list_operations(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM operations WHERE run_id = ? ORDER BY rowid",
            (run_id,),
        ).fetchall()
        return [self._operation_row(row) for row in rows]

    @staticmethod
    def _operation_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "operation_id": row["operation_id"],
            "run_id": row["run_id"],
            "tool_name": row["tool_name"],
            "call": json.loads(row["call_json"]) if row["call_json"] else None,
            "args_hash": row["args_hash"],
            "status": row["status"],
            "attempts": row["attempts"],
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "error": json.loads(row["error_json"]) if row["error_json"] else None,
            "updated_at": row["updated_at"],
        }

    def operation_result(self, operation_id: str) -> dict[str, Any] | None:
        record = self.operation_record(operation_id)
        if record is None or record["status"] != OperationStatus.COMMITTED.value:
            return None
        return record["result"]

    def save_operation(self, operation_id: str, result: dict[str, Any]) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO operations(operation_id, result_json, status, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(operation_id) DO UPDATE SET
                    result_json = excluded.result_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    operation_id,
                    json.dumps(result),
                    OperationStatus.COMMITTED.value,
                    self._now(),
                ),
            )

    def _insert_audit(self, event: AuditEvent) -> None:
        self.connection.execute(
            "INSERT INTO audit_events(event_id, run_id, event_json) VALUES (?, ?, ?)",
            (event.event_id, event.run_id, json.dumps(asdict(event))),
        )

    def append_audit(self, event: AuditEvent) -> None:
        with self.connection:
            self._insert_audit(event)

    def list_audit(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT event_json FROM audit_events WHERE run_id = ? ORDER BY rowid",
            (run_id,),
        ).fetchall()
        return [json.loads(row["event_json"]) for row in rows]

    def close(self) -> None:
        self.connection.close()
