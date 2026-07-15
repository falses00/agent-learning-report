from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field

from .contracts import ContractError
from .foundation import IdempotencyConflict, Ticket, TicketRepository, TicketService


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)


class TicketResponse(BaseModel):
    ticket_id: str
    tenant_id: str
    title: str
    status: str
    created_at: str

    @classmethod
    def from_ticket(cls, ticket: Ticket) -> "TicketResponse":
        return cls(**ticket.to_dict())


def create_app(db_path: str | Path | None = None) -> FastAPI:
    path = str(db_path or os.environ.get("OPSPILOT_DB_PATH", "opspilot-f0.db"))
    repository = TicketRepository(path)
    service = TicketService(repository)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        repository.close()

    app = FastAPI(title="OpsPilot F0 Service", version="1.0.0", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/tickets",
        response_model=TicketResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_ticket(
        payload: TicketCreate,
        response: Response,
        tenant_id: str = Header(alias="X-Tenant-ID", min_length=1),
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=8),
    ) -> TicketResponse:
        try:
            ticket, replayed = service.create_ticket(
                tenant_id=tenant_id,
                title=payload.title,
                idempotency_key=idempotency_key,
            )
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except ContractError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        response.status_code = status.HTTP_200_OK if replayed else status.HTTP_201_CREATED
        response.headers["Idempotency-Replayed"] = str(replayed).lower()
        return TicketResponse.from_ticket(ticket)

    @app.get("/tickets", response_model=list[TicketResponse])
    def list_tickets(
        tenant_id: str = Header(alias="X-Tenant-ID", min_length=1),
    ) -> list[TicketResponse]:
        return [TicketResponse.from_ticket(ticket) for ticket in service.list_tickets(tenant_id=tenant_id)]

    @app.get("/tickets/{ticket_id}", response_model=TicketResponse)
    def get_ticket(
        ticket_id: str,
        tenant_id: str = Header(alias="X-Tenant-ID", min_length=1),
    ) -> TicketResponse:
        ticket = service.get_ticket(tenant_id=tenant_id, ticket_id=ticket_id)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ticket not found")
        return TicketResponse.from_ticket(ticket)

    return app
