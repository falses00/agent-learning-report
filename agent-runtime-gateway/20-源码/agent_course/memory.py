from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from .contracts import ContractError


class MemoryDecision(StrEnum):
    ALLOW = "allow"
    SCOPED_ALLOW = "scoped_allow"
    SESSION_ONLY = "session_only"
    NEEDS_CONFIRMATION = "needs_confirmation"
    VERSIONED_UPDATE = "versioned_update"
    DENY = "deny"
    DENY_AND_REDACT = "deny_and_redact"
    DELETE_VERIFY = "delete_verify"
    EXCLUDE = "exclude"


class MemorySourceKind(StrEnum):
    USER_STATEMENT = "user_statement"
    USER_MESSAGE = "user_message"
    MODEL_INFERENCE = "model_inference"
    TOOL_RESULT = "tool_result"
    VERIFIED_EXPERIENCE = "verified_experience"
    UNTRUSTED_CONTENT = "untrusted_content"


class MemorySensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"
    PII = "pii"
    SECRET = "secret"


class MemoryScope(StrEnum):
    RUN = "run"
    USER = "user"
    TENANT = "tenant"
    RESOURCE = "resource"


class MemoryType(StrEnum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"


class MemoryAccessPolicy:
    """Trusted authorization facts supplied by the application boundary."""

    def __init__(
        self,
        *,
        tenant_memberships: dict[str, set[str]],
        resource_grants: dict[tuple[str, str], set[str]] | None = None,
        tenant_admins: set[tuple[str, str]] | None = None,
    ) -> None:
        self._tenant_memberships = {
            principal: frozenset(tenants)
            for principal, tenants in tenant_memberships.items()
        }
        self._resource_grants = {
            key: frozenset(subject_ids)
            for key, subject_ids in (resource_grants or {}).items()
        }
        self._tenant_admins = frozenset(tenant_admins or set())

    def has_tenant_access(self, principal_id: str, tenant_id: str) -> bool:
        return tenant_id in self._tenant_memberships.get(principal_id, frozenset())

    def resource_subjects(self, principal_id: str, tenant_id: str) -> frozenset[str]:
        return self._resource_grants.get((principal_id, tenant_id), frozenset())

    def is_tenant_admin(self, principal_id: str, tenant_id: str) -> bool:
        return (principal_id, tenant_id) in self._tenant_admins


@dataclass(frozen=True)
class MemoryCandidate:
    content: str
    source_kind: MemorySourceKind
    source_ref: str
    tenant_id: str
    principal_id: str
    scope: MemoryScope
    subject_id: str
    sensitivity: MemorySensitivity
    memory_type: MemoryType
    ttl_seconds: int | None
    confidence: float
    run_id: str

    def __post_init__(self) -> None:
        for name in (
            "content",
            "source_ref",
            "tenant_id",
            "principal_id",
            "subject_id",
            "run_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{name} must be a non-empty string")
        for name, enum_type in (
            ("source_kind", MemorySourceKind),
            ("scope", MemoryScope),
            ("sensitivity", MemorySensitivity),
            ("memory_type", MemoryType),
        ):
            if not isinstance(getattr(self, name), enum_type):
                raise ContractError(f"{name} must be a valid {enum_type.__name__}")
        if self.ttl_seconds is not None and (
            isinstance(self.ttl_seconds, bool)
            or not isinstance(self.ttl_seconds, int)
            or self.ttl_seconds <= 0
        ):
            raise ContractError("ttl_seconds must be a positive integer or null")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not 0 <= self.confidence <= 1
        ):
            raise ContractError("confidence must be between 0 and 1")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryCandidate":
        allowed = {
            "content",
            "source_kind",
            "source_ref",
            "tenant_id",
            "principal_id",
            "scope",
            "subject_id",
            "sensitivity",
            "memory_type",
            "ttl_seconds",
            "confidence",
            "run_id",
        }
        unknown = set(data) - allowed
        missing = allowed - set(data)
        if unknown:
            raise ContractError(f"unknown memory candidate fields: {sorted(unknown)}")
        if missing:
            raise ContractError(f"missing memory candidate fields: {sorted(missing)}")
        values = dict(data)
        values["source_kind"] = MemorySourceKind(values["source_kind"])
        values["scope"] = MemoryScope(values["scope"])
        values["sensitivity"] = MemorySensitivity(values["sensitivity"])
        values["memory_type"] = MemoryType(values["memory_type"])
        return cls(**values)


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    content: str
    content_hash: str
    source_kind: str
    source_ref: str
    tenant_id: str
    principal_id: str
    scope: str
    subject_id: str
    sensitivity: str
    memory_type: str
    confidence: float
    version: int
    valid_from: str
    valid_to: str | None
    expires_at: str
    deleted_at: str | None
    supersedes_id: str | None
    delete_policy: str
    run_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemoryWriteResult:
    decision: MemoryDecision
    reason_code: str
    memory_id: str | None = None
    redacted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_code": self.reason_code,
            "memory_id": self.memory_id,
            "redacted": self.redacted,
        }


