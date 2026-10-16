from __future__ import annotations

import os
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infrai_usage import InfraiError, InfraiUsageClient
from .usage_ledger import UsageEvent, UsageLedger


class UsageEventRequest(BaseModel):
    event_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    kind: Literal[
        "digital_asset_delivery",
        "subscriber_update",
        "content_processing",
    ]
    units: Annotated[int, Field(gt=0)]


class MeterResponse(BaseModel):
    event_id: str
    customer_id: str
    recorded: bool
    total_units: int


class CustomerUsageResponse(BaseModel):
    customer_id: str
    usage: dict[str, int]


def create_service(database_path: str | None = None) -> FastAPI:
    ledger = UsageLedger(database_path or os.environ.get("METER_DB", "usage.db"))
    service = FastAPI(title="Creator customer usage meter")

    @service.post("/usage/events", response_model=MeterResponse)
    def meter_usage(request: UsageEventRequest) -> MeterResponse:
        result = ledger.record(UsageEvent(**request.model_dump()))
        return MeterResponse(**result.__dict__)

    @service.get(
        "/customers/{customer_id}/usage",
        response_model=CustomerUsageResponse,
    )
    def customer_usage(customer_id: str) -> CustomerUsageResponse:
        return CustomerUsageResponse(
            customer_id=customer_id,
            usage=ledger.totals(customer_id),
        )

    @service.get("/reconciliation/infrai")
    def infrai_reconciliation() -> dict[str, object]:
        client = InfraiUsageClient()
        try:
            return {"source": "infrai", "timeseries": client.usage_timeseries()}
        except InfraiError as error:
            status = error.status_code if 400 <= error.status_code < 500 else 502
            raise HTTPException(
                status_code=status,
                detail={"code": error.code, "error": error.details},
            ) from error
        finally:
            client.close()

    return service


app = create_service()

