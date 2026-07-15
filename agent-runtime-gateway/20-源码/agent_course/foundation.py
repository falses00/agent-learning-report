from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4

from .contracts import ContractError


class IdempotencyConflict(ContractError):
    pass


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    tenant_id: str
    title: str
    status: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class TicketRepository:
    """Small transactional store used by the F0 HTTP/CLI lab."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (tenant_id, idempotency_key)
            );
            CREATE INDEX IF NOT EXISTS idx_tickets_tenant_created
                ON tickets(tenant_id, created_at);
            """
        )
        self.connection.commit()

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def create(self, *, tenant_id: str, title: str, idempotency_key: str) -> tuple[Ticket, bool]:
        request_hash = self._request_hash(tenant_id=tenant_id, title=title)
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                existing = self.connection.execute(
                    """
                    SELECT * FROM tickets
                    WHERE tenant_id = ? AND idempotency_key = ?
                    """,
                    (tenant_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["request_hash"] != request_hash:
                        raise IdempotencyConflict(
                            "idempotency key was already used with a different request"
                        )
                    self.connection.commit()
                    return self._row_to_ticket(existing), True

                ticket = Ticket(
                    ticket_id=str(uuid4()),
                    tenant_id=tenant_id,
                    title=title,
                    status="open",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                self.connection.execute(
                    """
                    INSERT INTO tickets(
                        ticket_id, tenant_id, title, status,
                        idempotency_key, request_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket.ticket_id,
                        ticket.tenant_id,
                        ticket.title,
                        ticket.status,
                        idempotency_key,
                        request_hash,
                        ticket.created_at,
                    ),
                )
                self.connection.commit()
                return ticket, False
            except Exception:
                self.connection.rollback()
                raise

    def get(self, *, tenant_id: str, ticket_id: str) -> Ticket | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM tickets WHERE tenant_id = ? AND ticket_id = ?",
                (tenant_id, ticket_id),
            ).fetchone()
        return self._row_to_ticket(row) if row else None

    def list(self, *, tenant_id: str) -> list[Ticket]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT * FROM tickets WHERE tenant_id = ? ORDER BY created_at, ticket_id",
                (tenant_id,),
            ).fetchall()
        return [self._row_to_ticket(row) for row in rows]

    @staticmethod
    def _request_hash(*, tenant_id: str, title: str) -> str:
        payload = json.dumps(
            {"tenant_id": tenant_id, "title": title},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _row_to_ticket(row: sqlite3.Row) -> Ticket:
        return Ticket(
            ticket_id=row["ticket_id"],
            tenant_id=row["tenant_id"],
            title=row["title"],
            status=row["status"],
            created_at=row["created_at"],
        )


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    def create_ticket(
        self,
        *,
        tenant_id: str,
        title: str,
        idempotency_key: str,
    ) -> tuple[Ticket, bool]:
        for name, value in {
            "tenant_id": tenant_id,
            "title": title,
            "idempotency_key": idempotency_key,
        }.items():
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{name} must be a non-empty string")
        if len(title.strip()) > 200:
            raise ContractError("title must be at most 200 characters")
        return self.repository.create(
            tenant_id=tenant_id.strip(),
            title=title.strip(),
            idempotency_key=idempotency_key.strip(),
        )

    def get_ticket(self, *, tenant_id: str, ticket_id: str) -> Ticket | None:
        return self.repository.get(tenant_id=tenant_id, ticket_id=ticket_id)

    def list_tickets(self, *, tenant_id: str) -> list[Ticket]:
        return self.repository.list(tenant_id=tenant_id)
