from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from agent_course.api import create_app
from agent_course.cli import main
from agent_course.foundation import IdempotencyConflict, TicketRepository, TicketService


def test_foundation_idempotency_key_is_bound_to_request(tmp_path) -> None:
    service = TicketService(TicketRepository(tmp_path / "tickets.db"))

    first, first_replayed = service.create_ticket(
        tenant_id="tenant-a",
        title="VPN access is failing",
        idempotency_key="request-0001",
    )
    second, second_replayed = service.create_ticket(
        tenant_id="tenant-a",
        title="VPN access is failing",
        idempotency_key="request-0001",
    )

    assert first_replayed is False
    assert second_replayed is True
    assert second.ticket_id == first.ticket_id

    with pytest.raises(IdempotencyConflict):
        service.create_ticket(
            tenant_id="tenant-a",
            title="A different request",
            idempotency_key="request-0001",
        )


def test_foundation_concurrent_retries_create_one_ticket(tmp_path) -> None:
    service = TicketService(TicketRepository(tmp_path / "concurrent.db"))

    def create_once() -> tuple[str, bool]:
        ticket, replayed = service.create_ticket(
            tenant_id="tenant-a",
            title="Password reset",
            idempotency_key="request-concurrent",
        )
        return ticket.ticket_id, replayed

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: create_once(), range(8)))

    assert len({ticket_id for ticket_id, _ in results}) == 1
    assert sum(not replayed for _, replayed in results) == 1
    assert len(service.list_tickets(tenant_id="tenant-a")) == 1


def test_foundation_http_contract_and_tenant_isolation(tmp_path) -> None:
    with TestClient(create_app(tmp_path / "api.db")) as client:
        headers = {"X-Tenant-ID": "tenant-a", "Idempotency-Key": "request-http-01"}

        created = client.post("/tickets", headers=headers, json={"title": "Cannot connect to VPN"})
        replayed = client.post("/tickets", headers=headers, json={"title": "Cannot connect to VPN"})
        conflict = client.post("/tickets", headers=headers, json={"title": "Different title"})
        unknown_field = client.post(
            "/tickets",
            headers={**headers, "Idempotency-Key": "request-http-02"},
            json={"title": "Cannot connect", "role": "admin"},
        )

        assert created.status_code == 201
        assert created.headers["Idempotency-Replayed"] == "false"
        assert replayed.status_code == 200
        assert replayed.headers["Idempotency-Replayed"] == "true"
        assert replayed.json()["ticket_id"] == created.json()["ticket_id"]
        assert conflict.status_code == 409
        assert unknown_field.status_code == 422

        own_ticket = client.get(
            f"/tickets/{created.json()['ticket_id']}", headers={"X-Tenant-ID": "tenant-a"}
        )
        other_tenant = client.get(
            f"/tickets/{created.json()['ticket_id']}", headers={"X-Tenant-ID": "tenant-b"}
        )
        assert own_ticket.status_code == 200
        assert other_tenant.status_code == 404


def test_foundation_cli_round_trip(tmp_path, monkeypatch, capsys) -> None:
    database = tmp_path / "cli.db"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "agent-course",
            "ticket",
            "--db",
            str(database),
            "create",
            "--tenant",
            "tenant-a",
            "--title",
            "Printer is offline",
            "--idempotency-key",
            "request-cli-01",
        ],
    )
    assert main() == 0
    created = json.loads(capsys.readouterr().out)

    monkeypatch.setattr(
        sys,
        "argv",
        ["agent-course", "ticket", "--db", str(database), "list", "--tenant", "tenant-a"],
    )
    assert main() == 0
    listed = json.loads(capsys.readouterr().out)

    assert created["replayed"] is False
    assert listed["tickets"][0]["ticket_id"] == created["ticket"]["ticket_id"]
    database.unlink()
    assert not database.exists()
