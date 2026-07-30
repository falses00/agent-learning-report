from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable

from .contracts import ContractError


class CrashPoint(StrEnum):
    BEFORE_PROVIDER_CALL = "before_provider_call"
    AFTER_PROVIDER_SUCCESS = "after_provider_success"


class SimulatedCrash(RuntimeError):
    """Deterministic process-crash boundary used by the S4 teaching lab."""


class FailureInjector:
    def __init__(self, points: Iterable[CrashPoint] = ()) -> None:
        self._points = set(points)

    def trip(self, point: CrashPoint) -> None:
        if point not in self._points:
            return
        self._points.remove(point)
        raise SimulatedCrash(f"simulated crash at {point.value}")


class ProviderLookupStatus(StrEnum):
    SUCCEEDED = "succeeded"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderLookup:
    status: ProviderLookupStatus
    result: dict[str, Any] | None = None
    request_hash: str | None = None


class ProviderIdempotencyConflict(ContractError):
    pass


def request_fingerprint(arguments: dict[str, Any]) -> str:
    encoded = json.dumps(arguments, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class MockRefundProvider:
    """A separately persisted downstream used to expose the dual-write crash window."""

    def __init__(self, path: str = ":memory:", *, lookup_available: bool = True) -> None:
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.lookup_available = lookup_available
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS provider_refunds (
                operation_id TEXT PRIMARY KEY,
                request_hash TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def execute(self, operation_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
        fingerprint = request_fingerprint(arguments)
        ticket_id = arguments.get("ticket_id")
        amount = arguments.get("amount")
        result = {
            "status": "refunded",
            "ticket_id": ticket_id,
            "amount": amount,
            "provider_reference": f"mock-refund-{operation_id}",
        }
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute(
                "SELECT request_hash, result_json FROM provider_refunds WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if row is not None:
                if row["request_hash"] != fingerprint:
                    raise ProviderIdempotencyConflict(
                        "operation_id was reused with different refund arguments"
                    )
                return json.loads(row["result_json"])
            self.connection.execute(
                "INSERT INTO provider_refunds(operation_id, request_hash, result_json) VALUES (?, ?, ?)",
                (operation_id, fingerprint, json.dumps(result)),
            )
        return result

    def lookup(self, operation_id: str) -> ProviderLookup:
        if not self.lookup_available:
            return ProviderLookup(ProviderLookupStatus.UNKNOWN)
        row = self.connection.execute(
            "SELECT request_hash, result_json FROM provider_refunds WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        if row is None:
            return ProviderLookup(ProviderLookupStatus.NOT_FOUND)
        return ProviderLookup(
            ProviderLookupStatus.SUCCEEDED,
            json.loads(row["result_json"]),
            row["request_hash"],
        )

    def execution_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM provider_refunds").fetchone()
        return int(row["count"])

    def close(self) -> None:
        self.connection.close()