@dataclass(frozen=True)
class MemorySearchResult:
    decision: MemoryDecision
    reason_code: str
    records: tuple[MemoryRecord, ...]
    context_items: tuple[dict[str, Any], ...]
    estimated_tokens: int
    filtered_expired: int = 0
    filtered_unauthorized: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_code": self.reason_code,
            "records": [record.to_dict() for record in self.records],
            "context_items": list(self.context_items),
            "estimated_tokens": self.estimated_tokens,
            "filtered_expired": self.filtered_expired,
            "filtered_unauthorized": self.filtered_unauthorized,
            "record_count": len(self.records),
        }


class MemoryStore:
    def __init__(self, path: str = ":memory:") -> None:
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                principal_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                sensitivity TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                version INTEGER NOT NULL,
                valid_from TEXT NOT NULL,
                valid_to TEXT,
                expires_at TEXT NOT NULL,
                deleted_at TEXT,
                supersedes_id TEXT,
                delete_policy TEXT NOT NULL,
                run_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_active_scope
            ON memory_records(tenant_id, principal_id, scope, subject_id, expires_at);
            CREATE TABLE IF NOT EXISTS memory_index (
                memory_id TEXT PRIMARY KEY,
                search_text TEXT NOT NULL,
                FOREIGN KEY(memory_id) REFERENCES memory_records(memory_id)
            );
            CREATE TABLE IF NOT EXISTS memory_tombstones (
                memory_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                deleted_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                requested_by TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_audit (
                event_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                actor TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                memory_id TEXT,
                content_hash TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def insert_record(self, record: MemoryRecord, audit: dict[str, Any]) -> None:
        with self.connection:
            self._insert_record(record)
            self._insert_audit(audit)

    def _insert_record(self, record: MemoryRecord) -> None:
        values = record.to_dict()
        self.connection.execute(
            f"INSERT INTO memory_records({', '.join(values)}) "
            f"VALUES ({', '.join('?' for _ in values)})",
            tuple(values.values()),
        )
        self.connection.execute(
            "INSERT INTO memory_index(memory_id, search_text) VALUES (?, ?)",
            (record.memory_id, _normalize(record.content)),
        )

    def append_audit(self, event: dict[str, Any]) -> None:
        with self.connection:
            self._insert_audit(event)

    def _insert_audit(self, event: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT INTO memory_audit(
                event_id, operation, decision, reason_code, actor, tenant_id,
                memory_id, content_hash, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["operation"],
                event["decision"],
                event["reason_code"],
                event["actor"],
                event["tenant_id"],
                event.get("memory_id"),
                event.get("content_hash"),
                json.dumps(event.get("metadata", {}), ensure_ascii=True, sort_keys=True),
                event["created_at"],
            ),
        )

    def get_record(self, memory_id: str) -> MemoryRecord | None:
        row = self.connection.execute(
            "SELECT * FROM memory_records WHERE memory_id = ?",
            (memory_id,),
        ).fetchone()
        return _record_from_row(row) if row else None

    def current_record(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        scope: str,
        subject_id: str,
        now: str,
    ) -> MemoryRecord | None:
        principal_clause = "AND principal_id = ?" if scope == MemoryScope.USER.value else ""
        parameters: list[Any] = [tenant_id, scope, subject_id, now]
        if principal_clause:
            parameters.append(principal_id)
        row = self.connection.execute(
            f"""
            SELECT * FROM memory_records
            WHERE tenant_id = ? AND scope = ? AND subject_id = ?
              AND deleted_at IS NULL AND valid_to IS NULL AND expires_at > ?
              {principal_clause}
            ORDER BY version DESC LIMIT 1
            """,
            parameters,
        ).fetchone()
        return _record_from_row(row) if row else None

    def search_rows(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        now: str,
        subject_id: str | None,
    ) -> list[sqlite3.Row]:
        subject_clause = "AND r.subject_id = ?" if subject_id else ""
        parameters: list[Any] = [tenant_id, now, principal_id]
        if subject_id:
            parameters.append(subject_id)
        return self.connection.execute(
            f"""
            SELECT r.*, i.search_text
            FROM memory_records r
            JOIN memory_index i ON i.memory_id = r.memory_id
            WHERE r.tenant_id = ?
              AND r.deleted_at IS NULL
              AND r.valid_to IS NULL
              AND r.expires_at > ?
              AND (r.scope != 'user' OR r.principal_id = ?)
              {subject_clause}
            """,
            parameters,
        ).fetchall()

    def expired_rows(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        now: str,
    ) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT r.*, i.search_text
            FROM memory_records r
            JOIN memory_index i ON i.memory_id = r.memory_id
            WHERE r.tenant_id = ? AND r.deleted_at IS NULL AND r.valid_to IS NULL
              AND r.expires_at <= ? AND (r.scope != 'user' OR r.principal_id = ?)
            """,
            (tenant_id, now, principal_id),
        ).fetchall()

    def due_for_expiry(self, *, tenant_id: str, now: str) -> list[MemoryRecord]:
        rows = self.connection.execute(
            """
            SELECT * FROM memory_records
            WHERE tenant_id = ? AND deleted_at IS NULL AND valid_to IS NULL
              AND expires_at <= ?
            """,
            (tenant_id, now),
        ).fetchall()
        return [_record_from_row(row) for row in rows]

    def expire_record(self, record: MemoryRecord, audit: dict[str, Any]) -> None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE memory_records SET valid_to = expires_at
                WHERE memory_id = ? AND deleted_at IS NULL AND valid_to IS NULL
                """,
                (record.memory_id,),
            )
            if cursor.rowcount != 1:
                raise ContractError("memory record is no longer eligible for expiry")
            self.connection.execute(
                "DELETE FROM memory_index WHERE memory_id = ?",
                (record.memory_id,),
            )
            self._insert_audit(audit)

    def supersede(
        self,
        old_record: MemoryRecord,
        new_record: MemoryRecord,
        audit: dict[str, Any],
    ) -> None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE memory_records SET valid_to = ?
                WHERE memory_id = ? AND valid_to IS NULL AND deleted_at IS NULL
                """,
                (new_record.valid_from, old_record.memory_id),
            )
            if cursor.rowcount != 1:
                raise ContractError("memory record is no longer current")
            self.connection.execute(
                "DELETE FROM memory_index WHERE memory_id = ?",
                (old_record.memory_id,),
            )
            self._insert_record(new_record)
            self._insert_audit(audit)

    def subject_records(self, record: MemoryRecord) -> list[MemoryRecord]:
        principal_clause = "AND principal_id = ?" if record.scope == MemoryScope.USER.value else ""
        parameters: list[Any] = [record.tenant_id, record.scope, record.subject_id]
        if principal_clause:
            parameters.append(record.principal_id)
        rows = self.connection.execute(
            f"""
            SELECT * FROM memory_records
            WHERE tenant_id = ? AND scope = ? AND subject_id = ? {principal_clause}
            ORDER BY version
            """,
            parameters,
        ).fetchall()
        return [_record_from_row(row) for row in rows]

    def delete_records(
        self,
        records: list[MemoryRecord],
        *,
        actor: str,
        reason: str,
        deleted_at: str,
        audit: dict[str, Any],
    ) -> None:
        if not records:
            raise ContractError("memory deletion requires at least one record")
        memory_ids = [record.memory_id for record in records]
        placeholders = ", ".join("?" for _ in memory_ids)
        with self.connection:
            self.connection.execute(
                f"DELETE FROM memory_index WHERE memory_id IN ({placeholders})",
                memory_ids,
            )
            cursor = self.connection.execute(
                f"DELETE FROM memory_records WHERE memory_id IN ({placeholders})",
                memory_ids,
            )
            if cursor.rowcount != len(memory_ids):
                raise ContractError("memory version chain changed during deletion")
            self.connection.executemany(
                """
                INSERT INTO memory_tombstones(memory_id, tenant_id, deleted_at, reason, requested_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (record.memory_id, record.tenant_id, deleted_at, reason, actor)
                    for record in records
                ],
            )
            self._insert_audit(audit)

    def active_count(self, *, tenant_id: str | None = None, now: str | None = None) -> int:
        clauses = ["deleted_at IS NULL", "valid_to IS NULL"]
        parameters: list[Any] = []
        if tenant_id:
            clauses.append("tenant_id = ?")
            parameters.append(tenant_id)
        if now:
            clauses.append("expires_at > ?")
            parameters.append(now)
        row = self.connection.execute(
            f"SELECT COUNT(*) AS count FROM memory_records WHERE {' AND '.join(clauses)}",
            parameters,
        ).fetchone()
        return int(row["count"])

    def index_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM memory_index").fetchone()
        return int(row["count"])

    def tombstone_count(self) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM memory_tombstones"
        ).fetchone()
        return int(row["count"])

    def history(self, *, tenant_id: str, subject_id: str) -> list[MemoryRecord]:
        rows = self.connection.execute(
            """
            SELECT * FROM memory_records
            WHERE tenant_id = ? AND subject_id = ? ORDER BY version
            """,
            (tenant_id, subject_id),
        ).fetchall()
        return [_record_from_row(row) for row in rows]

    def list_audit(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM memory_audit ORDER BY rowid"
        ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "operation": row["operation"],
                "decision": row["decision"],
                "reason_code": row["reason_code"],
                "actor": row["actor"],
                "tenant_id": row["tenant_id"],
                "memory_id": row["memory_id"],
                "content_hash": row["content_hash"],
                "metadata": json.loads(row["metadata_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def serialized_state(self) -> str:
        state: dict[str, list[dict[str, Any]]] = {}
        for table in (
            "memory_records",
            "memory_index",
            "memory_tombstones",
            "memory_audit",
        ):
            rows = self.connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            state[table] = [dict(row) for row in rows]
        return json.dumps(state, ensure_ascii=False, sort_keys=True)

    def close(self) -> None:
        self.connection.close()


class MemoryService:
    def __init__(
        self,
        store: MemoryStore | None = None,
        *,
        access_policy: MemoryAccessPolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store = store or MemoryStore()
        self.access_policy = access_policy
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def write(self, candidate: MemoryCandidate) -> MemoryWriteResult:
        decision, reason_code = self._write_decision(candidate)
        content_hash = _content_hash(candidate.content)
        if decision in {MemoryDecision.ALLOW, MemoryDecision.SCOPED_ALLOW}:
            authorization_reason = self._write_authorization_failure(candidate)
            if authorization_reason:
                decision = MemoryDecision.DENY
                reason_code = authorization_reason
        if decision not in {MemoryDecision.ALLOW, MemoryDecision.SCOPED_ALLOW}:
            self.store.append_audit(
                self._audit(
                    operation="memory.add",
                    decision=decision,
                    reason_code=reason_code,
                    actor=candidate.principal_id,
                    tenant_id=candidate.tenant_id,
                    content_hash=(
                        None
                        if decision is MemoryDecision.DENY_AND_REDACT
                        else content_hash
                    ),
                    metadata={
                        "source_kind": candidate.source_kind.value,
                        "scope": candidate.scope.value,
                        "redacted": decision is MemoryDecision.DENY_AND_REDACT,
                    },
                )
            )
            return MemoryWriteResult(
                decision,
                reason_code,
                redacted=decision is MemoryDecision.DENY_AND_REDACT,
            )

        now = self._now()
        existing = self.store.current_record(
            tenant_id=candidate.tenant_id,
            principal_id=candidate.principal_id,
            scope=candidate.scope.value,
            subject_id=candidate.subject_id,
            now=now,
        )
        if existing is not None:
            self.store.append_audit(
                self._audit(
                    operation="memory.add",
                    decision=MemoryDecision.DENY,
                    reason_code="DUPLICATE_CURRENT_MEMORY_REQUIRES_UPDATE",
                    actor=candidate.principal_id,
                    tenant_id=candidate.tenant_id,
                    content_hash=content_hash,
                    metadata={
                        "scope": candidate.scope.value,
                        "subject_hash": _content_hash(candidate.subject_id),
                    },
                )
            )
            return MemoryWriteResult(
                MemoryDecision.DENY,
                "DUPLICATE_CURRENT_MEMORY_REQUIRES_UPDATE",
            )
        record = self._record(candidate, version=1, valid_from=now)
        self.store.insert_record(
            record,
            self._audit(
                operation="memory.add",
                decision=decision,
                reason_code=reason_code,
                actor=candidate.principal_id,
                tenant_id=candidate.tenant_id,
                memory_id=record.memory_id,
                content_hash=record.content_hash,
                metadata={
                    "source_kind": record.source_kind,
                    "scope": record.scope,
                    "expires_at": record.expires_at,
                    "memory_type": record.memory_type,
                },
            ),
        )
        return MemoryWriteResult(decision, reason_code, memory_id=record.memory_id)

    def search(
        self,
        *,
        principal_id: str,
        tenant_id: str,
        query: str,
        requested_tenant_id: str | None = None,
        subject_id: str | None = None,
        allowed_subject_ids: list[str] | None = None,
        max_items: int = 5,
        max_context_tokens: int = 256,
    ) -> MemorySearchResult:
        for name, value in {
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "query": query,
        }.items():
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{name} must be a non-empty string")
        if max_items <= 0 or max_context_tokens <= 0:
            raise ContractError("memory search budgets must be positive")
        target_tenant = requested_tenant_id or tenant_id
        if not self.access_policy.has_tenant_access(principal_id, tenant_id):
            self.store.append_audit(
                self._audit(
                    operation="memory.search",
                    decision=MemoryDecision.DENY,
                    reason_code="TENANT_MEMBERSHIP_REQUIRED",
                    actor=principal_id,
                    tenant_id=tenant_id,
                )
            )
            return MemorySearchResult(
                MemoryDecision.DENY,
                "TENANT_MEMBERSHIP_REQUIRED",
                (),
                (),
                0,
            )
        if target_tenant != tenant_id:
            self.store.append_audit(
                self._audit(
                    operation="memory.search",
                    decision=MemoryDecision.DENY,
                    reason_code="CROSS_TENANT_REQUEST_DENIED",
                    actor=principal_id,
                    tenant_id=tenant_id,
                    metadata={"requested_tenant_hash": _content_hash(target_tenant)},
                )
            )
            return MemorySearchResult(
                MemoryDecision.DENY,
                "CROSS_TENANT_REQUEST_DENIED",
                (),
                (),
                0,
            )

        now = self._now()
        rows = self.store.search_rows(
            tenant_id=tenant_id,
            principal_id=principal_id,
            now=now,
            subject_id=subject_id,
        )
        query_terms = _terms(query)
        trusted_resources = set(
            self.access_policy.resource_subjects(principal_id, tenant_id)
        )
        allowed_resources = (
            trusted_resources
            if allowed_subject_ids is None
            else trusted_resources.intersection(allowed_subject_ids)
        )
        ranked: list[tuple[float, MemoryRecord]] = []
        filtered_unauthorized = 0
        for row in rows:
            if (
                row["scope"] == MemoryScope.RESOURCE.value
                and row["subject_id"] not in allowed_resources
            ):
                filtered_unauthorized += 1
                continue
            score = _relevance(query, query_terms, row["search_text"])
            if score > 0:
                ranked.append((score, _record_from_row(row)))
        ranked.sort(key=lambda item: (-item[0], item[1].expires_at, item[1].memory_id))

        selected: list[MemoryRecord] = []
        context_items: list[dict[str, Any]] = []
        estimated_tokens = 0
        for _, record in ranked[:max_items]:
            item_tokens = max(1, math.ceil(len(record.content) / 4))
            if estimated_tokens + item_tokens > max_context_tokens:
                continue
            selected.append(record)
            estimated_tokens += item_tokens
            context_items.append(
                {
                    "memory_id": record.memory_id,
                    "content": record.content,
                    "source_ref": record.source_ref,
                    "version": record.version,
                    "valid_from": record.valid_from,
                    "expires_at": record.expires_at,
                    "memory_type": record.memory_type,
                }
            )

        filtered_expired = sum(
            1
            for row in self.store.expired_rows(
                tenant_id=tenant_id,
                principal_id=principal_id,
                now=now,
            )
            if (
                row["scope"] != MemoryScope.RESOURCE.value
                or row["subject_id"] in allowed_resources
            )
            and _relevance(query, query_terms, row["search_text"]) > 0
        )
        decision = MemoryDecision.ALLOW
        reason_code = "MEMORY_SEARCH_ALLOWED"
        if not selected and filtered_expired:
            decision = MemoryDecision.EXCLUDE
            reason_code = "STALE_MEMORY_FILTERED"
        self.store.append_audit(
            self._audit(
                operation="memory.search",
                decision=decision,
                reason_code=reason_code,
                actor=principal_id,
                tenant_id=tenant_id,
                content_hash=_content_hash(query),
                metadata={
                    "result_count": len(selected),
                    "filtered_expired": filtered_expired,
                    "filtered_unauthorized": filtered_unauthorized,
                    "estimated_tokens": estimated_tokens,
                },
            )
        )
        return MemorySearchResult(
            decision,
            reason_code,
            tuple(selected),
            tuple(context_items),
            estimated_tokens,
            filtered_expired,
            filtered_unauthorized,
        )

    def expire_due(self, *, tenant_id: str, actor: str = "memory-lifecycle") -> int:
        now = self._now()
        records = self.store.due_for_expiry(tenant_id=tenant_id, now=now)
        for record in records:
            self.store.expire_record(
                record,
                self._audit(
                    operation="memory.expire",
                    decision=MemoryDecision.EXCLUDE,
                    reason_code="MEMORY_TTL_EXPIRED",
                    actor=actor,
                    tenant_id=tenant_id,
                    memory_id=record.memory_id,
                    content_hash=record.content_hash,
                    metadata={"expired_at": record.expires_at, "index_removed": True},
                ),
            )
        return len(records)

    def update(
        self,
        memory_id: str,
        candidate: MemoryCandidate,
    ) -> MemoryWriteResult:
        old = self.store.get_record(memory_id)
        if old is None:
            raise ContractError("memory record not found")
        if old.tenant_id != candidate.tenant_id:
            raise ContractError("memory update tenant mismatch")
        if old.subject_id != candidate.subject_id:
            raise ContractError("memory update subject mismatch")
        if old.scope != candidate.scope.value:
            raise ContractError("memory update scope mismatch")
        if old.principal_id != candidate.principal_id:
            raise ContractError("memory update is not authorized")
        authorization_reason = self._write_authorization_failure(candidate)
        if authorization_reason:
            raise ContractError(f"memory update is not authorized: {authorization_reason}")
        now = self._now()
        if old.deleted_at is not None or old.valid_to is not None or old.expires_at <= now:
            raise ContractError("memory record is no longer current")
        decision, reason = self._write_decision(candidate)
        if decision not in {MemoryDecision.ALLOW, MemoryDecision.SCOPED_ALLOW}:
            raise ContractError(f"memory update was not allowed: {reason}")
        new_record = self._record(
            candidate,
            version=old.version + 1,
            valid_from=now,
            supersedes_id=old.memory_id,
        )
        self.store.supersede(
            old,
            new_record,
            self._audit(
                operation="memory.update",
                decision=MemoryDecision.VERSIONED_UPDATE,
                reason_code="MEMORY_VERSION_SUPERSEDED",
                actor=candidate.principal_id,
                tenant_id=candidate.tenant_id,
                memory_id=new_record.memory_id,
                content_hash=new_record.content_hash,
                metadata={"supersedes_id": old.memory_id, "version": new_record.version},
            ),
        )
        return MemoryWriteResult(
            MemoryDecision.VERSIONED_UPDATE,
            "MEMORY_VERSION_SUPERSEDED",
            memory_id=new_record.memory_id,
        )

    def delete(
        self,
        memory_id: str,
        *,
        actor: str,
        tenant_id: str,
        reason: str,
        is_tenant_admin: bool = False,
    ) -> MemoryWriteResult:
        record = self.store.get_record(memory_id)
        if record is None:
            raise ContractError("memory record not found")
        if record.tenant_id != tenant_id:
            raise ContractError("memory delete tenant mismatch")
        if not self.access_policy.has_tenant_access(actor, tenant_id):
            raise ContractError("memory delete tenant membership is required")
        trusted_admin = self.access_policy.is_tenant_admin(actor, tenant_id)
        if is_tenant_admin and not trusted_admin:
            raise ContractError("memory delete tenant admin claim is not trusted")
        if record.principal_id != actor and not trusted_admin:
            raise ContractError("memory delete is not authorized")
        if not isinstance(reason, str) or not reason.strip():
            raise ContractError("delete reason must be non-empty")
        if _contains_secret(reason) or _contains_pii(reason):
            raise ContractError("delete reason must not contain sensitive data")
        deleted_at = self._now()
        records = self.store.subject_records(record)
        self.store.delete_records(
            records,
            actor=actor,
            reason=reason,
            deleted_at=deleted_at,
            audit=self._audit(
                operation="memory.delete",
                decision=MemoryDecision.DELETE_VERIFY,
                reason_code="MEMORY_TOMBSTONED_AND_DEINDEXED",
                actor=actor,
                tenant_id=tenant_id,
                memory_id=memory_id,
                content_hash=record.content_hash,
                metadata={
                    "index_removed": True,
                    "delete_policy": record.delete_policy,
                    "deleted_version_count": len(records),
                },
            ),
        )
        return MemoryWriteResult(
            MemoryDecision.DELETE_VERIFY,
            "MEMORY_TOMBSTONED_AND_DEINDEXED",
            memory_id=memory_id,
        )

    def evaluate_retrieval(
        self,
        cases: list[dict[str, str]],
        *,
        principal_id: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        if not cases:
            raise ContractError("memory retrieval eval requires at least one case")
        started = perf_counter()
        hits = 0
        returned = 0
        tokens = 0
        for case in cases:
            result = self.search(
                principal_id=principal_id,
                tenant_id=tenant_id,
                query=case["query"],
                subject_id=case.get("subject_id"),
            )
            returned += len(result.records)
            tokens += result.estimated_tokens
            if any(case["expected_text"] in record.content for record in result.records):
                hits += 1
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        recall = hits / len(cases)
        precision = hits / returned if returned else 0.0
        return {
            "decision": "compare",
            "case_count": len(cases),
            "with_memory_recall": recall,
            "without_memory_recall": 0.0,
            "quality_delta": recall,
            "precision": precision,
            "estimated_tokens": tokens,
            "latency_ms": elapsed_ms,
            "risk_delta": 0 if precision == 1.0 else returned - hits,
        }

    def _write_decision(
        self,
        candidate: MemoryCandidate,
    ) -> tuple[MemoryDecision, str]:
        if candidate.sensitivity in {MemorySensitivity.SECRET, MemorySensitivity.PII}:
            return MemoryDecision.DENY_AND_REDACT, "SENSITIVE_DATA_REJECTED"
        if _contains_secret(candidate.content) or _contains_pii(candidate.content):
            return MemoryDecision.DENY_AND_REDACT, "SENSITIVE_DATA_REJECTED"
        if candidate.source_kind is MemorySourceKind.MODEL_INFERENCE:
            return MemoryDecision.DENY, "MODEL_INFERENCE_NOT_A_FACT"
        if candidate.source_kind is MemorySourceKind.UNTRUSTED_CONTENT:
            reason = (
                "PERSISTENT_INJECTION_REJECTED"
                if _contains_injection(candidate.content)
                else "UNTRUSTED_CONTENT_REJECTED"
            )
            return MemoryDecision.DENY, reason
        if candidate.scope is MemoryScope.RUN:
            return MemoryDecision.SESSION_ONLY, "RUN_SCOPED_CONTEXT_NOT_PERSISTED"
        if candidate.ttl_seconds is None:
            return MemoryDecision.NEEDS_CONFIRMATION, "RETENTION_POLICY_REQUIRED"
        if candidate.source_kind is MemorySourceKind.USER_STATEMENT:
            if candidate.scope is MemoryScope.USER and candidate.confidence >= 0.8:
                return MemoryDecision.ALLOW, "EXPLICIT_USER_PREFERENCE"
            return MemoryDecision.NEEDS_CONFIRMATION, "USER_FACT_REQUIRES_CONFIRMATION"
        if candidate.source_kind in {
            MemorySourceKind.TOOL_RESULT,
            MemorySourceKind.VERIFIED_EXPERIENCE,
        }:
            if candidate.confidence < 0.8:
                return MemoryDecision.NEEDS_CONFIRMATION, "SOURCE_CONFIDENCE_TOO_LOW"
            if candidate.scope not in {MemoryScope.TENANT, MemoryScope.RESOURCE}:
                return MemoryDecision.DENY, "TRUSTED_FACT_SCOPE_TOO_BROAD"
            if candidate.memory_type is MemoryType.PROCEDURAL and (
                candidate.source_kind is not MemorySourceKind.VERIFIED_EXPERIENCE
            ):
                return MemoryDecision.DENY, "PROCEDURE_REQUIRES_VERIFIED_EXPERIENCE"
            return MemoryDecision.SCOPED_ALLOW, "TRUSTED_SCOPED_FACT"
        return MemoryDecision.NEEDS_CONFIRMATION, "SOURCE_REQUIRES_CONFIRMATION"

    def _write_authorization_failure(self, candidate: MemoryCandidate) -> str | None:
        if not self.access_policy.has_tenant_access(
            candidate.principal_id,
            candidate.tenant_id,
        ):
            return "TENANT_MEMBERSHIP_REQUIRED"
        if candidate.scope is MemoryScope.RESOURCE and (
            candidate.subject_id
            not in self.access_policy.resource_subjects(
                candidate.principal_id,
                candidate.tenant_id,
            )
            and not self.access_policy.is_tenant_admin(
                candidate.principal_id,
                candidate.tenant_id,
            )
        ):
            return "RESOURCE_WRITE_GRANT_REQUIRED"
        if candidate.scope is MemoryScope.TENANT and not self.access_policy.is_tenant_admin(
            candidate.principal_id,
            candidate.tenant_id,
        ):
            return "TENANT_ADMIN_REQUIRED"
        return None

    def _record(
        self,
        candidate: MemoryCandidate,
        *,
        version: int,
        valid_from: str,
        supersedes_id: str | None = None,
    ) -> MemoryRecord:
        if candidate.ttl_seconds is None:
            raise ContractError("persisted memory requires ttl_seconds")
        expires_at = (
            _parse_time(valid_from) + timedelta(seconds=candidate.ttl_seconds)
        ).isoformat()
        return MemoryRecord(
            memory_id=str(uuid4()),
            content=candidate.content.strip(),
            content_hash=_content_hash(candidate.content),
            source_kind=candidate.source_kind.value,
            source_ref=candidate.source_ref,
            tenant_id=candidate.tenant_id,
            principal_id=candidate.principal_id,
            scope=candidate.scope.value,
            subject_id=candidate.subject_id,
            sensitivity=candidate.sensitivity.value,
            memory_type=candidate.memory_type.value,
            confidence=float(candidate.confidence),
            version=version,
            valid_from=valid_from,
            valid_to=None,
            expires_at=expires_at,
            deleted_at=None,
            supersedes_id=supersedes_id,
            delete_policy="owner_or_tenant_admin",
            run_id=candidate.run_id,
            created_at=valid_from,
        )

    def _audit(
        self,
        *,
        operation: str,
        decision: MemoryDecision,
        reason_code: str,
        actor: str,
        tenant_id: str,
        memory_id: str | None = None,
        content_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "event_id": str(uuid4()),
            "operation": operation,
            "decision": decision.value,
            "reason_code": reason_code,
            "actor": actor,
            "tenant_id": tenant_id,
            "memory_id": memory_id,
            "content_hash": content_hash,
            "metadata": metadata or {},
            "created_at": self._now(),
        }

    def _now(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()


def _record_from_row(row: sqlite3.Row) -> MemoryRecord:
    fields = MemoryRecord.__dataclass_fields__
    return MemoryRecord(**{name: row[name] for name in fields})


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _terms(value: str) -> set[str]:
    normalized = _normalize(value)
    words = set(re.findall(r"[a-z0-9_]+", normalized))
    words.update(character for character in normalized if "\u4e00" <= character <= "\u9fff")
    return words


def _relevance(query: str, query_terms: set[str], search_text: str) -> float:
    if _normalize(query) in search_text:
        return 2.0
    if not query_terms:
        return 0.0
    overlap = query_terms & _terms(search_text)
    return len(overlap) / len(query_terms)


SECRET_PATTERNS = (
    re.compile(r"\bsk-[a-z0-9_-]{8,}\b", re.IGNORECASE),
    re.compile(r"\bapi[_ -]?key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bbearer\s+[a-z0-9._-]{8,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
PII_PATTERNS = (
    re.compile(r"\b1[3-9]\d{9}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
)
INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "modify core memory",
    "reveal system prompt",
    "忽略之前",
    "忽略所有规则",
    "修改核心记忆",
    "泄露系统提示词",
)


def _contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def _contains_pii(value: str) -> bool:
    return any(pattern.search(value) for pattern in PII_PATTERNS)


def _contains_injection(value: str) -> bool:
    normalized = value.casefold()
    return any(marker in normalized for marker in INJECTION_MARKERS)
