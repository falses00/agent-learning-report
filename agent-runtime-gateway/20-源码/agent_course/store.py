from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from typing import Any

from .contracts import AuditEvent, ErrorModel, RunRecord, RunRequest, RunStatus, ToolCall


class SQLiteStore:
    def __init__(self, path: str = ":memory:") -> None:
        self.connection = sqlite3.connect(path)
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
                result_json TEXT NOT NULL
            );
            """
        )

    def save_run(self, run: RunRecord) -> None:
        self.connection.execute(
            """
            INSERT INTO runs(run_id, trace_id, request_json, status, pending_call_json, result_json, error_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status = excluded.status,
                pending_call_json = excluded.pending_call_json,
                result_json = excluded.result_json,
                error_json = excluded.error_json
            """,
            (
                run.run_id,
                run.trace_id,
                json.dumps(asdict(run.request)),
                run.status.value,
                json.dumps(run.pending_call.to_dict()) if run.pending_call else None,
                json.dumps(run.result) if run.result is not None else None,
                json.dumps(asdict(run.error)) if run.error else None,
            ),
        )
        self.connection.commit()
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
            result=json.loads(row["result_json"]) if row["result_json"] else None,
            error=error,
        )

    def append_audit(self, event: AuditEvent) -> None:
        self.connection.execute(
            "INSERT INTO audit_events(event_id, run_id, event_json) VALUES (?, ?, ?)",
            (event.event_id, event.run_id, json.dumps(asdict(event))),
        )
        self.connection.commit()

    def list_audit(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT event_json FROM audit_events WHERE run_id = ? ORDER BY rowid", (run_id,)
        ).fetchall()
        return [json.loads(row["event_json"]) for row in rows]

    def operation_result(self, operation_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT result_json FROM operations WHERE operation_id = ?", (operation_id,)
        ).fetchone()
        return json.loads(row["result_json"]) if row else None

    def save_operation(self, operation_id: str, result: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO operations(operation_id, result_json) VALUES (?, ?)",
            (operation_id, json.dumps(result)),
        )
        self.connection.commit()
